"""Build a deterministic DuckDB fixture for the web E2E tests.

The fixture mirrors the serving tables produced by the pipeline. It is explicit:
no random values, no dependency on the real bulk. Run it standalone with:

    python web/tests/seed_db.py --output C:/temp/contratamype-test.duckdb
"""

from __future__ import annotations

import argparse
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb

TENDER_COLUMNS = [
    "ocid",
    "title",
    "description",
    "category",
    "method",
    "amount_pen",
    "currency",
    "published_date",
    "tender_start",
    "tender_end",
    "status",
    "buyer_id",
    "buyer_name",
    "department",
    "department_code",
    "segmentation_id",
    "segmentation_year",
    "mype_fit",
    "dates_valid",
    "period_start_eq_end",
]
BUYER_COLUMNS = ["buyer_id", "name", "ruc", "department"]
SUPPLIER_COLUMNS = ["supplier_id", "name", "ruc", "department"]
AWARD_COLUMNS = [
    "ocid",
    "award_id",
    "supplier_id",
    "supplier_name",
    "amount_pen",
    "award_date",
    "status",
]
CONTRACT_COLUMNS = ["ocid", "contract_id", "award_id", "amount_pen", "signed_date", "status"]

DDL = {
    "tenders": """
        CREATE TABLE tenders (
            ocid VARCHAR, title VARCHAR, description VARCHAR, category VARCHAR,
            method VARCHAR, amount_pen DECIMAL(18,2), currency VARCHAR,
            published_date DATE, tender_start DATE, tender_end DATE, status VARCHAR,
            buyer_id VARCHAR, buyer_name VARCHAR, department VARCHAR,
            department_code VARCHAR, segmentation_id VARCHAR, segmentation_year INTEGER,
            mype_fit BOOLEAN, dates_valid BOOLEAN, period_start_eq_end BOOLEAN
        )
    """,
    "buyers": (
        "CREATE TABLE buyers (buyer_id VARCHAR, name VARCHAR, ruc VARCHAR, department VARCHAR)"
    ),
    "suppliers": (
        "CREATE TABLE suppliers "
        "(supplier_id VARCHAR, name VARCHAR, ruc VARCHAR, department VARCHAR)"
    ),
    "awards": """
        CREATE TABLE awards (
            ocid VARCHAR, award_id VARCHAR, supplier_id VARCHAR, supplier_name VARCHAR,
            amount_pen DECIMAL(18,2), award_date DATE, status VARCHAR
        )
    """,
    "contracts": """
        CREATE TABLE contracts (
            ocid VARCHAR, contract_id VARCHAR, award_id VARCHAR,
            amount_pen DECIMAL(18,2), signed_date DATE, status VARCHAR
        )
    """,
}


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _money(value: str | int | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


BUYERS = [
    {
        "buyer_id": "B1",
        "name": "Municipalidad Distrital de San Isidro",
        "ruc": "20100000001",
        "department": "LIMA",
    },
    {
        "buyer_id": "B2",
        "name": "Gobierno Regional de Cusco",
        "ruc": "20100000002",
        "department": "CUSCO",
    },
    {
        "buyer_id": "B3",
        "name": "Municipalidad Provincial de Arequipa",
        "ruc": "20100000003",
        "department": "AREQUIPA",
    },
    {
        "buyer_id": "B4",
        "name": "Entidad Pública de Prueba",
        "ruc": "20100000004",
        "department": "PIURA",
    },
    {
        "buyer_id": "B5",
        "name": "Gobierno Regional de Loreto",
        "ruc": "20100000005",
        "department": "LORETO",
    },
]

SUPPLIERS = [
    {
        "supplier_id": "S1",
        "name": "Tecnología Andina SAC",
        "ruc": "20500000001",
        "department": "LIMA",
    },
    {
        "supplier_id": "S2",
        "name": "Consultores del Sur EIRL",
        "ruc": "20500000002",
        "department": "CUSCO",
    },
    {
        "supplier_id": "S3",
        "name": "Suministros del Norte SAC",
        "ruc": "20500000003",
        "department": "LORETO",
    },
]

TENDERS = [
    {
        "ocid": "ocds-test-0001",
        "title": "Compra de laptops para capacitación",
        "description": (
            "Adquisición de 40 laptops para el programa de capacitación digital "
            "de la municipalidad."
        ),
        "category": "goods",
        "method": "Adjudicación Simplificada",
        "amount_pen": _money(120000),
        "currency": "PEN",
        "published_date": _d("2025-02-20"),
        "tender_start": _d("2025-03-01"),
        "tender_end": _d("2025-03-15"),
        "status": "En evaluación",
        "buyer_id": "B1",
        "buyer_name": "Municipalidad Distrital de San Isidro",
        "department": "LIMA",
        "department_code": "15",
        "segmentation_id": "2025-02",
        "segmentation_year": 2025,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0002",
        "title": "Servicio de limpieza de oficinas",
        "description": None,
        "category": "services",
        "method": "Adjudicación de Menor Cuantía",
        "amount_pen": _money(80000),
        "currency": "PEN",
        "published_date": _d("2025-04-01"),
        "tender_start": _d("2025-04-10"),
        "tender_end": _d("2025-04-10"),
        "status": "En evaluación",
        "buyer_id": "B2",
        "buyer_name": "Gobierno Regional de Cusco",
        "department": "CUSCO",
        "department_code": "08",
        "segmentation_id": "2025-04",
        "segmentation_year": 2025,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": True,
    },
    {
        "ocid": "ocds-test-0003",
        "title": "Obra de mejoramiento de vereda",
        "description": "Mejoramiento de veredas en la av. Los Próceres, tramo de 300 metros.",
        "category": "works",
        "method": "Adjudicación Simplificada",
        "amount_pen": _money(0),
        "currency": "PEN",
        "published_date": _d("2025-04-15"),
        "tender_start": _d("2025-05-01"),
        "tender_end": _d("2025-05-20"),
        "status": "En evaluación",
        "buyer_id": "B3",
        "buyer_name": "Municipalidad Provincial de Arequipa",
        "department": "AREQUIPA",
        "department_code": "04",
        "segmentation_id": "2025-04",
        "segmentation_year": 2025,
        "mype_fit": False,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0004",
        "title": "Consultoría para expediente técnico",
        "description": "Elaboración del expediente técnico para la ampliación del mercado central.",
        "category": "services",
        "method": "Adjudicación Simplificada",
        "amount_pen": _money(95000),
        "currency": "PEN",
        "published_date": _d("2025-05-20"),
        "tender_start": _d("2025-06-01"),
        "tender_end": _d("2025-06-30"),
        "status": "Adjudicado",
        "buyer_id": "B1",
        "buyer_name": "Municipalidad Distrital de San Isidro",
        "department": "LIMA",
        "department_code": "15",
        "segmentation_id": "2025-05",
        "segmentation_year": 2025,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0005",
        "title": "Adquisición de mobiliario escolar",
        "description": "Compra de carpetas y sillas para instituciones educativas.",
        "category": "goods",
        "method": "Adjudicación Directa Selectiva",
        "amount_pen": _money(50000),
        "currency": "PEN",
        "published_date": _d("2025-06-10"),
        "tender_start": _d("2025-07-01"),
        "tender_end": _d("2025-07-15"),
        "status": "En evaluación",
        "buyer_id": None,
        "buyer_name": None,
        "department": "DESCONOCIDO",
        "department_code": None,
        "segmentation_id": "2025-06",
        "segmentation_year": 2025,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0006",
        "title": "Servicio de jardinería y mantenimiento",
        "description": "Mantenimiento de áreas verdes de la sede regional.",
        "category": "services",
        "method": "Comparación de Precios",
        "amount_pen": _money(30000),
        "currency": "PEN",
        "published_date": _d("2025-07-05"),
        "tender_start": _d("2025-08-01"),
        "tender_end": _d("2025-08-05"),
        "status": "Adjudicado",
        "buyer_id": "B4",
        "buyer_name": "Entidad Pública de Prueba",
        "department": "PIURA",
        "department_code": "20",
        "segmentation_id": "2025-07",
        "segmentation_year": 2025,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0007",
        "title": "Compra de uniformes escolares",
        "description": "Adquisición de uniformes para el año escolar 2026.",
        "category": "goods",
        "method": "Licitación Pública",
        "amount_pen": _money(250000),
        "currency": "PEN",
        "published_date": _d("2025-08-10"),
        "tender_start": _d("2025-09-01"),
        "tender_end": _d("2025-09-20"),
        "status": "En evaluación",
        "buyer_id": "B1",
        "buyer_name": "Municipalidad Distrital de San Isidro",
        "department": "LIMA",
        "department_code": "15",
        "segmentation_id": "2025-08",
        "segmentation_year": 2025,
        "mype_fit": False,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0008",
        "title": "Obra de saneamiento rural",
        "description": "Construcción de redes de agua potable en la comunidad de Pumamarca.",
        "category": "works",
        "method": "Licitación Pública Abreviada",
        "amount_pen": _money(450000),
        "currency": "PEN",
        "published_date": _d("2025-08-20"),
        "tender_start": _d("2025-09-05"),
        "tender_end": _d("2025-10-05"),
        "status": "En evaluación",
        "buyer_id": "B2",
        "buyer_name": "Gobierno Regional de Cusco",
        "department": "CUSCO",
        "department_code": "08",
        "segmentation_id": "2025-08",
        "segmentation_year": 2025,
        "mype_fit": False,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0009",
        "title": "Servicio de internet dedicado",
        "description": "Contratación del servicio de internet dedicado para las oficinas.",
        "category": "services",
        "method": "Comparación de Precios",
        "amount_pen": _money(15000),
        "currency": "PEN",
        "published_date": _d("2025-09-01"),
        "tender_start": _d("2025-10-01"),
        "tender_end": _d("2025-10-10"),
        "status": "Desierto",
        "buyer_id": "B1",
        "buyer_name": "Municipalidad Distrital de San Isidro",
        "department": "LIMA",
        "department_code": "15",
        "segmentation_id": "2025-09",
        "segmentation_year": 2025,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0010",
        "title": "Compra histórica fuera de la cohorte",
        "description": "Registro de 2024 que no debe aparecer en la búsqueda por defecto.",
        "category": "goods",
        "method": "Adjudicación Simplificada",
        "amount_pen": _money(10000),
        "currency": "PEN",
        "published_date": _d("2024-12-01"),
        "tender_start": _d("2024-12-05"),
        "tender_end": _d("2024-12-10"),
        "status": "Adjudicado",
        "buyer_id": "B1",
        "buyer_name": "Municipalidad Distrital de San Isidro",
        "department": "LIMA",
        "department_code": "15",
        "segmentation_id": "2024-12",
        "segmentation_year": 2024,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0011",
        "title": "Mantenimiento de local escolar",
        "description": "Mantenimiento preventivo de la infraestructura de un local escolar.",
        "category": "works",
        "method": "Adjudicación de Menor Cuantía",
        "amount_pen": _money(200000),
        "currency": "PEN",
        "published_date": _d("2025-09-15"),
        "tender_start": _d("2025-10-01"),
        "tender_end": _d("2025-10-15"),
        "status": "En evaluación",
        "buyer_id": "B1",
        "buyer_name": "Municipalidad Distrital de San Isidro",
        "department": "LIMA",
        "department_code": "15",
        "segmentation_id": "2025-09",
        "segmentation_year": 2025,
        "mype_fit": False,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
    {
        "ocid": "ocds-test-0012",
        "title": "Suministro de alimentos no perecibles",
        "description": "Compra de alimentos para los comedores populares de la región.",
        "category": "goods",
        "method": "Subasta Inversa Electrónica",
        "amount_pen": _money(60000),
        "currency": "PEN",
        "published_date": _d("2025-10-01"),
        "tender_start": _d("2025-10-20"),
        "tender_end": _d("2025-10-30"),
        "status": "Desierto",
        "buyer_id": "B5",
        "buyer_name": "Gobierno Regional de Loreto",
        "department": "LORETO",
        "department_code": "16",
        "segmentation_id": "2025-10",
        "segmentation_year": 2025,
        "mype_fit": True,
        "dates_valid": True,
        "period_start_eq_end": False,
    },
]

# Deterministic filler used only by pagination regressions: it must not match the
# filters asserted by the other tests, so all rows are non-MYPE services in Lima.
BULK_TENDERS = [
    {
        "ocid": f"ocds-test-bulk-{index:02d}",
        "title": f"Servicio recurrente {index:02d}",
        "description": f"Contrato repetitivo de servicios para la sede {index:02d}.",
        "category": "services",
        "method": "Comparación de Precios",
        "amount_pen": _money(12345),
        "currency": "PEN",
        "published_date": _d("2025-11-01"),
        "tender_start": _d("2025-11-10"),
        "tender_end": _d("2025-11-20"),
        "status": "En evaluación",
        "buyer_id": "B1",
        "buyer_name": "Municipalidad Distrital de San Isidro",
        "department": "LIMA",
        "department_code": "15",
        "segmentation_id": "2025-11",
        "segmentation_year": 2025,
        "mype_fit": False,
        "dates_valid": True,
        "period_start_eq_end": False,
    }
    for index in range(1, 26)
]
TENDERS.extend(BULK_TENDERS)

AWARDS = [
    {
        "ocid": "ocds-test-0001",
        "award_id": "A1",
        "supplier_id": "S1",
        "supplier_name": "Tecnología Andina SAC",
        "amount_pen": _money(120000),
        "award_date": _d("2025-04-01"),
        "status": "active",
    },
    {
        "ocid": "ocds-test-0003",
        "award_id": "A2",
        "supplier_id": None,
        "supplier_name": None,
        "amount_pen": None,
        "award_date": None,
        "status": "active",
    },
    {
        "ocid": "ocds-test-0004",
        "award_id": "A3",
        "supplier_id": "S2",
        "supplier_name": "Consultores del Sur EIRL",
        "amount_pen": _money(95000),
        "award_date": _d("2025-06-20"),
        "status": "active",
    },
    {
        "ocid": "ocds-test-0007",
        "award_id": "A4",
        "supplier_id": "S3",
        "supplier_name": "Suministros del Norte SAC",
        "amount_pen": _money(250000),
        "award_date": _d("2025-10-01"),
        "status": "active",
    },
]

CONTRACTS = [
    {
        "ocid": "ocds-test-0001",
        "contract_id": "C1",
        "award_id": "A1",
        "amount_pen": _money(120000),
        "signed_date": _d("2025-04-05"),
        "status": "active",
    },
    {
        "ocid": "ocds-test-0004",
        "contract_id": "C2",
        "award_id": "A-missing",
        "amount_pen": _money(95000),
        "signed_date": _d("2025-07-01"),
        "status": "active",
    },
]


def _insert(
    conn: duckdb.DuckDBPyConnection, table: str, columns: list[str], rows: list[dict]
) -> None:
    placeholders = ", ".join("?" for _ in columns)
    conn.executemany(
        f"INSERT INTO {table} VALUES ({placeholders})",
        [tuple(row[column] for column in columns) for row in rows],
    )


def seed_database(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    path.with_suffix(path.suffix + ".wal").unlink(missing_ok=True)

    conn = duckdb.connect(str(path))
    try:
        for statement in DDL.values():
            conn.execute(statement)
        _insert(conn, "buyers", BUYER_COLUMNS, BUYERS)
        _insert(conn, "suppliers", SUPPLIER_COLUMNS, SUPPLIERS)
        _insert(conn, "tenders", TENDER_COLUMNS, TENDERS)
        _insert(conn, "awards", AWARD_COLUMNS, AWARDS)
        _insert(conn, "contracts", CONTRACT_COLUMNS, CONTRACTS)
    finally:
        conn.close()
    return path


def default_path() -> Path:
    return Path(tempfile.gettempdir()) / "contratamype-e2e" / "contratamype-test.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_path())
    args = parser.parse_args()
    path = seed_database(args.output)
    print(f"seeded {path}")
    print(f"tenders={len(TENDERS)} awards={len(AWARDS)} contracts={len(CONTRACTS)}")


if __name__ == "__main__":
    main()
