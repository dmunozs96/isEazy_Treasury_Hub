from pathlib import Path

import pandas as pd

from .base import (
    BankParser,
    ParsedRow,
    _is_na,
    _parse_dmy_slash,
    _serialize_row,
    _str_or_none,
    _to_decimal,
)

# Sheet that contains the operation code lookup table — skip it
_SKIP_SHEET = "Hoja1"
# Sentinel text indicating an empty sheet
_NO_MOVEMENTS = "NO HAY MOVIMIENTOS"
# Expected column count for the standard 12-column Santander format
_EXPECTED_COLS = {"Fecha Operación", "Fecha Valor", "Concepto", "Importe", "Saldo"}


def _read_santander_sheet(
    file_path: str,
    sheet_name: str,
    engine: str,
) -> pd.DataFrame | None:
    """
    Try to read one sheet.  Santander LMS 3917.xls has one sheet (MARZO - ABRIL)
    with header at row 0; all other sheets use row 7.  Detect which by checking
    if row-7 header produces the expected columns; if not, fall back to row 0.
    Returns a normalised DataFrame or None when the sheet has no movements.
    """
    for header_row in (7, 0):
        try:
            df = pd.read_excel(file_path, engine=engine, sheet_name=sheet_name, header=header_row)
        except Exception:
            continue
        # Drop fully-empty columns
        df = df.dropna(axis=1, how="all")
        if df.empty:
            return None
        # Check for "no movements" sentinel anywhere in the first few rows
        flat_values = df.iloc[:3].values.flatten()
        if any(_NO_MOVEMENTS in str(v) for v in flat_values):
            return None
        if _EXPECTED_COLS.issubset(set(df.columns)):
            return df
    return None


class SantanderParser(BankParser):
    bank_name = "SANTANDER"
    file_engine = "openpyxl"  # default for .xlsx; .xls uses xlrd

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Santander_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        path = Path(file_path)
        engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
        return self._parse_with_engine(file_path, engine)

    # ── internals ─────────────────────────────────────────────────────────

    def _parse_with_engine(self, file_path: str, engine: str) -> list[ParsedRow]:
        xl = pd.ExcelFile(file_path, engine=engine)
        rows: list[ParsedRow] = []
        for sheet in xl.sheet_names:
            if sheet == _SKIP_SHEET:
                continue
            df = _read_santander_sheet(file_path, sheet, engine)
            if df is None or df.empty:
                continue
            rows.extend(self._parse_df(df, file_path))
        return rows

    def _parse_df(self, df: pd.DataFrame, file_path: str) -> list[ParsedRow]:
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("Fecha Operación")):
                continue
            ref_raw = row.get("Número de documento")
            reference: str | None = None
            if not _is_na(ref_raw):
                try:
                    reference = str(int(float(ref_raw)))
                except (ValueError, OverflowError):
                    reference = _str_or_none(ref_raw)
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_parse_dmy_slash(row["Fecha Operación"]),
                value_date=_parse_dmy_slash(row["Fecha Valor"]) if not _is_na(row.get("Fecha Valor")) else _parse_dmy_slash(row["Fecha Operación"]),
                description=_str_or_none(row.get("Concepto")) or "",
                amount=_to_decimal(row.get("Importe")),
                running_balance=_to_decimal(row.get("Saldo")),
                description_detail=_str_or_none(row.get("Referencia 1")),
                operation_code=_str_or_none(row.get("Código")),
                reference=reference,
                raw_row=_serialize_row(row),
            ))
        return rows
