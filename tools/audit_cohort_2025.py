"""Profile the 2025 OCDS cohort using the publisher's dataSegmentation id.

The annual bulk is an update snapshot: it contains 2025 records plus older
processes updated in 2025. The 2025 cohort is the set whose dataSegmentation
starts with the target year. This tool makes that distinction reproducible.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_ocds import amount_pen, iter_releases, party_department, sha256_file  # noqa: E402

BUCKETS = (50_000, 100_000, 200_000, 400_000, 1_000_000)


def percentile(values: list[float], p: float) -> float:
    index = min(len(values) - 1, max(0, int(round(p * (len(values) - 1)))))
    return round(values[index], 2)


def profile(input_path: Path, year: str) -> dict:
    stats = Counter()
    categories = Counter()
    departments = Counter()
    methods = Counter()
    amounts: list[float] = []
    awards = 0
    contracts = 0

    opener = gzip.open if input_path.suffix == ".gz" else open
    with opener(input_path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            for release in iter_releases(payload):
                segmentation = release.get("dataSegmentation") or {}
                seg_id = str(segmentation.get("id") or "")
                if not seg_id.startswith(year):
                    continue
                stats["records"] += 1
                tender = release.get("tender") or {}
                parties = release.get("parties") or []
                department, _ = party_department(parties)
                if department:
                    departments[department] += 1
                else:
                    stats["missing_department"] += 1
                category = tender.get("mainProcurementCategory")
                if category:
                    categories[str(category)] += 1
                else:
                    stats["invalid_category"] += 1
                method = tender.get("procurementMethodDetails") or tender.get("procurementMethod")
                if method:
                    methods[str(method)] += 1
                amount = amount_pen(tender)
                if amount is None:
                    stats["amount_missing"] += 1
                else:
                    amounts.append(amount)
                    if amount == 0:
                        stats["amount_zero"] += 1
                    for bucket in BUCKETS:
                        if amount <= bucket:
                            stats[f"amount_le_{bucket}"] += 1
                period = tender.get("tenderPeriod") or {}
                if period.get("startDate") and period.get("endDate"):
                    if str(period["startDate"])[:10] == str(period["endDate"])[:10]:
                        stats["period_start_eq_end"] += 1
                else:
                    stats["period_missing"] += 1
                release_awards = release.get("awards") or []
                release_contracts = release.get("contracts") or []
                awards += len(release_awards)
                contracts += len(release_contracts)
                for award in release_awards:
                    if not award.get("suppliers"):
                        stats["awards_without_supplier"] += 1
                for contract in release_contracts:
                    if not contract.get("awardID"):
                        stats["contracts_without_award"] += 1

    amounts.sort()
    if amounts:
        amount_summary = {
            "count": len(amounts),
            "min": round(amounts[0], 2),
            "median": round(median(amounts), 2),
            "p90": percentile(amounts, 0.90),
            "p99": percentile(amounts, 0.99),
            "max": round(amounts[-1], 2),
        }
    else:
        amount_summary = {"count": 0}

    return {
        "cohort": f"dataSegmentation {year}",
        "input": str(input_path),
        "input_bytes": input_path.stat().st_size,
        "input_sha256": sha256_file(input_path),
        "records": stats["records"],
        "awards": awards,
        "contracts": contracts,
        "quality": {
            key: stats[key]
            for key in (
                "amount_missing",
                "amount_zero",
                "missing_department",
                "invalid_category",
                "period_missing",
                "period_start_eq_end",
                "awards_without_supplier",
                "contracts_without_award",
            )
        },
        "amounts": amount_summary,
        "amount_buckets": {f"le_{bucket}": stats[f"amount_le_{bucket}"] for bucket in BUCKETS},
        "categories": dict(categories.most_common()),
        "departments": dict(departments.most_common()),
        "methods": dict(methods.most_common(20)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--year", default="2025")
    args = parser.parse_args()
    result = profile(args.input, args.year)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: result[key] for key in ("cohort", "records", "awards", "contracts")},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
