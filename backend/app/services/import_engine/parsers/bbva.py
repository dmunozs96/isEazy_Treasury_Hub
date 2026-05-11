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


class BBVAParser(BankParser):
    bank_name = "BBVA"
    file_engine = "openpyxl"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("BBVA_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="openpyxl", header=15)
        # Drop leading empty columns (A, B in spreadsheet become Unnamed)
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("F. OPERACIÓN")):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_parse_dmy_slash(row["F. OPERACIÓN"]),
                value_date=_parse_dmy_slash(row["F. VALOR"]),
                description=_str_or_none(row.get("CONCEPTO")) or "",
                amount=_to_decimal(row.get("IMPORTE")),
                running_balance=_to_decimal(row.get("SALDO")),
                description_detail=_str_or_none(row.get("OBSERVACIONES")),
                counterpart_name=_str_or_none(row.get("BENEFICIARIO/ORDENANTE")),
                operation_code=_str_or_none(row.get("CÓDIGO")),
                reference=_str_or_none(row.get("REMESA")),
                raw_row=_serialize_row(row),
            ))
        return rows

    def extract_account_iban(self, file_path: str) -> str | None:
        df = pd.read_excel(file_path, engine="openpyxl", header=None, nrows=15)
        try:
            val = str(df.iloc[7, 5]).strip()
            return val if val.upper().startswith("ES") else None
        except (IndexError, ValueError):
            return None
