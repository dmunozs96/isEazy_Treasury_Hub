import uuid
from datetime import datetime

from pydantic import BaseModel


class BankAccountResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str | None = None
    company_short_name: str | None = None
    bank_name: str
    account_name: str
    iban: str
    currency: str
    is_internal: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
