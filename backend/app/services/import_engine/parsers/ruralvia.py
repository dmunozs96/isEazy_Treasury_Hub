from pathlib import Path

import pandas as pd

from .base import BankParser, ParsedRow, _is_na, _serialize_row, _str_or_none, _to_date, _to_decimal


class RuralviaParser(BankParser):
    bank_name = "RURALVIA"
    file_engine = "openpyxl"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Ruralvia_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="openpyxl", header=3)
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("Fecha de la operación")):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_to_date(row["Fecha de la operación"]),
                value_date=_to_date(row["Fecha valor"]) if not _is_na(row.get("Fecha valor")) else _to_date(row["Fecha de la operación"]),
                description=_str_or_none(row.get("Tipo movimiento")) or "",
                amount=_to_decimal(row.get("Importe")),
                running_balance=_to_decimal(row.get("Saldo")),
                raw_row=_serialize_row(row),
            ))
        return rows

    def extract_account_iban(self, file_path: str) -> str | None:
        df = pd.read_excel(file_path, engine="openpyxl", header=None, nrows=4)
        try:
            val = str(df.iloc[1, 1]).strip()
            return val if val.upper().startswith("ES") else None
        except (IndexError, ValueError):
            return None
