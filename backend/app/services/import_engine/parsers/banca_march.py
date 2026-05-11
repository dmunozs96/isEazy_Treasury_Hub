from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from .base import (
    BankParser,
    ParsedRow,
    _is_na,
    _parse_dmy_slash,
    _serialize_row,
    _str_or_none,
    _to_date,
    _to_decimal,
)


def _banca_march_value_date(val: Any, booking_date: date) -> date:
    """
    F. valor has mixed formats: full datetime or short DD/MM (year omitted).
    Excel stores short dates with year=1900; replace year from booking_date.
    """
    try:
        d = _to_date(val)
        if d.year < 2020:
            return d.replace(year=booking_date.year)
        return d
    except (ValueError, AttributeError):
        # fallback: try parsing as DD/MM/YYYY string
        try:
            return _parse_dmy_slash(val)
        except ValueError:
            return booking_date


class BancaMarchParser(BankParser):
    bank_name = "BANCA_MARCH"
    file_engine = "openpyxl"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("BancaMarch_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="openpyxl", header=3)
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("F. operación")):
                continue
            booking = _parse_dmy_slash(row["F. operación"])
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=booking,
                value_date=_banca_march_value_date(row.get("F. valor"), booking),
                description=_str_or_none(row.get("Concepto")) or "",
                amount=_to_decimal(row.get("Importe")),
                running_balance=_to_decimal(row.get("Saldo")),
                description_detail=_str_or_none(row.get("Concepto ordenante")),
                raw_row=_serialize_row(row),
            ))
        return rows
