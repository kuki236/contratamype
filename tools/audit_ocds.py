"""Stream the OECE OCDS bulk and produce a reproducible 2025 data profile.

The bulk is JSONL (one process per line). This tool does not build the product
model; it only measures volume, coverage, quality and amount distribution so
the v1.0.0 data window and the MYPE threshold are chosen with evidence.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from statistics import median

CATEGORY_VALUES = {"goods", "services", "works"}
AMOUNT_BUCKETS = (50_000, 100_000, 200_000, 400_000, 1_000_000)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_releases(payload: dict) -> Iterator[dict]:
    if isinstance(payload.get("compiledRelease"), dict):
        yield payload["compiledRelease"]
        return
    records = payload.get("records")
    if isinstance(records, list):
        for record in records:
            if isinstance(record.get("compiledRelease"), dict):
                yield record["compiledRelease"]
            elif isinstance(record, dict):
                yield record
        return
    release = payload.get("release")
    if isinstance(release, dict):
        yield release
        return
    yield payload


def party_department(parties: Iterable[dict]) -> tuple[str | None, str | None]:
    for party in parties:
        roles = set(party.get("roles") or [])
        if not roles.intersection({"buyer", "procuringEntity"}):
            continue
        address = party.get("address") or {}
        department = (address.get("department") or address.get("region") or "").strip()
        if department:
            return department.upper(), party.get("name")
    return None, None


def amount_pen(tender: dict) -> float | None:
    value = tender.get("value") or {}
    for key in ("amount_PEN", "amount"):
        raw = value.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
    return None


def supplier_ids(release: dict) -> set[str]:
    out: set[str] = set()
    for award in release.get("awards") or []:
        for supplier in award.get("suppliers") or []:
            identifier = supplier.get("id") or supplier.get("name")
            if identifier:
                out.add(str(identifier))
    return out


def audit(input_path: Path) -> dict:
    stats = Counter()
    categories = Counter()
    departments = Counter()
    methods = Counter()
    months = Counter()
    tenderers = Counter()
    awards_total = 0
    contracts_total = 0
    awards_without_supplier = 0
    contracts_without_award = 0
    duplicate_tenderers_records = 0
    amounts: list[float] = []
    ocids: set[str] = set()
    buyers: set[str] = set()
    suppliers: set[str] = set()
    dates: list[str] = []
    lines = 0
    parse_errors = 0

    opener = gzip.open if input_path.suffix == ".gz" else open
    with opener(input_path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            for release in iter_releases(payload):
                ocid = release.get("ocid")
                if not ocid:
                    stats["missing_ocid"] += 1
                    continue
                ocids.add(str(ocid))
                stats["records"] += 1
                date = str(release.get("date") or "")[:10]
                if len(date) == 10:
                    dates.append(date)

                tender = release.get("tender") or {}
                buyer = release.get("buyer") or {}
                parties = release.get("parties") or []
                department, _ = party_department(parties)
                if not buyer.get("id") and not buyer.get("name"):
                    stats["missing_buyer"] += 1
                else:
                    buyers.add(str(buyer.get("id") or buyer.get("name")))
                if department:
                    departments[department] += 1
                else:
                    stats["missing_department"] += 1

                title = (tender.get("title") or "").strip()
                description = (tender.get("description") or "").strip()
                if not title:
                    stats["missing_tender_title"] += 1
                if not description:
                    stats["missing_tender_description"] += 1
                category = tender.get("mainProcurementCategory")
                if category in CATEGORY_VALUES:
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
                    if amount < 0:
                        stats["amount_negative"] += 1
                    for bucket in AMOUNT_BUCKETS:
                        if amount <= bucket:
                            stats[f"amount_le_{bucket}"] += 1

                period = tender.get("tenderPeriod") or {}
                if (
                    period.get("startDate")
                    and period.get("endDate")
                    and str(period["startDate"])[:10] == str(period["endDate"])[:10]
                ):
                    stats["tender_period_start_eq_end"] += 1
                if not period.get("startDate") or not period.get("endDate"):
                    stats["tender_period_missing"] += 1

                tenderer_list = tender.get("tenderers") or [
                    party for party in parties if "tenderer" in (party.get("roles") or [])
                ]
                tenderer_keys = [
                    str(party.get("id") or party.get("name"))
                    for party in tenderer_list
                    if party.get("id") or party.get("name")
                ]
                if len(tenderer_keys) != len(set(tenderer_keys)):
                    duplicate_tenderers_records += 1
                for key in set(tenderer_keys):
                    tenderers[key] += 1

                awards = release.get("awards") or []
                contracts = release.get("contracts") or []
                awards_total += len(awards)
                contracts_total += len(contracts)
                for award in awards:
                    if not award.get("suppliers"):
                        awards_without_supplier += 1
                for contract in contracts:
                    if not contract.get("awardID"):
                        contracts_without_award += 1
                suppliers |= supplier_ids(release)

                month = (
                    str(period.get("startDate") or "")[:7]
                    or str(tender.get("datePublished") or "")[:7]
                    or date[:7]
                )
                if len(month) == 7:
                    months[month] += 1

    amounts_sorted = sorted(amounts)
    if amounts_sorted:

        def pct(p: float) -> float:
            index = min(len(amounts_sorted) - 1, max(0, int(round(p * (len(amounts_sorted) - 1)))))
            return round(amounts_sorted[index], 2)

        amount_summary = {
            "count": len(amounts_sorted),
            "min": round(amounts_sorted[0], 2),
            "median": round(median(amounts_sorted), 2),
            "p90": pct(0.90),
            "p99": pct(0.99),
            "max": round(amounts_sorted[-1], 2),
        }
    else:
        amount_summary = {"count": 0}

    return {
        "input": str(input_path),
        "input_bytes": input_path.stat().st_size,
        "input_sha256": sha256_file(input_path),
        "lines": lines,
        "parse_errors": parse_errors,
        "records": stats["records"],
        "unique_ocids": len(ocids),
        "unique_buyers": len(buyers),
        "unique_suppliers": len(suppliers),
        "unique_tenderers": len(tenderers),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "awards_total": awards_total,
        "contracts_total": contracts_total,
        "quality": {
            "missing_ocid": stats["missing_ocid"],
            "missing_buyer": stats["missing_buyer"],
            "missing_department": stats["missing_department"],
            "missing_tender_title": stats["missing_tender_title"],
            "missing_tender_description": stats["missing_tender_description"],
            "invalid_category": stats["invalid_category"],
            "amount_missing": stats["amount_missing"],
            "amount_zero": stats["amount_zero"],
            "amount_negative": stats["amount_negative"],
            "tender_period_start_eq_end": stats["tender_period_start_eq_end"],
            "tender_period_missing": stats["tender_period_missing"],
            "duplicate_tenderers_records": duplicate_tenderers_records,
            "awards_without_supplier": awards_without_supplier,
            "contracts_without_award": contracts_without_award,
        },
        "amounts": amount_summary,
        "amount_buckets": {
            f"le_{bucket}": stats[f"amount_le_{bucket}"] for bucket in AMOUNT_BUCKETS
        },
        "categories": dict(categories.most_common()),
        "departments": dict(departments.most_common()),
        "methods": dict(methods.most_common(20)),
        "months": dict(sorted(months.items())),
    }


def markdown(profile: dict) -> str:
    quality = profile["quality"]
    buckets = profile["amount_buckets"]
    lines = [
        "# Perfil de datos OCDS 2025",
        "",
        f"- Archivo: `{profile['input']}`",
        f"- Bytes: {profile['input_bytes']:,}",
        f"- SHA-256: `{profile['input_sha256']}`",
        f"- Líneas: {profile['lines']:,}",
        f"- Registros: {profile['records']:,}",
        f"- OCIDs únicos: {profile['unique_ocids']:,}",
        f"- Compradores únicos: {profile['unique_buyers']:,}",
        f"- Proveedores únicos (awards): {profile['unique_suppliers']:,}",
        f"- Postores únicos: {profile['unique_tenderers']:,}",
        f"- Fechas: {profile['date_min']} → {profile['date_max']}",
        f"- Awards: {profile['awards_total']:,}",
        f"- Contratos: {profile['contracts_total']:,}",
        "",
        "## Calidad",
        "",
        "| Regla | Fallos |",
        "|---|---:|",
    ]
    for key, value in quality.items():
        lines.append(f"| `{key}` | {value:,} |")
    lines += [
        "",
        "## Montos (PEN)",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
    ]
    for key, value in profile["amounts"].items():
        lines.append(f"| `{key}` | {value:,} |")
    lines += [
        "",
        "| Umbral | Registros ≤ umbral |",
        "|---|---:|",
    ]
    for key, value in buckets.items():
        lines.append(f"| {key.replace('le_', '≤ ')} | {value:,} |")
    lines += [
        "",
        "## Categorías",
        "",
        "| Categoría | Registros |",
        "|---|---:|",
    ]
    for key, value in profile["categories"].items():
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "## Departamentos (top 15)",
        "",
        "| Departamento | Registros |",
        "|---|---:|",
    ]
    for key, value in list(profile["departments"].items())[:15]:
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "## Meses",
        "",
        "| Mes | Registros |",
        "|---|---:|",
    ]
    for key, value in profile["months"].items():
        lines.append(f"| {key} | {value:,} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()
    profile = audit(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "data-profile-2025.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "data-profile-2025.md").write_text(markdown(profile), encoding="utf-8")
    print(
        json.dumps(
            {
                k: profile[k]
                for k in ("records", "unique_ocids", "unique_buyers", "unique_suppliers")
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
