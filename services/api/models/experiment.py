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