from pathlib import Path

import pandas as pd

from .base import (
    BankParser,
    ParsedRow,
    _eu_str_to_decimal,
    _is_na,
    _parse_dmy_dot,
    _serialize_row,
    _str_or_none,
)


class DeutscheBankParser(BankParser):
    bank_name = "DEUTSCHE_BANK"
    file_engine = "xlrd"

    def can_parse(self, filename: str) -> bool:
        # Actual filename uses the typo "DEUSTCHE" from sample files
        name = Path(filename).name
        return name.startswith("DEUSTCHE_") or name.startswith("DEUTSCHE_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        df = pd.read_excel(file_path, engine="xlrd", header=5)
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("FECHA OPERACIÓN")):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_parse_dmy_dot(row["FECHA OPERACIÓN"]),
                value_date=_parse_dmy_dot(row["FECHA VALOR"]),
                description=(_str_or_none(row.get("CONCEPTO")) or "").strip(),
                amount=_eu_str_to_decimal(row.get("IMPORTE")),
                running_balance=_eu_str_to_decimal(row.get("SALDO")),
                raw_row=_serialize_row(row),
            ))
        return rows

    def extract_account_iban(self, file_path: str) -> str | None:
        df = pd.read_excel(file_path, engine="xlrd", header=None, nrows=5)
        try:
            val = str(df.iloc[1, 1]).strip()
            return val if val.upper().startswith("ES") else None
        except (IndexError, ValueError):
            return None
