from pathlib import Path

import pandas as pd

from .base import (
    BankParser,
    ParsedRow,
    _eu_str_to_decimal,
    _is_na,
    _parse_dmy_hhmm,
    _parse_dmy_slash,
    _serialize_row,
    _str_or_none,
)


class EurocajaRuralParser(BankParser):
    bank_name = "EUROCAJA_RURAL"
    file_engine = "csv"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("EUROCAJA_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_csv(
            file_path,
            encoding="utf-8-sig",
            sep=";",
            skiprows=9,
            header=0,
        )
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            booking_raw = row.iloc[0]
            if _is_na(booking_raw):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_parse_dmy_hhmm(booking_raw),
                value_date=_parse_dmy_slash(row.iloc[1]) if not _is_na(row.iloc[1]) else _parse_dmy_hhmm(booking_raw),
                description=_str_or_none(row.iloc[2]) or "",
                amount=_eu_str_to_decimal(row.iloc[3]),
                running_balance=_eu_str_to_decimal(row.iloc[4]),
                raw_row=_serialize_row(row),
            ))
        return rows

    def extract_account_iban(self, file_path: str) -> str | None:
        df = pd.read_csv(
            file_path,
            encoding="utf-8-sig",
            sep=";",
            nrows=6,
            header=None,
        )
        try:
            val = str(df.iloc[3, 1]).strip()
            iban_part = val.split(" - ")[0].strip()
            return iban_part if iban_part.upper().startswith("ES") else None
        except (IndexError, ValueError):
            return None
