from pathlib import Path

import pandas as pd

from .base import BankParser, ParsedRow, _is_na, _serialize_row, _str_or_none, _to_date, _to_decimal


class CajamarParser(BankParser):
    bank_name = "CAJAMAR"
    file_engine = "calamine"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Cajamar_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="calamine", header=0)
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("Fecha")):
                continue
            concepto = _str_or_none(row.get("Concepto")) or ""
            # Split on first newline: part before → description, after → detail
            if "\n" in concepto:
                description, detail = concepto.split("\n", 1)
                description = description.strip()
                detail = detail.strip() or None
            else:
                description = concepto
                detail = None
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_to_date(row["Fecha"]),
                value_date=_to_date(row["F. valor"]) if not _is_na(row.get("F. valor")) else _to_date(row["Fecha"]),
                description=description,
                amount=_to_decimal(row.get("Importe")),
                running_balance=_to_decimal(row.get("Saldo")),
                description_detail=detail,
                raw_row=_serialize_row(row),
            ))
        return rows
