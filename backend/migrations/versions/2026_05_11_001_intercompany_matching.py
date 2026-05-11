"""add intercompany matching full implementation

Revision ID: 0002_intercompany_matching
Revises: 0001_initial_schema
Create Date: 2026-05-11 01:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002_intercompany_matching"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add IN_TRANSIT and UNRESOLVED to match_status enum
    # PostgreSQL requires COMMIT between ALTER TYPE and table use, so we use raw SQL
    op.execute("ALTER TYPE match_status ADD VALUE IF NOT EXISTS 'IN_TRANSIT'")
    op.execute("ALTER TYPE match_status ADD VALUE IF NOT EXISTS 'UNRESOLVED'")

    # Drop unique constraints on movement legs (a movement can appear in REJECTED matches
    # before being in a new PROPOSED match)
    op.drop_constraint("intercompany_matches_movement_out_id_key", "intercompany_matches", type_="unique")
    op.drop_constraint("intercompany_matches_movement_in_id_key", "intercompany_matches", type_="unique")

    # Make movement_in_id nullable — IN_TRANSIT records only have one leg
    op.alter_column("intercompany_matches", "movement_in_id", nullable=True)

    # Make company_to_id nullable — may be unknown during IN_TRANSIT
    op.alter_column("intercompany_matches", "company_to_id", nullable=True)

    # Add score column (0.0 – 1.0 composite match quality)
    op.add_column(
        "intercompany_matches",
        sa.Column("score", sa.Numeric(5, 4), nullable=True),
    )

    # Add transit_expires_at for IN_TRANSIT escalation window
    op.add_column(
        "intercompany_matches",
        sa.Column("transit_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add useful indexes
    op.create_index("idx_intercompany_status", "intercompany_matches", ["status"])
    op.create_index("idx_intercompany_movement_out", "intercompany_matches", ["movement_out_id"])
    op.create_index(
        "idx_intercompany_movement_in",
        "intercompany_matches",
        ["movement_in_id"],
        postgresql_where=sa.text("movement_in_id IS NOT NULL"),
    )
    op.create_index(
        "idx_intercompany_companies",
        "intercompany_matches",
        ["company_from_id", "company_to_id"],
    )

    # Create foreign_entities table
    op.create_table(
        "foreign_entities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("country", sa.Text, nullable=False),
        sa.Column(
            "known_ibans",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "keyword_patterns",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("foreign_entities")
    op.drop_index("idx_intercompany_companies", "intercompany_matches")
    op.drop_index("idx_intercompany_movement_in", "intercompany_matches")
    op.drop_index("idx_intercompany_movement_out", "intercompany_matches")
    op.drop_index("idx_intercompany_status", "intercompany_matches")
    op.drop_column("intercompany_matches", "transit_expires_at")
    op.drop_column("intercompany_matches", "score")
    op.alter_column("intercompany_matches", "company_to_id", nullable=False)
    op.alter_column("intercompany_matches", "movement_in_id", nullable=False)
    op.create_unique_constraint(
        "intercompany_matches_movement_in_id_key", "intercompany_matches", ["movement_in_id"]
    )
    op.create_unique_constraint(
        "intercompany_matches_movement_out_id_key", "intercompany_matches", ["movement_out_id"]
    )
    # Note: PostgreSQL does not support removing enum values — IN_TRANSIT/UNRESOLVED remain
