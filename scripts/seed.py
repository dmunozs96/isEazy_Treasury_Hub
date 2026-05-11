"""
Seed script — populates companies, category taxonomy (v1.1), and classification rules.
Run once after `alembic upgrade head` on a fresh database.

Usage:
    cd backend
    python ../scripts/seed.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/treasury_hub",
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Companies — confirmed by CFO 2026-05-11
# ---------------------------------------------------------------------------

COMPANIES = [
    {"name": "Bizpills Group BPO, S.L.", "short_name": "BPO", "tax_id": None, "is_holding": True},
    {"name": "IsEazy, S.L.", "short_name": "AUTHOR", "tax_id": None, "is_holding": False},
    {"name": "IsEazy Skills, S.L.", "short_name": "SKILLS", "tax_id": None, "is_holding": False},
    {"name": "IsEazy Factory, S.L.", "short_name": "FACTORY", "tax_id": None, "is_holding": False},
    {"name": "IsEazy Engage, S.L.", "short_name": "ENGAGE", "tax_id": None, "is_holding": False},
    {"name": "IsEazy LMS, S.L.", "short_name": "LMS", "tax_id": None, "is_holding": False},
]


# ---------------------------------------------------------------------------
# Category taxonomy v1.1 — validated by CFO (Spec 08 v1.1, session 2 2026-05-11)
# Ordered: level-1 section headers first, then level-2 leaves.
# ---------------------------------------------------------------------------

TAXONOMY = [
    # Section headers (level 1) — grouping only, not directly assignable
    {"code": "OPERATING",  "parent_code": None, "name": "Flujos de Operaciones",
     "description": "Cobros y pagos de la actividad ordinaria",           "cash_flow_section": "OPERATING",    "level": 1},
    {"code": "INVESTING",  "parent_code": None, "name": "Flujos de Inversión",
     "description": "Adquisiciones y ventas de activos",                  "cash_flow_section": "INVESTING",    "level": 1},
    {"code": "FINANCING",  "parent_code": None, "name": "Flujos de Financiación",
     "description": "Deuda, depósitos, dividendos y capital",             "cash_flow_section": "FINANCING",    "level": 1},
    {"code": "INTERNAL",   "parent_code": None, "name": "Flujos Internos",
     "description": "Transferencias entre entidades del grupo",           "cash_flow_section": "INTERNAL",     "level": 1},

    # Operating (OCF)
    {"code": "OCF_INCOME",   "parent_code": "OPERATING", "name": "Ingresos de Explotación",
     "description": "Cobros de clientes y otros ingresos operativos",     "cash_flow_section": "OPERATING",    "level": 2},
    {"code": "OCF_PAYMENTS", "parent_code": "OPERATING", "name": "Pagos de Explotación",
     "description": "Pagos a proveedores y gastos operativos",            "cash_flow_section": "OPERATING",    "level": 2},
    {"code": "OCF_PAYROLL",  "parent_code": "OPERATING", "name": "Nóminas y Seguridad Social",
     "description": "Salarios, nóminas y cotizaciones a la SS",           "cash_flow_section": "OPERATING",    "level": 2},
    {"code": "OCF_TAX",      "parent_code": "OPERATING", "name": "Impuestos",
     "description": "IVA, Impuesto de Sociedades, IRPF y otros tributos", "cash_flow_section": "OPERATING",    "level": 2},

    # Investing (ICF)
    {"code": "ICF_CAPEX",      "parent_code": "INVESTING", "name": "Inversión en Inmovilizado (CAPEX)",
     "description": "Adquisición de activos fijos e intangibles",         "cash_flow_section": "INVESTING",    "level": 2},
    {"code": "ICF_ASSET_SALE", "parent_code": "INVESTING", "name": "Venta de Activos",
     "description": "Ingresos por venta o desinversión de inmovilizado",  "cash_flow_section": "INVESTING",    "level": 2},

    # Financing (FCF)
    {"code": "FCF_DEBT_DRAWDOWN",  "parent_code": "FINANCING", "name": "Disposición de Deuda",
     "description": "Entrada de efectivo por préstamos o líneas de crédito","cash_flow_section": "FINANCING",  "level": 2},
    {"code": "FCF_DEBT_REPAYMENT", "parent_code": "FINANCING", "name": "Amortización de Deuda",
     "description": "Devolución de principal de préstamos",               "cash_flow_section": "FINANCING",    "level": 2},
    {"code": "FCF_INTEREST",       "parent_code": "FINANCING", "name": "Pago de Intereses",
     "description": "Intereses pagados sobre deuda financiera",           "cash_flow_section": "FINANCING",    "level": 2},
    {"code": "FCF_DEPOSIT_ISSUED", "parent_code": "FINANCING", "name": "Depósito Constituido",
     "description": "Efectivo colocado en depósito bancario (salida)",    "cash_flow_section": "FINANCING",    "level": 2},
    {"code": "FCF_DEPOSIT_INCOME", "parent_code": "FINANCING", "name": "Intereses de Depósito",
     "description": "Intereses periódicos recibidos durante el depósito", "cash_flow_section": "FINANCING",    "level": 2},
    {"code": "FCF_DEPOSIT_RETURN", "parent_code": "FINANCING", "name": "Vencimiento de Depósito",
     "description": "Devolución del principal al vencimiento",            "cash_flow_section": "FINANCING",    "level": 2},
    {"code": "FCF_DIVIDENDS",      "parent_code": "FINANCING", "name": "Dividendos",
     "description": "Dividendos pagados a socios o accionistas (poco frecuente)", "cash_flow_section": "FINANCING", "level": 2},
    {"code": "FCF_EQUITY",         "parent_code": "FINANCING", "name": "Aportaciones de Capital",
     "description": "Ampliaciones de capital o aportaciones de socios",  "cash_flow_section": "FINANCING",    "level": 2},

    # Internal
    {"code": "INT_INTERCOMPANY",         "parent_code": "INTERNAL", "name": "Transferencia Intercompany",
     "description": "Transferencias entre las 6 entidades del grupo español — eliminadas en consolidado",
     "cash_flow_section": "INTERNAL", "level": 2},
    {"code": "INT_INTERCOMPANY_FOREIGN", "parent_code": "INTERNAL", "name": "Intercompany Extranjero",
     "description": "Transferencias con entidades extranjeras (Bélgica, Colombia, México, Puerto Rico) — NO eliminadas",
     "cash_flow_section": "INTERNAL", "level": 2},

    # Unclassified — standalone (no parent)
    {"code": "UNCLASSIFIED", "parent_code": None, "name": "Sin Clasificar",
     "description": "Sin categoría asignada — pendiente de revisión manual",
     "cash_flow_section": "UNCLASSIFIED", "level": 1},
]


# ---------------------------------------------------------------------------
# Classification rules — Spec 08 v1.1 Section 7
# Intercompany first (priority 5), then standard treasury rules
# ---------------------------------------------------------------------------

# Keywords from company_registry.md — confirmed by CFO 2026-05-11
_INTERCOMPANY_KEYWORDS = [
    "BIZPILLS", "BPO",
    "ISEAZY", "ISAZY", "AUTHOR", "AUTHORING",
    "SKILLS",
    "FACTORY",
    "ENGAGE",
    "LMS",
]

RULES = [
    *[
        {
            "name": f"Intercompany doméstico — {kw}",
            "priority": 5,
            "match_type": "KEYWORD",
            "match_field": "description",
            "match_pattern": kw,
            "category_code": "INT_INTERCOMPANY",
        }
        for kw in _INTERCOMPANY_KEYWORDS
    ],

    # Standard treasury rules
    {"name": "Seguridad Social",            "priority": 10, "match_type": "COUNTERPART_NAME", "match_field": "counterpart_name", "match_pattern": "TESORERIA GENERAL",    "category_code": "OCF_PAYROLL"},
    {"name": "Hacienda — contraparte",      "priority": 11, "match_type": "COUNTERPART_NAME", "match_field": "counterpart_name", "match_pattern": "AGENCIA TRIBUTARIA",   "category_code": "OCF_TAX"},
    {"name": "Hacienda — descripción",      "priority": 12, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "HACIENDA",             "category_code": "OCF_TAX"},
    {"name": "Nóminas",                     "priority": 20, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "NOMINA",               "category_code": "OCF_PAYROLL"},
    {"name": "Salarios",                    "priority": 21, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "SALARIO",              "category_code": "OCF_PAYROLL"},
    {"name": "IVA",                         "priority": 30, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "LIQUIDACION IVA",      "category_code": "OCF_TAX"},
    {"name": "Impuesto Sociedades",         "priority": 31, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "IMPUESTO SOCIEDADES",  "category_code": "OCF_TAX"},
    {"name": "Liquidación intereses deuda", "priority": 40, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "LIQUIDACION INTERES",  "category_code": "FCF_INTEREST"},
    {"name": "Cuota interés préstamo",      "priority": 41, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "CUOTA INTERES",        "category_code": "FCF_INTEREST"},
    {"name": "Amortización préstamo",       "priority": 50, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "AMORTIZACION PRESTAMO","category_code": "FCF_DEBT_REPAYMENT"},
    {"name": "Cuota préstamo",              "priority": 51, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "CUOTA PRESTAMO",       "category_code": "FCF_DEBT_REPAYMENT"},
    {"name": "Disposición crédito",         "priority": 60, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "DISPOSICION CREDITO",  "category_code": "FCF_DEBT_DRAWDOWN"},
    {"name": "Constitución depósito",       "priority": 70, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "CONSTITUCION DEPOSITO","category_code": "FCF_DEPOSIT_ISSUED"},
    {"name": "Cancelación depósito",        "priority": 71, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "CANCELACION DEPOSITO", "category_code": "FCF_DEPOSIT_RETURN"},
    {"name": "Liquidación depósito",        "priority": 72, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "LIQUIDACION DEPOSITO", "category_code": "FCF_DEPOSIT_INCOME"},
    {"name": "Compra inmovilizado (CAPEX)", "priority": 80, "match_type": "KEYWORD",          "match_field": "description",      "match_pattern": "COMPRA INMOVILIZADO",  "category_code": "ICF_CAPEX"},
]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

async def seed_companies(db: AsyncSession):
    for data in COMPANIES:
        result = await db.execute(
            text("SELECT id FROM companies WHERE short_name = :short_name"),
            {"short_name": data["short_name"]},
        )
        if result.fetchone():
            print(f"  Company '{data['short_name']}' already exists, skipping.")
            continue
        await db.execute(
            text("""
                INSERT INTO companies (name, short_name, tax_id, is_holding, is_active)
                VALUES (:name, :short_name, :tax_id, :is_holding, true)
            """),
            data,
        )
        print(f"  Inserted company: {data['short_name']}")


async def seed_taxonomy(db: AsyncSession):
    # Process level 1 first to satisfy FK constraints
    for entry in sorted(TAXONOMY, key=lambda x: x["level"]):
        result = await db.execute(
            text("SELECT code FROM category_taxonomy WHERE code = :code"),
            {"code": entry["code"]},
        )
        if result.fetchone():
            print(f"  Taxonomy '{entry['code']}' already exists, skipping.")
            continue
        await db.execute(
            text("""
                INSERT INTO category_taxonomy (code, parent_code, name, description, cash_flow_section, level, is_active)
                VALUES (:code, :parent_code, :name, :description, :cash_flow_section, :level, true)
            """),
            entry,
        )
        print(f"  Inserted taxonomy: {entry['code']}")


async def seed_rules(db: AsyncSession):
    for rule in RULES:
        result = await db.execute(
            text("SELECT id FROM classification_rules WHERE name = :name"),
            {"name": rule["name"]},
        )
        if result.fetchone():
            print(f"  Rule '{rule['name']}' already exists, skipping.")
            continue
        await db.execute(
            text("""
                INSERT INTO classification_rules
                    (name, priority, is_active, match_type, match_field, match_pattern, category_code, created_by)
                VALUES
                    (:name, :priority, true, :match_type, :match_field, :match_pattern, :category_code, 'seed')
            """),
            rule,
        )
        print(f"  Inserted rule: {rule['name']}")


async def seed():
    async with SessionLocal() as db:
        print("\n--- Companies ---")
        await seed_companies(db)
        print("\n--- Category taxonomy ---")
        await seed_taxonomy(db)
        print("\n--- Classification rules ---")
        await seed_rules(db)
        await db.commit()
    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
