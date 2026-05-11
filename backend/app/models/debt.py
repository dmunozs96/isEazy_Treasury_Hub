import uuid
from datetime import date, datetime
from decimal import Decimal

import enum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InstrumentType(str, enum.Enum):
    LOAN = "LOAN"
    CREDIT_LINE = "CREDIT_LINE"
    BOND = "BOND"
    LEASING = "LEASING"
    OTHER = "OTHER"


class InterestType(str, enum.Enum):
    FIXED = "FIXED"
    VARIABLE = "VARIABLE"
    MIXED = "MIXED"


class AmortizationType(str, enum.Enum):
    BULLET = "BULLET"
    FRENCH = "FRENCH"
    GERMAN = "GERMAN"
    CUSTOM = "CUSTOM"


class PaymentType(str, enum.Enum):
    PRINCIPAL = "PRINCIPAL"
    INTEREST = "INTEREST"
    MIXED = "MIXED"


class ScheduleStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class DebtInstrument(Base):
    __tablename__ = "debt_instruments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    instrument_type: Mapped[InstrumentType] = mapped_column(Enum(InstrumentType, name="instrument_type", native_enum=False), nullable=False)
    lender_name: Mapped[str] = mapped_column(Text, nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="EUR")
    drawdown_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    interest_type: Mapped[InterestType] = mapped_column(Enum(InterestType, name="interest_type", native_enum=False), nullable=False)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    reference_rate: Mapped[str | None] = mapped_column(Text, nullable=True)
    spread: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    amortization_type: Mapped[AmortizationType] = mapped_column(Enum(AmortizationType, name="amortization_type", native_enum=False), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_debt_instruments_company", "company_id"),
        Index("idx_debt_instruments_maturity", "maturity_date", postgresql_where=text("is_active = TRUE")),
    )


class DebtScheduleEntry(Base):
    __tablename__ = "debt_schedule_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debt_instrument_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("debt_instruments.id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType, name="payment_type", native_enum=False), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    principal_component: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    interest_component: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus, name="schedule_status", native_enum=False), nullable=False, default=ScheduleStatus.SCHEDULED
    )
    movement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("movements.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_debt_schedule_instrument", "debt_instrument_id"),
        Index("idx_debt_schedule_payment_date", "payment_date"),
        Index("idx_debt_schedule_status", "status"),
    )
