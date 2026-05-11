from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd


@dataclass
class ParsedRow:
    bank: str
    file_path: str
    row_index: int
    booking_date: date
    value_date: date
    description: str
    amount: Decimal
    running_balance: Decimal
    description_detail: str | None = None
    counterpart_name: str | None = None
    operation_code: str | None = None
    reference: str | None = None
    raw_row: dict[str, Any] = field(default_factory=dict)


class BankParser(ABC):
    bank_name: str
    file_engine: str

    @abstractmethod
    def can_parse(self, filename: str) -> bool:
        ...

    @abstractmethod
    def parse(self, file_path: str) -> list[ParsedRow]:
        ...

    def extract_account_iban(self, file_path: str) -> str | None:
        return None


# ── helpers ────────────────────────────────────────────────────────────────

def _is_na(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    try:
        return bool(pd.isna(val))
    except (TypeError, ValueError):
        return False


def _str_or_none(val: Any) -> str | None:
    if _is_na(val):
        return None
    s = str(val).strip()
    return s if s else None


def _to_date(val: Any) -> date:
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if hasattr(val, "date"):
        return val.date()
    raise ValueError(f"Cannot convert {val!r} to date")


def _parse_dmy_slash(val: Any) -> date:
    if isinstance(val, date):
        return _to_date(val)
    return datetime.strptime(str(val).strip(), "%d/%m/%Y").date()


def _parse_dmy_hyphen(val: Any) -> date:
    return datetime.strptime(str(val).strip(), "%d-%m-%Y").date()


def _parse_dmy_dot(val: Any) -> date:
    return datetime.strptime(str(val).strip(), "%d.%m.%Y").date()


def _parse_dmy_hhmm(val: Any) -> date:
    """Parse DD/MM/YYYY HH:MM, return date only."""
    s = str(val).strip()
    return datetime.strptime(s, "%d/%m/%Y %H:%M").date()


def _to_decimal(val: Any) -> Decimal:
    if _is_na(val):
        return Decimal("0")
    try:
        return Decimal(str(round(float(val), 2)))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _eu_str_to_decimal(val: Any) -> Decimal:
    """Parse European number strings: '1.234,56' or '-38.000,00 €'."""
    s = str(val).strip().replace("€", "").replace("\xa0", "").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def _serialize_row(row: pd.Series) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in row.items():
        if _is_na(v):
            result[str(k)] = None
        elif hasattr(v, "item"):  # numpy scalar
            result[str(k)] = v.item()
        elif isinstance(v, (datetime, date)):
            result[str(k)] = v.isoformat()
        elif hasattr(v, "isoformat"):
            result[str(k)] = v.isoformat()
        else:
            result[str(k)] = v
    return result
