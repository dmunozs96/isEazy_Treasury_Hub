"""
Normalizer: ParsedRow → dict of Movement fields ready for ORM insertion.

Mapping decisions:
- booking_date   → accounting_date
- value_date     → value_date
- description    → description  (description_detail appended with " | " when present)
- counterpart_name → counterpart_name
- amount         → amount
- running_balance → balance_after
- reference      → reference
- counterpart_iban: not extracted by any parser in Phase 1 (always None)
"""
from __future__ import annotations

import uuid
from typing import Any

from .deduplicator import movement_hash
from .parsers.base import ParsedRow


def normalise(
    row: ParsedRow,
    bank_account_id: uuid.UUID,
    company_id: uuid.UUID,
    import_batch_id: uuid.UUID,
    raw_movement_id: uuid.UUID,
    created_by: str = "system",
) -> dict[str, Any]:
    """Return a dict suitable for constructing a Movement ORM instance."""
    description = _build_description(row)
    return {
        "company_id": company_id,
        "bank_account_id": bank_account_id,
        "import_batch_id": import_batch_id,
        "raw_movement_id": raw_movement_id,
        "value_date": row.value_date,
        "accounting_date": row.booking_date,
        "amount": row.amount,
        "currency": "EUR",
        "balance_after": row.running_balance if row.running_balance else None,
        "description": description,
        "counterpart_name": row.counterpart_name,
        "counterpart_iban": None,
        "reference": row.reference,
        "deduplication_hash": movement_hash(
            bank_account_id, row.value_date, row.amount, description
        ),
        "is_intercompany": False,
        "intercompany_match_id": None,
        "created_by": created_by,
        "is_deleted": False,
    }


def _build_description(row: ParsedRow) -> str:
    """Concatenate description and description_detail so all text is searchable."""
    base = (row.description or "").strip()
    if row.description_detail:
        detail = row.description_detail.strip()
        if detail:
            return f"{base} | {detail}" if base else detail
    return base
