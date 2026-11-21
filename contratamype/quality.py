"""Twelve quality checks plus non-gating coverage audits.

Checks at level ``fail`` block the app exports when they find rows; checks at
level ``warn`` are reported but do not block. This is deliberate for known OCDS
realities such as zero amounts, incomplete periods and missing supplier
addresses. Every check that finds bad rows keeps up to five real samples so the
report is actionable without opening DuckDB.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import duckdb

from contratamype.config import DEPARTMENT_CODES, Settings
from contratamype.ingest import RawStats

CATEGORY_LIST = "'goods', 'services', 'works'"


def _scalar(conn: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(conn.execute(query).fetchone()[0])


def _rows(
    conn: duckdb.DuckDBPyConnection,
    query: str,
    limit: int = 5,
) -> list[dict]:
    result = conn.execute(query)
    names = [column[0] for column in result.description]
    return [dict(zip(names, row, strict=True)) for row in result.fetchmany(limit)]


def _check(
    name: str,
    layer: str,
    level: str,
    rows_checked: int,
    rows_failed: int,
    sample: list[dict],
    sql: str,
    duration_ms: float,
    **extra,
) -> dict:
    if rows_failed > 0:
        status = "fail" if level == "fail" else "warn"
    else:
        status = "pass"
    return {
        "name": name,
        "layer": layer,
        "level": level,
        "status": status,
        "rows_checked": rows_checked,
        "rows_failed": rows_failed,
        "duration_ms": round(duration_ms, 2),
        "sql": sql,
        "failed_sample": sample,
        **extra,
    }


def _audits(conn: duckdb.DuckDBPyConnection, settings: Settings) -> list[dict]:
    year = int(settings.cohort_year)
    expected_months = [f"{year}-{month:02d}" for month in range(1, 13)]
    observed_months = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT substr(segmentation_id, 1, 7) FROM tenders "
            "WHERE segmentation_year = ? AND segmentation_id IS NOT NULL",
            [year],
        ).fetchall()
    }
    missing_months = [month for month in expected_months if month not in observed_months]
    present_months = [month for month in expected_months if month in observed_months]

    expected_codes = sorted(set(DEPARTMENT_CODES.values()))
    observed_codes = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT department_code FROM tenders "
            "WHERE segmentation_year = ? AND department_code IS NOT NULL",
            [year],
        ).fetchall()
    }
    missing_codes = [code for code in expected_codes if code not in observed_codes]

    duplicate_ruc = _scalar(
        conn,
        """
        SELECT COALESCE(SUM(n - 1), 0)
        FROM (
            SELECT ruc, COUNT(*) AS n
            FROM suppliers
            WHERE ruc IS NOT NULL AND trim(ruc) <> ''
            GROUP BY ruc
            HAVING COUNT(*) > 1
        )
        """,
    )
    duplicate_name = _scalar(
        conn,
        r"""
        SELECT COALESCE(SUM(n - 1), 0)
        FROM (
            SELECT regexp_replace(trim(upper(name)), '\s+', ' ', 'g') AS normalized_name,
                   COUNT(*) AS n
            FROM suppliers
            WHERE name IS NOT NULL AND trim(name) <> ''
            GROUP BY normalized_name
            HAVING COUNT(*) > 1
        )
        """,
    )
    duplicate_ruc_sample = _rows(
        conn,
        """
        SELECT ruc, COUNT(*) AS rows
        FROM suppliers
        WHERE ruc IS NOT NULL AND trim(ruc) <> ''
        GROUP BY ruc
        HAVING COUNT(*) > 1
        ORDER BY rows DESC, ruc
        """,
    )
    duplicate_name_sample = _rows(
        conn,
        r"""
        SELECT regexp_replace(trim(upper(name)), '\s+', ' ', 'g') AS normalized_name,
               COUNT(*) AS rows
        FROM suppliers
        WHERE name IS NOT NULL AND trim(name) <> ''
        GROUP BY normalized_name
        HAVING COUNT(*) > 1
        ORDER BY rows DESC, normalized_name
        """,
    )

    return [
        {
            "name": "month_coverage",
            "status": "pass" if not missing_months else "incomplete",
            "expected": len(expected_months),
            "observed": len(present_months),
            "missing": missing_months,
        },
        {
            "name": "region_coverage",
            "status": "pass" if not missing_codes else "incomplete",
            "expected": len(expected_codes),
            "observed": len(expected_codes) - len(missing_codes),
            "missing_codes": missing_codes,
        },
        {
            "name": "duplicate_parties",
            "status": "pass" if duplicate_ruc == 0 and duplicate_name == 0 else "warn",
            "duplicate_ruc_rows": duplicate_ruc,
            "duplicate_name_rows": duplicate_name,
            "duplicate_ruc_sample": duplicate_ruc_sample,
            "duplicate_name_sample": duplicate_name_sample,
        },
        {
            "name": "api_vs_bulk_spot_check",
            "status": "not_run",
            "reason": (
                "the bulk pipeline runs offline; the beta API spot-check needs "
                "network access and is not part of the pipeline or the gate"
            ),
        },
    ]


def run_checks(
    conn: duckdb.DuckDBPyConnection,
    settings: Settings,
    stats: RawStats,
) -> dict:
    started = time.perf_counter()
    raw_count = _scalar(conn, "SELECT COUNT(*) FROM raw_tenders")
    awards_count = _scalar(conn, "SELECT COUNT(*) FROM awards")
    contracts_count = _scalar(conn, "SELECT COUNT(*) FROM contracts")
    suppliers_count = _scalar(conn, "SELECT COUNT(*) FROM suppliers")
    checks: list[dict] = []

    def add(
        name: str,
        layer: str,
        level: str,
        rows_checked: int,
        table: str,
        where: str,
        columns: str,
        order_by: str,
    ) -> None:
        count_sql = f"SELECT COUNT(*) FROM {table} WHERE {where}"
        check_started = time.perf_counter()
        failed = _scalar(conn, count_sql)
        sample = (
            _rows(conn, f"SELECT {columns} FROM {table} WHERE {where} ORDER BY {order_by}")
            if failed
            else []
        )
        checks.append(
            _check(
                name,
                layer,
                level,
                rows_checked,
                failed,
                sample,
                count_sql,
                (time.perf_counter() - check_started) * 1000,
            )
        )

    raw_schema_failed = (
        stats.parse_errors + stats.missing_ocid + stats.missing_tender + stats.missing_title
    )
    raw_sample = [
        {"line": line, "missing": "json"} for line in stats.parse_error_lines
    ] + stats.schema_samples
    checks.append(
        _check(
            "raw_schema_present",
            "raw",
            "fail",
            stats.lines,
            raw_schema_failed,
            raw_sample[:5],
            "parse_errors + missing_ocid + missing_tender + missing_title == 0",
            0.0,
            parse_error_lines=stats.parse_error_lines,
        )
    )

    duplicates = _scalar(
        conn,
        "SELECT COUNT(*) - COUNT(DISTINCT ocid) FROM raw_tenders",
    )
    checks.append(
        _check(
            "ocid_unique",
            "tender",
            "fail",
            raw_count,
            duplicates,
            _rows(
                conn,
                "SELECT ocid, COUNT(*) AS rows FROM raw_tenders "
                "GROUP BY ocid HAVING COUNT(*) > 1 ORDER BY rows DESC, ocid",
            )
            if duplicates
            else [],
            "COUNT(*) - COUNT(DISTINCT ocid) FROM raw_tenders",
            0.0,
        )
    )

    add(
        "buyer_present",
        "tender",
        "fail",
        raw_count,
        "raw_tenders",
        "(buyer_id IS NULL OR trim(buyer_id) = '') "
        "AND (buyer_name IS NULL OR trim(buyer_name) = '')",
        "ocid, buyer_id, buyer_name",
        "ocid",
    )
    add(
        "category_valid",
        "tender",
        "fail",
        raw_count,
        "raw_tenders",
        f"category IS NULL OR category NOT IN ({CATEGORY_LIST})",
        "ocid, category",
        "ocid",
    )
    add(
        "department_valid",
        "tender",
        "fail",
        raw_count,
        "raw_tenders",
        "department_code IS NULL",
        "ocid, department, department_code",
        "ocid",
    )
    add(
        "dates_valid",
        "tender",
        "fail",
        raw_count,
        "raw_tenders",
        "dates_valid = false",
        "ocid, published_date, tender_start, tender_end",
        "ocid",
    )
    add(
        "period_quality",
        "tender",
        "warn",
        raw_count,
        "raw_tenders",
        "tender_start IS NULL OR tender_end IS NULL OR tender_start = tender_end",
        "ocid, tender_start, tender_end",
        "ocid",
    )
    add(
        "amount_non_negative",
        "tender",
        "fail",
        raw_count,
        "raw_tenders",
        "amount_pen < 0",
        "ocid, amount_pen",
        "ocid",
    )
    add(
        "amount_zero",
        "tender",
        "warn",
        raw_count,
        "raw_tenders",
        "amount_pen = 0",
        "ocid, amount_pen",
        "ocid",
    )
    add(
        "award_complete",
        "award",
        "warn",
        awards_count,
        "awards",
        "supplier_id IS NULL OR supplier_id = '' "
        "OR (amount_pen IS NULL AND (status IS NULL OR trim(status) = ''))",
        "ocid, award_id, supplier_id, amount_pen, status",
        "ocid, award_id, supplier_id",
    )

    linked_where = """
        WITH contract_awards AS (
            SELECT DISTINCT ocid, contract_id, award_id FROM contracts
        ),
        awarded AS (
            SELECT DISTINCT ocid, award_id FROM awards
        )
        SELECT COUNT(*)
        FROM contract_awards c
        LEFT JOIN awarded a
          ON c.ocid = a.ocid AND c.award_id = a.award_id
        WHERE c.award_id IS NULL OR c.award_id = '' OR a.award_id IS NULL
        """
    linked_started = time.perf_counter()
    linked = _scalar(conn, linked_where)
    linked_sample = (
        _rows(
            conn,
            """
            WITH contract_awards AS (
                SELECT DISTINCT ocid, contract_id, award_id FROM contracts
            ),
            awarded AS (
                SELECT DISTINCT ocid, award_id FROM awards
            )
            SELECT c.ocid, c.contract_id, c.award_id
            FROM contract_awards c
            LEFT JOIN awarded a
              ON c.ocid = a.ocid AND c.award_id = a.award_id
            WHERE c.award_id IS NULL OR c.award_id = '' OR a.award_id IS NULL
            ORDER BY c.ocid, c.contract_id
            """,
        )
        if linked
        else []
    )
    checks.append(
        _check(
            "contract_award_linked",
            "contract",
            "warn",
            contracts_count,
            linked,
            linked_sample,
            "contract.award_id is present and exists in awards for the same ocid",
            (time.perf_counter() - linked_started) * 1000,
        )
    )

    add(
        "supplier_address_present",
        "supplier",
        "warn",
        suppliers_count,
        "suppliers",
        "department IS NULL",
        "supplier_id, name, ruc, department",
        "supplier_id",
    )

    failed = sum(1 for check in checks if check["status"] == "fail")
    warned = sum(1 for check in checks if check["status"] == "warn")
    passed = sum(1 for check in checks if check["status"] == "pass")
    blocking = [check["name"] for check in checks if check["status"] == "fail"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "cohort_year": settings.cohort_year,
        "summary": {
            "total_checks": len(checks),
            "failed_checks": failed,
            "warn_checks": warned,
            "passed_checks": passed,
        },
        "gate": {
            "blocked": bool(blocking),
            "blocking_checks": blocking,
            "rule": "any level=fail check with status=fail blocks app exports",
        },
        "checks": checks,
        "audits": _audits(conn, settings),
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
    }
