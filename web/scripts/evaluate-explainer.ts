/**
 * Reproducible evaluation of the template explainer against the 15 real OCIDs in
 * docs/llm-eval-sample-2025.json and the live API detail endpoint.
 *
 * Usage (from web/):
 *   npx tsx scripts/evaluate-explainer.ts
 *
 * The API must be running against the real DuckDB, for example:
 *   CONTRATAMYPE_DB=data/processed/contratamype.duckdb uvicorn api.app:app --port 8000
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { getExplainer } from "../lib/explainer";
import type { OpportunityDetail } from "../lib/types";

interface SampleBucketCase {
  ocid: string;
}

interface SampleFile {
  buckets: Record<string, SampleBucketCase[]>;
}

interface CaseResult {
  bucket: string;
  ocid: string;
  points: number;
  citations: boolean;
  review: boolean;
  missingSection: boolean;
  missingCovered: boolean;
  disclaimer: boolean;
  noLegalClaim: boolean;
  missingText: string;
}

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const samplePath = path.resolve(webRoot, "..", "docs", "llm-eval-sample-2025.json");
const apiBaseUrl = (process.env.CONTRATAMYPE_API_URL ?? "http://127.0.0.1:8000").replace(
  /\/+$/,
  "",
);

const LEGAL_CLAIM_PATTERNS = [
  /\belegible\b/i,
  /\bpuede postular\b/i,
  /\bcalifica\b/i,
  /\bcumple los requisitos\b/i,
];

async function fetchDetail(ocid: string): Promise<OpportunityDetail> {
  const response = await fetch(`${apiBaseUrl}/opportunities/${encodeURIComponent(ocid)}`, {
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) {
    throw new Error(`API ${response.status} for ${ocid}: ${await response.text()}`);
  }
  const detail = (await response.json()) as OpportunityDetail;
  if (detail.ocid !== ocid) {
    throw new Error(`API returned ${detail.ocid} when asked for ${ocid}`);
  }
  return detail;
}

function expectedMissingLabels(detail: OpportunityDetail): string[] {
  const quality = detail.data_quality;
  const expected: string[] = [];
  if (quality.missing_description) expected.push("Descripción");
  if (!quality.amount_reported) expected.push("Monto");
  if (!detail.published_date) expected.push("Fecha de publicación");
  if (!detail.tender_start && !detail.tender_end) expected.push("Fechas del período");
  if (detail.tender_start && !detail.tender_end) expected.push("Fecha de fin");
  if (!detail.tender_start && detail.tender_end) expected.push("Fecha de inicio");
  if (quality.buyer_missing) expected.push("Entidad compradora");
  if (quality.department_missing) expected.push("Departamento");
  if (!detail.category) expected.push("Categoría");
  if (!detail.method) expected.push("Método");
  if (!quality.has_awards) expected.push("Adjudicaciones");
  if (!quality.has_contracts) expected.push("Contratos");
  if (quality.awards_without_supplier > 0) expected.push("proveedor");
  if (quality.contracts_without_award > 0) expected.push("adjudicación vinculada");
  if (detail.mype_fit === null || detail.mype_fit === undefined) expected.push("mype_fit");
  if (quality.start_eq_end) expected.push("Cronograma");
  return expected;
}

async function main(): Promise<void> {
  const sample = JSON.parse(await readFile(samplePath, "utf8")) as SampleFile;
  const cases = Object.entries(sample.buckets).flatMap(([bucket, entries]) =>
    entries.map((entry) => ({ bucket, ocid: entry.ocid })),
  );
  const explainer = getExplainer();
  const results: CaseResult[] = [];

  for (const sampleCase of cases) {
    const detail = await fetchDetail(sampleCase.ocid);
    const explanation = explainer(detail);
    const review = explanation.points.find((point) => point.label === "Qué revisar");
    const missing = explanation.points.find((point) => point.label === "Datos faltantes");
    const missingText = missing?.text ?? "";
    const expected = expectedMissingLabels(detail);
    const allText = `${explanation.intro} ${explanation.points.map((p) => p.text).join(" ")} ${
      explanation.disclaimer
    }`;
    const missingCovered =
      expected.length > 0
        ? expected.every((label) => missingText.includes(label))
        : missingText.includes("No se detectaron");

    results.push({
      bucket: sampleCase.bucket,
      ocid: sampleCase.ocid,
      points: explanation.points.length,
      citations:
        explanation.provider === "template" &&
        explanation.points.length > 0 &&
        explanation.points.every((point) => point.source.trim().length > 0),
      review: Boolean(review?.text.trim()) && Boolean(review?.source.includes("Bases del proceso")),
      missingSection:
        Boolean(missing?.text.trim()) && (missing?.source ?? "").includes("data_quality.*"),
      missingCovered,
      disclaimer:
        explanation.disclaimer.includes("heurística de compatibilidad MYPE") &&
        explanation.disclaimer.includes("no elegibilidad legal"),
      noLegalClaim: !LEGAL_CLAIM_PATTERNS.some((pattern) => pattern.test(allText)),
      missingText,
    });
  }

  console.log(
    "| Bucket | OCID | Puntos | Citas | Qué revisar | Datos faltantes | Vacíos cubiertos | Disclaimer | Sin elegibilidad | Resultado |",
  );
  console.log("|---|---|---:|---|---|---|---|---|---|---|");
  for (const result of results) {
    const pass =
      result.citations &&
      result.review &&
      result.missingSection &&
      result.missingCovered &&
      result.disclaimer &&
      result.noLegalClaim;
    console.log(
      `| ${result.bucket} | ${result.ocid} | ${result.points} | ${result.citations ? "sí" : "no"} | ${
        result.review ? "sí" : "no"
      } | ${result.missingSection ? "sí" : "no"} | ${result.missingCovered ? "sí" : "no"} | ${
        result.disclaimer ? "sí" : "no"
      } | ${result.noLegalClaim ? "sí" : "no"} | ${pass ? "PASA" : "FALLA"} |`,
    );
  }

  console.log("\n## Datos faltantes declarados por caso\n");
  for (const result of results) {
    console.log(`- **${result.bucket} / ${result.ocid}**: ${result.missingText}`);
  }

  const failures = results.filter(
    (result) =>
      !result.citations ||
      !result.review ||
      !result.missingSection ||
      !result.missingCovered ||
      !result.disclaimer ||
      !result.noLegalClaim,
  );
  console.log(
    `\n${results.length - failures.length}/${results.length} casos cumplen todos los criterios.`,
  );
  if (failures.length > 0) {
    console.error(`Fallaron: ${failures.map((result) => result.ocid).join(", ")}`);
    process.exitCode = 1;
  }
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
