import uuid
from datetime import date, datetime
from decimal import Decimal

import enum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ForecastSource(str, enum.Enum):
    OFFICIAL = "OFFICIAL"
    AI = "AI"


class ForecastScenario(Base):
    __tablename__ = "forecast_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[ForecastSource] = mapped_column(Enum(ForecastSource, name="forecast_source", native_enum=False), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    import_batch_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by: Mapped[str] = mapped_column(Text, nullable=False)


class ForecastEntry(Base):
    __tablename__ = "forecast_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forecast_scenarios.id"), nullable=False)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    category_code: Mapped[str] = mapped_column(Text, ForeignKey("category_taxonomy.code"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="EUR")
    source: Mapped[ForecastSource] = mapped_column(Enum(ForecastSource, name="forecast_source", native_enum=False), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_forecast_entries_company", "company_id"),
        Index("idx_forecast_entries_scenario", "scenario_id"),
        Index("idx_forecast_entries_week", "week_start_date"),
    )
