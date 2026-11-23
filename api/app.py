"""FastAPI application: read-only search, detail, stats and checklist endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any

import duckdb
from fastapi import FastAPI, HTTPException, Query

from api.checklist import build_checklist
from api.config import COHORT_YEARS
from api.db import Connection, fetch_all, fetch_one, money
from api.schemas import (
    AmountStats,
    Award,
    Buyer,
    CategoryStat,
    Checklist,
    Contract,
    DataQuality,
    DepartmentStat,
    Health,
    Meta,
    MethodStat,
    OpportunityDetail,
    OpportunityPage,
    OpportunitySummary,
    Stats,
    Supplier,
)

app = FastAPI(
    title="ContrataMYPE API",
    version="1.1.0",
    description=(
        "API de solo lectura sobre DuckDB. La etiqueta mype_fit se lee de la base; "
        "la API no recalcula la regla MYPE. Sin parámetro year, los endpoints "
        "agregan la cohorte 2024-2025; las filas históricas quedan fuera."
    ),
)

logger = logging.getLogger(__name__)

SUMMARY_COLUMNS = """
    t.ocid, t.title, t.description, t.category, t.method, t.amount_pen, t.currency,
    t.published_date, t.tender_start, t.tender_end, t.status, t.buyer_id, t.buyer_name,
    t.department, t.department_code, t.segmentation_id, t.segmentation_year,
    t.mype_fit, t.dates_valid, t.period_start_eq_end
