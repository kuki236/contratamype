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

const templateExplainer: Explainer = (detail) => {
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
