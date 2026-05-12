import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bank_account import BankAccount
from app.models.company import Company
from app.schemas.bank_account import BankAccountResponse

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])


@router.get("/", response_model=list[BankAccountResponse])
async def list_bank_accounts(
    company_id: uuid.UUID | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            BankAccount,
            Company.name.label("company_name"),
            Company.short_name.label("company_short_name"),
        )
        .join(Company, BankAccount.company_id == Company.id)
        .order_by(Company.short_name, BankAccount.bank_name, BankAccount.account_name)
    )
    if company_id:
        stmt = stmt.where(BankAccount.company_id == company_id)
    if active_only:
        stmt = stmt.where(BankAccount.is_active.is_(True), Company.is_active.is_(True))

    rows = (await db.execute(stmt)).all()
    return [
        BankAccountResponse.model_validate(
            {
                **account.__dict__,
                "company_name": company_name,
                "company_short_name": company_short_name,
            }
        )
        for account, company_name, company_short_name in rows
    ]