"""


def _summary(row: dict[str, Any]) -> OpportunitySummary:
    return OpportunitySummary(
        ocid=row["ocid"],
        title=row["title"],
        description=row["description"],
        category=row["category"],
        method=row["method"],
        amount_pen=money(row["amount_pen"]),
        currency=row["currency"],
        published_date=row["published_date"],
        tender_start=row["tender_start"],
        tender_end=row["tender_end"],
        status=row["status"],
        buyer_id=row["buyer_id"],
        buyer_name=row["buyer_name"],
        department=row["department"],
        department_code=row["department_code"],
        segmentation_id=row["segmentation_id"],
        segmentation_year=row["segmentation_year"],
        mype_fit=row["mype_fit"],
        dates_valid=row["dates_valid"],
        period_start_eq_end=row["period_start_eq_end"],
    )


def _like_pattern(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _year_filter(year: int | None) -> tuple[str, list[Any]]:
    """SQL predicate for the cohort scope; ``None`` means the 2024-2025 cohort."""
    if year is None:
        placeholders = ", ".join("?" for _ in COHORT_YEARS)
        return f"segmentation_year IN ({placeholders})", list(COHORT_YEARS)
    return "segmentation_year = ?", [year]


def _distinct(connection: duckdb.DuckDBPyConnection, column: str, year: int | None) -> list[str]:
    condition, parameters = _year_filter(year)
    rows = fetch_all(
        connection,
        f"""
        SELECT DISTINCT {column} AS value
        FROM tenders
        WHERE {condition} AND {column} IS NOT NULL AND trim({column}) <> ''
        ORDER BY 1
        """,
        parameters,
    )
    return [row["value"] for row in rows]


def _detail(connection: duckdb.DuckDBPyConnection, ocid: str) -> OpportunityDetail:
    row = fetch_one(
        connection,
        f"""
        SELECT {SUMMARY_COLUMNS},
               b.name AS buyer_dim_name,
               b.ruc AS buyer_dim_ruc,
               b.department AS buyer_dim_department
        FROM tenders t
        LEFT JOIN buyers b ON b.buyer_id = t.buyer_id
        WHERE t.ocid = ?
        """,
        [ocid],
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada.")

    summary = _summary(row)
    buyer = None
    if row["buyer_id"] or row["buyer_name"]:
        buyer = Buyer(
            id=row["buyer_id"],
            name=row["buyer_dim_name"] or row["buyer_name"],
            ruc=row["buyer_dim_ruc"],
            department=row["buyer_dim_department"],
        )

    award_rows = fetch_all(
        connection,
        """
        SELECT a.award_id, a.supplier_id, a.supplier_name, a.amount_pen, a.award_date,
               a.status, s.name AS supplier_dim_name, s.ruc AS supplier_ruc,
               s.department AS supplier_department
        FROM awards a
        LEFT JOIN suppliers s ON s.supplier_id = a.supplier_id
        WHERE a.ocid = ?
        ORDER BY a.award_id NULLS LAST
        """,
        [ocid],
    )
    awards: list[Award] = []
    for award_row in award_rows:
        supplier = None
        if award_row["supplier_id"] or award_row["supplier_dim_name"]:
            supplier = Supplier(
                id=award_row["supplier_id"],
                name=award_row["supplier_dim_name"] or award_row["supplier_name"],
                ruc=award_row["supplier_ruc"],
                department=award_row["supplier_department"],
            )
        awards.append(
            Award(
                award_id=award_row["award_id"],
                supplier=supplier,
                supplier_name=award_row["supplier_name"] or award_row["supplier_dim_name"],
                amount_pen=money(award_row["amount_pen"]),
                award_date=award_row["award_date"],
                status=award_row["status"],
            )
        )

    contract_rows = fetch_all(
        connection,
        """
        SELECT contract_id, award_id, amount_pen, signed_date, status
        FROM contracts
        WHERE ocid = ?
        ORDER BY signed_date NULLS LAST, contract_id
        """,
        [ocid],
    )
    award_ids = {award.award_id for award in awards if award.award_id}
    contracts = [
        Contract(
            contract_id=contract_row["contract_id"],
            award_id=contract_row["award_id"],
            award_linked=bool(contract_row["award_id"]) and contract_row["award_id"] in award_ids,
            amount_pen=money(contract_row["amount_pen"]),
            signed_date=contract_row["signed_date"],
            status=contract_row["status"],
        )
        for contract_row in contract_rows
    ]

    start_eq_end = bool(row["period_start_eq_end"]) or (
        row["tender_start"] is not None and row["tender_start"] == row["tender_end"]
    )
    data_quality = DataQuality(
        missing_description=not (row["description"] or "").strip(),
        amount_reported=row["amount_pen"] is not None and row["amount_pen"] != 0,
        start_eq_end=start_eq_end,
        has_awards=bool(awards),
        has_contracts=bool(contracts),
        awards_without_supplier=sum(
            1 for award in awards if award.supplier is None and not award.supplier_name
        ),
        contracts_without_award=sum(1 for contract in contracts if not contract.award_linked),
        buyer_missing=buyer is None or not buyer.name,
        department_missing=not (row["department"] or "").strip(),
    )

    return OpportunityDetail(
        **summary.model_dump(),
        buyer=buyer,
        awards=awards,
        contracts=contracts,
        data_quality=data_quality,
    )


@app.get("/health", response_model=Health)
def health(connection: Connection) -> Health:
    try:
        connection.execute("SELECT 1 FROM tenders LIMIT 1").fetchall()
    except duckdb.Error as exc:
        logger.error("Health check failed on tenders: %s", exc)
        raise HTTPException(status_code=503, detail="Base de datos no disponible.") from exc
    return Health(status="ok")


@app.get("/meta", response_model=Meta)
def meta(
    connection: Connection,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> Meta:
    condition, parameters = _year_filter(year)
    categories = fetch_all(
        connection,
        f"""
        SELECT DISTINCT category AS value
        FROM tenders
        WHERE {condition} AND category IS NOT NULL AND trim(category) <> ''
        ORDER BY CASE category
            WHEN 'goods' THEN 1 WHEN 'services' THEN 2 WHEN 'works' THEN 3 ELSE 4
        END, category
        """,
        parameters,
    )
    amounts = fetch_one(
        connection,
        f"""
        SELECT MIN(CASE WHEN amount_pen > 0 THEN amount_pen END) AS min_amount,
               MAX(CASE WHEN amount_pen > 0 THEN amount_pen END) AS max_amount
        FROM tenders
        WHERE {condition}
        """,
        parameters,
    )
    cohort_condition, cohort_parameters = _year_filter(None)
    year_rows = fetch_all(
        connection,
        f"""
        SELECT DISTINCT segmentation_year AS value
        FROM tenders
        WHERE {cohort_condition}
        ORDER BY 1
        """,
        cohort_parameters,
    )
    return Meta(
        years=[int(row["value"]) for row in year_rows],
        departments=_distinct(connection, "department", year),
        categories=[row["value"] for row in categories],
        methods=_distinct(connection, "method", year),
        statuses=_distinct(connection, "status", year),
        amount_min=money(amounts["min_amount"]) if amounts else None,
        amount_max=money(amounts["max_amount"]) if amounts else None,
        currency="PEN",
    )


@app.get("/opportunities", response_model=OpportunityPage)
def opportunities(
    connection: Connection,
    q: Annotated[str | None, Query(max_length=200)] = None,
    department: str | None = None,
    category: str | None = None,
    method: str | None = None,
    min_amount: Annotated[float | None, Query(ge=0)] = None,
    max_amount: Annotated[float | None, Query(ge=0)] = None,
    status: str | None = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    mype_only: bool = False,
    page: Annotated[int, Query(ge=1, le=100000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OpportunityPage:
    condition, year_parameters = _year_filter(year)
    where = [condition]
    parameters: list[Any] = [*year_parameters]

    if q and q.strip():
        pattern = _like_pattern(q.strip())
        where.append(
            "(t.title ILIKE ? ESCAPE '\\' OR t.description ILIKE ? ESCAPE '\\' "
            "OR t.buyer_name ILIKE ? ESCAPE '\\' OR t.ocid ILIKE ? ESCAPE '\\')"
        )
        parameters.extend([pattern, pattern, pattern, pattern])
    if department:
        where.append("t.department = ?")
        parameters.append(department)
    if category:
        where.append("t.category = ?")
        parameters.append(category)
    if method:
        where.append("t.method = ?")
        parameters.append(method)
    if min_amount is not None:
        where.append("t.amount_pen >= ?")
        parameters.append(min_amount)
    if max_amount is not None:
        where.append("t.amount_pen <= ?")
        parameters.append(max_amount)
    if status:
        where.append("t.status = ?")
        parameters.append(status)
    if mype_only:
        where.append("t.mype_fit = true")

    where_sql = " AND ".join(where)
    total_row = fetch_one(
        connection,
        f"SELECT COUNT(*) AS total FROM tenders t WHERE {where_sql}",
        parameters,
    )
    total = int(total_row["total"]) if total_row else 0

    offset = (page - 1) * page_size
    rows = fetch_all(
        connection,
        f"""
        SELECT {SUMMARY_COLUMNS}
        FROM tenders t
        WHERE {where_sql}
        ORDER BY t.published_date DESC NULLS LAST, t.ocid
        LIMIT ? OFFSET ?
        """,
        [*parameters, page_size, offset],
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return OpportunityPage(
        items=[_summary(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@app.get("/opportunities/{ocid}", response_model=OpportunityDetail)
def opportunity_detail(connection: Connection, ocid: str) -> OpportunityDetail:
    return _detail(connection, ocid)


@app.get("/stats", response_model=Stats)
def stats(
    connection: Connection,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> Stats:
    condition, year_parameters = _year_filter(year)
    totals = fetch_one(
        connection,
        f"""
        SELECT COUNT(*) AS total,
               COALESCE(SUM(CASE WHEN mype_fit THEN 1 ELSE 0 END), 0) AS mype,
               COALESCE(SUM(CASE WHEN amount_pen = 0 THEN 1 ELSE 0 END), 0) AS zero_amount,
               COALESCE(SUM(
                   CASE WHEN description IS NULL OR trim(description) = '' THEN 1 ELSE 0 END
               ), 0) AS missing_description,
               COALESCE(SUM(CASE WHEN period_start_eq_end THEN 1 ELSE 0 END), 0) AS start_eq_end,
               MIN(CASE WHEN amount_pen > 0 THEN amount_pen END) AS amount_min,
               MAX(CASE WHEN amount_pen > 0 THEN amount_pen END) AS amount_max,
               MEDIAN(CASE WHEN amount_pen > 0 THEN amount_pen END) AS amount_median
        FROM tenders
        WHERE {condition}
        """,
        year_parameters,
    )
    if totals is None:
        raise HTTPException(status_code=500, detail="No se pudieron calcular las estadísticas.")

    group_sql = """
        SELECT {column} AS value, COUNT(*) AS total,
               COALESCE(SUM(CASE WHEN mype_fit THEN 1 ELSE 0 END), 0) AS mype
        FROM tenders
        WHERE {condition} AND {column} IS NOT NULL AND trim({column}) <> ''
        GROUP BY 1
        ORDER BY total DESC, value
    """
    departments = fetch_all(
        connection,
        group_sql.format(column="department", condition=condition),
        year_parameters,
    )
    categories = fetch_all(
        connection,
        group_sql.format(column="category", condition=condition),
        year_parameters,
    )
    methods = fetch_all(
        connection,
        group_sql.format(column="method", condition=condition),
        year_parameters,
    )

    return Stats(
        year=year,
        total=int(totals["total"]),
        mype_opportunities=int(totals["mype"]),
        missing_description=int(totals["missing_description"]),
        zero_amount=int(totals["zero_amount"]),
        start_eq_end=int(totals["start_eq_end"]),
        amount=AmountStats(
            min=money(totals["amount_min"]),
            max=money(totals["amount_max"]),
            median=money(totals["amount_median"]),
        ),
        by_department=[
            DepartmentStat(
                department=row["value"],
                total=int(row["total"]),
                mype=int(row["mype"]),
            )
            for row in departments
        ],
        by_category=[
            CategoryStat(
                category=row["value"],
                total=int(row["total"]),
                mype=int(row["mype"]),
            )
            for row in categories
        ],
        by_method=[
            MethodStat(
                method=row["value"],
                total=int(row["total"]),
                mype=int(row["mype"]),
            )
            for row in methods
        ],
    )


@app.get("/checklist/{ocid}", response_model=Checklist)
def checklist(connection: Connection, ocid: str) -> Checklist:
    return build_checklist(_detail(connection, ocid))
