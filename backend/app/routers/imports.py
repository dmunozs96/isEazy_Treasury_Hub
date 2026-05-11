import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bank_account import BankAccount
from app.models.import_batch import ImportBatch
from app.schemas.import_batch import ImportBatchResponse
from app.services.import_engine.import_service import run_import

router = APIRouter(prefix="/imports", tags=["imports"])

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/", response_model=ImportBatchResponse, status_code=201)
async def create_import(
    file: UploadFile,
    bank_account_id: uuid.UUID = Form(...),
    notes: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Upload a bank statement file and trigger the import pipeline."""
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    # Resolve bank account → company
    account = await db.scalar(
        select(BankAccount).where(BankAccount.id == bank_account_id)
    )
    if not account:
        raise HTTPException(status_code=404, detail="BankAccount not found")

    filename = file.filename or "upload"
    try:
        batch = await run_import(
            session=db,
            file_content=content,
            filename=filename,
            bank_account_id=account.id,
            company_id=account.company_id,
            imported_by="system",  # Phase 1: no auth
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return batch


@router.get("/", response_model=list[ImportBatchResponse])
async def list_imports(
    company_id: uuid.UUID | None = None,
    bank_account_id: uuid.UUID | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List import batches, optionally filtered by company or account."""
    stmt = select(ImportBatch).order_by(ImportBatch.imported_at.desc()).limit(limit)
    if company_id:
        stmt = stmt.where(ImportBatch.company_id == company_id)
    if bank_account_id:
        stmt = stmt.where(ImportBatch.bank_account_id == bank_account_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{batch_id}", response_model=ImportBatchResponse)
async def get_import(batch_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single import batch by ID."""
    batch = await db.scalar(
        select(ImportBatch).where(ImportBatch.id == batch_id)
    )
    if not batch:
        raise HTTPException(status_code=404, detail="ImportBatch not found")
    return batch
