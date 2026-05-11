from pathlib import Path

import pandas as pd

from .base import (
    BankParser,
    ParsedRow,
    _is_na,
    _parse_dmy_hyphen,
    _serialize_row,
    _str_or_none,
    _to_decimal,
)


def _ibercaja_reference(val) -> str | None:
    """Referencia is read as float (e.g. 6.503116e+11) — convert to int string."""
    if _is_na(val):
        return None
    try:
        return str(int(float(val)))
    except (ValueError, OverflowError):
        s = str(val).strip()
        return s if s else None


class IbercajaParser(BankParser):
    bank_name = "IBERCAJA"
    file_engine = "openpyxl"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Ibercaja_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="openpyxl", header=6)
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("Fecha Oper")):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_parse_dmy_hyphen(row["Fecha Oper"]),
                value_date=_parse_dmy_hyphen(row["Fecha Valor"]) if not _is_na(row.get("Fecha Valor")) else _parse_dmy_hyphen(row["Fecha Oper"]),
                description=_str_or_none(row.get("Descripción")) or "",
                amount=_to_decimal(row.get("Importe")),
                running_balance=_to_decimal(row.get("Saldo")),
                operation_code=_str_or_none(row.get("Concepto")),
                reference=_ibercaja_reference(row.get("Referencia")),
                raw_row=_serialize_row(row),
            ))
        return rows
