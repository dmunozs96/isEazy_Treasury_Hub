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


class SabadellParser(BankParser):
    bank_name = "SABADELL"
    file_engine = "calamine"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Sabadell_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="calamine", header=7)
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("F. Operativa")):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_parse_dmy_slash(row["F. Operativa"]),
                value_date=_parse_dmy_slash(row["F. Valor"]) if not _is_na(row.get("F. Valor")) else _parse_dmy_slash(row["F. Operativa"]),
                description=_str_or_none(row.get("Concepto")) or "",
                amount=_to_decimal(row.get("Importe")),
                running_balance=_to_decimal(row.get("Saldo")),
                description_detail=_str_or_none(row.get("Referencia 2")),
                reference=_str_or_none(row.get("Referencia 1")),
                raw_row=_serialize_row(row),
            ))
        return rows
