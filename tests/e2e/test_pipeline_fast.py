"""Fast E2E: medium-hard OCDS fixture through the real CLI/artifacts.

The fixture is intentionally dirty: a malformed JSON line, duplicate OCID,
amount 0, negative amount, invalid category, missing department, missing buyer,
missing title, unparseable date, missing period, award without supplier, award
without contract, supplier without address, duplicate supplier RUC, contract
without award and a dangling contract -> award reference. The test proves the
quality gate, samples, audits and artifacts, not just that the code runs.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BULK_2024 = REPO_ROOT / "data" / "raw" / "ocds" / "2024.jsonl.gz"
BULK_2025 = REPO_ROOT / "data" / "raw" / "ocds" / "2025.jsonl.gz"
BULK_2024_SHA256 = "9f50c84423c65605b4280d2d88b9da0853ebeb0b556d2dedf66add435cbde6e0"
BULK_2025_SHA256 = "65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b"


def _value(amount: float | None) -> dict:
    if amount is None:
        return {"currency": "PEN"}
    return {"amount": amount, "currency": "PEN", "amount_PEN": amount}


def _release(
    ocid: str,
    *,
    title: str | None = None,
    category: str = "goods",
    amount: float | None = 100_000,
    start: str | None = "2025-02-01",
    end: str | None = "2025-02-10",
    period: bool = True,
    published: str | None = None,
    department: str | None = "LIMA",
    buyer: bool = True,
    buyer_party: bool = True,
    award: bool = True,
    award_supplier: bool = True,
    supplier_id: str | None = None,
    supplier_ruc: str | None = None,
    supplier_address: bool = True,
    contract: bool = True,
    contract_award: bool = True,
    dangling_award: bool = False,
    segmentation: str = "2025-02",
    release_date: str = "2025-02-01T10:00:00-05:00",
) -> dict:
    buyer_id = f"PE-CONSUCODE-{ocid}"
    supplier_id = supplier_id or f"PE-RUC-{ocid}"
    parties = []
    if buyer_party:
        address = {"department": department} if department else {"countryName": "PERU"}
        parties.append(
            {
                "id": buyer_id,
                "name": f"BUYER {ocid}",
                "roles": ["buyer", "procuringEntity"],
                "address": address,
                "additionalIdentifiers": [{"scheme": "PE-RUC", "id": "20100000001"}],
            }
        )
    if award:
        supplier = {
            "id": supplier_id,
            "name": f"SUPPLIER {ocid}",
            "roles": ["supplier", "tenderer"],
        }
        if supplier_address:
            supplier["address"] = {"department": department or "LIMA"}
        if supplier_ruc:
            supplier["additionalIdentifiers"] = [{"scheme": "PE-RUC", "id": supplier_ruc}]
        parties.append(supplier)
    tender = {
        "title": title if title is not None else f"TENDER {ocid}",
        "description": f"DESCRIPTION {ocid}",
        "mainProcurementCategory": category,
        "procurementMethodDetails": "Adjudicación Simplificada",
        "value": _value(amount),
        "status": "active",
    }
    if published is not None:
        tender["datePublished"] = published
    if period:
        tender["tenderPeriod"] = {"startDate": start, "endDate": end}
    release = {
        "ocid": ocid,
        "date": release_date,
        "dataSegmentation": {"id": segmentation, "criteria": ["añoInicioConvocatoria"]},
        "tender": tender,
        "parties": parties,
    }
    if buyer:
        release["buyer"] = {"id": buyer_id, "name": f"BUYER {ocid}"}
    if award:
        suppliers = [{"id": supplier_id, "name": f"SUPPLIER {ocid}"}] if award_supplier else []
        release["awards"] = [
            {
                "id": f"award-{ocid}",
                "suppliers": suppliers,
                "value": _value(amount),
                "date": "2025-02-15",
                "status": "awarded",
            }
        ]
    if contract:
        contract_row = {
            "id": f"contract-{ocid}",
            "value": _value(amount),
            "dateSigned": "2025-02-20",
            "status": "active",
        }
        if contract_award:
            contract_row["awardID"] = f"award-{ocid}"
        elif dangling_award:
            contract_row["awardID"] = f"award-missing-{ocid}"
        release["contracts"] = [contract_row]
    return {"ocid": ocid, "compiledRelease": release}


def hard_records() -> list[dict]:
    return [
        _release("ocds-hard-001"),
        _release("ocds-hard-001", title="DUPLICADO"),
        _release(
            "ocds-hard-002",
            category="services",
            amount=0,
            start="2025-03-01",
            end="2025-03-01",
            department="CUSCO",
            award=False,
            contract=False,
        ),
        _release(
            "ocds-hard-003",
            category="other",
            amount=-10,
            department="LIMA",
            award=False,
            contract=False,
        ),
        _release(
            "ocds-hard-004",
            category="works",
            amount=50_000,
            department=None,
            award=False,
            contract=True,
            contract_award=False,
            dangling_award=True,
        ),
        _release(
            "ocds-hard-005",
            category="goods",
            amount=20_000,
            department="PIURA",
            award_supplier=False,
            contract_award=False,
        ),
        _release(
            "ocds-hard-006",
            category="services",
            amount=30_000,
            department="LIMA",
            buyer=False,
            buyer_party=True,
            award=False,
            contract=False,
        ),
        _release(
            "ocds-hard-007",
            category="goods",
            amount=150_000,
            supplier_address=False,
            contract=False,
        ),
        _release("ocds-hard-008", title=""),
        _release("ocds-hard-009", published="not-a-date"),
        _release("ocds-hard-010", period=False),
        _release(
            "ocds-hard-011",
            supplier_id="PE-RUC-SUP-011",
            supplier_ruc="20555555555",
        ),
        _release(
            "ocds-hard-012",
            supplier_id="PE-RUC-SUP-012",
            supplier_ruc="20555555555",
        ),
    ]


def clean_records() -> list[dict]:
    return [
        _release("ocds-clean-001"),
        _release(
            "ocds-clean-002",
            category="services",
            amount=50_000,
            department="CUSCO",
            start="2025-03-01",
            end="2025-03-05",
        ),
    ]


def snapshot_records() -> tuple[list[dict], list[dict]]:
    shared = {
        "amount": 10_000,
        "start": "2024-05-01",
        "end": "2024-05-10",
        "published": "2024-05-01",
        "department": "LIMA",
        "release_date": "2024-05-01T10:00:00-05:00",
    }
    records_2024 = [
        _release("ocds-snap-001", title="SHARED 2024", segmentation="2024-05", **shared),
        _release(
            "ocds-snap-2024-b",
            title="PROCESO 2024 B",
            category="services",
            amount=20_000,
            published="2024-07-05",
            start="2024-06-01",
            end="2024-06-10",
            department="CUSCO",
            segmentation="2024-06",
            release_date="2024-06-01T10:00:00-05:00",
        ),
        _release(
            "ocds-snap-2024-c",
            title="PROCESO 2024 C",
            amount=300_000,
            published="2024-08-05",
            start="2024-07-01",
            end="2024-07-10",
            department="PIURA",
            segmentation="2024-07",
            release_date="2024-07-01T10:00:00-05:00",
        ),
        _release(
            "ocds-snap-2024-g",
            title="PROCESO 2025 G EN SNAPSHOT 2024",
            category="services",
            amount=60_000,
            published="2025-03-10",
            start="2025-03-10",
            end="2025-03-20",
            department="LIMA",
            segmentation="2025-03",
            release_date="2025-03-10T10:00:00-05:00",
        ),
    ]
    records_2025 = [
        _release("ocds-snap-001", title="SHARED UPDATED 2025", segmentation="2025-01", **shared),
        _release(
            "ocds-snap-2025-d",
            title="PROCESO 2025 D",
            amount=50_000,
            published="2025-01-10",
            start="2025-01-10",
            end="2025-01-20",
            department="LIMA",
            segmentation="2025-01",
            release_date="2025-01-10T10:00:00-05:00",
        ),
        _release(
            "ocds-snap-2025-e",
            title="PROCESO 2025 E",
            category="services",
            amount=100_000,
            published="2025-02-10",
            start="2025-02-10",
            end="2025-02-20",
            department="CUSCO",
            segmentation="2025-02",
            release_date="2025-02-10T10:00:00-05:00",
        ),
        _release(
            "ocds-snap-2025-f",
            title="PROCESO 2024 F EN SNAPSHOT 2025",
            amount=40_000,
            published="2024-08-15",
            start="2024-08-01",
            end="2024-08-10",
            department="CUSCO",
            segmentation="2024-08",
            release_date="2024-08-15T10:00:00-05:00",
        ),
    ]
    return records_2024, records_2025


def write_jsonl(path: Path, records: list[dict], *, malformed_first: bool = False) -> None:
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    if malformed_first:
        lines.insert(0, '{"ocid": "broken"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def settings(tmp_path: Path):
    from contratamype.config import Settings

    return Settings(
        artifacts_dir=tmp_path / "artifacts",
        db_path=tmp_path / "contratamype.duckdb",
    )


def verify_checksums(artifacts: Path, manifest: dict) -> None:
    lines = (artifacts / "checksums.sha256").read_text(encoding="utf-8").strip().splitlines()
    assert lines
    for line in lines:
        digest, name = line.split("  ", 1)
        actual = hashlib.sha256((artifacts / name).read_bytes()).hexdigest()
        assert actual == digest, name
    assert manifest["artifacts_sha256"]
    for name, digest in manifest["artifacts_sha256"].items():
        assert hashlib.sha256((artifacts / name).read_bytes()).hexdigest() == digest, name


def assert_samples(report: dict) -> None:
    for check in report["checks"]:
        if check["rows_failed"] > 0:
            assert check["failed_sample"], check["name"]
            assert len(check["failed_sample"]) <= 5, check["name"]
        else:
            assert check["failed_sample"] == [], check["name"]


@pytest.mark.fast
def test_hard_fixture_blocks_and_reports_exact_counts(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    input_path = tmp_path / "hard.jsonl"
    write_jsonl(input_path, hard_records(), malformed_first=True)
    artifacts = tmp_path / "artifacts"
    summary = run_pipeline(input_path, settings(tmp_path))

    assert summary["raw_records"] == 13
    assert summary["tenders"] == 12
    assert summary["awards"] == 8
    assert summary["contracts"] == 8
    assert summary["buyers"] == 11
    assert summary["suppliers"] == 7
    assert summary["cohort_records"] == 12
    assert summary["cohort_records_by_year"] == {2024: 0, 2025: 12}
    assert summary["mype_opportunities"] == 9
    assert summary["mype_opportunities_by_year"] == {2024: 0, 2025: 9}

    connection = duckdb.connect(str(tmp_path / "contratamype.duckdb"), read_only=True)
    try:
        missing_address = connection.execute(
            "SELECT COUNT(*) FROM suppliers WHERE department IS NULL"
        ).fetchone()[0]
        raw_duplicates = connection.execute(
            "SELECT COUNT(*) FROM raw_tenders WHERE ocid = 'ocds-hard-001'"
        ).fetchone()[0]
        tenders_rows = connection.execute(
            "SELECT COUNT(*) FROM tenders WHERE ocid = 'ocds-hard-001'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert missing_address == 1
    assert (raw_duplicates, tenders_rows) == (2, 1)
    assert summary["quality_gate"] == {
        "blocked": True,
        "blocking_checks": [
            "raw_schema_present",
            "buyer_present",
            "category_valid",
            "department_valid",
            "dates_valid",
            "amount_non_negative",
        ],
        "rule": "any level=fail check with status=fail blocks app exports",
    }
    assert summary["quality_summary"] == {
        "total_checks": 12,
        "failed_checks": 6,
        "warn_checks": 5,
        "passed_checks": 1,
    }

    report = json.loads((artifacts / "quality_report.json").read_text(encoding="utf-8"))
    assert [check["name"] for check in report["checks"]] == [
        "raw_schema_present",
        "ocid_unique",
        "buyer_present",
        "category_valid",
        "department_valid",
        "dates_valid",
        "period_quality",
        "amount_non_negative",
        "amount_zero",
        "award_complete",
        "contract_award_linked",
        "supplier_address_present",
    ]
    assert {check["name"]: check["rows_checked"] for check in report["checks"]} == {
        "raw_schema_present": 14,
        "ocid_unique": 12,
        "buyer_present": 13,
        "category_valid": 13,
        "department_valid": 13,
        "dates_valid": 13,
        "period_quality": 13,
        "amount_non_negative": 13,
        "amount_zero": 13,
        "award_complete": 8,
        "contract_award_linked": 8,
        "supplier_address_present": 7,
    }
    failed = {
        check["name"]: check["rows_failed"]
        for check in report["checks"]
        if check["status"] == "fail"
    }
    warned = {
        check["name"]: check["rows_failed"]
        for check in report["checks"]
        if check["status"] == "warn"
    }
    assert failed == {
        "raw_schema_present": 2,
        "buyer_present": 1,
        "category_valid": 1,
        "department_valid": 1,
        "dates_valid": 1,
        "amount_non_negative": 1,
    }
    assert warned == {
        "period_quality": 2,
        "amount_zero": 1,
        "award_complete": 1,
        "contract_award_linked": 2,
        "supplier_address_present": 1,
    }
    assert report["summary"] == {
        "total_checks": 12,
        "failed_checks": 6,
        "warn_checks": 5,
        "passed_checks": 1,
    }
    assert_samples(report)

    raw_check = report["checks"][0]
    assert raw_check["name"] == "raw_schema_present"
    assert raw_check["rows_checked"] == 14
    assert raw_check["parse_error_lines"] == [1]
    assert {"line": 1, "missing": "json"} in raw_check["failed_sample"]
    assert {
        "line": 10,
        "ocid": "ocds-hard-008",
        "missing": "title",
    } in raw_check["failed_sample"]

    samples = {check["name"]: check["failed_sample"] for check in report["checks"]}
    assert samples["ocid_unique"] == []
    assert samples["category_valid"][0]["ocid"] == "ocds-hard-003"
    assert samples["department_valid"][0]["ocid"] == "ocds-hard-004"
    assert samples["dates_valid"][0]["ocid"] == "ocds-hard-009"
    assert samples["amount_zero"][0]["ocid"] == "ocds-hard-002"
    assert samples["amount_non_negative"][0]["ocid"] == "ocds-hard-003"
    assert samples["award_complete"][0]["ocid"] == "ocds-hard-005"
    assert samples["supplier_address_present"][0]["supplier_id"] == "PE-RUC-ocds-hard-007"

    audits = {audit["name"]: audit for audit in report["audits"]}
    assert audits["month_coverage"] == {
        "name": "month_coverage",
        "status": "incomplete",
        "expected": 24,
        "observed": 1,
        "by_year": {
            "2024": {
                "expected": 12,
                "observed": 0,
                "missing": [f"2024-{month:02d}" for month in range(1, 13)],
            },
            "2025": {
                "expected": 12,
                "observed": 1,
                "missing": [f"2025-{month:02d}" for month in range(1, 13) if month != 2],
            },
        },
        "missing": [
            *[f"2024-{month:02d}" for month in range(1, 13)],
            *[f"2025-{month:02d}" for month in range(1, 13) if month != 2],
        ],
    }
    assert audits["region_coverage"]["status"] == "incomplete"
    assert audits["region_coverage"]["observed"] == 3
    assert audits["duplicate_parties"]["status"] == "warn"
    assert audits["duplicate_parties"]["duplicate_ruc_rows"] == 1
    assert audits["duplicate_parties"]["duplicate_name_rows"] == 0
    assert audits["duplicate_parties"]["duplicate_ruc_sample"] == [
        {"ruc": "20555555555", "rows": 2}
    ]
    assert audits["api_vs_bulk_spot_check"]["status"] == "not_run"
    assert "offline" in audits["api_vs_bulk_spot_check"]["reason"]

    assert not (artifacts / "tenders.parquet").exists()
    assert not (artifacts / "mype_opportunities.csv").exists()
    manifest = json.loads((artifacts / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_sha256"] == hashlib.sha256(input_path.read_bytes()).hexdigest()
    assert manifest["inputs"] == [
        {
            "path": str(input_path),
            "sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "bytes": input_path.stat().st_size,
            "records": 13,
        }
    ]
    settings_block = manifest["settings"]
    assert settings_block["mype_threshold"] == "200000"
    assert settings_block["target_categories"] == ["goods", "services"]
    assert settings_block["target_departments"] == []
    assert settings_block["cohort_year"] == 2025
    assert settings_block["cohort_years"] == [2024, 2025]
    assert re.fullmatch(r"\d+\.\d+\.\d+|unknown", settings_block["pipeline_version"])
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", settings_block["git_sha"])
    verify_checksums(artifacts, manifest)


@pytest.mark.fast
def test_clean_fixture_passes_and_exports(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    input_path = tmp_path / "clean.jsonl"
    write_jsonl(input_path, clean_records())
    artifacts = tmp_path / "artifacts"
    summary = run_pipeline(input_path, settings(tmp_path))

    assert summary["tenders"] == 2
    assert summary["cohort_records"] == 2
    assert summary["mype_opportunities"] == 2
    assert summary["quality_gate"]["blocked"] is False
    assert summary["quality_summary"] == {
        "total_checks": 12,
        "failed_checks": 0,
        "warn_checks": 0,
        "passed_checks": 12,
    }
    assert (artifacts / "tenders.parquet").exists()
    assert (artifacts / "mype_opportunities.csv").exists()
    assert len((artifacts / "mype_opportunities.csv").read_text(encoding="utf-8").splitlines()) == 3
    manifest = json.loads((artifacts / "run_manifest.json").read_text(encoding="utf-8"))
    verify_checksums(artifacts, manifest)


@pytest.mark.fast
def test_two_snapshots_merge_cohorts_and_export_both_years(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    records_2024, records_2025 = snapshot_records()
    path_2024 = tmp_path / "2024.jsonl"
    path_2025 = tmp_path / "2025.jsonl"
    write_jsonl(path_2024, records_2024)
    write_jsonl(path_2025, records_2025)
    artifacts = tmp_path / "artifacts"

    summary = run_pipeline([path_2025, path_2024], settings(tmp_path))

    assert summary["raw_records"] == 8
    assert summary["tenders"] == 7
    assert summary["buyers"] == 7
    assert summary["suppliers"] == 7
    assert summary["awards"] == 7
    assert summary["contracts"] == 7
    assert summary["cohort_records"] == 7
    assert summary["cohort_records_by_year"] == {2024: 3, 2025: 4}
    assert summary["mype_opportunities"] == 6
    assert summary["mype_opportunities_by_year"] == {2024: 2, 2025: 4}
    assert summary["cohort_years"] == [2024, 2025]
    assert summary["quality_gate"]["blocked"] is False
    assert summary["quality_summary"] == {
        "total_checks": 12,
        "failed_checks": 0,
        "warn_checks": 0,
        "passed_checks": 12,
    }
    assert summary["input"] == [str(path_2024), str(path_2025)]

    sha_2024 = hashlib.sha256(path_2024.read_bytes()).hexdigest()
    sha_2025 = hashlib.sha256(path_2025.read_bytes()).hexdigest()
    expected_combined = hashlib.sha256(
        f"{path_2024.name}:{sha_2024}\n{path_2025.name}:{sha_2025}".encode()
    ).hexdigest()
    assert summary["input_sha256"] == expected_combined

    connection = duckdb.connect(str(tmp_path / "contratamype.duckdb"), read_only=True)
    try:
        raw_snapshot_rows = connection.execute(
            "SELECT COUNT(*) FROM raw_tenders WHERE ocid = 'ocds-snap-001'"
        ).fetchone()[0]
        winner = connection.execute(
            "SELECT snapshot_year, title, segmentation_year FROM tenders "
            "WHERE ocid = 'ocds-snap-001'"
        ).fetchone()
        snapshot_years = {
            row[0]
            for row in connection.execute("SELECT DISTINCT snapshot_year FROM tenders").fetchall()
        }
        cross_year = connection.execute(
            "SELECT COUNT(*) FROM tenders WHERE snapshot_year <> segmentation_year"
        ).fetchone()[0]
    finally:
        connection.close()
    assert raw_snapshot_rows == 2
    assert winner == (2025, "SHARED UPDATED 2025", 2025)
    assert snapshot_years == {2024, 2025}
    assert cross_year == 2

    parquet_path = (artifacts / "tenders.parquet").as_posix()
    parquet_years = {
        row[0]
        for row in duckdb.connect()
        .execute(f"SELECT DISTINCT snapshot_year FROM read_parquet('{parquet_path}')")
        .fetchall()
    }
    assert parquet_years == {2024, 2025}

    csv_text = (artifacts / "mype_opportunities.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == 6
    assert "segmentation_year" in rows[0]
    assert {row["segmentation_year"] for row in rows} == {"2024", "2025"}
    assert {row["ocid"] for row in rows} == {
        "ocds-snap-001",
        "ocds-snap-2024-b",
        "ocds-snap-2024-g",
        "ocds-snap-2025-d",
        "ocds-snap-2025-e",
        "ocds-snap-2025-f",
    }

    report = json.loads((artifacts / "quality_report.json").read_text(encoding="utf-8"))
    audits = {audit["name"]: audit for audit in report["audits"]}
    assert audits["month_coverage"]["expected"] == 24
    assert audits["month_coverage"]["observed"] == 6
    assert {
        year: info["observed"] for year, info in audits["month_coverage"]["by_year"].items()
    } == {
        "2024": 3,
        "2025": 3,
    }
    assert audits["region_coverage"]["observed"] == 3
    assert audits["duplicate_parties"]["status"] == "pass"
    assert audits["api_vs_bulk_spot_check"]["status"] == "not_run"

    manifest = json.loads((artifacts / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_sha256"] == expected_combined
    assert manifest["inputs"] == [
        {
            "path": str(path_2024),
            "sha256": sha_2024,
            "bytes": path_2024.stat().st_size,
            "records": 4,
        },
        {
            "path": str(path_2025),
            "sha256": sha_2025,
            "bytes": path_2025.stat().st_size,
            "records": 4,
        },
    ]
    assert manifest["counts"]["cohort_records_by_year"] == {"2024": 3, "2025": 4}
    assert manifest["counts"]["mype_opportunities_by_year"] == {"2024": 2, "2025": 4}
    assert manifest["settings"]["cohort_years"] == [2024, 2025]
    verify_checksums(artifacts, manifest)


@pytest.mark.fast
def test_cli_accepts_repeated_inputs(tmp_path: Path) -> None:
    records_2024, records_2025 = snapshot_records()
    path_2024 = tmp_path / "2024.jsonl"
    path_2025 = tmp_path / "2025.jsonl"
    write_jsonl(path_2024, records_2024)
    write_jsonl(path_2025, records_2025)
    artifacts = tmp_path / "artifacts"
    db_path = tmp_path / "cli.duckdb"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "contratamype",
            "run",
            "--input",
            str(path_2025),
            "--input",
            str(path_2024),
            "--artifacts",
            str(artifacts),
            "--db",
            str(db_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["tenders"] == 7
    assert payload["cohort_records_by_year"] == {"2024": 3, "2025": 4}
    manifest = json.loads((artifacts / "run_manifest.json").read_text(encoding="utf-8"))
    assert [Path(item["path"]).name for item in manifest["inputs"]] == [
        "2024.jsonl",
        "2025.jsonl",
    ]


@pytest.mark.fast
def test_unknown_and_zero_amounts_are_not_mype(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    records = [
        _release("ocds-mype-001", amount=None),
        _release("ocds-mype-002", amount=0),
        _release("ocds-mype-003", amount=200_000),
    ]
    input_path = tmp_path / "mype.jsonl"
    write_jsonl(input_path, records)
    summary = run_pipeline(input_path, settings(tmp_path))

    assert summary["tenders"] == 3
    assert summary["mype_opportunities"] == 1
    assert summary["quality_gate"]["blocked"] is False
    assert summary["quality_summary"] == {
        "total_checks": 12,
        "failed_checks": 0,
        "warn_checks": 1,
        "passed_checks": 11,
    }


@pytest.mark.fast
def test_large_amount_keeps_cents(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    amount = 123_456_789.12
    input_path = tmp_path / "money.jsonl"
    write_jsonl(input_path, [_release("ocds-money-001", amount=amount)])
    artifacts = tmp_path / "artifacts"
    summary = run_pipeline(input_path, settings(tmp_path))
    assert summary["quality_gate"]["blocked"] is False
    assert summary["mype_opportunities"] == 0

    connection = duckdb.connect(str(tmp_path / "contratamype.duckdb"), read_only=True)
    try:
        stored, data_type = connection.execute(
            "SELECT amount_pen, typeof(amount_pen) FROM tenders"
        ).fetchone()
    finally:
        connection.close()
    assert data_type == "DECIMAL(18,2)"
    assert stored == Decimal("123456789.12")

    parquet_amount = (
        duckdb.connect()
        .execute(
            f"SELECT amount_pen FROM read_parquet('{(artifacts / 'tenders.parquet').as_posix()}')"
        )
        .fetchone()[0]
    )
    assert parquet_amount == Decimal("123456789.12")


@pytest.mark.fast
def test_cli_returns_nonzero_when_gate_blocks(tmp_path: Path) -> None:
    input_path = tmp_path / "hard.jsonl"
    write_jsonl(input_path, hard_records(), malformed_first=True)
    artifacts = tmp_path / "artifacts"
    db_path = tmp_path / "cli.duckdb"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "contratamype",
            "run",
            "--input",
            str(input_path),
            "--artifacts",
            str(artifacts),
            "--db",
            str(db_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["quality_gate"]["blocked"] is True


@pytest.mark.slow
@pytest.mark.skipif(
    not (BULK_2024.exists() and BULK_2025.exists()),
    reason="2024/2025 bulks are local-only and gitignored",
)
def test_multi_year_bulk_full_pipeline(tmp_path: Path) -> None:
    from contratamype.run import run_pipeline

    artifacts = tmp_path / "artifacts"
    summary = run_pipeline([BULK_2025, BULK_2024], settings(tmp_path))

    expected_inputs = [
        {
            "path": str(BULK_2024),
            "sha256": BULK_2024_SHA256,
            "bytes": 125_638_249,
            "records": 108_451,
        },
        {
            "path": str(BULK_2025),
            "sha256": BULK_2025_SHA256,
            "bytes": 148_719_573,
            "records": 124_538,
        },
    ]
    expected_combined = hashlib.sha256(
        f"{BULK_2024.name}:{BULK_2024_SHA256}\n{BULK_2025.name}:{BULK_2025_SHA256}".encode()
    ).hexdigest()
    assert summary["inputs"] == expected_inputs
    assert summary["input_sha256"] == expected_combined
    assert summary["raw_records"] == 232_989
    assert summary["tenders"] == 232_989
    assert summary["cohort_records"] == 123_931
    assert summary["cohort_records_by_year"] == {2024: 64_783, 2025: 59_148}
    assert summary["mype_opportunities"] == 58_380
    assert summary["mype_opportunities_by_year"] == {2024: 28_458, 2025: 29_922}
    assert summary["quality_gate"]["blocked"] is False
    assert summary["quality_summary"] == {
        "total_checks": 12,
        "failed_checks": 0,
        "warn_checks": 5,
        "passed_checks": 7,
    }
    report = json.loads((artifacts / "quality_report.json").read_text(encoding="utf-8"))
    assert {
        check["name"]: check["rows_failed"]
        for check in report["checks"]
        if check["status"] == "warn"
    } == {
        "period_quality": 232_982,
        "amount_zero": 19_100,
        "award_complete": 3_866,
        "contract_award_linked": 11_274,
        "supplier_address_present": 91_879,
    }
    assert all(check["failed_sample"] for check in report["checks"] if check["rows_failed"] > 0)
    audits = {audit["name"]: audit for audit in report["audits"]}
    assert audits["month_coverage"]["expected"] == 24
    assert audits["month_coverage"]["observed"] == 24
    assert {
        year: info["observed"] for year, info in audits["month_coverage"]["by_year"].items()
    } == {"2024": 12, "2025": 12}
    assert audits["region_coverage"]["observed"] == 25
    assert audits["duplicate_parties"]["duplicate_ruc_rows"] == 0
    assert audits["duplicate_parties"]["duplicate_name_rows"] == 16_021
    assert audits["api_vs_bulk_spot_check"]["status"] == "not_run"
    assert (artifacts / "tenders.parquet").exists()

    csv_text = (artifacts / "mype_opportunities.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == 58_380
    assert "segmentation_year" in rows[0]
    assert {
        year: sum(1 for row in rows if row["segmentation_year"] == year)
        for year in ("2024", "2025")
    } == {"2024": 28_458, "2025": 29_922}

    manifest = json.loads((artifacts / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["inputs"] == expected_inputs
    assert manifest["input_sha256"] == expected_combined
    assert manifest["counts"]["cohort_records_by_year"] == {"2024": 64_783, "2025": 59_148}
    assert manifest["settings"]["cohort_years"] == [2024, 2025]
    verify_checksums(artifacts, manifest)
