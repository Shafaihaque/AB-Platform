from fastapi import APIRouter, HTTPException
from scipy.stats import chi2_contingency
from models.experiment import ExperimentResult, VariantResult
from db.database import get_pool
from db.clickhouse import get_clickhouse

router = APIRouter(tags=["results"])


def run_stats(variants: list[dict]) -> tuple[float | None, bool, str | None]:
    """Runs a chi-squared test and returns (p_value, significant, winner).

    Returns None values if there isn't enough data to run the test.
    p_value < 0.05 means 95% confidence the result is not random noise.
    """
    if len(variants) < 2 or any(v["users"] == 0 for v in variants):
        return None, False, None

    # Each row is [conversions, non-conversions] — chi2 needs both sides
    table = [
        [v["conversions"], v["users"] - v["conversions"]]
        for v in variants
    ]

    _, p_value, _, _ = chi2_contingency(table)
    significant = p_value < 0.05
    winner = max(variants, key=lambda v: v["conversion_rate"])["variant_name"] if significant else None
    return round(p_value, 4), significant, winner


@router.get("/results/{experiment_id}", response_model=ExperimentResult)
async def get_results(experiment_id: str):
    """Returns per-variant conversion stats and significance for an experiment."""
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

    # Maps variant UUID → name so ClickHouse rows can be matched back to variant names
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
