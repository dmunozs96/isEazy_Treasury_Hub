import hashlib
import uuid
from datetime import date
from decimal import Decimal


def movement_hash(
    bank_account_id: uuid.UUID,
    value_date: date,
    amount: Decimal,
    description: str,
) -> str:
    """
    Canonical deduplication hash per Spec 03.
    SHA-256 of pipe-joined fields; prevents re-importing the same movement.
    """
    payload = f"{bank_account_id}|{value_date.isoformat()}|{amount}|{description.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(content: bytes) -> str:
    """SHA-256 hash of raw file bytes — used for ImportBatch deduplication."""
    return hashlib.sha256(content).hexdigest()
