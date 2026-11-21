"""Select a deterministic LLM evaluation sample from the 2025 cohort.

Buckets: complete, zero amount, start=end, no award, dangling contract.
The output is consumed by the explainer evaluation described in
`docs/llm-policy.md`; it contains only official OCDS fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

COLUMNS = [
    "ocid",
    "title",
    "description",
    "category",
    "amount_pen",
    "department",
    "published_date",
    "tender_start",
    "tender_end",
    "mype_fit",
    "dates_valid",
    "period_start_eq_end",
    "has_award",
    "has_contract",
    "dangling_contract",
]

BASE = """
WITH base AS (
    SELECT t.ocid, t.title, t.description, t.category, t.amount_pen, t.department,
           t.published_date, t.tender_start, t.tender_end, t.mype_fit, t.dates_valid,
           t.period_start_eq_end,
           EXISTS (SELECT 1 FROM awards a WHERE a.ocid = t.ocid) AS has_award,
           EXISTS (SELECT 1 FROM contracts c WHERE c.ocid = t.ocid) AS has_contract,
           EXISTS (
               SELECT 1 FROM contracts c
               WHERE c.ocid = t.ocid
                 AND NOT EXISTS (
                     SELECT 1 FROM awards a
                     WHERE a.ocid = c.ocid AND a.award_id = c.award_id
                 )
           ) AS dangling_contract
    FROM tenders t
    WHERE t.segmentation_year = ?
)
"""

BUCKETS = {
    "complete": """
        SELECT * FROM base
        WHERE mype_fit AND amount_pen > 0 AND description IS NOT NULL
          AND dates_valid AND has_award AND has_contract AND NOT dangling_contract
        ORDER BY ocid LIMIT ?
    """,
    "zero_amount": """
        SELECT * FROM base
        WHERE amount_pen = 0
        ORDER BY ocid LIMIT ?
    """,
    "start_eq_end": """
        SELECT * FROM base
        WHERE period_start_eq_end AND amount_pen > 0
        ORDER BY ocid LIMIT ?
    """,
    "no_award": """
        SELECT * FROM base
        WHERE NOT has_award AND amount_pen > 0
        ORDER BY ocid LIMIT ?
    """,
    "dangling_contract": """
        SELECT * FROM base
        WHERE dangling_contract
        ORDER BY ocid LIMIT ?
    """,
}


def _json_row(values: tuple) -> dict:
    row = dict(zip(COLUMNS, values, strict=True))
    for key in ("published_date", "tender_start", "tender_end"):
        row[key] = row[key].isoformat() if row[key] else None
    row["amount_pen"] = float(row["amount_pen"]) if row["amount_pen"] is not None else None
    return row


def select(
    db_path: Path,
    out_path: Path,
    cohort_year: int = 2025,
    per_bucket: int = 3,
) -> dict:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        selected: dict[str, list[dict]] = {}
        seen: set[str] = set()
        for name, query in BUCKETS.items():
            rows = conn.execute(BASE + query, [cohort_year, per_bucket * 10]).fetchall()
            bucket: list[dict] = []
            for values in rows:
                row = _json_row(values)
                if row["ocid"] in seen:
                    continue
                seen.add(row["ocid"])
                bucket.append(row)
                if len(bucket) == per_bucket:
                    break
            selected[name] = bucket
    finally:
        conn.close()

    payload = {
        "cohort": cohort_year,
        "purpose": "Evaluación del explicador: campos oficiales, vacíos y disclaimer",
        "buckets": selected,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"path": str(out_path), "counts": {name: len(rows) for name, rows in selected.items()}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/processed/contratamype.duckdb"))
    parser.add_argument("--out", type=Path, default=Path("docs/llm-eval-sample-2025.json"))
    parser.add_argument("--cohort-year", type=int, default=2025)
    parser.add_argument("--per-bucket", type=int, default=3)
    args = parser.parse_args(argv)
    print(
        json.dumps(select(args.db, args.out, args.cohort_year, args.per_bucket), ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
