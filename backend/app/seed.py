"""Seed baseline reference data for a fresh Railway database.

Run inside the backend container:
    python -m app.seed
"""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.database import AsyncSessionLocal


COMPANIES = [
    {"name": "Bizpills Group BPO, S.L.", "short_name": "BPO", "is_holding": True},
    {"name": "IsEazy, S.L.", "short_name": "AUTHOR", "is_holding": False},
    {"name": "IsEazy Skills, S.L.", "short_name": "SKILLS", "is_holding": False},
    {"name": "IsEazy Factory, S.L.", "short_name": "FACTORY", "is_holding": False},
    {"name": "IsEazy Engage, S.L.", "short_name": "ENGAGE", "is_holding": False},
    {"name": "IsEazy LMS, S.L.", "short_name": "LMS", "is_holding": False},
]


TAXONOMY = [
    ("OPERATING", None, "Flujos de Operaciones", "Cobros y pagos de la actividad ordinaria", "OPERATING", 1),
    ("INVESTING", None, "Flujos de Inversion", "Adquisiciones y ventas de activos", "INVESTING", 1),
    ("FINANCING", None, "Flujos de Financiacion", "Deuda, depositos, dividendos y capital", "FINANCING", 1),
    ("INTERNAL", None, "Flujos Internos", "Transferencias entre entidades del grupo", "INTERNAL", 1),
    ("OCF_INCOME", "OPERATING", "Ingresos de Explotacion", "Cobros de clientes y otros ingresos operativos", "OPERATING", 2),
    ("OCF_PAYMENTS", "OPERATING", "Pagos de Explotacion", "Pagos a proveedores y gastos operativos", "OPERATING", 2),
    ("OCF_PAYROLL", "OPERATING", "Nominas y Seguridad Social", "Salarios, nominas y cotizaciones", "OPERATING", 2),
    ("OCF_TAX", "OPERATING", "Impuestos", "IVA, sociedades, IRPF y otros tributos", "OPERATING", 2),
    ("ICF_CAPEX", "INVESTING", "Inversion en Inmovilizado", "Adquisicion de activos fijos e intangibles", "INVESTING", 2),
    ("ICF_ASSET_SALE", "INVESTING", "Venta de Activos", "Ingresos por venta de inmovilizado", "INVESTING", 2),
    ("FCF_DEBT_DRAWDOWN", "FINANCING", "Disposicion de Deuda", "Entrada de efectivo por deuda", "FINANCING", 2),
    ("FCF_DEBT_REPAYMENT", "FINANCING", "Amortizacion de Deuda", "Devolucion de principal", "FINANCING", 2),
    ("FCF_INTEREST", "FINANCING", "Pago de Intereses", "Intereses pagados sobre deuda", "FINANCING", 2),
    ("FCF_DEPOSIT_ISSUED", "FINANCING", "Deposito Constituido", "Efectivo colocado en deposito", "FINANCING", 2),
    ("FCF_DEPOSIT_INCOME", "FINANCING", "Intereses de Deposito", "Intereses recibidos de depositos", "FINANCING", 2),
    ("FCF_DEPOSIT_RETURN", "FINANCING", "Vencimiento de Deposito", "Devolucion del principal", "FINANCING", 2),
    ("FCF_DIVIDENDS", "FINANCING", "Dividendos", "Dividendos pagados", "FINANCING", 2),
    ("FCF_EQUITY", "FINANCING", "Aportaciones de Capital", "Capital y aportaciones de socios", "FINANCING", 2),
    ("INT_INTERCOMPANY", "INTERNAL", "Transferencia Intercompany", "Transferencias entre entidades espanolas del grupo", "INTERNAL", 2),
    ("INT_INTERCOMPANY_FOREIGN", "INTERNAL", "Intercompany Extranjero", "Transferencias con entidades extranjeras", "INTERNAL", 2),
    ("UNCLASSIFIED", None, "Sin Clasificar", "Pendiente de revision manual", "UNCLASSIFIED", 1),
]


INTERCOMPANY_KEYWORDS = [
    "BIZPILLS",
    "BPO",
    "ISEAZY",
    "ISAZY",
    "AUTHOR",
    "AUTHORING",
    "SKILLS",
    "FACTORY",
    "ENGAGE",
    "LMS",
]


