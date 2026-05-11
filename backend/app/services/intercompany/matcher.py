"""
Intercompany matching engine.

Algorithm:
1. Escalate expired IN_TRANSIT → UNRESOLVED
2. Resolve existing IN_TRANSIT records by searching for their second leg
3. Scan remaining unmatched movements in internal accounts:
   - If a valid pair is found → create PROPOSED
   - If movement counterpart_iban is a known internal IBAN but second leg not yet imported → IN_TRANSIT

Only movements in internal bank accounts are candidates.
INT_INTERCOMPANY_FOREIGN movements are never matched here.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank_account import BankAccount
from app.models.company import Company
from app.models.intercompany import IntercompanyMatch, MatchMethod, MatchStatus
from app.models.movement import Movement

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AMOUNT_TOLERANCE = Decimal("2.00")     # €2 tolerance for bank-fee rounding
DATE_TOLERANCE_DAYS = 3               # business days
TRANSIT_WINDOW_DAYS = 5              # business days before IN_TRANSIT → UNRESOLVED


# ---------------------------------------------------------------------------
# Business day helpers
# ---------------------------------------------------------------------------

def _add_business_days(d: date, n: int) -> date:
    current = d
    added = 0
    while added < n:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def _business_days_between(d1: date, d2: date) -> int:
    if d1 == d2:
        return 0
    if d1 > d2:
        d1, d2 = d2, d1
    count = 0
    current = d1
    while current < d2:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_match(m_out: Movement, m_in: Movement) -> Decimal:
    """Return a 0.0–1.0 composite score. Higher = better match."""
    score = Decimal("0")

    # Amount match component (0.0–0.4)
    diff = abs(abs(m_out.amount) - abs(m_in.amount))
    if diff == 0:
        score += Decimal("0.4")
    elif diff <= AMOUNT_TOLERANCE:
        score += Decimal("0.2")

    # Date proximity component (0.0–0.4)
    days_apart = _business_days_between(m_out.value_date, m_in.value_date)
    if days_apart == 0:
        score += Decimal("0.4")
    elif days_apart <= DATE_TOLERANCE_DAYS:
        remaining = Decimal(DATE_TOLERANCE_DAYS - days_apart) / Decimal(DATE_TOLERANCE_DAYS)
        score += remaining * Decimal("0.4")

    # Counterpart IBAN cross-identification (0.0–0.2)
    if m_out.counterpart_iban and m_in.counterpart_iban:
        score += Decimal("0.2")

    return score


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _load_internal_accounts(
    db: AsyncSession,
) -> tuple[dict[str, object], set[object]]:
    """Return (iban→company_id dict, account_id set) for all active internal accounts."""
    result = await db.execute(
        select(BankAccount.iban, BankAccount.id, BankAccount.company_id).where(
            BankAccount.is_internal == True,
            BankAccount.is_active == True,
        )
    )
    rows = result.all()
    iban_to_company: dict[str, object] = {r.iban: r.company_id for r in rows}
    account_ids: set[object] = {r.id for r in rows}
    return iban_to_company, account_ids


def _active_match_subqueries(db: AsyncSession):
    """Return (already_out_sq, already_in_sq) scalar subqueries for non-REJECTED matches."""
    active_statuses = [MatchStatus.IN_TRANSIT, MatchStatus.PROPOSED, MatchStatus.CONFIRMED]
    already_out_sq = select(IntercompanyMatch.movement_out_id).where(
        IntercompanyMatch.status.in_(active_statuses)
    )
    already_in_sq = select(IntercompanyMatch.movement_in_id).where(
        IntercompanyMatch.status.in_(active_statuses),
        IntercompanyMatch.movement_in_id.is_not(None),
    )
    return already_out_sq, already_in_sq


# ---------------------------------------------------------------------------
# Step 1 — Escalate expired IN_TRANSIT
# ---------------------------------------------------------------------------

async def _escalate_expired_transit(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(IntercompanyMatch).where(
            IntercompanyMatch.status == MatchStatus.IN_TRANSIT,
            IntercompanyMatch.transit_expires_at <= now,
        )
    )
    expired = result.scalars().all()
    for match in expired:
        match.status = MatchStatus.UNRESOLVED
    return len(expired)


# ---------------------------------------------------------------------------
# Step 2 — Resolve existing IN_TRANSIT records
# ---------------------------------------------------------------------------

async def _resolve_transit_matches(
    db: AsyncSession,
    account_ids: set[object],
) -> int:
    """Try to find the missing second leg for each IN_TRANSIT match."""
    result = await db.execute(
        select(IntercompanyMatch).where(
            IntercompanyMatch.status == MatchStatus.IN_TRANSIT
        )
    )
    in_transit = result.scalars().all()
    if not in_transit:
        return 0

    already_out_sq, already_in_sq = _active_match_subqueries(db)
    resolved = 0

    for match in in_transit:
        known_result = await db.execute(
            select(Movement).where(Movement.id == match.movement_out_id)
        )
        known = known_result.scalar_one_or_none()
        if not known:
            continue

        is_outflow = known.amount < 0
        min_abs = abs(known.amount) - AMOUNT_TOLERANCE
        max_abs = abs(known.amount) + AMOUNT_TOLERANCE

        # Build amount filter for the opposite sign
        if is_outflow:
            amount_filter = and_(Movement.amount >= min_abs, Movement.amount <= max_abs)
        else:
            amount_filter = and_(Movement.amount >= -max_abs, Movement.amount <= -min_abs)

        candidates_result = await db.execute(
            select(Movement).where(
                Movement.is_deleted == False,
                Movement.bank_account_id.in_(account_ids),
                amount_filter,
                Movement.id.not_in(already_out_sq),
                Movement.id.not_in(already_in_sq),
            )
        )
        candidates: Sequence[Movement] = candidates_result.scalars().all()

        valid = [
            c for c in candidates
            if _business_days_between(known.value_date, c.value_date) <= DATE_TOLERANCE_DAYS
        ]
        if not valid:
            continue

        # Pick highest-scoring candidate
        if is_outflow:
            valid.sort(key=lambda c: _score_match(known, c), reverse=True)
            m_out, m_in = known, valid[0]
        else:
            valid.sort(key=lambda c: _score_match(c, known), reverse=True)
            m_out, m_in = valid[0], known

        match.movement_out_id = m_out.id
        match.movement_in_id = m_in.id
        match.company_from_id = m_out.company_id
        match.company_to_id = m_in.company_id
        match.amount = abs(m_out.amount)
        match.match_date = m_out.value_date
        match.status = MatchStatus.PROPOSED
        match.score = _score_match(m_out, m_in)
        match.transit_expires_at = None
        resolved += 1

    return resolved


# ---------------------------------------------------------------------------
# Step 3 — Scan for new matches among unmatched candidates
# ---------------------------------------------------------------------------

async def _scan_new_matches(
    db: AsyncSession,
    iban_to_company: dict[str, object],
    account_ids: set[object],
) -> tuple[int, int]:
    """
    Scan unmatched movements in internal accounts.
    Returns (new_transit_count, new_proposed_count).
    """
    already_out_sq, already_in_sq = _active_match_subqueries(db)

    result = await db.execute(
        select(Movement).where(
            Movement.is_deleted == False,
            Movement.bank_account_id.in_(account_ids),
            Movement.id.not_in(already_out_sq),
            Movement.id.not_in(already_in_sq),
        )
    )
    candidates: list[Movement] = list(result.scalars().all())

    new_proposed = 0
    new_transit = 0
    processed_ids: set[object] = set()

    for movement in candidates:
        if movement.id in processed_ids:
            continue

        is_outflow = movement.amount < 0
        min_abs = abs(movement.amount) - AMOUNT_TOLERANCE
        max_abs = abs(movement.amount) + AMOUNT_TOLERANCE

        # Find a matching counterpart among remaining candidates
        counterparts = [
            c for c in candidates
            if c.id != movement.id
            and c.id not in processed_ids
            and (c.amount > 0 if is_outflow else c.amount < 0)
            and min_abs <= abs(c.amount) <= max_abs
            and _business_days_between(movement.value_date, c.value_date) <= DATE_TOLERANCE_DAYS
        ]

        if counterparts:
            if is_outflow:
                counterparts.sort(key=lambda c: _score_match(movement, c), reverse=True)
                m_out, m_in = movement, counterparts[0]
            else:
                counterparts.sort(key=lambda c: _score_match(c, movement), reverse=True)
                m_out, m_in = counterparts[0], movement

            match = IntercompanyMatch(
                movement_out_id=m_out.id,
                movement_in_id=m_in.id,
                company_from_id=m_out.company_id,
                company_to_id=m_in.company_id,
                amount=abs(m_out.amount),
                match_date=m_out.value_date,
                status=MatchStatus.PROPOSED,
                match_method=MatchMethod.AUTOMATIC,
                score=_score_match(m_out, m_in),
            )
            db.add(match)
            processed_ids.add(m_out.id)
            processed_ids.add(m_in.id)
            new_proposed += 1

        else:
            # No pair found — create IN_TRANSIT only if counterpart_iban is a known internal IBAN
            if movement.counterpart_iban and movement.counterpart_iban in iban_to_company:
                company_to_id = iban_to_company[movement.counterpart_iban]
                expires_on = _add_business_days(movement.value_date, TRANSIT_WINDOW_DAYS)
                transit_expires_at = datetime(
                    expires_on.year, expires_on.month, expires_on.day, tzinfo=timezone.utc
                )

                match = IntercompanyMatch(
                    movement_out_id=movement.id,
                    movement_in_id=None,
                    company_from_id=movement.company_id,
                    company_to_id=company_to_id,
                    amount=abs(movement.amount),
                    match_date=movement.value_date,
                    status=MatchStatus.IN_TRANSIT,
                    match_method=MatchMethod.AUTOMATIC,
                    score=None,
                    transit_expires_at=transit_expires_at,
                )
                db.add(match)
                processed_ids.add(movement.id)
                new_transit += 1

    return new_transit, new_proposed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def scan_for_matches(db: AsyncSession) -> dict:
    """
    Full scan: escalate expired IN_TRANSIT, resolve existing IN_TRANSIT,
    then find new matches among unmatched movements.
    Returns stats dict with keys: escalated, new_transit, new_proposed.
    """
    iban_to_company, account_ids = await _load_internal_accounts(db)

    escalated = await _escalate_expired_transit(db)
    resolved_transit = await _resolve_transit_matches(db, account_ids)
    new_transit, new_proposed = await _scan_new_matches(db, iban_to_company, account_ids)

    await db.commit()

    return {
        "new_transit": new_transit,
        "new_proposed": new_proposed + resolved_transit,
        "escalated": escalated,
    }
