"""DuckDB star schema: vectorized raw load + SQL dedupe into serving tables."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

import duckdb
import pyarrow as pa

from contratamype.normalize import Normalized

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

RAW_TABLES = {
    "raw_tenders": TENDER_COLUMNS,
    "raw_buyers": BUYER_COLUMNS,
    "raw_suppliers": SUPPLIER_COLUMNS,
    "raw_awards": AWARD_COLUMNS,
    "raw_contracts": CONTRACT_COLUMNS,
}

DATE_COLUMNS = {"published_date", "tender_start", "tender_end", "award_date", "signed_date"}
FLOAT_COLUMNS = {"amount_pen"}
INT_COLUMNS = {"segmentation_year"}
BOOL_COLUMNS = {"mype_fit", "dates_valid", "period_start_eq_end"}


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE OR REPLACE TABLE raw_tenders (
            ocid VARCHAR, title VARCHAR, description VARCHAR, category VARCHAR,
            method VARCHAR, amount_pen DECIMAL(18,2), currency VARCHAR,
            published_date DATE, tender_start DATE, tender_end DATE, status VARCHAR,
            buyer_id VARCHAR, buyer_name VARCHAR, department VARCHAR,
            department_code VARCHAR, segmentation_id VARCHAR, segmentation_year INTEGER,
            mype_fit BOOLEAN, dates_valid BOOLEAN, period_start_eq_end BOOLEAN
        )
        """
    )
    conn.execute(
        "CREATE OR REPLACE TABLE raw_buyers "
        "(buyer_id VARCHAR, name VARCHAR, ruc VARCHAR, department VARCHAR)"
    )
    conn.execute(
        "CREATE OR REPLACE TABLE raw_suppliers "
        "(supplier_id VARCHAR, name VARCHAR, ruc VARCHAR, department VARCHAR)"
    )
    conn.execute(
        "CREATE OR REPLACE TABLE raw_awards "
        "(ocid VARCHAR, award_id VARCHAR, supplier_id VARCHAR, supplier_name VARCHAR, "
        "amount_pen DECIMAL(18,2), award_date DATE, status VARCHAR)"
    )
    conn.execute(
        "CREATE OR REPLACE TABLE raw_contracts "
        "(ocid VARCHAR, contract_id VARCHAR, award_id VARCHAR, amount_pen DECIMAL(18,2), "
        "signed_date DATE, status VARCHAR)"
    )


def _row(values: dict, columns: list[str]) -> tuple:
    return tuple(values.get(column) for column in columns)


def _parse_date(value: object) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _insert(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns: list[str],
    rows: list[tuple],
) -> None:
    if not rows:
        return
    arrays = []
    for index, column in enumerate(columns):
        values = [row[index] for row in rows]
        if column in DATE_COLUMNS:
            array = pa.array([_parse_date(value) for value in values], type=pa.date32())
        elif column in FLOAT_COLUMNS:
            array = pa.array(values, type=pa.float64())
        elif column in INT_COLUMNS:
            array = pa.array(values, type=pa.int64())
        elif column in BOOL_COLUMNS:
            array = pa.array(values, type=pa.bool_())
        else:
            array = pa.array(values, type=pa.string())
        arrays.append(array)
    batch = pa.Table.from_arrays(arrays, names=columns)
    conn.register("_batch", batch)
    conn.execute(f"INSERT INTO {table} SELECT * FROM _batch")
    conn.unregister("_batch")


def load(
    conn: duckdb.DuckDBPyConnection,
    records: Iterable[Normalized],
    batch_size: int = 5_000,
) -> None:
    batches: dict[str, list[tuple]] = {name: [] for name in RAW_TABLES}

    def flush() -> None:
        for table, columns in RAW_TABLES.items():
            _insert(conn, table, columns, batches[table])
            batches[table].clear()

    for record in records:
        batches["raw_tenders"].append(_row(record.tender, TENDER_COLUMNS))
        if record.buyer:
            batches["raw_buyers"].append(_row(record.buyer, BUYER_COLUMNS))
        batches["raw_suppliers"].extend(_row(row, SUPPLIER_COLUMNS) for row in record.suppliers)
        batches["raw_awards"].extend(_row(row, AWARD_COLUMNS) for row in record.awards)
        batches["raw_contracts"].extend(_row(row, CONTRACT_COLUMNS) for row in record.contracts)
        if len(batches["raw_tenders"]) >= batch_size:
            flush()
    flush()
    finalize(conn)


def finalize(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE OR REPLACE TABLE tenders AS
        SELECT * EXCLUDE (rn)
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY ocid
                       ORDER BY published_date DESC NULLS LAST, title
                   ) AS rn
            FROM raw_tenders
        )
        WHERE rn = 1
        """
    )
    for table, key in (("buyers", "buyer_id"), ("suppliers", "supplier_id")):
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT * EXCLUDE (rn)
            FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY name) AS rn
                FROM raw_{table}
            )
            WHERE rn = 1 AND {key} IS NOT NULL AND {key} <> ''
            """
        )
    conn.execute(
        """
        CREATE OR REPLACE TABLE awards AS
        SELECT * EXCLUDE (rn)
        FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY ocid, award_id, supplier_id
                ORDER BY supplier_name
            ) AS rn
            FROM raw_awards
        )
        WHERE rn = 1
        """
    )
    conn.execute(
        """
        CREATE OR REPLACE TABLE contracts AS
        SELECT * EXCLUDE (rn)
        FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY ocid, contract_id
                ORDER BY signed_date DESC NULLS LAST
            ) AS rn
            FROM raw_contracts
        )
        WHERE rn = 1
        """
    )


def counts(conn: duckdb.DuckDBPyConnection, cohort_year: int) -> dict[str, int]:
    def scalar(query: str) -> int:
        return int(conn.execute(query).fetchone()[0])

    return {
        "raw_records": scalar("SELECT COUNT(*) FROM raw_tenders"),
        "tenders": scalar("SELECT COUNT(*) FROM tenders"),
        "buyers": scalar("SELECT COUNT(*) FROM buyers"),
        "suppliers": scalar("SELECT COUNT(*) FROM suppliers"),
        "awards": scalar("SELECT COUNT(*) FROM awards"),
        "contracts": scalar("SELECT COUNT(*) FROM contracts"),
        "cohort_records": scalar(
            f"SELECT COUNT(*) FROM tenders WHERE segmentation_year = {int(cohort_year)}"
        ),
        "mype_opportunities": scalar(
            f"SELECT COUNT(*) FROM tenders "
            f"WHERE segmentation_year = {int(cohort_year)} AND mype_fit = true"
        ),
    }
