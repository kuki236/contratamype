import { formatDate, formatPEN } from "./format";
import { categoryLabel, methodLabel } from "./labels";
import type { OpportunityDetail } from "./types";

export const MYPE_DISCLAIMER =
  "La etiqueta de compatibilidad es una heurística de compatibilidad MYPE, no elegibilidad legal.";

export interface ExplanationPoint {
  label: string;
  text: string;
  source: string;
}

export interface Explanation {
  intro: string;
  points: ExplanationPoint[];
  disclaimer: string;
  provider: string;
}

export type Explainer = (detail: OpportunityDetail) => Explanation;

function missingDataText(detail: OpportunityDetail): string {
  const quality = detail.data_quality;
  const missing: string[] = [];
  if (quality.missing_description) missing.push("Descripción del objeto");
  if (!quality.amount_reported) {
    missing.push(
      detail.amount_pen === 0 ? "Monto útil (la fuente registra S/ 0.00)" : "Monto del proceso",
    );
  }
  if (!detail.published_date) missing.push("Fecha de publicación");
  if (!detail.tender_start && !detail.tender_end) {
    missing.push("Fechas del período");
  } else if (!detail.tender_start) {
    missing.push("Fecha de inicio del período");
  } else if (!detail.tender_end) {
    missing.push("Fecha de fin del período");
  }
  if (quality.buyer_missing) missing.push("Entidad compradora");
  if (quality.department_missing) missing.push("Departamento del proceso");
  if (!detail.category) missing.push("Categoría");
  if (!detail.method) missing.push("Método de contratación");
  if (!quality.has_awards) missing.push("Adjudicaciones");
  if (!quality.has_contracts) missing.push("Contratos");
  if (quality.awards_without_supplier > 0) {
    missing.push(`${quality.awards_without_supplier} adjudicación(es) sin proveedor identificado`);
  }
  if (quality.contracts_without_award > 0) {
    missing.push(`${quality.contracts_without_award} contrato(s) sin adjudicación vinculada`);
  }
  if (detail.mype_fit === null || detail.mype_fit === undefined) {
    missing.push("Etiqueta mype_fit");
  }
  if (quality.start_eq_end) {
    missing.push("Cronograma completo (inicio y fin registran la misma fecha)");
  }
  return missing.length > 0
    ? `No informado o incompleto en la fuente: ${missing.join("; ")}. No se completa con supuestos.`
    : "No se detectaron campos faltantes entre los datos que muestra esta ficha.";
}

export const templateExplainer: Explainer = (detail) => {
  const buyer = detail.buyer;
  const buyerText = buyer?.name
    ? `${buyer.name}${buyer.ruc ? ` (RUC ${buyer.ruc})` : ""}, ${
        buyer.department ?? "departamento no informado"
      }.`
    : "La fuente no identifica a la entidad compradora.";

  const mypeText =
    detail.mype_fit === true
      ? "El campo mype_fit de la base marca este proceso como compatible con MYPE."
      : detail.mype_fit === false
        ? "El campo mype_fit de la base no marca este proceso como compatible con MYPE."
        : "La base no tiene una etiqueta mype_fit para este proceso.";

  return {
    provider: "template",
    intro:
      "Esta explicación se genera con una plantilla a partir de los campos publicados. " +
      "No agrega requisitos ni decide elegibilidad legal.",
    points: [
      {
        label: "Qué es este proceso",
        text: detail.title
          ? `${detail.title}. ${
              detail.description?.trim() ||
              "La fuente no incluye una descripción del objeto; revisa las bases."
            }`
          : "La fuente no informa el título del proceso. Revisa el OCID en el portal oficial.",
        source: "tenders.title, tenders.description",
      },
      {
        label: "Fechas",
        text:
          `Publicado el ${formatDate(detail.published_date)}. ` +
          `Período registrado: ${formatDate(detail.tender_start)} a ${formatDate(
            detail.tender_end,
          )}.` +
          (detail.data_quality.start_eq_end
            ? " La fuente registra la misma fecha de inicio y fin; confirma el cronograma en las bases."
            : "") +
          " La fecha de publicación no es el plazo de postulación.",
        source: "tenders.published_date, tenders.tender_start, tenders.tender_end",
      },
      {
        label: "Monto",
        text: detail.data_quality.amount_reported
          ? `La fuente registra ${formatPEN(detail.amount_pen)} como monto del proceso. ` +
            "Confirma el valor referencial y las garantías en las bases."
          : "La fuente registra un monto de S/ 0.00 o no lo informa. " +
            "No significa que el proceso sea gratuito: confírmalo en las bases.",
        source: "tenders.amount_pen, tenders.currency",
      },
      {
        label: "Entidad compradora",
        text: buyerText,
        source: "buyers.name, buyers.ruc, buyers.department",
      },
      {
        label: "Categoría y método",
        text: `Categoría: ${categoryLabel(detail.category)}. Método: ${methodLabel(
          detail.method,
        )}. Los requisitos de calificación están en las bases del proceso.`,
        source: "tenders.category, tenders.method",
      },
      {
        label: "Compatibilidad MYPE",
        text: `${mypeText} Se calcula en el pipeline con monto, categoría y departamento objetivo; esta aplicación no recalcula la regla.`,
        source: "tenders.mype_fit (regla del pipeline)",
      },
      {
        label: "Qué revisar",
        text:
          `Antes de postular, busca el OCID ${detail.ocid} en el portal oficial y revisa las bases integradas, ` +
          "el cronograma publicado y los requisitos de calificación. Esta ficha no enumera documentos ni " +
          "requisitos específicos; el checklist solo plantea verificaciones genéricas.",
        source: "Bases del proceso (no incluidas en los campos OCDS); tenders.ocid",
      },
      {
        label: "Datos faltantes",
        text: missingDataText(detail),
        source: "data_quality.* (flags de la API), tenders.*, buyers.*, awards.*, contracts.*",
      },
    ],
    disclaimer: MYPE_DISCLAIMER,
  };
};

const EXPLAINERS: Record<string, Explainer> = {
  template: templateExplainer,
};

export function getExplainer(): Explainer {
  const configured = process.env.CONTRATAMYPE_EXPLAINER?.trim().toLowerCase();
  return (configured && EXPLAINERS[configured]) || templateExplainer;
}
