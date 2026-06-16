import hashlib
from fastapi import APIRouter, HTTPException
from db.database import get_pool

router = APIRouter(tags=["assignment"])


def get_variant_for_user(user_id: str, experiment_id: str, variants: list[dict]) -> dict:
    """Deterministically maps a user to a variant using consistent hashing.

    Same user + same experiment always returns the same variant — no randomness per request.
    Uses MD5 for even distribution across buckets (not for security).
    """
    key = f"{user_id}:{experiment_id}".encode("utf-8")
    bucket = int(hashlib.md5(key).hexdigest(), 16) % 100

    cumulative = 0
    for variant in variants:
        cumulative += variant["traffic_weight"]
        if bucket < cumulative:
            return variant

    return variants[-1]


@router.get("/assign")
async def assign_user(experiment_id: str, user_id: str):
    """Returns the variant a user is assigned to for a given experiment."""
    pool = get_pool()
    async with pool.acquire() as conn:
        experiment = await conn.fetchrow(
            "SELECT * FROM experiments WHERE id = $1",
            experiment_id,
        )
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        if experiment["status"] != "running":
            raise HTTPException(status_code=400, detail="Experiment is not running")

        variants = await conn.fetch(
            "SELECT * FROM variants WHERE experiment_id = $1 ORDER BY created_at ASC",
            experiment_id,
        )
        if not variants:
            raise HTTPException(status_code=400, detail="Experiment has no variants")

    variants = [dict(v) for v in variants]
    assigned = get_variant_for_user(user_id, experiment_id, variants)

    return {
        "user_id": user_id,
        "experiment_id": experiment_id,
        "variant_id": str(assigned["id"]),
        "variant_name": assigned["name"],
    }
