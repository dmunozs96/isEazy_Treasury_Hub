from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

MatchStatus = str  # "IN_TRANSIT" | "PROPOSED" | "CONFIRMED" | "REJECTED" | "UNRESOLVED"
MatchMethod = str  # "AUTOMATIC" | "MANUAL"


# ---------------------------------------------------------------------------
# IntercompanyMatch
# ---------------------------------------------------------------------------

class MovementSummary(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_short_name: str | None
    bank_account_id: uuid.UUID
    bank_name: str | None
    value_date: date
    amount: Decimal
    description: str
    counterpart_name: str | None
    counterpart_iban: str | None

    model_config = {"from_attributes": True}


class IntercompanyMatchResponse(BaseModel):
    id: uuid.UUID
    movement_out_id: uuid.UUID
    movement_in_id: uuid.UUID | None
    company_from_id: uuid.UUID
    company_from_name: str | None
    company_to_id: uuid.UUID | None
    company_to_name: str | None
    amount: Decimal
    match_date: date
    status: MatchStatus
    match_method: MatchMethod
    score: Decimal | None
    transit_expires_at: datetime | None
    confirmed_by: str | None
    confirmed_at: datetime | None
    rejection_reason: str | None
    notes: str | None
    created_at: datetime
    # Embedded movement detail (populated by router)
    movement_out: MovementSummary | None = None
    movement_in: MovementSummary | None = None

    model_config = {"from_attributes": True}


class ConfirmMatchRequest(BaseModel):
    notes: str | None = None


class RejectMatchRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class ManualMatchRequest(BaseModel):
    movement_out_id: uuid.UUID
    movement_in_id: uuid.UUID
    notes: str | None = None


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

class ScanResponse(BaseModel):
    new_transit: int
    new_proposed: int
    escalated: int


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class CompanyPairSummary(BaseModel):
    company_from_id: uuid.UUID
    company_from_name: str | None
    company_to_id: uuid.UUID
    company_to_name: str | None
    total_out: Decimal       # total confirmed outflows from A to B
    total_in: Decimal        # total confirmed inflows from B to A (i.e., outflows B→A)
    net: Decimal             # total_out - total_in (net flow from A to B)
    confirmed_count: int


class IntercomparySummaryResponse(BaseModel):
    pairs: list[CompanyPairSummary]
    pending_proposed: int    # matches awaiting human review
    in_transit: int          # single-leg, within transit window
    unresolved: int          # expired IN_TRANSIT requiring investigation


# ---------------------------------------------------------------------------
# ForeignEntity
# ---------------------------------------------------------------------------

class ForeignEntityCreate(BaseModel):
    name: str
    country: str
    known_ibans: list[str] = []
    keyword_patterns: list[str] = []


class ForeignEntityResponse(BaseModel):
    id: uuid.UUID
    name: str
    country: str
    known_ibans: list[str]
    keyword_patterns: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
