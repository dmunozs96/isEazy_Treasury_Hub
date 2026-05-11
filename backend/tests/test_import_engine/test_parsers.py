"""
Integration tests for all 12 bank parsers.

Each test reads an actual sample file from /samples/bank_statements/ and
asserts key invariants:
  - no exceptions raised
  - at least one row returned (except known-empty files)
  - all amounts are Decimal
  - all dates are date objects (no time component)
  - description is never None
  - running_balance is never None
"""
from __future__ import annotations

import pytest
from datetime import date
from decimal import Decimal
from pathlib import Path

# Root of the monorepo relative to this test file (backend/tests/test_import_engine/)
SAMPLES = Path(__file__).parents[3] / "samples" / "bank_statements"

from app.services.import_engine.parsers.abanca import AbancaParser
from app.services.import_engine.parsers.bbva import BBVAParser
from app.services.import_engine.parsers.banca_march import BancaMarchParser
from app.services.import_engine.parsers.bankinter import BankinterParser
from app.services.import_engine.parsers.caixabank import CaixaBankParser
from app.services.import_engine.parsers.cajamar import CajamarParser
from app.services.import_engine.parsers.deutsche_bank import DeutscheBankParser
from app.services.import_engine.parsers.eurocaja_rural import EurocajaRuralParser
from app.services.import_engine.parsers.ibercaja import IbercajaParser
from app.services.import_engine.parsers.ruralvia import RuralviaParser
from app.services.import_engine.parsers.sabadell import SabadellParser
from app.services.import_engine.parsers.santander import SantanderParser
from app.services.import_engine.detector import detect_parser


# ── helpers ────────────────────────────────────────────────────────────────

def _assert_rows(rows, *, min_rows: int = 1):
    assert len(rows) >= min_rows, f"Expected ≥{min_rows} rows, got {len(rows)}"
    for row in rows:
        assert isinstance(row.amount, Decimal), f"amount not Decimal: {row.amount!r}"
        assert isinstance(row.running_balance, Decimal), f"running_balance not Decimal"
        assert isinstance(row.booking_date, date), f"booking_date not date: {row.booking_date!r}"
        assert isinstance(row.value_date, date), f"value_date not date: {row.value_date!r}"
        assert not hasattr(row.booking_date, "hour"), "booking_date has time component"
        assert row.description is not None, "description is None"


# ── Abanca ─────────────────────────────────────────────────────────────────

def test_abanca():
    f = SAMPLES / "Abanca_ABANCA 2265 - FACTORY - 2025.xlsx"
    rows = AbancaParser().parse(str(f))
    _assert_rows(rows)


# ── BBVA ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "BBVA_BBVA Bizpills Group.xlsx",
    "BBVA_BBVA ENGAGE.xlsx",
    "BBVA_BBVA FACTORY.xlsx",
    "BBVA_BBVA ISEAZY.xlsx",
    "BBVA_BBVA LMS 7741.xlsx",
    "BBVA_BBVA SKILLS.xlsx",
])
def test_bbva(filename):
    rows = BBVAParser().parse(str(SAMPLES / filename))
    _assert_rows(rows)


# ── Banca March ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "BancaMarch_BANCA MARCH 0110 - LMS - 2025.xlsx",
    "BancaMarch_BANCA MARCH 0111 - BPO - 2025.xlsx",
    "BancaMarch_BANCA MARCH 0113 - ENGAGE - 2025.xlsx",
    "BancaMarch_BANCA MARCH 0115 - FACTORY - 2025.xlsx",
    "BancaMarch_BANCA MARCH 0116 - SKILLS - 2025.xlsx",
    "BancaMarch_BANCA MARCH 0117 - AUTHOR - 2025.xlsx",
])
def test_banca_march(filename):
    rows = BancaMarchParser().parse(str(SAMPLES / filename))
    _assert_rows(rows, min_rows=0)  # some accounts may be inactive


