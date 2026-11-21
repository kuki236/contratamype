"""Checklist derived only from official fields; no process-specific requirements."""

from __future__ import annotations

from datetime import date

from api.schemas import (
    Checklist,
    ChecklistItem,
    ChecklistProcess,
    ChecklistSource,
    OpportunityDetail,
)

DISCLAIMER = (
    "La etiqueta de compatibilidad es una heurística de compatibilidad MYPE, "
    "no elegibilidad legal. Las bases del proceso son la fuente vinculante."
)

SOURCE = ChecklistSource(
    name="OECE — Portal de Contrataciones Abiertas (OCDS)",
    url="https://contratacionesabiertas.oece.gob.pe/",
    license="CC BY 4.0",
)

CATEGORY_LABELS = {
    "goods": "Bienes",
    "services": "Servicios",
    "works": "Obras",
}


def _money(value: float | None) -> str:
    return f"S/ {value:,.2f}" if value is not None else "monto no informado"


def _date(value: date | None) -> str:
    return value.isoformat() if value is not None else "fecha no informada"


def _category(value: str | None) -> str:
    if not value:
        return "categoría no informada"
    return CATEGORY_LABELS.get(value, value)


def _warnings(detail: OpportunityDetail) -> list[str]:
    quality = detail.data_quality
    warnings: list[str] = []
    if quality.missing_description:
        warnings.append("La fuente no incluye una descripción del objeto.")
    if not quality.amount_reported:
        warnings.append(
            "La fuente registra S/ 0.00 como monto. "
            "No asumas que el proceso es gratuito; confírmalo en las bases."
        )
    if quality.start_eq_end:
        warnings.append(
            "La fuente registra la misma fecha de inicio y fin. "
            "Confirma el cronograma en las bases del proceso."
        )
    if not quality.has_awards:
        warnings.append("La fuente no reporta adjudicaciones para este proceso.")
    if not quality.has_contracts:
        warnings.append("La fuente no reporta contratos para este proceso.")
    if quality.awards_without_supplier:
        warnings.append("Adjudicación sin proveedor identificado.")
    if quality.contracts_without_award:
        warnings.append("Contrato sin adjudicación vinculada.")
    if quality.buyer_missing:
        warnings.append("Entidad compradora no informada.")
    if quality.department_missing:
        warnings.append("Departamento del proceso no informado.")
    return warnings


