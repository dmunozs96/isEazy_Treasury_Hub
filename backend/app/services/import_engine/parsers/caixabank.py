from pathlib import Path

import pandas as pd

from .base import BankParser, ParsedRow, _is_na, _serialize_row, _str_or_none, _to_date, _to_decimal


class CaixaBankParser(BankParser):
    bank_name = "CAIXABANK"
    file_engine = "xlrd"

    def can_parse(self, filename: str) -> bool:
        return Path(filename).name.startswith("Caixa_")

    def parse(self, file_path: str) -> list[ParsedRow]:
        try:
            df = pd.read_excel(file_path, engine="xlrd", header=2)
        except ValueError as exc:
            if "Passed header=[2]" in str(exc):
                return []
            raise
        # Empty account file: shape is (0, 1) with text "SIN MOVIMIENTOS"
        if df.shape[1] < 4:
            return []
        rows: list[ParsedRow] = []
        for idx, row in df.iterrows():
            if _is_na(row.get("Fecha")):
                continue
            rows.append(ParsedRow(
                bank=self.bank_name,
                file_path=file_path,
                row_index=int(idx),
                booking_date=_to_date(row["Fecha"]),
                value_date=_to_date(row["Fecha valor"]) if not _is_na(row.get("Fecha valor")) else _to_date(row["Fecha"]),
                description=_str_or_none(row.get("Movimiento")) or "",
                amount=_to_decimal(row.get("Importe")),
                running_balance=_to_decimal(row.get("Saldo")),
                description_detail=_str_or_none(row.get("Más datos")),
                raw_row=_serialize_row(row),
            ))
        return rows
