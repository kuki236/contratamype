"""Normalize OCDS releases into flat rows for the DuckDB star schema."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from contratamype.config import CATEGORY_VALUES, DEPARTMENT_CODES, Settings

CENT = Decimal("0.01")


@dataclass(slots=True)
class Normalized:
    tender: dict[str, Any]
    buyer: dict[str, Any] | None
    suppliers: list[dict[str, Any]]
    awards: list[dict[str, Any]]
    contracts: list[dict[str, Any]]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _date_value(value: Any) -> tuple[str | None, bool]:
    if not value:
        return None, True
    try:
        parsed = date.fromisoformat(str(value)[:10])
    except ValueError:
        return None, False
    return parsed.isoformat(), True


def _amount(value: dict[str, Any] | None) -> Decimal | None:
    if not value:
        return None
    raw = value.get("amount_PEN")
    if raw is None:
        raw = value.get("amount")
    if raw is None or isinstance(raw, bool):
        return None
    try:
        amount = Decimal(str(raw)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() else None


def _normalize_department(value: Any) -> str | None:
    text = _text(value)
    if not text:
        return None
    decomposed = unicodedata.normalize("NFKD", text.upper())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _party_ruc(party: dict[str, Any] | None) -> str | None:
    if not party:
        return None
    identifiers = list(party.get("additionalIdentifiers") or [])
    identifier = party.get("identifier")
    if isinstance(identifier, dict):
        identifiers.append(identifier)
    for candidate in identifiers:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("scheme") == "PE-RUC":
            value = _text(candidate.get("id"))
            if value:
                return value.removeprefix("PE-RUC-")
    return None


def _party_department(party: dict[str, Any] | None) -> str | None:
    if not party:
        return None
    address = party.get("address") or {}
    return _normalize_department(address.get("department") or address.get("region"))


def _roles(party: dict[str, Any]) -> set[str]:
    roles = party.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    return {str(role) for role in roles}


def _buyer_party(parties: list[dict[str, Any]]) -> dict[str, Any] | None:
    for party in parties:
        if _roles(party).intersection({"buyer", "procuringEntity"}):
            return party
    return None


def _supplier_rows(
    release: dict[str, Any],
    parties_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    awards: list[dict[str, Any]] = []
    suppliers: dict[str, dict[str, Any]] = {}
    for index, award in enumerate(release.get("awards") or []):
        award_id = _text(award.get("id")) or f"award-{index}"
        amount = _amount(award.get("value"))
        award_date, _ = _date_value(award.get("date"))
        status = _text(award.get("status"))
        award_suppliers = award.get("suppliers") or []
        if not award_suppliers:
            awards.append(
                {
                    "ocid": release.get("ocid"),
                    "award_id": award_id,
                    "supplier_id": "",
                    "supplier_name": "",
                    "amount_pen": amount,
                    "award_date": award_date,
                    "status": status,
                }
            )
        for supplier in award_suppliers:
            supplier_id = _text(supplier.get("id")) or _text(supplier.get("name")) or ""
            supplier_name = _text(supplier.get("name")) or ""
            party = parties_by_id.get(supplier_id)
            suppliers[supplier_id] = {
                "supplier_id": supplier_id,
                "name": supplier_name,
                "ruc": _party_ruc(party),
                "department": _party_department(party),
            }
            awards.append(
                {
                    "ocid": release.get("ocid"),
                    "award_id": award_id,
                    "supplier_id": supplier_id,
                    "supplier_name": supplier_name,
                    "amount_pen": amount,
                    "award_date": award_date,
                    "status": status,
                }
            )
    return awards, list(suppliers.values())


def _contract_rows(release: dict[str, Any]) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for index, contract in enumerate(release.get("contracts") or []):
        signed_date, _ = _date_value(contract.get("dateSigned"))
        contracts.append(
            {
                "ocid": release.get("ocid"),
                "contract_id": _text(contract.get("id")) or f"contract-{index}",
                "award_id": _text(contract.get("awardID")) or "",
                "amount_pen": _amount(contract.get("value")),
                "signed_date": signed_date,
                "status": _text(contract.get("status")),
            }
        )
    return contracts


def normalize_release(
    release: dict[str, Any],
    settings: Settings,
    snapshot_year: int,
) -> Normalized:
    ocid = _text(release.get("ocid")) or ""
    tender = release.get("tender") or {}
    buyer = release.get("buyer") or {}
    parties = release.get("parties") or []
    parties_by_id = {
        str(party.get("id")): party for party in parties if party.get("id") is not None
    }
    buyer_party = _buyer_party(parties)
    buyer_id = _text(buyer.get("id")) or ""
    buyer_name = _text(buyer.get("name")) or ""
    department = _party_department(buyer_party)
    department_code = DEPARTMENT_CODES.get(department or "")
    category = _text(tender.get("mainProcurementCategory"))
    amount = _amount(tender.get("value"))
    start, start_valid = _date_value((tender.get("tenderPeriod") or {}).get("startDate"))
    end, end_valid = _date_value((tender.get("tenderPeriod") or {}).get("endDate"))
    published_date, published_valid = _date_value(
        tender.get("datePublished") or release.get("date")
    )
    segmentation = release.get("dataSegmentation") or {}
    segmentation_id = _text(segmentation.get("id"))
    segmentation_year = None
    if segmentation_id and len(segmentation_id) >= 4 and segmentation_id[:4].isdigit():
        segmentation_year = int(segmentation_id[:4])
    elif start:
        segmentation_year = int(start[:4])
    elif published_date:
        segmentation_year = int(published_date[:4])

    mype_fit = (
        amount is not None
        and amount > 0
        and amount <= settings.mype_threshold
        and category in CATEGORY_VALUES
        and category in settings.target_categories
        and (not settings.target_departments or department in settings.target_departments)
    )

    tender_row = {
        "ocid": ocid,
        "title": _text(tender.get("title")),
        "description": _text(tender.get("description")),
        "category": category,
        "method": _text(tender.get("procurementMethodDetails"))
        or _text(tender.get("procurementMethod")),
        "amount_pen": amount,
        "currency": _text((tender.get("value") or {}).get("currency")),
        "published_date": published_date,
        "tender_start": start,
        "tender_end": end,
        "status": _text(tender.get("status")),
        "buyer_id": buyer_id,
        "buyer_name": buyer_name,
        "department": department,
        "department_code": department_code,
        "segmentation_id": segmentation_id,
        "segmentation_year": segmentation_year,
        "snapshot_year": int(snapshot_year),
        "mype_fit": bool(mype_fit),
        "dates_valid": start_valid and end_valid and published_valid,
        "period_start_eq_end": bool(start and end and start == end),
    }

    buyer_row = None
    if buyer_id or buyer_name:
        buyer_row = {
            "buyer_id": buyer_id or buyer_name,
            "name": buyer_name,
            "ruc": _party_ruc(buyer_party),
            "department": department,
        }

    awards, suppliers = _supplier_rows(release, parties_by_id)
    contracts = _contract_rows(release)

    return Normalized(
        tender=tender_row,
        buyer=buyer_row,
        suppliers=suppliers,
        awards=awards,
        contracts=contracts,
    )
