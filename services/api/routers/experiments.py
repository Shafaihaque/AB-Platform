from fastapi import APIRouter, HTTPException
from models.experiment import ExperimentCreate, ExperimentResponse, ExperimentStatusUpdate, VariantCreate, VariantResponse
from db.database import get_pool

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentResponse, status_code=201)
async def create_experiment(body: ExperimentCreate):
    """Creates a new experiment in draft status."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO experiments (name, description)
            VALUES ($1, $2)
            RETURNING *
            """,
            body.name,
            body.description,
        )
    return dict(row)


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments():
    """Returns all experiments, newest first."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM experiments ORDER BY created_at DESC"
        )
    return [dict(row) for row in rows]


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str):
    """Returns a single experiment by ID."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM experiments WHERE id = $1",
            experiment_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return dict(row)


@router.patch("/{experiment_id}/status", response_model=ExperimentResponse)
async def update_experiment_status(experiment_id: str, body: ExperimentStatusUpdate):
    """Updates the status of an experiment (draft, running, paused, stopped)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE experiments
            SET status = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING *
            """,
            body.status,
            experiment_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return dict(row)


@router.get("/{experiment_id}/variants", response_model=list[VariantResponse])
async def list_variants(experiment_id: str):
    """Returns all variants for an experiment."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM variants WHERE experiment_id = $1 ORDER BY created_at ASC",
            experiment_id,
        )
    return [VariantResponse(**dict(row)) for row in rows]


@router.post("/{experiment_id}/variants", response_model=VariantResponse, status_code=201)
async def create_variant(experiment_id: str, body: VariantCreate):
    """Adds a variant to an existing experiment."""
    pool = get_pool()
    async with pool.acquire() as conn:
        experiment = await conn.fetchrow(
            "SELECT id FROM experiments WHERE id = $1",
            experiment_id,
        )
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")

        row = await conn.fetchrow(
            """
            INSERT INTO variants (experiment_id, name, traffic_weight)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            experiment_id,
            body.name,
            body.traffic_weight,
        )
    return VariantResponse(**dict(row))
