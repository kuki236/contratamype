"""Compute the headline market metrics for a cohort from the pipeline DB.

The output is JSON so docs and release notes can be regenerated without
copying numbers by hand. Money is aggregated in DuckDB and only converted to
float for JSON display.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


def _scalar(conn: duckdb.DuckDBPyConnection, query: str, params: list[object]) -> object:
    return conn.execute(query, params).fetchone()[0]


def snapshot_metrics(db_path: Path, year: int = 2025) -> dict:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        base = "FROM tenders WHERE segmentation_year = ?"
        processes = int(_scalar(conn, f"SELECT COUNT(*) {base}", [year]))
        total_amount = _scalar(conn, f"SELECT SUM(amount_pen) {base}", [year])
        median_amount = _scalar(conn, f"SELECT MEDIAN(amount_pen) {base}", [year])
        mype = int(_scalar(conn, f"SELECT COUNT(*) {base} AND mype_fit", [year]))
        mype_amount = _scalar(conn, f"SELECT SUM(amount_pen) {base} AND mype_fit", [year])

        def share(part: object, total: object) -> float | None:
            if total in (None, 0) or part is None:
                return None
            return round(100 * float(part) / float(total), 1)

        by_category = [
            {
                "category": row[0],
                "processes": row[1],
                "amount": float(row[2]) if row[2] is not None else None,
                "mype": row[3],
                "mype_share": share(row[3], row[1]),
            }
            for row in conn.execute(
                f"""
                SELECT category, COUNT(*), SUM(amount_pen),
                       COUNT(*) FILTER (WHERE mype_fit)
                {base}
                GROUP BY 1 ORDER BY 2 DESC
                """,
                [year],
            ).fetchall()
        ]
        top_departments = [
            {
                "department": row[0],
                "processes": row[1],
                "amount": float(row[2]) if row[2] is not None else None,
                "mype": row[3],
                "mype_share": share(row[3], row[1]),
            }
            for row in conn.execute(
                f"""
                SELECT department, COUNT(*), SUM(amount_pen),
                       COUNT(*) FILTER (WHERE mype_fit)
                {base}
                GROUP BY 1 ORDER BY 2 DESC LIMIT 10
                """,
                [year],
            ).fetchall()
        ]
        top_buyers = [
            {
                "buyer": row[0],
                "processes": row[1],
                "amount": float(row[2]) if row[2] is not None else None,
            }
            for row in conn.execute(
                f"""
                SELECT buyer_name, COUNT(*), SUM(amount_pen)
                {base}
                GROUP BY 1 ORDER BY 3 DESC NULLS LAST LIMIT 10
                """,
                [year],
            ).fetchall()
        ]
        by_month = [
            {"month": str(row[0])[:7], "processes": row[1], "mype": row[2]}
            for row in conn.execute(
                f"""
                SELECT date_trunc('month', published_date) AS month, COUNT(*),
                       COUNT(*) FILTER (WHERE mype_fit)
                {base} AND published_date IS NOT NULL
                  AND EXTRACT(year FROM published_date) = ?
                GROUP BY 1 ORDER BY 1
                """,
                [year, year],
            ).fetchall()
        ]
        top_methods = [
            {"method": row[0], "processes": row[1]}
            for row in conn.execute(
                f"SELECT method, COUNT(*) {base} GROUP BY 1 ORDER BY 2 DESC LIMIT 8",
                [year],
            ).fetchall()
        ]

        return {
            "cohort_year": year,
            "processes": processes,
            "total_amount": float(total_amount) if total_amount is not None else None,
            "median_amount": float(median_amount) if median_amount is not None else None,
            "mype": mype,
            "mype_share": share(mype, processes),
            "mype_amount": float(mype_amount) if mype_amount is not None else None,
            "mype_amount_share": share(mype_amount, total_amount),
            "zero_amount": int(_scalar(conn, f"SELECT COUNT(*) {base} AND amount_pen = 0", [year])),
            "missing_description": int(
                _scalar(
                    conn,
                    f"SELECT COUNT(*) {base} AND (description IS NULL OR trim(description) = '')",
                    [year],
                )
            ),
            "start_eq_end": int(
                _scalar(conn, f"SELECT COUNT(*) {base} AND period_start_eq_end", [year])
            ),
            "with_award": int(
                _scalar(
                    conn,
                    "SELECT COUNT(DISTINCT t.ocid) FROM tenders t "
                    "JOIN awards a USING (ocid) WHERE t.segmentation_year = ?",
                    [year],
                )
            ),
            "with_contract": int(
                _scalar(
                    conn,
                    "SELECT COUNT(DISTINCT t.ocid) FROM tenders t "
                    "JOIN contracts c USING (ocid) WHERE t.segmentation_year = ?",
                    [year],
                )
            ),
            "published_outside_year": int(
                _scalar(
                    conn,
                    f"SELECT COUNT(*) {base} AND published_date IS NOT NULL "
                    "AND EXTRACT(year FROM published_date) <> ?",
                    [year, year],
                )
            ),
            "by_category": by_category,
            "top_departments": top_departments,
            "top_buyers": top_buyers,
            "by_month": by_month,
            "top_methods": top_methods,
        }
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/processed/contratamype.duckdb"))
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = snapshot_metrics(args.db, args.year)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(json.dumps({"out": str(args.out), "processes": payload["processes"]}))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
