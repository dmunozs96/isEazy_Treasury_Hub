import uuid
from datetime import date, datetime
from decimal import Decimal

import enum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MatchStatus(str, enum.Enum):
    IN_TRANSIT = "IN_TRANSIT"
    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


class MatchMethod(str, enum.Enum):
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"


class IntercompanyMatch(Base):
    __tablename__ = "intercompany_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # movement_out_id: the outflow leg (or the only known leg in IN_TRANSIT)
    movement_out_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id"), nullable=False
    )
    # movement_in_id: NULL for IN_TRANSIT records (second leg not yet imported)
    movement_in_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id"), nullable=True
    )

    company_from_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    # company_to_id: may be NULL for IN_TRANSIT if counterpart IBAN unknown
    company_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    match_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status", native_enum=False), nullable=False, default=MatchStatus.PROPOSED
    )
    match_method: Mapped[MatchMethod] = mapped_column(
        Enum(MatchMethod, name="match_method", native_enum=False), nullable=False
    )

    # 0.0–1.0 composite score; NULL for manual matches and IN_TRANSIT
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    # IN_TRANSIT escalation: if still IN_TRANSIT after this timestamp → UNRESOLVED
    transit_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    confirmed_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ForeignEntity(Base):
    """Registry of non-Spanish group entities for INT_INTERCOMPANY_FOREIGN classification."""

    __tablename__ = "foreign_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    known_ibans: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    keyword_patterns: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
