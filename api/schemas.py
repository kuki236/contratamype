"""Response models for the read-only API."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class Health(BaseModel):
    status: str


class Buyer(BaseModel):
    id: str | None
    name: str | None
    ruc: str | None
    department: str | None


class Supplier(BaseModel):
    id: str | None
    name: str | None
    ruc: str | None
    department: str | None


class OpportunitySummary(BaseModel):
    ocid: str
    title: str | None
    description: str | None
    category: str | None
    method: str | None
    amount_pen: float | None
    currency: str | None
    published_date: date | None
    tender_start: date | None
    tender_end: date | None
    status: str | None
    buyer_id: str | None
    buyer_name: str | None
    department: str | None
    department_code: str | None
    segmentation_id: str | None
    segmentation_year: int | None
    mype_fit: bool | None
    dates_valid: bool | None
    period_start_eq_end: bool | None


class Award(BaseModel):
    award_id: str | None
    supplier: Supplier | None
    supplier_name: str | None
    amount_pen: float | None
    award_date: date | None
    status: str | None


class Contract(BaseModel):
    contract_id: str | None
    award_id: str | None
    award_linked: bool
    amount_pen: float | None
    signed_date: date | None
    status: str | None


class DataQuality(BaseModel):
    missing_description: bool
    amount_reported: bool
    start_eq_end: bool
    has_awards: bool
    has_contracts: bool
    awards_without_supplier: int
    contracts_without_award: int
    buyer_missing: bool
    department_missing: bool


class OpportunityDetail(OpportunitySummary):
    buyer: Buyer | None
    awards: list[Award]
    contracts: list[Contract]
    data_quality: DataQuality


class OpportunityPage(BaseModel):
    items: list[OpportunitySummary]
    total: int
    page: int
    page_size: int
    pages: int


class Meta(BaseModel):
    cohort_year: int
    departments: list[str]
    categories: list[str]
    methods: list[str]
    statuses: list[str]
    amount_min: float | None
    amount_max: float | None
    currency: str


class DepartmentStat(BaseModel):
    department: str
    total: int
    mype: int


class CategoryStat(BaseModel):
    category: str
    total: int
    mype: int


class MethodStat(BaseModel):
    method: str
    total: int
    mype: int


class AmountStats(BaseModel):
    min: float | None
    max: float | None
    median: float | None


class Stats(BaseModel):
    year: int
    total: int
    mype_opportunities: int
    missing_description: int
    zero_amount: int
    start_eq_end: int
    amount: AmountStats
    by_department: list[DepartmentStat]
    by_category: list[CategoryStat]
    by_method: list[MethodStat]


class ChecklistProcess(BaseModel):
    title: str | None
    buyer_name: str | None
    department: str | None
    amount_pen: float | None
    published_date: date | None
    tender_start: date | None
    tender_end: date | None
    category: str | None
    method: str | None
    mype_fit: bool | None


class ChecklistItem(BaseModel):
    id: str
    title: str
    detail: str
    source: str


class ChecklistSource(BaseModel):
    name: str
    url: str
    license: str


class Checklist(BaseModel):
    ocid: str
    process: ChecklistProcess
    source: ChecklistSource
    items: list[ChecklistItem]
    warnings: list[str]
    disclaimer: str
