from pathlib import Path

import pandas as pd

from .base import BankParser, ParsedRow, _is_na, _serialize_row, _str_or_none, _to_date, _to_decimal


class BankinterParser(BankParser):
    bank_name = "BANKINTER"
    file_engine = "openpyxl"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Bankinter_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="openpyxl", header=5)
        rows: list[ParsedRow] = []
        has_ref16 = "REF. 16" in df.columns
        for idx, row in df.iterrows():
            if _is_na(row.get("FECHA CONTABLE")):
                continue
            try:
                booking_date = _to_date(row["FECHA CONTABLE"])
            except ValueError:
                continue
            value_date = booking_date
            if not _is_na(row.get("FECHA VALOR")):
                try:
                    value_date = _to_date(row["FECHA VALOR"])
                except ValueError:
                    value_date = booking_date
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=booking_date,
                value_date=value_date,
                description=_str_or_none(row.get("DESCRIPCIÓN")) or "",
                amount=_to_decimal(row.get("IMPORTE")),
                running_balance=_to_decimal(row.get("SALDO")),
                description_detail=_str_or_none(row.get("REF. 16")) if has_ref16 else None,
                operation_code=_str_or_none(row.get("CLAVE")),
                reference=_str_or_none(row.get("REFERENCIA")),
                raw_row=_serialize_row(row),
            ))
        return rows
