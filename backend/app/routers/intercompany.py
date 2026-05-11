from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bank_account import BankAccount
from app.models.company import Company
from app.models.intercompany import ForeignEntity, IntercompanyMatch, MatchMethod, MatchStatus
from app.models.movement import Movement
from app.schemas.intercompany import (
    ConfirmMatchRequest,
    ForeignEntityCreate,
    ForeignEntityResponse,
    IntercompanyMatchResponse,
    IntercomparySummaryResponse,
    ManualMatchRequest,
    MovementSummary,
    RejectMatchRequest,
    ScanResponse,
    CompanyPairSummary,
)
from app.services.intercompany.matcher import scan_for_matches

router = APIRouter(prefix="/intercompany", tags=["intercompany"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _build_movement_summary(db: AsyncSession, movement_id: uuid.UUID | None) -> MovementSummary | None:
    if movement_id is None:
        return None
    result = await db.execute(
        select(
            Movement.id,
            Movement.company_id,
            Company.short_name.label("company_short_name"),
            Movement.bank_account_id,
            BankAccount.bank_name.label("bank_name"),
            Movement.value_date,
            Movement.amount,
            Movement.description,
            Movement.counterpart_name,
            Movement.counterpart_iban,
        )
        .join(Company, Company.id == Movement.company_id)
        .join(BankAccount, BankAccount.id == Movement.bank_account_id)
        .where(Movement.id == movement_id)
    )
    row = result.one_or_none()
    if not row:
        return None
    return MovementSummary(
        id=row.id,
        company_id=row.company_id,
        company_short_name=row.company_short_name,
        bank_account_id=row.bank_account_id,
        bank_name=row.bank_name,
        value_date=row.value_date,
        amount=row.amount,
        description=row.description,
        counterpart_name=row.counterpart_name,
        counterpart_iban=row.counterpart_iban,
    )


async def _get_company_name(db: AsyncSession, company_id: uuid.UUID | None) -> str | None:
    if company_id is None:
        return None
    result = await db.execute(select(Company.short_name).where(Company.id == company_id))
    return result.scalar_one_or_none()


async def _enrich_match(db: AsyncSession, match: IntercompanyMatch) -> IntercompanyMatchResponse:
    company_from_name = await _get_company_name(db, match.company_from_id)
    company_to_name = await _get_company_name(db, match.company_to_id)
    movement_out = await _build_movement_summary(db, match.movement_out_id)
    movement_in = await _build_movement_summary(db, match.movement_in_id)

    return IntercompanyMatchResponse(
        id=match.id,
        movement_out_id=match.movement_out_id,
        movement_in_id=match.movement_in_id,
        company_from_id=match.company_from_id,
        company_from_name=company_from_name,
        company_to_id=match.company_to_id,
        company_to_name=company_to_name,
        amount=match.amount,
        match_date=match.match_date,
        status=match.status.value,
        match_method=match.match_method.value,
        score=match.score,
        transit_expires_at=match.transit_expires_at,
        confirmed_by=match.confirmed_by,
        confirmed_at=match.confirmed_at,
        rejection_reason=match.rejection_reason,
        notes=match.notes,
        created_at=match.created_at,
        movement_out=movement_out,
        movement_in=movement_in,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/matches", response_model=list[IntercompanyMatchResponse])
async def list_matches(
    status: str | None = Query(None, description="Filter by status"),
    company_id: uuid.UUID | None = Query(None),
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if status:
        try:
            filters.append(IntercompanyMatch.status == MatchStatus(status))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid status: {status}")
    if company_id:
        filters.append(
            (IntercompanyMatch.company_from_id == company_id)
            | (IntercompanyMatch.company_to_id == company_id)
        )
    if date_from:
        filters.append(IntercompanyMatch.match_date >= date_from)
    if date_to:
        filters.append(IntercompanyMatch.match_date <= date_to)

    result = await db.execute(
        select(IntercompanyMatch)
        .where(*filters)
        .order_by(IntercompanyMatch.created_at.desc())
    )
    matches = result.scalars().all()
    return [await _enrich_match(db, m) for m in matches]


@router.get("/matches/{match_id}", response_model=IntercompanyMatchResponse)
async def get_match(match_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IntercompanyMatch).where(IntercompanyMatch.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return await _enrich_match(db, match)


@router.post("/matches/{match_id}/confirm", response_model=IntercompanyMatchResponse)
async def confirm_match(
    match_id: uuid.UUID,
    body: ConfirmMatchRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IntercompanyMatch).where(IntercompanyMatch.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status not in (MatchStatus.PROPOSED, MatchStatus.IN_TRANSIT):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot confirm a match in status {match.status.value}",
        )
    if match.movement_in_id is None:
        raise HTTPException(
            status_code=409,
            detail="Cannot confirm an IN_TRANSIT match — second leg not yet found",
        )

    match.status = MatchStatus.CONFIRMED
    match.confirmed_by = "admin"
    match.confirmed_at = datetime.now(timezone.utc)
    if body.notes:
        match.notes = body.notes

    # Mark both movements as intercompany and link them to this match
    for mvt_id in (match.movement_out_id, match.movement_in_id):
        mvt_result = await db.execute(select(Movement).where(Movement.id == mvt_id))
        mvt = mvt_result.scalar_one_or_none()
        if mvt:
            mvt.is_intercompany = True
            mvt.intercompany_match_id = match.id

    await db.commit()
    await db.refresh(match)
    return await _enrich_match(db, match)


@router.post("/matches/{match_id}/reject", response_model=IntercompanyMatchResponse)
async def reject_match(
    match_id: uuid.UUID,
    body: RejectMatchRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IntercompanyMatch).where(IntercompanyMatch.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status == MatchStatus.CONFIRMED:
        raise HTTPException(status_code=409, detail="Cannot reject an already confirmed match")

    match.status = MatchStatus.REJECTED
    match.rejection_reason = body.reason

    # Restore movements to non-intercompany if they were marked
    for mvt_id in filter(None, (match.movement_out_id, match.movement_in_id)):
        mvt_result = await db.execute(select(Movement).where(Movement.id == mvt_id))
        mvt = mvt_result.scalar_one_or_none()
        if mvt and mvt.intercompany_match_id == match.id:
            mvt.is_intercompany = False
            mvt.intercompany_match_id = None

    await db.commit()
    await db.refresh(match)
    return await _enrich_match(db, match)


@router.post("/matches/manual", response_model=IntercompanyMatchResponse)
async def create_manual_match(
    body: ManualMatchRequest,
    db: AsyncSession = Depends(get_db),
):
    # Validate both movements exist
    out_result = await db.execute(select(Movement).where(Movement.id == body.movement_out_id))
    m_out = out_result.scalar_one_or_none()
    if not m_out:
        raise HTTPException(status_code=404, detail="movement_out_id not found")

    in_result = await db.execute(select(Movement).where(Movement.id == body.movement_in_id))
    m_in = in_result.scalar_one_or_none()
    if not m_in:
        raise HTTPException(status_code=404, detail="movement_in_id not found")

    # Ensure neither movement is already in an active match
    active_statuses = [MatchStatus.IN_TRANSIT, MatchStatus.PROPOSED, MatchStatus.CONFIRMED]
    for mvt_id in (body.movement_out_id, body.movement_in_id):
        existing = await db.execute(
            select(IntercompanyMatch).where(
                (IntercompanyMatch.movement_out_id == mvt_id)
                | (IntercompanyMatch.movement_in_id == mvt_id),
                IntercompanyMatch.status.in_(active_statuses),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Movement {mvt_id} is already in an active match",
            )

    match = IntercompanyMatch(
        movement_out_id=body.movement_out_id,
        movement_in_id=body.movement_in_id,
        company_from_id=m_out.company_id,
        company_to_id=m_in.company_id,
        amount=abs(m_out.amount),
        match_date=m_out.value_date,
        status=MatchStatus.PROPOSED,
        match_method=MatchMethod.MANUAL,
        notes=body.notes,
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return await _enrich_match(db, match)


@router.post("/scan", response_model=ScanResponse)
async def trigger_scan(db: AsyncSession = Depends(get_db)):
    """Run the intercompany matching scan over all unmatched movements."""
    stats = await scan_for_matches(db)
    return ScanResponse(**stats)


@router.get("/summary", response_model=IntercomparySummaryResponse)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Return net intercompany positions per company pair (confirmed matches only)."""
    confirmed_result = await db.execute(
        select(IntercompanyMatch).where(
            IntercompanyMatch.status == MatchStatus.CONFIRMED
        )
    )
    confirmed = confirmed_result.scalars().all()

    # Aggregate by (company_from, company_to) pair
    pairs: dict[tuple, dict] = {}
    for m in confirmed:
        key = (m.company_from_id, m.company_to_id)
        if key not in pairs:
            pairs[key] = {"total_out": Decimal("0"), "confirmed_count": 0}
        pairs[key]["total_out"] += m.amount
        pairs[key]["confirmed_count"] += 1

    # Build pair summaries with net calculation
    pair_summaries: list[CompanyPairSummary] = []
    seen_pairs: set[tuple] = set()

    for (from_id, to_id), data in pairs.items():
        if (from_id, to_id) in seen_pairs:
            continue
        seen_pairs.add((from_id, to_id))
        seen_pairs.add((to_id, from_id))

        reverse_data = pairs.get((to_id, from_id), {"total_out": Decimal("0"), "confirmed_count": 0})

        from_name = await _get_company_name(db, from_id)
        to_name = await _get_company_name(db, to_id)

        pair_summaries.append(
            CompanyPairSummary(
                company_from_id=from_id,
                company_from_name=from_name,
                company_to_id=to_id,
                company_to_name=to_name,
                total_out=data["total_out"],
                total_in=reverse_data["total_out"],
                net=data["total_out"] - reverse_data["total_out"],
                confirmed_count=data["confirmed_count"] + reverse_data["confirmed_count"],
            )
        )

    # Counts for other statuses
    pending_result = await db.execute(
        select(func.count()).where(IntercompanyMatch.status == MatchStatus.PROPOSED)
    )
    pending_proposed = pending_result.scalar() or 0

    transit_result = await db.execute(
        select(func.count()).where(IntercompanyMatch.status == MatchStatus.IN_TRANSIT)
    )
    in_transit = transit_result.scalar() or 0

    unresolved_result = await db.execute(
        select(func.count()).where(IntercompanyMatch.status == MatchStatus.UNRESOLVED)
    )
    unresolved = unresolved_result.scalar() or 0

    return IntercomparySummaryResponse(
        pairs=pair_summaries,
        pending_proposed=pending_proposed,
        in_transit=in_transit,
        unresolved=unresolved,
    )


# ---------------------------------------------------------------------------
# Foreign entity registry
# ---------------------------------------------------------------------------

@router.get("/foreign-entities", response_model=list[ForeignEntityResponse])
async def list_foreign_entities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ForeignEntity).where(ForeignEntity.is_active == True).order_by(ForeignEntity.name)
    )
    return result.scalars().all()


@router.post("/foreign-entities", response_model=ForeignEntityResponse, status_code=201)
async def create_foreign_entity(
    body: ForeignEntityCreate,
    db: AsyncSession = Depends(get_db),
):
    entity = ForeignEntity(**body.model_dump())
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return entity