RULES = [
    *[
        (f"Intercompany domestico - {kw}", 5, "KEYWORD", "description", kw, "INT_INTERCOMPANY")
        for kw in INTERCOMPANY_KEYWORDS
    ],
    ("Seguridad Social", 10, "COUNTERPART_NAME", "counterpart_name", "TESORERIA GENERAL", "OCF_PAYROLL"),
    ("Hacienda - contraparte", 11, "COUNTERPART_NAME", "counterpart_name", "AGENCIA TRIBUTARIA", "OCF_TAX"),
    ("Hacienda - descripcion", 12, "KEYWORD", "description", "HACIENDA", "OCF_TAX"),
    ("Nominas", 20, "KEYWORD", "description", "NOMINA", "OCF_PAYROLL"),
    ("Salarios", 21, "KEYWORD", "description", "SALARIO", "OCF_PAYROLL"),
    ("IVA", 30, "KEYWORD", "description", "LIQUIDACION IVA", "OCF_TAX"),
    ("Impuesto Sociedades", 31, "KEYWORD", "description", "IMPUESTO SOCIEDADES", "OCF_TAX"),
    ("Liquidacion intereses deuda", 40, "KEYWORD", "description", "LIQUIDACION INTERES", "FCF_INTEREST"),
    ("Cuota interes prestamo", 41, "KEYWORD", "description", "CUOTA INTERES", "FCF_INTEREST"),
    ("Amortizacion prestamo", 50, "KEYWORD", "description", "AMORTIZACION PRESTAMO", "FCF_DEBT_REPAYMENT"),
    ("Cuota prestamo", 51, "KEYWORD", "description", "CUOTA PRESTAMO", "FCF_DEBT_REPAYMENT"),
    ("Disposicion credito", 60, "KEYWORD", "description", "DISPOSICION CREDITO", "FCF_DEBT_DRAWDOWN"),
    ("Constitucion deposito", 70, "KEYWORD", "description", "CONSTITUCION DEPOSITO", "FCF_DEPOSIT_ISSUED"),
    ("Cancelacion deposito", 71, "KEYWORD", "description", "CANCELACION DEPOSITO", "FCF_DEPOSIT_RETURN"),
    ("Liquidacion deposito", 72, "KEYWORD", "description", "LIQUIDACION DEPOSITO", "FCF_DEPOSIT_INCOME"),
    ("Compra inmovilizado", 80, "KEYWORD", "description", "COMPRA INMOVILIZADO", "ICF_CAPEX"),
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        for company in COMPANIES:
            await db.execute(
                text(
                    """
                    INSERT INTO companies (name, short_name, tax_id, is_holding, is_active)
                    SELECT :name, :short_name, NULL, :is_holding, true
                    WHERE NOT EXISTS (
                        SELECT 1 FROM companies WHERE short_name = :short_name
                    )
                    """
                ),
                company,
            )
            await db.execute(
                text(
                    """
                    UPDATE companies
                    SET name = :name, is_holding = :is_holding, is_active = true
                    WHERE short_name = :short_name
                    """
                ),
                company,
            )

        for code, parent_code, name, description, section, level in TAXONOMY:
            await db.execute(
                text(
                    """
                    INSERT INTO category_taxonomy
                        (code, parent_code, name, description, cash_flow_section, level, is_active)
                    VALUES
                        (:code, :parent_code, :name, :description, :section, :level, true)
                    ON CONFLICT (code) DO UPDATE SET
                        parent_code = EXCLUDED.parent_code,
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        cash_flow_section = EXCLUDED.cash_flow_section,
                        level = EXCLUDED.level,
                        is_active = true
                    """
                ),
                {
                    "code": code,
                    "parent_code": parent_code,
                    "name": name,
                    "description": description,
                    "section": section,
                    "level": level,
                },
            )

        for name, priority, match_type, match_field, match_pattern, category_code in RULES:
            await db.execute(
                text(
                    """
                    INSERT INTO classification_rules
                        (name, priority, is_active, match_type, match_field, match_pattern, category_code, created_by)
                    VALUES
                        (:name, :priority, true, :match_type, :match_field, :match_pattern, :category_code, 'seed')
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "name": name,
                    "priority": priority,
                    "match_type": match_type,
                    "match_field": match_field,
                    "match_pattern": match_pattern,
                    "category_code": category_code,
                },
            )

        await db.commit()

    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(main())
