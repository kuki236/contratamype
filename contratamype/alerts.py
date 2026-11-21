"""Deterministic alert digest with dedupe state.

The digest is built from the pipeline DB (mype_fit is never recomputed here).
A JSON state file records which OCIDs were already alerted; re-running the same
window produces zero new rows.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb

DIGEST_COLUMNS = [
    "ocid",
    "title",
    "category",
    "amount_pen",
    "department",
    "buyer_name",
    "published_date",
    "tender_start",
    "tender_end",
]


def _gate_open(artifacts_dir: Path) -> None:
    report_path = artifacts_dir / "quality_report.json"
    if not report_path.exists():
        raise RuntimeError(f"quality report not found: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report["gate"]["blocked"]:
        blocking = ", ".join(report["gate"]["blocking_checks"])
        raise RuntimeError(f"quality gate is blocked by: {blocking}")


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"sent": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state.get("sent"), dict):
        raise RuntimeError(f"invalid alert state: {path}")
    return state


def _write_state(path: Path, sent: dict[str, str], run_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"updated_at": run_at, "sent": dict(sorted(sent.items()))}
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _rows(
    db_path: Path,
    since: date,
    until: date | None,
    sent: dict[str, str],
    cohort_year: int,
) -> list[dict]:
    clauses = [
        "mype_fit = true",
        f"segmentation_year = {int(cohort_year)}",
        "published_date >= ?",
    ]
    params: list[object] = [since]
    if until is not None:
        clauses.append("published_date <= ?")
        params.append(until)
    query = (
        f"SELECT {', '.join(DIGEST_COLUMNS)} FROM tenders "
        f"WHERE {' AND '.join(clauses)} ORDER BY published_date, ocid"
    )
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        result = conn.execute(query, params).fetchall()
    finally:
        conn.close()
    rows = []
    for values in result:
        row = dict(zip(DIGEST_COLUMNS, values, strict=True))
        if row["ocid"] in sent:
            continue
        row["amount_pen"] = float(row["amount_pen"]) if row["amount_pen"] is not None else None
        for key in ("published_date", "tender_start", "tender_end"):
            row[key] = row[key].isoformat() if row[key] is not None else None
        rows.append(row)
    return rows


def _write_csv(path: Path, rows: list[dict]) -> str:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DIGEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_digest(
    db_path: Path,
    artifacts_dir: Path,
    out_dir: Path,
    state_path: Path,
    since: date,
    until: date | None = None,
    cohort_year: int = 2025,
) -> dict:
    db_path = Path(db_path)
    out_dir = Path(out_dir)
    state_path = Path(state_path)
    if until is not None and until < since:
        raise ValueError("until must be on or after since")
    if not db_path.exists():
        raise FileNotFoundError(f"database not found: {db_path}")

    _gate_open(Path(artifacts_dir))
    run_at = datetime.now(UTC).isoformat()
    state = _load_state(state_path)
    rows = _rows(db_path, since, until, state["sent"], cohort_year)

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "alert_digest.csv"
    digest_sha256 = _write_csv(csv_path, rows)

    payload = {
        "subject": f"ContrataMYPE: {len(rows)} nuevas oportunidades compatibles",
        "generated_at": run_at,
        "window": {"since": since.isoformat(), "until": until.isoformat() if until else None},
        "count": len(rows),
        "rows": rows,
        "disclaimer": "Heurística de compatibilidad MYPE, no elegibilidad legal.",
        "source": "OECE — Portal de Contrataciones Abiertas (OCDS)",
        "license": "CC BY 4.0",
        "consent": (
            "Enviar solo a destinatarios que aceptaron recibir alertas; "
            "incluir un enlace de baja en cada envío."
        ),
    }
    json_path = out_dir / "alert_digest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    power_automate_path = out_dir / "power_automate_payload.json"
    power_automate_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for row in rows:
        state["sent"][row["ocid"]] = run_at
    _write_state(state_path, state["sent"], run_at)

    return {
        "generated_at": run_at,
        "status": "ok",
        "window": payload["window"],
        "candidates": len(rows),
        "sent": len(rows),
        "state_size": len(state["sent"]),
        "csv": str(csv_path),
        "csv_sha256": digest_sha256,
        "json": str(json_path),
        "power_automate_payload": str(power_automate_path),
        "state": str(state_path),
    }
