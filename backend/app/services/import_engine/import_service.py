"""
Import service — orchestrates the full ImportBatch lifecycle:
  1. Hash file content (file-level deduplication)
  2. Detect parser from filename
  3. Parse file → list[ParsedRow]
  4. Persist RawMovement rows
  5. Normalise + deduplicate → persist Movement rows
  6. Update ImportBatch status and counters
"""
from __future__ import annotations

import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_batch import ImportBatch, ImportStatus
from app.models.movement import Movement, ParseStatus, RawMovement

from .deduplicator import file_hash, movement_hash
from .detector import detect_parser
from .normalizer import normalise
from .parsers.base import ParsedRow

log = structlog.get_logger(__name__)


async def run_import(
    *,
    session: AsyncSession,
    file_content: bytes,
    filename: str,
    bank_account_id: uuid.UUID,
    company_id: uuid.UUID,
    imported_by: str = "system",
    notes: str | None = None,
) -> ImportBatch:
    """
    Full import pipeline.  Returns the completed ImportBatch record.
    Raises ValueError for unsupported file formats.
    """
    fhash = file_hash(file_content)

    # ── duplicate file guard ───────────────────────────────────────────────
    existing = await session.scalar(
        select(ImportBatch).where(ImportBatch.file_hash == fhash)
    )
    if existing:
        log.info("import.duplicate_file", filename=filename, batch_id=str(existing.id))
        existing.status = ImportStatus.DUPLICATE
        await session.commit()
        return existing

    # ── create batch record ───────────────────────────────────────────────
    parser = detect_parser(filename)
    batch = ImportBatch(
        company_id=company_id,
        bank_account_id=bank_account_id,
        filename=filename,
        file_hash=fhash,
        file_format=parser.bank_name,
        status=ImportStatus.PROCESSING,
        imported_by=imported_by,
        notes=notes,
    )
    session.add(batch)
    await session.flush()  # get batch.id

    log.info("import.started", filename=filename, bank=parser.bank_name, batch_id=str(batch.id))

    # ── parse ─────────────────────────────────────────────────────────────
    errors: list[dict[str, Any]] = []
    parsed_rows: list[ParsedRow] = []
    with tempfile.NamedTemporaryFile(
        suffix=Path(filename).suffix, delete=False
    ) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    try:
        parsed_rows = parser.parse(tmp_path)
    except Exception as exc:
        log.error("import.parse_failed", filename=filename, error=str(exc))
        batch.status = ImportStatus.FAILED
        batch.error_log = [{"type": "parse_error", "message": str(exc)}]
        await session.commit()
        return batch
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    batch.row_count = len(parsed_rows)
    imported_count = 0
    skipped_count = 0

    # ── persist rows ──────────────────────────────────────────────────────
    for raw_row in parsed_rows:
        raw_mv = RawMovement(
            import_batch_id=batch.id,
            row_number=raw_row.row_index,
            raw_data=raw_row.raw_row,
            normalized_date=raw_row.value_date,
            normalized_amount=raw_row.amount,
            normalized_description=raw_row.description,
            parse_status=ParseStatus.OK,
        )
        session.add(raw_mv)
        await session.flush()  # get raw_mv.id

        # Movement deduplication
        dedup_hash = movement_hash(
            bank_account_id, raw_row.value_date, raw_row.amount, raw_row.description
        )
        already_exists = await session.scalar(
            select(Movement).where(Movement.deduplication_hash == dedup_hash)
        )
        if already_exists:
            raw_mv.parse_status = ParseStatus.SKIPPED
            skipped_count += 1
            continue

        mv_fields = normalise(
            row=raw_row,
            bank_account_id=bank_account_id,
            company_id=company_id,
            import_batch_id=batch.id,
            raw_movement_id=raw_mv.id,
            created_by=imported_by,
        )
        movement = Movement(**mv_fields)
        session.add(movement)
        await session.flush()

        raw_mv.movement_id = movement.id
        imported_count += 1

    # ── finalise batch ────────────────────────────────────────────────────
    batch.imported_count = imported_count
    batch.error_count = len(errors)
    batch.error_log = errors
    batch.status = ImportStatus.COMPLETED
    batch.processed_at = datetime.now(timezone.utc)

    await session.commit()

    log.info(
        "import.completed",
        batch_id=str(batch.id),
        imported=imported_count,
        skipped=skipped_count,
        errors=len(errors),
    )
    return batch
