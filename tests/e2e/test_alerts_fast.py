"""Fast E2E for the alert digest: new-only rows, dedupe and blocked gate."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from contratamype.alerts import build_digest
from contratamype.config import Settings
from contratamype.run import run_pipeline


def release(ocid: str, published: str, *, amount: float, category: str, department: str) -> dict:
    buyer_id = f"PE-CONSUCODE-{ocid}"
    supplier_id = f"PE-RUC-{ocid}"
    payload = {
        "ocid": ocid,
        "date": f"{published}T10:00:00-05:00",
        "dataSegmentation": {"id": published[:7], "criteria": ["añoInicioConvocatoria"]},
        "tender": {
            "title": f"PROCESO {ocid}",
            "description": f"DESCRIPCION {ocid}",
            "mainProcurementCategory": category,
            "procurementMethodDetails": "Adjudicación Simplificada",
            "value": {"amount": amount, "currency": "PEN", "amount_PEN": amount},
            "datePublished": published,
            "tenderPeriod": {"startDate": published, "endDate": published},
            "status": "active",
        },
        "buyer": {"id": buyer_id, "name": f"BUYER {ocid}"},
        "parties": [
            {
                "id": buyer_id,
                "name": f"BUYER {ocid}",
                "roles": ["buyer"],
                "address": {"department": department},
                "additionalIdentifiers": [{"scheme": "PE-RUC", "id": "20100000001"}],
            },
            {
                "id": supplier_id,
                "name": f"SUPPLIER {ocid}",
                "roles": ["supplier"],
                "address": {"department": department},
            },
        ],
        "awards": [
            {
                "id": f"award-{ocid}",
                "suppliers": [{"id": supplier_id, "name": f"SUPPLIER {ocid}"}],
                "value": {"amount": amount, "currency": "PEN", "amount_PEN": amount},
                "date": published,
                "status": "awarded",
            }
        ],
        "contracts": [
            {
                "id": f"contract-{ocid}",
                "awardID": f"award-{ocid}",
                "value": {"amount": amount, "currency": "PEN", "amount_PEN": amount},
                "dateSigned": published,
                "status": "active",
            }
        ],
    }
    return {"ocid": ocid, "compiledRelease": payload}


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


def run(tmp_path: Path, records: list[dict], name: str):
    input_path = tmp_path / f"{name}.jsonl"
    write_jsonl(input_path, records)
    settings = Settings(
        artifacts_dir=tmp_path / f"{name}-artifacts",
        db_path=tmp_path / f"{name}.duckdb",
    )
    return run_pipeline(input_path, settings), settings


@pytest.mark.fast
def test_digest_is_new_only_and_deduplicated(tmp_path: Path) -> None:
    records = [
        release(
            "ocds-alert-001", "2025-02-01", amount=100_000, category="goods", department="LIMA"
        ),
        release(
            "ocds-alert-002", "2025-03-01", amount=50_000, category="services", department="CUSCO"
        ),
        release(
            "ocds-alert-003", "2025-04-01", amount=300_000, category="goods", department="LIMA"
        ),
    ]
    summary, settings = run(tmp_path, records, "alerts")
    assert summary["tenders"] == 3
    assert summary["mype_opportunities"] == 2

    state = tmp_path / "alerts" / "state.json"
    first = build_digest(
        settings.db_path,
        settings.artifacts_dir,
        tmp_path / "alerts" / "run1",
        state,
        since=date(2025, 1, 1),
        until=date(2025, 12, 31),
    )
    assert first["sent"] == 2
    assert first["state_size"] == 2
    csv_path = Path(first["csv"])
    assert len(csv_path.read_text(encoding="utf-8").splitlines()) == 3

    second = build_digest(
        settings.db_path,
        settings.artifacts_dir,
        tmp_path / "alerts" / "run2",
        state,
        since=date(2025, 1, 1),
        until=date(2025, 12, 31),
    )
    assert second["sent"] == 0
    assert second["state_size"] == 2
    assert Path(second["csv"]).read_text(encoding="utf-8").strip() == ",".join(
        [
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
    )

    records.append(
        release("ocds-alert-004", "2025-05-01", amount=20_000, category="goods", department="PIURA")
    )
    summary, settings = run(tmp_path, records, "alerts")
    third = build_digest(
        settings.db_path,
        settings.artifacts_dir,
        tmp_path / "alerts" / "run3",
        state,
        since=date(2025, 5, 1),
        until=date(2025, 12, 31),
    )
    assert third["sent"] == 1
    assert third["state_size"] == 3
    rows = json.loads(Path(third["json"]).read_text(encoding="utf-8"))["rows"]
    assert [row["ocid"] for row in rows] == ["ocds-alert-004"]


@pytest.mark.fast
def test_digest_is_deterministic_for_same_input(tmp_path: Path) -> None:
    records = [
        release("ocds-alert-010", "2025-06-01", amount=10_000, category="goods", department="LIMA"),
        release(
            "ocds-alert-011", "2025-06-02", amount=90_000, category="services", department="CUSCO"
        ),
    ]
    summary, settings = run(tmp_path, records, "deterministic")
    assert summary["mype_opportunities"] == 2
    first = build_digest(
        settings.db_path,
        settings.artifacts_dir,
        tmp_path / "a",
        tmp_path / "state-a.json",
        since=date(2025, 1, 1),
    )
    second = build_digest(
        settings.db_path,
        settings.artifacts_dir,
        tmp_path / "b",
        tmp_path / "state-b.json",
        since=date(2025, 1, 1),
    )
    assert Path(first["csv"]).read_bytes() == Path(second["csv"]).read_bytes()
    assert first["csv_sha256"] == second["csv_sha256"]
    assert first["sent"] == second["sent"] == 2


@pytest.mark.fast
def test_digest_refuses_blocked_quality_gate(tmp_path: Path) -> None:
    broken = release(
        "ocds-alert-020", "2025-07-01", amount=10_000, category="goods", department="LIMA"
    )
    broken["compiledRelease"]["tender"]["mainProcurementCategory"] = "invalid"
    summary, settings = run(tmp_path, [broken], "blocked")
    assert summary["quality_gate"]["blocked"] is True

    with pytest.raises(RuntimeError, match="quality gate is blocked by: category_valid"):
        build_digest(
            settings.db_path,
            settings.artifacts_dir,
            tmp_path / "alerts",
            tmp_path / "state.json",
            since=date(2025, 1, 1),
        )
