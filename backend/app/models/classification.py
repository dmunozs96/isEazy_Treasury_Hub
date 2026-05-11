import uuid
from datetime import datetime
from decimal import Decimal

import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CashFlowSection(str, enum.Enum):
    OPERATING = "OPERATING"
    INVESTING = "INVESTING"
    FINANCING = "FINANCING"
    INTERNAL = "INTERNAL"
    UNCLASSIFIED = "UNCLASSIFIED"


class MatchType(str, enum.Enum):
    KEYWORD = "KEYWORD"
    REGEX = "REGEX"
    COUNTERPART_NAME = "COUNTERPART_NAME"
    AMOUNT_RANGE = "AMOUNT_RANGE"
    COMPOSITE = "COMPOSITE"


class ClassificationSource(str, enum.Enum):
    RULE = "RULE"
    MANUAL = "MANUAL"
    AI_SUGGESTION = "AI_SUGGESTION"


class CategoryTaxonomy(Base):
    __tablename__ = "category_taxonomy"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    parent_code: Mapped[str | None] = mapped_column(Text, ForeignKey("category_taxonomy.code"), nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cash_flow_section: Mapped[CashFlowSection] = mapped_column(
        Enum(CashFlowSection, name="cash_flow_section"), nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClassificationRule(Base):
    __tablename__ = "classification_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    match_type: Mapped[MatchType] = mapped_column(Enum(MatchType, name="match_type"), nullable=False)
    match_field: Mapped[str] = mapped_column(Text, nullable=False)
    match_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    category_code: Mapped[str] = mapped_column(Text, ForeignKey("category_taxonomy.code"), nullable=False)
    subcategory_code: Mapped[str | None] = mapped_column(Text, ForeignKey("category_taxonomy.code"), nullable=True)
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_classification_rules_priority", "priority", postgresql_where=text("is_active = TRUE")),
    )


class MovementClassification(Base):
    __tablename__ = "movement_classifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("movements.id"), nullable=False, unique=True)
    category_code: Mapped[str] = mapped_column(Text, ForeignKey("category_taxonomy.code"), nullable=False)
    subcategory_code: Mapped[str | None] = mapped_column(Text, ForeignKey("category_taxonomy.code"), nullable=True)
    source: Mapped[ClassificationSource] = mapped_column(
        Enum(ClassificationSource, name="classification_source"), nullable=False
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("classification_rules.id"), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    classified_by: Mapped[str] = mapped_column(Text, nullable=False, default="system")
    classified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_category_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_movement_classifications_category", "category_code"),
    )
