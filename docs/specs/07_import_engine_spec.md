# Spec 07 — Bank Import Engine

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Responsibility

The Bank Import Engine is responsible for:
1. Accepting raw bank files (Excel or CSV) from users
2. Detecting the file format (which bank, which format version)
3. Parsing the file into normalized row data
4. Deduplicating against already-imported movements
5. Creating ImportBatch and Movement records in the Treasury Ledger
6. Reporting per-row errors without losing the rest of the data

---

## 2. Supported Formats (Phase 1)

| Format ID | Bank | File Type | Detection Strategy |
|-----------|------|-----------|-------------------|
| SANTANDER_EXCEL | Banco Santander | .xlsx | Header row pattern |
| BBVA_EXCEL | BBVA | .xlsx | Header row pattern |
| CAIXABANK_EXCEL | CaixaBank | .xlsx | Header row pattern |
| SABADELL_EXCEL | Banco Sabadell | .xlsx | Header row pattern |
| GENERIC_CSV | Any bank | .csv | Fallback with column mapping |

Additional formats added via new parser classes — no changes to core pipeline.

---

## 3. Pipeline Architecture

```
File Upload
    │
    ▼
[Format Detector]
    Input: raw bytes + filename
    Output: format_id: str
    Raises: UnrecognizedFormatError
    │
    ▼
[Parser] (selected by format_id)
    Input: raw bytes + format_id
    Output: List[RawRow]  — list of dicts with normalized keys
    Raises: ParseError (per-row, collected, not fatal)
    │
    ▼
[Normalizer]
    Input: List[RawRow]
    Output: List[NormalizedRow]  — typed, validated fields
    - Date parsing (multiple format patterns)
    - Amount sign normalization
    - Description cleaning
    │
    ▼
[Deduplicator]
    Input: List[NormalizedRow] + bank_account_id
    Output: (new: List[NormalizedRow], duplicates: List[NormalizedRow])
    - Computes deduplication_hash per row
    - Checks against movements table
    │
    ▼
[Persister]
    Input: ImportBatch + new: List[NormalizedRow]
    Output: ImportBatch (updated with counts)
    - Creates RawMovement records
    - Creates Movement records
    - Updates ImportBatch status
    - All in single DB transaction
```

---

## 4. Format Detector

Detection algorithm:
1. Check file extension (.xlsx vs .csv)
2. For .xlsx: read first 10 rows, match header patterns against known format signatures
3. For .csv: detect delimiter, read first row, match header patterns
4. If no match: raise UnrecognizedFormatError with detected headers (for user feedback)

Format signature examples:
```python
SANTANDER_EXCEL = {
    "required_headers": ["Fecha", "F. Valor", "Concepto", "Importe", "Saldo"],
    "header_row": 4,  # 0-indexed
}
BBVA_EXCEL = {
    "required_headers": ["Fecha", "Fecha valor", "Descripción", "Importe", "Saldo"],
    "header_row": 0,
}
```

---

## 5. Parser Interface (Abstract Base)

```python
class BankParser(ABC):
    format_id: ClassVar[str]
    
    @abstractmethod
    def parse(self, file_bytes: bytes) -> List[RawRow]:
        """Parse file bytes into raw rows. Collect errors, don't raise on row errors."""
        ...
    
    @abstractmethod
    def detect(self, file_bytes: bytes, filename: str) -> bool:
        """Return True if this parser can handle the given file."""
        ...
```

Each parser outputs `RawRow`:
```python
@dataclass
class RawRow:
    row_number: int
    raw_data: dict          # original key-value pairs from the file
    value_date: str | None  # raw string, not yet parsed
    accounting_date: str | None
    amount_raw: str | None  # raw string, e.g. "1.234,56" or "-500.00"
    description: str | None
    counterpart_name: str | None
    counterpart_iban: str | None
    reference: str | None
    balance_raw: str | None
    parse_error: str | None # set if this row had an error
```

---

## 6. Normalizer

Responsibilities:
- Parse date strings to `date` objects (handles `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-MM-YYYY`)
- Parse amount strings to `Decimal` (handles Spanish comma-decimal format: "1.234,56")
- Normalize sign: credits = positive, debits = negative (parser handles sign convention per bank)
- Strip description whitespace, remove repeated spaces
- Mask IBAN (for storage in display fields)

Outputs `NormalizedRow`:
```python
@dataclass
class NormalizedRow:
    row_number: int
    raw_data: dict
    value_date: date
    accounting_date: date | None
    amount: Decimal
    description: str
    counterpart_name: str | None
    counterpart_iban: str | None
    reference: str | None
    balance_after: Decimal | None
    deduplication_hash: str  # computed during normalization
```

---

## 7. Deduplication

Hash computation:
```python
def compute_hash(bank_account_id: str, value_date: date, amount: Decimal, description: str) -> str:
    payload = f"{bank_account_id}|{value_date}|{amount:.2f}|{description}"
    return hashlib.sha256(payload.encode()).hexdigest()
```

Deduplication check:
- Batch-level: check `import_batches.file_hash` — if exists, mark batch as DUPLICATE immediately
- Row-level: check `movements.deduplication_hash` for each normalized row — skip already-imported rows

On duplicate rows: row is counted as `duplicate`, not `error`. ImportBatch still succeeds.

---

## 8. Error Handling

### Per-Row Errors (non-fatal)

Collected into `ImportBatch.error_log` as:
```json
[
  {
    "row_number": 5,
    "error": "INVALID_DATE",
    "raw_value": "31/02/2026",
    "field": "value_date"
  }
]
```

Import continues with remaining rows.

### Fatal Errors (abort batch)

- File is corrupt/unreadable
- Format detected but zero rows parsed
- DB transaction failure

On fatal error: ImportBatch.status = FAILED, raw file reference preserved.

---

## 9. API Endpoints

```
POST /api/v1/imports
  - Body: multipart/form-data
    - file: UploadFile
    - bank_account_id: UUID
    - notes: str (optional)
  - Response: ImportBatchResponse (with status=PENDING or PROCESSING)

GET /api/v1/imports/{id}/status
  - Response: ImportBatchResponse (with current status and counts)

GET /api/v1/imports
  - Query: company_id, bank_account_id, status, date_from, date_to
  - Response: PaginatedResponse[ImportBatchResponse]

GET /api/v1/imports/{id}/errors
  - Response: { errors: List[RowError] }
```

---

## 10. Acceptance Criteria

- [ ] A Santander Excel file with 200 rows imports successfully in < 5 seconds
- [ ] Re-uploading the same file produces status=DUPLICATE, no duplicated movements
- [ ] A file with 10 invalid rows: 190 rows imported, 10 errors logged, batch status=COMPLETED
- [ ] An unrecognized file format returns clear error with detected headers
- [ ] A corrupt/unreadable file returns FAILED status with error message
- [ ] All imported movements have correct sign (inflows positive, outflows negative)
- [ ] All imported movements have a valid `deduplication_hash`
- [ ] ImportBatch is always created before any movements (traceability)

---

## 11. Edge Cases

| Case | Handling |
|------|---------|
| File with only header row, no data | batch COMPLETED with imported_count=0, warning in notes |
| Duplicate rows within same file | first occurrence imported, subsequent flagged as duplicate |
| Amount = 0.00 | import normally, flag for review |
| Description is empty | use empty string, do not reject |
| Date in future (>7 days from now) | import normally, flag in error_log as WARNING |
| IBAN in wrong format | store as-is, do not reject |
| File larger than 10MB | reject with clear size limit error |
| Mixed encodings in CSV | try UTF-8, then latin-1 |
