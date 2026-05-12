import uuid
import re
import unicodedata

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bank_account import BankAccount
from app.models.company import Company
from app.models.import_batch import ImportBatch
from app.schemas.import_batch import ImportBatchResponse
from app.services.import_engine.detector import detect_parser
from app.services.import_engine.import_service import run_import

router = APIRouter(prefix="/imports", tags=["imports"])

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

_COMPANY_ALIASES = {
    "AUTHOR": ["author", "iseazy", "is easy"],
    "BPO": ["bpo", "bizpills", "bizpills group"],
    "ENGAGE": ["engage"],
    "FACTORY": ["factory"],
    "LMS": ["lms"],
    "SKILLS": ["skills"],
}

_BANK_ALIASES = {
    "ABANCA": ["abanca"],
    "BANCA MARCH": ["banca march", "bancamarch"],
    "BANKINTER": ["bankinter"],
    "BBVA": ["bbva"],
    "CAIXABANK": ["caixa", "caixabank", "la caixa"],
    "CAIXA": ["caixa", "caixabank", "la caixa"],
    "CAJAMAR": ["cajamar"],
    "DEUTSCHE": ["deutsche", "deustche"],
    "DEUTSCHE BANK": ["deutsche", "deustche", "deutsche bank"],
    "EUROCAJA": ["eurocaja", "eurocaja rural"],
    "IBERCAJA": ["ibercaja"],
    "RURALVIA": ["ruralvia", "rural via"],
    "SABADELL": ["sabadell"],
    "SANTANDER": ["santander"],
}


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFD", value.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _bank_aliases(bank_name: str) -> list[str]:
    normalized_bank = bank_name.upper()
    aliases = [bank_name]
    for key, values in _BANK_ALIASES.items():
        if key in normalized_bank:
            aliases.extend(values)
    return [_normalize(alias) for alias in aliases if _normalize(alias)]


def _company_aliases(short_name: str | None, company_name: str | None) -> list[str]:
    aliases = [short_name or "", company_name or ""]
    aliases.extend(_COMPANY_ALIASES.get((short_name or "").upper(), []))
    return [_normalize(alias) for alias in aliases if _normalize(alias)]


def _digits(value: str) -> list[str]:
    return re.findall(r"\d{3,4}", value)


def _score_account(filename: str, parser_bank_name: str, row) -> int:
    normalized_name = _normalize(filename)
    file_digits = _digits(filename)
    iban_digits = re.sub(r"\D", "", row.iban or "")
    account_digits = _digits(row.account_name or "")
    bank_hit = any(alias in normalized_name for alias in _bank_aliases(row.bank_name))
    parser_bank_hit = any(alias in normalized_name for alias in _bank_aliases(parser_bank_name))
    company_hit = any(
        alias in normalized_name
        for alias in _company_aliases(row.company_short_name, row.company_name)
    )
    number_hit = any(
        digit in file_digits
        for digit in [iban_digits[-4:], *account_digits]
        if digit
    )

    score = 0
    if bank_hit:
        score += 40
    if parser_bank_hit:
        score += 30
    if company_hit:
        score += 35
    if number_hit:
        score += 60
    if (bank_hit or parser_bank_hit) and number_hit:
        score += 35
    if company_hit and number_hit:
        score += 25
    if (bank_hit or parser_bank_hit) and company_hit:
        score += 20
    return score


async def _resolve_account_from_filename(
    db: AsyncSession,
    *,
    filename: str,
) -> BankAccount:
    parser = detect_parser(filename)
    rows = (
        await db.execute(
            select(
                BankAccount,
                Company.name.label("company_name"),
                Company.short_name.label("company_short_name"),
            )
            .join(Company, BankAccount.company_id == Company.id)
            .where(BankAccount.is_active.is_(True), Company.is_active.is_(True))
        )
    ).all()

    scored = [
        (account, _score_account(filename, parser.bank_name, row))
        for account, company_name, company_short_name in rows
        for row in [
            type(
                "AccountMatchRow",
                (),
                {
                    "bank_name": account.bank_name,
                    "account_name": account.account_name,
                    "iban": account.iban,
                    "company_name": company_name,
                    "company_short_name": company_short_name,
                },
            )()
        ]
    ]
    scored.sort(key=lambda item: item[1], reverse=True)

    if not scored or scored[0][1] < 65:
        raise HTTPException(
            status_code=422,
            detail=f"Could not auto-detect bank account for '{filename}'",
        )
    if len(scored) > 1 and scored[0][1] == scored[1][1]:
        raise HTTPException(
            status_code=422,
            detail=f"Ambiguous bank account for '{filename}'",
        )
    return scored[0][0]


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


@router.post("/auto", response_model=ImportBatchResponse, status_code=201)
async def create_auto_import(
    file: UploadFile,
    notes: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Upload a bank statement and infer its bank account from the filename."""
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    filename = file.filename or "upload"
    account = await _resolve_account_from_filename(db, filename=filename)

    try:
        batch = await run_import(
            session=db,
            file_content=content,
            filename=filename,
            bank_account_id=account.id,
            company_id=account.company_id,
            imported_by="system",
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
