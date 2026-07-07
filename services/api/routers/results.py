import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from scipy.stats import chi2_contingency
from models.experiment import ExperimentResult, VariantResult
from db.database import get_pool
from db.clickhouse import get_clickhouse
import anthropic
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["results"])


def run_stats(variants: list[dict]) -> tuple[float | None, bool, str | None]:
    if len(variants) < 2 or any(v["users"] == 0 for v in variants):
        return None, False, None

    table = [
        [v["conversions"], v["users"] - v["conversions"]]
        for v in variants
    ]

    _, p_value, _, _ = chi2_contingency(table)
    significant = p_value < 0.05
    winner = max(variants, key=lambda v: v["conversion_rate"])["variant_name"] if significant else None
    return round(p_value, 4), significant, winner


async def _fetch_results(experiment_id: str) -> ExperimentResult:
    pool = get_pool()

    async with pool.acquire() as conn:
        experiment = await conn.fetchrow(
            "SELECT id FROM experiments WHERE id = $1", experiment_id
        )
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")

        pg_variants = await conn.fetch(
            "SELECT id, name FROM variants WHERE experiment_id = $1", experiment_id,
        )

    if not pg_variants:
        raise HTTPException(status_code=400, detail="Experiment has no variants")

    variant_map = {str(row["id"]): row["name"] for row in pg_variants}

    ch = get_clickhouse()
    result = ch.query(
        """
        SELECT
            variant_id,
            count(DISTINCT user_id) AS users,
            countIf(event_type = 'conversion') AS conversions
        FROM events
        WHERE experiment_id = {experiment_id:String}
        GROUP BY variant_id
        """,
        parameters={"experiment_id": experiment_id},
    )

    variant_results = []
    for row in result.named_results():
        vid = row["variant_id"]
        users = row["users"]
        conversions = row["conversions"]
        variant_results.append(VariantResult(
            variant_id=vid,
            variant_name=variant_map.get(vid, "unknown"),
            users=users,
            conversions=conversions,
            conversion_rate=round(conversions / users, 4) if users > 0 else 0.0,
        ))

    p_value, significant, winner = run_stats([v.model_dump() for v in variant_results])

    return ExperimentResult(
        experiment_id=experiment_id,
        variants=variant_results,
        p_value=p_value,
        significant=significant,
        winner=winner,
    )


@router.get("/results/{experiment_id}", response_model=ExperimentResult)
async def get_results(experiment_id: str):
    return await _fetch_results(experiment_id)


class InterpretationResponse(BaseModel):
    interpretation: str


@router.get("/results/{experiment_id}/interpret", response_model=InterpretationResponse)
async def interpret_results(experiment_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        experiment = await conn.fetchrow(
            "SELECT name, description FROM experiments WHERE id = $1", experiment_id
        )
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")

    result = await _fetch_results(experiment_id)

    variant_lines = "\n".join(
        f"  - {v.variant_name}: {v.users} users, {v.conversions} conversions, "
        f"{(v.conversion_rate * 100):.1f}% conversion rate"
        for v in result.variants
    )

    prompt = f"""You are an experimentation analyst. Interpret the following A/B test results and give a clear, concise recommendation.

Experiment: {experiment["name"]}
Description: {experiment["description"] or "No description provided"}

Variants:
{variant_lines}

Statistical significance: {"Yes" if result.significant else "No"} (p-value: {result.p_value if result.p_value is not None else "N/A"})
Winner: {result.winner or "None (not significant)"}

Write 2-3 sentences max. State what the data shows, whether it's significant, and give a clear ship / don't ship / keep running recommendation. Be direct — no fluff. Plain text only, no markdown."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    return InterpretationResponse(interpretation=message.content[0].text)
