from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

#Request models

class ExperimentCreate(BaseModel):
    name: str
    description: str | None = None


#Response models

class ExperimentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

class ExperimentStatusUpdate(BaseModel):
    status: str


class VariantCreate(BaseModel):
    name: str
    traffic_weight: int = 50

class VariantResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    name: str
    traffic_weight: int
    created_at: datetime


# --- Results models ---

class VariantResult(BaseModel):
    variant_id: str
    variant_name: str
    users: int
    conversions: int
    conversion_rate: float

class ExperimentResult(BaseModel):
    experiment_id: str
    variants: list[VariantResult]
    p_value: float | None
    significant: bool
    winner: str | None