def _items(detail: OpportunityDetail) -> list[ChecklistItem]:
    quality = detail.data_quality
    buyer = detail.buyer
    buyer_text = "Entidad compradora no informada."
    if buyer and buyer.name:
        buyer_text = f"Entidad: {buyer.name}."
        if buyer.ruc:
            buyer_text += f" RUC: {buyer.ruc}."
        if buyer.department:
            buyer_text += f" Departamento registrado: {buyer.department}."

    if detail.description and detail.description.strip():
        object_text = f"La fuente describe: {detail.description.strip()}"
    else:
        object_text = (
            "La fuente no incluye una descripción del objeto. Revisa el título y las bases."
        )

    if quality.amount_reported:
        amount_text = (
            f"La fuente registra {_money(detail.amount_pen)} (PEN). "
            "Confirma en las bases el valor referencial y las garantías aplicables."
        )
    else:
        amount_text = (
            "La fuente registra S/ 0.00 o no informa un monto útil. "
            "No asumas que el proceso es gratuito: confírmalo en las bases."
        )

    dates_text = (
        f"Publicación: {_date(detail.published_date)}. "
        f"Período registrado: {_date(detail.tender_start)} a {_date(detail.tender_end)}. "
        "La fecha de publicación no es el plazo de postulación."
    )
    if quality.start_eq_end:
        dates_text += " La fuente registra la misma fecha de inicio y fin; verifica el cronograma."

    if quality.has_awards:
        awards_text = (
            f"La fuente reporta {len(detail.awards)} adjudicación(es). "
            "Revisa el proveedor y el monto, pero ten en cuenta que pueden existir "
            "etapas posteriores no publicadas."
        )
    else:
        awards_text = (
            "La fuente no reporta adjudicaciones. Esto no impide que el proceso "
            "siga vigente o que se adjudique más adelante."
        )

    if quality.awards_without_supplier:
        awards_text += " Hay adjudicaciones sin proveedor identificado."
    if quality.contracts_without_award:
        awards_text += " Hay contratos sin adjudicación vinculada."

    if detail.mype_fit is True:
        mype_text = (
            "El campo mype_fit de la base indica compatibilidad MYPE para este proceso. "
            "Es una heurística de compatibilidad MYPE, no elegibilidad legal."
        )
    elif detail.mype_fit is False:
        mype_text = (
            "El campo mype_fit de la base no marca este proceso como compatible. "
            "Es una heurística de compatibilidad MYPE, no un impedimento legal."
        )
    else:
        mype_text = (
            "La base no tiene una etiqueta mype_fit para este proceso. "
            "No se puede afirmar compatibilidad ni elegibilidad."
        )

    return [
        ChecklistItem(
            id="official-lookup",
            title="Ubica el proceso en el portal oficial",
            detail=(
                f"Busca el OCID {detail.ocid} en Contrataciones Abiertas (OECE). "
                "Las bases y el cronograma oficiales prevalecen sobre esta ficha."
            ),
            source="tenders.ocid",
        ),
        ChecklistItem(
            id="object",
            title="Revisa el objeto del proceso",
            detail=object_text,
            source="tenders.title, tenders.description",
        ),
        ChecklistItem(
            id="amount",
            title="Confirma el valor referencial",
            detail=amount_text,
            source="tenders.amount_pen, tenders.currency",
        ),
        ChecklistItem(
            id="schedule",
            title="Verifica el cronograma",
            detail=dates_text,
            source="tenders.published_date, tenders.tender_start, tenders.tender_end",
        ),
        ChecklistItem(
            id="buyer",
            title="Identifica a la entidad compradora",
            detail=buyer_text,
            source="buyers.name, buyers.ruc, buyers.department",
        ),
        ChecklistItem(
            id="category-method",
            title="Revisa categoría y método",
            detail=(
                f"Categoría registrada: {_category(detail.category)}. "
                f"Método registrado: {detail.method or 'no informado'}. "
                "Los requisitos de calificación y las reglas del método están en las bases."
            ),
            source="tenders.category, tenders.method",
        ),
        ChecklistItem(
            id="awards-contracts",
            title="Revisa adjudicaciones y contratos publicados",
            detail=awards_text,
            source="awards.*, contracts.*",
        ),
        ChecklistItem(
            id="documents",
            title="Prepara la documentación exigida en las bases",
            detail=(
                "Esta ficha no enumera requisitos específicos porque no están en los campos OCDS. "
                "Verifica en las bases: RUC y representación legal, experiencia y capacidad, "
                "declaraciones juradas y garantías si corresponden. No presentes documentos "
                "de una lista genérica sin confirmarlos en el proceso."
            ),
            source="Bases del proceso (no incluidas en los campos OCDS)",
        ),
        ChecklistItem(
            id="mype",
            title="Confirma tu compatibilidad MYPE",
            detail=mype_text,
            source="tenders.mype_fit (regla calculada por el pipeline)",
        ),
    ]


def build_checklist(detail: OpportunityDetail) -> Checklist:
    return Checklist(
        ocid=detail.ocid,
        process=ChecklistProcess(
            title=detail.title,
            buyer_name=detail.buyer.name if detail.buyer else detail.buyer_name,
            department=detail.department,
            amount_pen=detail.amount_pen,
            published_date=detail.published_date,
            tender_start=detail.tender_start,
            tender_end=detail.tender_end,
            category=detail.category,
            method=detail.method,
            mype_fit=detail.mype_fit,
        ),
        source=SOURCE,
        items=_items(detail),
        warnings=_warnings(detail),
        disclaimer=DISCLAIMER,
    )
