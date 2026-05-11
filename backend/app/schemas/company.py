import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyBase(BaseModel):
    name: str
    short_name: str
    tax_id: str | None = None
    is_holding: bool = False
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