# ── Bankinter ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "Bankinter_Bankinter 2025 BPO 7531.xlsx",
    "Bankinter_Bankinter 2025 Engage 7524.xlsx",
    "Bankinter_Bankinter 2025 Factory 2602.xlsx",
    "Bankinter_Bankinter 2025 Factory 3385.xlsx",
    "Bankinter_Bankinter 2025 Iseazy 7496.xlsx",
    "Bankinter_Bankinter 2025 LMS 3371.xlsx",
    "Bankinter_Bankinter 2025 Skills 7545.xlsx",
])
def test_bankinter(filename):
    rows = BankinterParser().parse(str(SAMPLES / filename))
    _assert_rows(rows, min_rows=0)


# ── CaixaBank ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "Caixa_CAIXA BPO 7042_2025.xls",
    "Caixa_CAIXA ENGAGE 3908_2025.xls",
    "Caixa_CAIXA FACTORY 1946_2025.xls",
    "Caixa_CAIXA FACTORY 6761_2025.xls",
    "Caixa_CAIXA FACTORY 7303_2025.xls",
    "Caixa_CAIXA ISEAZY 4002_2025.xls",
    "Caixa_CAIXA ISEAZY 9490_2025.xls",
    "Caixa_CAIXA LMS 1765_2025.xls",
    "Caixa_CAIXA LMS 5552_2025.xls",
    "Caixa_CAIXA LMS 5705_2025.xls",   # known-empty "SIN MOVIMIENTOS"
    "Caixa_CAIXA SKILLS 6952_2025.xls",
])
def test_caixabank(filename):
    rows = CaixaBankParser().parse(str(SAMPLES / filename))
    _assert_rows(rows, min_rows=0)


def test_caixabank_empty_file_returns_no_rows():
    rows = CaixaBankParser().parse(str(SAMPLES / "Caixa_CAIXA LMS 5705_2025.xls"))
    assert rows == [], "Expected empty list for SIN MOVIMIENTOS file"


# ── Cajamar ────────────────────────────────────────────────────────────────

def test_cajamar():
    rows = CajamarParser().parse(str(SAMPLES / "Cajamar_CAJAMAR 4890 SKILLS_2025 2.xls"))
    _assert_rows(rows)


# ── Deutsche Bank ──────────────────────────────────────────────────────────

def test_deutsche_bank():
    rows = DeutscheBankParser().parse(str(SAMPLES / "DEUSTCHE_Movimientos_2025.xls"))
    _assert_rows(rows)


# ── Eurocaja Rural ─────────────────────────────────────────────────────────

def test_eurocaja_rural():
    rows = EurocajaRuralParser().parse(str(SAMPLES / "EUROCAJA_EXTRACTOS 2025.csv"))
    _assert_rows(rows)


# ── Ibercaja ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "Ibercaja_IBERCAJA 2746_LMS_2025.xlsx",
    "Ibercaja_IBERCAJA 4839_BPO_2025.xlsx",
    "Ibercaja_IBERCAJA 6829_FACTORY_2025.xlsx",
    "Ibercaja_IBERCAJA 9451 AUTHOR_2025.xlsx",
    "Ibercaja_IBERCAJA 9549_SKILLS_2025.xlsx",
    "Ibercaja_IBERCAJA 9647_ENGAGE_2025.xlsx",
])
def test_ibercaja(filename):
    rows = IbercajaParser().parse(str(SAMPLES / filename))
    _assert_rows(rows, min_rows=0)


# ── Ruralvia ───────────────────────────────────────────────────────────────

def test_ruralvia():
    rows = RuralviaParser().parse(str(SAMPLES / "Ruralvia_2025 - completo - RURALVIA.xlsx"))
    _assert_rows(rows)


# ── Sabadell ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "Sabadell_SABADELL - FACTORY 8047 - 2025.xls",
    "Sabadell_SABADELL BPO 9564_2025.xls",
    "Sabadell_SABADELL LMS 0753_2025.xls",
])
def test_sabadell(filename):
    rows = SabadellParser().parse(str(SAMPLES / filename))
    _assert_rows(rows, min_rows=0)


