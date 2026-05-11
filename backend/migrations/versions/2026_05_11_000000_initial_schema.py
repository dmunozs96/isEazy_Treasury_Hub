"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enum types ---
    op.execute("CREATE TYPE import_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'DUPLICATE')")
    op.execute("CREATE TYPE parse_status AS ENUM ('OK', 'ERROR', 'SKIPPED')")
    op.execute("CREATE TYPE cash_flow_section AS ENUM ('OPERATING', 'INVESTING', 'FINANCING', 'INTERNAL', 'UNCLASSIFIED')")
    op.execute("CREATE TYPE match_type AS ENUM ('KEYWORD', 'REGEX', 'COUNTERPART_NAME', 'AMOUNT_RANGE', 'COMPOSITE')")
    op.execute("CREATE TYPE classification_source AS ENUM ('RULE', 'MANUAL', 'AI_SUGGESTION')")
    op.execute("CREATE TYPE match_status AS ENUM ('PROPOSED', 'CONFIRMED', 'REJECTED')")
    op.execute("CREATE TYPE match_method AS ENUM ('AUTOMATIC', 'MANUAL')")
    op.execute("CREATE TYPE forecast_source AS ENUM ('OFFICIAL', 'AI')")
    op.execute("CREATE TYPE instrument_type AS ENUM ('LOAN', 'CREDIT_LINE', 'BOND', 'LEASING', 'OTHER')")
    op.execute("CREATE TYPE interest_type AS ENUM ('FIXED', 'VARIABLE', 'MIXED')")
    op.execute("CREATE TYPE amortization_type AS ENUM ('BULLET', 'FRENCH', 'GERMAN', 'CUSTOM')")
    op.execute("CREATE TYPE payment_type AS ENUM ('PRINCIPAL', 'INTEREST', 'MIXED')")
    op.execute("CREATE TYPE schedule_status AS ENUM ('SCHEDULED', 'PAID', 'OVERDUE', 'CANCELLED')")

    # --- companies ---
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("short_name", sa.Text, nullable=False),
        sa.Column("tax_id", sa.Text, unique=True, nullable=True),
        sa.Column("is_holding", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # --- bank_accounts ---
    op.create_table(
        "bank_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("bank_name", sa.Text, nullable=False),
        sa.Column("account_name", sa.Text, nullable=False),
        sa.Column("iban", sa.Text, nullable=False, unique=True),
        sa.Column("currency", sa.Text, nullable=False, server_default="EUR"),
        sa.Column("is_internal", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_bank_accounts_company", "bank_accounts", ["company_id"])
    op.create_index("idx_bank_accounts_internal", "bank_accounts", ["is_internal"], postgresql_where=sa.text("is_internal = TRUE"))

    # --- import_batches ---
    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("bank_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bank_accounts.id"), nullable=False),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("file_hash", sa.Text, nullable=False, unique=True),
        sa.Column("file_format", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="PENDING"),
        sa.Column("row_count", sa.Integer, nullable=True),
        sa.Column("imported_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_log", postgresql.JSONB, nullable=False, server_default="'[]'"),
        sa.Column("imported_by", sa.Text, nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("idx_import_batches_company", "import_batches", ["company_id"])
    op.create_index("idx_import_batches_account", "import_batches", ["bank_account_id"])
    op.create_index("idx_import_batches_status", "import_batches", ["status"])

    # --- category_taxonomy ---
    op.create_table(
        "category_taxonomy",
        sa.Column("code", sa.Text, primary_key=True),
        sa.Column("parent_code", sa.Text, sa.ForeignKey("category_taxonomy.code"), nullable=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("cash_flow_section", sa.Text, nullable=False),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )

    # --- raw_movements ---
    op.create_table(
        "raw_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("raw_data", postgresql.JSONB, nullable=False),
        sa.Column("normalized_date", sa.Date, nullable=True),
        sa.Column("normalized_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("normalized_description", sa.Text, nullable=True),
        sa.Column("parse_status", sa.Text, nullable=False, server_default="OK"),
        sa.Column("parse_error", sa.Text, nullable=True),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("idx_raw_movements_batch", "raw_movements", ["import_batch_id"])
    op.create_index("idx_raw_movements_movement", "raw_movements", ["movement_id"], postgresql_where=sa.text("movement_id IS NOT NULL"))

    # --- movements ---
    op.create_table(
        "movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("bank_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bank_accounts.id"), nullable=False),
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("raw_movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_movements.id"), nullable=True),
        sa.Column("value_date", sa.Date, nullable=False),
        sa.Column("accounting_date", sa.Date, nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.Text, nullable=False, server_default="EUR"),
        sa.Column("balance_after", sa.Numeric(18, 2), nullable=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("counterpart_name", sa.Text, nullable=True),
        sa.Column("counterpart_iban", sa.Text, nullable=True),
        sa.Column("reference", sa.Text, nullable=True),
        sa.Column("deduplication_hash", sa.Text, nullable=False, unique=True),
        sa.Column("is_intercompany", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("intercompany_match_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.Text, nullable=False, server_default="system"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("idx_movements_company", "movements", ["company_id"])
    op.create_index("idx_movements_account", "movements", ["bank_account_id"])
    op.create_index("idx_movements_value_date", "movements", ["value_date"])
    op.create_index("idx_movements_amount", "movements", ["amount"])
    op.create_index("idx_movements_intercompany", "movements", ["is_intercompany"], postgresql_where=sa.text("is_intercompany = TRUE"))
    op.create_index("idx_movements_not_deleted", "movements", ["is_deleted"], postgresql_where=sa.text("is_deleted = FALSE"))

    # --- classification_rules ---
    op.create_table(
        "classification_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("match_type", sa.Text, nullable=False),
        sa.Column("match_field", sa.Text, nullable=False),
        sa.Column("match_pattern", sa.Text, nullable=False),
        sa.Column("category_code", sa.Text, sa.ForeignKey("category_taxonomy.code"), nullable=False),
        sa.Column("subcategory_code", sa.Text, sa.ForeignKey("category_taxonomy.code"), nullable=True),
        sa.Column("created_by", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_classification_rules_priority", "classification_rules", ["priority"], postgresql_where=sa.text("is_active = TRUE"))

    # --- movement_classifications ---
    op.create_table(
        "movement_classifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movements.id"), nullable=False, unique=True),
        sa.Column("category_code", sa.Text, sa.ForeignKey("category_taxonomy.code"), nullable=False),
        sa.Column("subcategory_code", sa.Text, sa.ForeignKey("category_taxonomy.code"), nullable=True),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classification_rules.id"), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("is_confirmed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("classified_by", sa.Text, nullable=False, server_default="system"),
        sa.Column("classified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("override_reason", sa.Text, nullable=True),
        sa.Column("previous_category_code", sa.Text, nullable=True),
    )
    op.create_index("idx_movement_classifications_category", "movement_classifications", ["category_code"])

    # --- intercompany_matches ---
    op.create_table(
        "intercompany_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("movement_out_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movements.id"), nullable=False, unique=True),
        sa.Column("movement_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movements.id"), nullable=False, unique=True),
        sa.Column("company_from_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("company_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("match_date", sa.Date, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="PROPOSED"),
        sa.Column("match_method", sa.Text, nullable=False),
        sa.Column("confirmed_by", sa.Text, nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("notes", sa.Text, nullable=True),
    )

    # --- forecast_scenarios ---
    op.create_table(
        "forecast_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("week_end", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("import_batch_ref", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.Text, nullable=False),
    )

    # --- forecast_entries ---
    op.create_table(
        "forecast_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("forecast_scenarios.id"), nullable=False),
        sa.Column("week_start_date", sa.Date, nullable=False),
        sa.Column("category_code", sa.Text, sa.ForeignKey("category_taxonomy.code"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.Text, nullable=False, server_default="EUR"),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.Text, nullable=False),
    )
    op.create_index("idx_forecast_entries_company", "forecast_entries", ["company_id"])
    op.create_index("idx_forecast_entries_scenario", "forecast_entries", ["scenario_id"])
    op.create_index("idx_forecast_entries_week", "forecast_entries", ["week_start_date"])

    # --- debt_instruments ---
    op.create_table(
        "debt_instruments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("instrument_type", sa.Text, nullable=False),
        sa.Column("lender_name", sa.Text, nullable=False),
        sa.Column("principal_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("outstanding_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.Text, nullable=False, server_default="EUR"),
        sa.Column("drawdown_date", sa.Date, nullable=False),
        sa.Column("maturity_date", sa.Date, nullable=False),
        sa.Column("interest_type", sa.Text, nullable=False),
        sa.Column("interest_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("reference_rate", sa.Text, nullable=True),
        sa.Column("spread", sa.Numeric(6, 4), nullable=True),
        sa.Column("amortization_type", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_debt_instruments_company", "debt_instruments", ["company_id"])
    op.create_index("idx_debt_instruments_maturity", "debt_instruments", ["maturity_date"], postgresql_where=sa.text("is_active = TRUE"))

    # --- debt_schedule_entries ---
    op.create_table(
        "debt_schedule_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("debt_instrument_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("debt_instruments.id"), nullable=False),
        sa.Column("payment_date", sa.Date, nullable=False),
        sa.Column("payment_type", sa.Text, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("principal_component", sa.Numeric(18, 2), nullable=True),
        sa.Column("interest_component", sa.Numeric(18, 2), nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="SCHEDULED"),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movements.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_debt_schedule_instrument", "debt_schedule_entries", ["debt_instrument_id"])
    op.create_index("idx_debt_schedule_payment_date", "debt_schedule_entries", ["payment_date"])
    op.create_index("idx_debt_schedule_status", "debt_schedule_entries", ["status"])


def downgrade() -> None:
    op.drop_table("debt_schedule_entries")
    op.drop_table("debt_instruments")
    op.drop_table("forecast_entries")
    op.drop_table("forecast_scenarios")
    op.drop_table("intercompany_matches")
    op.drop_table("movement_classifications")
    op.drop_table("classification_rules")
    op.drop_table("movements")
    op.drop_table("raw_movements")
    op.drop_table("category_taxonomy")
    op.drop_table("import_batches")
    op.drop_table("bank_accounts")
    op.drop_table("companies")

    for enum_name in [
        "schedule_status", "payment_type", "amortization_type", "interest_type",
        "instrument_type", "forecast_source", "match_method", "match_status",
        "classification_source", "match_type", "cash_flow_section",
        "parse_status", "import_status",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
