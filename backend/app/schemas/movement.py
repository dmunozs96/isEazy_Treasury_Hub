import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.classification import ClassificationSource


class ClassificationInfo(BaseModel):
    category_code: str
    category_name: str | None
    cash_flow_section: str | None
    subcategory_code: str | None
    source: ClassificationSource
    is_confirmed: bool
    classified_at: datetime
    override_reason: str | None


class MovementResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_short_name: str | None
    bank_account_id: uuid.UUID
    bank_name: str | None
    import_batch_id: uuid.UUID
    value_date: date
    accounting_date: date | None
    amount: Decimal
    currency: str
    balance_after: Decimal | None
    description: str
    counterpart_name: str | None
    counterpart_iban: str | None
    reference: str | None
    is_intercompany: bool
    created_at: datetime
    is_deleted: bool
    classification: ClassificationInfo | None


class ClassificationOverride(BaseModel):
    category_code: str
    subcategory_code: str | None = None
    override_reason: str | None = None
