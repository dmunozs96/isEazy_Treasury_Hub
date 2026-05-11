import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.import_batch import ImportStatus


class ImportBatchResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    bank_account_id: uuid.UUID
    filename: str
    file_hash: str
    file_format: str
    status: ImportStatus
    row_count: int | None
    imported_count: int
    error_count: int
    error_log: list
    imported_by: str
    imported_at: datetime
    processed_at: datetime | None
    notes: str | None

    model_config = {"from_attributes": True}


class ImportBatchCreate(BaseModel):
    bank_account_id: uuid.UUID
    notes: str | None = None
