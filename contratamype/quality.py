"""Twelve quality checks with a gate.

Fail checks block the app exports. Warn checks are reported but do not block;
this is deliberate for known OCDS realities such as zero amounts and
start=end tender periods.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import duckdb

from contratamype.config import Settings
from contratamype.ingest import RawStats


def _scalar(conn: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(conn.execute(query).fetchone()[0])


def _check(
    name: str,
    layer: str,
    level: str,
    rows_checked: int,
    rows_failed: int,
    sql: str,
    duration_ms: float,
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
        "failed_sample": [],
    }


def run_checks(
    conn: duckdb.DuckDBPyConnection,
    settings: Settings,
    stats: RawStats,
) -> dict:
    started = time.perf_counter()
    raw_count = _scalar(conn, "SELECT COUNT(*) FROM raw_tenders")
    awards_count = _scalar(conn, "SELECT COUNT(*) FROM awards")
    contracts_count = _scalar(conn, "SELECT COUNT(*) FROM contracts")
    checks: list[dict] = []

    def add(
        name: str,
        layer: str,
        level: str,
        rows_checked: int,
        query: str,
    ) -> None:
        before = time.perf_counter()
        failed = _scalar(conn, query)
        checks.append(
            _check(
                name,
                layer,
                level,
                rows_checked,
                failed,
                query,
                (time.perf_counter() - before) * 1000,
            )
        )

    raw_schema_failed = stats.parse_errors + stats.missing_ocid + stats.missing_tender
    schema_started = time.perf_counter()
    checks.append(
        _check(
            "raw_schema_present",
            "raw",
            "fail",
            stats.lines,
            raw_schema_failed,
            "parse_errors + missing_ocid + missing_tender == 0",
            (time.perf_counter() - schema_started) * 1000,
        )
    )

    distinct_ocids = _scalar(conn, "SELECT COUNT(DISTINCT ocid) FROM raw_tenders")
    checks.append(
        _check(
            "ocid_unique",
            "tender",
            "fail",
            raw_count,
            raw_count - distinct_ocids,
            "COUNT(*) - COUNT(DISTINCT ocid) FROM raw_tenders",
            0.0,
        )
    )

    add(
        "tender_title_present",
        "tender",
        "fail",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders WHERE title IS NULL OR trim(title) = ''",
    )
    add(
        "category_valid",
        "tender",
        "fail",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders "
        "WHERE category IS NULL OR category NOT IN ('goods', 'services', 'works')",
    )
    add(
        "department_valid",
        "tender",
        "fail",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders WHERE department_code IS NULL",
    )
    add(
        "buyer_present",
        "tender",
        "fail",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders WHERE buyer_id IS NULL OR buyer_id = ''",
    )
    add(
        "amount_non_negative",
        "tender",
        "fail",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders WHERE amount_pen < 0",
    )
    add(
        "amount_zero",
        "tender",
        "warn",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders WHERE amount_pen = 0",
    )
    add(
        "dates_parseable",
        "tender",
        "fail",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders WHERE dates_valid = false",
    )
    add(
        "period_start_eq_end",
        "tender",
        "warn",
        raw_count,
        "SELECT COUNT(*) FROM raw_tenders WHERE period_start_eq_end = true",
    )
    add(
        "award_supplier_present",
        "award",
        "warn",
        awards_count,
        "SELECT COUNT(*) FROM awards WHERE supplier_id IS NULL OR supplier_id = ''",
    )
    add(
        "contract_award_linked",
        "contract",
        "warn",
        contracts_count,
        """
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
        """,
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
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
    }
