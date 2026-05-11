from pathlib import Path

import pandas as pd

from .base import BankParser, ParsedRow, _is_na, _serialize_row, _str_or_none, _to_date, _to_decimal


class AbancaParser(BankParser):
    bank_name = "ABANCA"
    file_engine = "openpyxl"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Abanca_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="openpyxl", header=4)
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("F. CONTABLE")):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_to_date(row["F. CONTABLE"]),
                value_date=_to_date(row["F. VALOR"]),
                description=_str_or_none(row.get("DESCRIPCIÓN")) or "",
                amount=_to_decimal(row.get("IMPORTE")),
                running_balance=_to_decimal(row.get("SALDO")),
                operation_code=_str_or_none(row.get("TIPO OPERACIÓN")),
                reference=_str_or_none(row.get("REFERENCIA")),
                raw_row=_serialize_row(row),
            ))
        return rows
