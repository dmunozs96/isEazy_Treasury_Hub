import uuid
from datetime import date, datetime
from decimal import Decimal

import enum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ParseStatus(str, enum.Enum):
    OK = "OK"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class RawMovement(Base):
    __tablename__ = "raw_movements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False)
    row_number: Mapped[int]
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    normalized_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[ParseStatus] = mapped_column(
        Enum(ParseStatus, name="parse_status", native_enum=False), nullable=False, default=ParseStatus.OK
    )
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    movement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("idx_raw_movements_batch", "import_batch_id"),
        Index("idx_raw_movements_movement", "movement_id", postgresql_where=text("movement_id IS NOT NULL")),
    )


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    bank_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    import_batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False)
    raw_movement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_movements.id"), nullable=True)

    value_date: Mapped[date] = mapped_column(Date, nullable=False)
    accounting_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="EUR")
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    counterpart_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    counterpart_iban: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)

    deduplication_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    is_intercompany: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    intercompany_match_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by: Mapped[str] = mapped_column(Text, nullable=False, default="system")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("idx_movements_company", "company_id"),
        Index("idx_movements_account", "bank_account_id"),
        Index("idx_movements_value_date", "value_date"),
        Index("idx_movements_amount", "amount"),
        Index("idx_movements_intercompany", "is_intercompany", postgresql_where=text("is_intercompany = TRUE")),
        Index("idx_movements_not_deleted", "is_deleted", postgresql_where=text("is_deleted = FALSE")),
    )
