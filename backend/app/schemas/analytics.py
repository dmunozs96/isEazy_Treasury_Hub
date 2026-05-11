import enum
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CompanyCashPosition(BaseModel):
    company_id: UUID
    company_name: str
    short_name: str
    # Last known balance (from most recent balance_after), else None
    last_balance: Decimal | None
    # Net flow = SUM of all movement amounts (always available)
    net_flow: Decimal
    # True when balance_after data is available for at least one account
    has_balance_data: bool

    model_config = {"from_attributes": True}


class WeeklyCashFlow(BaseModel):
    week_start: date
    week_label: str   # "W20 2026"
    inflow: Decimal   # SUM of positive amounts
    outflow: Decimal  # SUM of negative amounts (negative number)
    net: Decimal

    model_config = {"from_attributes": True}


class CashFlowPeriod(BaseModel):
    key: str
    label: str
    start_date: date
    end_date: date


class CashFlowRow(BaseModel):
    section: str
    category_code: str
    category_name: str
    values: list[Decimal]
    total: Decimal


class CashFlowSectionSummary(BaseModel):
    section: str
    values: list[Decimal]
    total: Decimal


class CashFlowStatement(BaseModel):
    granularity: str
    date_from: date
    date_to: date
    company_id: UUID | None
    include_intercompany: bool
    periods: list[CashFlowPeriod]
    sections: list[CashFlowSectionSummary]
    rows: list[CashFlowRow]
    net_cash_flow: list[Decimal]
    net_cash_flow_total: Decimal
    as_of: date

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    cash_by_company: list[CompanyCashPosition]
    # Sum of last_balance across companies (falls back to net_flow if no balance data)
    total_cash: Decimal
    net_flow_wtd: Decimal           # Week-to-date net movement
    pending_ic_matches: int         # PROPOSED intercompany matches
    in_transit_ic: int              # IN_TRANSIT intercompany matches
    unresolved_ic: int              # UNRESOLVED intercompany matches
    weekly_cash_flow: list[WeeklyCashFlow]  # Last 13 ISO weeks, oldest first
    as_of: date

    model_config = {"from_attributes": True}


# ── Consistency & Completeness Panel (Milestone 1.6b) ─────────────────────


class ImportCoverageStatus(str, enum.Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class AccountImportStatus(BaseModel):
    bank_account_id: UUID
    account_name: str
    bank_name: str
    company_name: str
    short_name: str
    iban_last4: str
    movement_count: int
    earliest_movement: date | None
    latest_movement: date | None
    last_batch_at: datetime | None
    status: ImportCoverageStatus

    model_config = {"from_attributes": True}


class BalanceReconciliation(BaseModel):
    bank_account_id: UUID
    account_name: str
    bank_name: str
    company_name: str
    period_label: str
    opening_balance: Decimal | None
    closing_balance_bank: Decimal | None
    closing_balance_computed: Decimal | None
    delta: Decimal | None
    # "OK" | "WARNING" | "ERROR" | "NO_DATA"
    status: str

    model_config = {"from_attributes": True}


class DataQualityWarning(BaseModel):
    rule: str
    company_name: str
    account_name: str | None
    movement_id: UUID | None
    movement_date: date | None
    movement_amount: Decimal | None
    description: str

    model_config = {"from_attributes": True}


class UnclassifiedRateWarning(BaseModel):
    company_name: str
    total_movements: int
    unclassified_count: int
    unclassified_rate: float

    model_config = {"from_attributes": True}


class ConsistencyReport(BaseModel):
    period_year: int
    period_month: int
    period_label: str
    section_a: list[AccountImportStatus]
    section_b: list[BalanceReconciliation]
    holdco_revenue_warnings: list[DataQualityWarning]
    high_unclassified_companies: list[UnclassifiedRateWarning]
    unresolved_ic_count: int
    in_transit_timeout_count: int
    as_of: date

    model_config = {"from_attributes": True}