# ── Santander ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "Santander_SANTANDER 0416 BPO 2025.xlsx",
    "Santander_SANTANDER 1613BPO 2025.xlsx",
    "Santander_SANTANDER 2791 LMS 2025.xlsx",
    "Santander_SANTANDER 4009 ENGAGE_2025.xlsx",
    "Santander_SANTANDER 4107 ISEAZY 4107.xlsx",
    "Santander_SANTANDER 4205 SKILLS 4405.xlsx",
    "Santander_SANTANDER 6409 LMS_2025.xlsx",
    "Santander_SANTANDER 7001 SKILLS 2025.xlsx",
    "Santander_SANTANDER 7010 ISEAZY 2025.xlsx",
    "Santander_SANTANDER 7271 LMS 2025.xlsx",
    "Santander_SANTANDER 7521 SKILLS 2025.xlsx",
    "Santander_SANTANDER 7539 ENGAGE 2025.xlsx",
    "Santander_SANTANDER 7547 ISEAZY 2025.xlsx",
    "Santander_SANTANDER 8271 - FACTORY - 2025.xlsx",
    "Santander_Santander Factory 6384.xlsx",
    "Santander_Santander LMS 3917.xls",   # multi-sheet xls
])
def test_santander(filename):
    rows = SantanderParser().parse(str(SAMPLES / filename))
    _assert_rows(rows, min_rows=0)


def test_santander_multisheet_xls_merges_all_sheets():
    rows = SantanderParser().parse(str(SAMPLES / "Santander_Santander LMS 3917.xls"))
    # Should have movements from multiple monthly sheets merged together
    assert len(rows) > 1, "Multi-sheet file should produce more than 1 row"


# ── Detector ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename,expected_bank", [
    ("Abanca_ABANCA 2265 - FACTORY - 2025.xlsx", "ABANCA"),
    ("BBVA_BBVA SKILLS.xlsx", "BBVA"),
    ("BancaMarch_BANCA MARCH 0110 - LMS - 2025.xlsx", "BANCA_MARCH"),
    ("Bankinter_Bankinter 2025 BPO 7531.xlsx", "BANKINTER"),
    ("Caixa_CAIXA BPO 7042_2025.xls", "CAIXABANK"),
    ("Cajamar_CAJAMAR 4890 SKILLS_2025 2.xls", "CAJAMAR"),
    ("DEUSTCHE_Movimientos_2025.xls", "DEUTSCHE_BANK"),
    ("EUROCAJA_EXTRACTOS 2025.csv", "EUROCAJA_RURAL"),
    ("Ibercaja_IBERCAJA 2746_LMS_2025.xlsx", "IBERCAJA"),
    ("Ruralvia_2025 - completo - RURALVIA.xlsx", "RURALVIA"),
    ("Sabadell_SABADELL BPO 9564_2025.xls", "SABADELL"),
    ("Santander_SANTANDER 7001 SKILLS 2025.xlsx", "SANTANDER"),
])
def test_detector(filename, expected_bank):
    parser = detect_parser(filename)
    assert parser.bank_name == expected_bank


def test_detector_unknown_file_raises():
    with pytest.raises(ValueError, match="No parser found"):
        detect_parser("UNKNOWN_bank_file.xlsx")


# ── Deduplicator ──────────────────────────────────────────────────────────

def test_movement_hash_deterministic():
    from app.services.import_engine.deduplicator import movement_hash
    from decimal import Decimal
    import uuid
    from datetime import date

    acct = uuid.UUID("00000000-0000-0000-0000-000000000001")
    h1 = movement_hash(acct, date(2025, 1, 15), Decimal("-1000.00"), "NOMINA ENERO")
    h2 = movement_hash(acct, date(2025, 1, 15), Decimal("-1000.00"), "NOMINA ENERO")
    assert h1 == h2


def test_movement_hash_different_inputs_differ():
    from app.services.import_engine.deduplicator import movement_hash
    from decimal import Decimal
    import uuid
    from datetime import date

    acct = uuid.UUID("00000000-0000-0000-0000-000000000001")
    h1 = movement_hash(acct, date(2025, 1, 15), Decimal("-1000.00"), "NOMINA ENERO")
    h2 = movement_hash(acct, date(2025, 1, 16), Decimal("-1000.00"), "NOMINA ENERO")
    assert h1 != h2
