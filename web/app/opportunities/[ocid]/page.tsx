import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { MypeBadge } from "@/components/mype-badge";
import { Notice } from "@/components/notice";
import { ApiError, getOpportunity } from "@/lib/api";
import { MYPE_DISCLAIMER } from "@/lib/explainer";
import { explainOpportunity } from "@/lib/explainer-server";
import { formatAmountUseful, formatDate, formatPEN } from "@/lib/format";
import { categoryLabel, methodLabel, statusLabel } from "@/lib/labels";
import type { OpportunityDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Detalle de oportunidad",
};

function dataAlerts(detail: OpportunityDetail): string[] {
  const alerts: string[] = [];
  if (detail.data_quality.missing_description) {
    alerts.push("La fuente no incluye una descripción del objeto.");
  }
  if (!detail.data_quality.amount_reported) {
    alerts.push(
      detail.amount_pen === 0
        ? "La fuente registra S/ 0.00 como monto (no informado útil)."
        : "La fuente no informa el monto del proceso.",
    );
  }
  if (detail.data_quality.start_eq_end) {
    alerts.push(
      "La fuente registra la misma fecha de inicio y fin. Confirma el cronograma en las bases del proceso.",
    );
  }
  if (detail.data_quality.buyer_missing) {
    alerts.push("Entidad compradora no informada.");
  }
  if (detail.data_quality.department_missing) {
    alerts.push("Departamento del proceso no informado.");
  }
  if (detail.data_quality.awards_without_supplier) {
    alerts.push("Adjudicación sin proveedor identificado.");
  }
  if (detail.data_quality.contracts_without_award) {
    alerts.push("Contrato sin adjudicación vinculada.");
  }
  return alerts;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-stone-900">{children}</dd>
    </div>
  );
}

async function loadOpportunity(ocid: string): Promise<OpportunityDetail | null> {
  try {
    return await getOpportunity(ocid);
  } catch (error) {
    if (error instanceof ApiError && error.isJsonNotFound) return null;
    throw error;
  }
}

export default async function OpportunityPage({ params }: { params: Promise<{ ocid: string }> }) {
  const { ocid } = await params;
  const detail = await loadOpportunity(ocid);
  if (!detail) notFound();

  const title = detail.title?.trim() || "Proceso sin título";
  const buyerName = detail.buyer?.name ?? detail.buyer_name;
  const alerts = dataAlerts(detail);
  const explanation = await explainOpportunity(detail);

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
      <Link
        href="/"
        className="inline-flex items-center gap-2 rounded-md text-sm font-semibold text-brand-800 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
      >
        <span aria-hidden="true">←</span> Volver a la búsqueda
      </Link>

      <div className="mt-5 grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          <header>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-stone-700">
                {categoryLabel(detail.category)}
              </span>
              <span className="rounded-full border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-stone-700">
                {methodLabel(detail.method)}
              </span>
              <span className="rounded-full border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-stone-700">
                Cohorte {detail.segmentation_year ?? "no informada"}
              </span>
            </div>
            <h1 className="mt-3 text-3xl font-bold leading-tight tracking-tight text-brand-950 sm:text-4xl">
              {title}
            </h1>
            <p className="mt-2 text-base text-stone-600">
              {buyerName || "Entidad compradora no informada"} ·{" "}
              {detail.department?.trim() || "Departamento no informado"}
            </p>
          </header>

          {alerts.length > 0 ? (
            <Notice tone="warning" title="Datos incompletos en la fuente">
              <ul className="list-inside list-disc space-y-1">
                {alerts.map((alert) => (
                  <li key={alert}>{alert}</li>
                ))}
              </ul>
              <p className="mt-2 text-xs">
                Estos vacíos se muestran tal como están en la fuente; no se reemplazan por valores
                inventados.
              </p>
            </Notice>
          ) : null}

          <section
            aria-labelledby="resumen"
            className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-6"
          >
            <h2 id="resumen" className="text-xl font-bold text-brand-950">
              Resumen del proceso
            </h2>
            {detail.description?.trim() ? (
              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-stone-700">
                {detail.description}
              </p>
            ) : (
              <p className="mt-3 text-sm italic leading-7 text-stone-500">
                Descripción no informada en la fuente. Revisa el título y las bases del proceso.
              </p>
            )}
          </section>

          <section
            aria-labelledby="datos"
            className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-6"
          >
            <h2 id="datos" className="text-xl font-bold text-brand-950">
              Datos del proceso
            </h2>
            <dl className="mt-4 grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
              <Field label="OCID">
                <span className="break-all font-mono text-xs sm:text-sm">{detail.ocid}</span>
              </Field>
              <Field label="Estado">
                <span>{statusLabel(detail.status)}</span>
              </Field>
              <Field label="Entidad compradora">
                {detail.buyer?.name ?? detail.buyer_name ?? "Entidad no informada"}
              </Field>
              <Field label="RUC de la entidad">{detail.buyer?.ruc ?? "No informado"}</Field>
              <Field label="Departamento">
                {detail.department?.trim() || "No informado"}
                {detail.department_code ? (
                  <span className="ml-1 font-normal text-stone-500">
                    (código {detail.department_code})
                  </span>
                ) : null}
              </Field>
              <Field label="Categoría">{categoryLabel(detail.category)}</Field>
              <Field label="Método de contratación">{methodLabel(detail.method)}</Field>
              <Field label="Monto registrado">{formatAmountUseful(detail.amount_pen)}</Field>
              <Field label="Publicado">{formatDate(detail.published_date)}</Field>
              <Field label="Inicio del período">{formatDate(detail.tender_start)}</Field>
              <Field label="Fin del período">
                {formatDate(detail.tender_end)}
                {detail.data_quality.start_eq_end ? (
                  <span className="ml-1 font-normal text-stone-500">
                    (misma fecha que el inicio)
                  </span>
                ) : null}
              </Field>
              <Field label="Segmentación">{detail.segmentation_id ?? "No informada"}</Field>
            </dl>
          </section>

          <section
            aria-labelledby="adjudicaciones"
            className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-6"
          >
            <h2 id="adjudicaciones" className="text-xl font-bold text-brand-950">
              Adjudicaciones
            </h2>
            {detail.awards.length === 0 ? (
              <p className="mt-3 text-sm leading-6 text-stone-600">
                La fuente no reporta adjudicaciones para este proceso.
              </p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <caption className="sr-only">Adjudicaciones publicadas para el proceso</caption>
                  <thead className="border-b border-stone-200 text-xs uppercase tracking-wide text-stone-500">
                    <tr>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Adjudicación
                      </th>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Proveedor
                      </th>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        RUC
                      </th>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Monto
                      </th>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Fecha
                      </th>
                      <th scope="col" className="py-2 font-semibold">
                        Estado
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {detail.awards.map((award, index) => (
                      <tr key={award.award_id ?? `award-${index}`}>
                        <td className="py-3 pr-4 font-mono text-xs">
                          {award.award_id ?? "No informado"}
                        </td>
                        <td className="py-3 pr-4">
                          {award.supplier?.name ??
                            award.supplier_name ??
                            "Adjudicación sin proveedor identificado."}
                        </td>
                        <td className="py-3 pr-4">{award.supplier?.ruc ?? "No informado"}</td>
                        <td className="py-3 pr-4">{formatPEN(award.amount_pen)}</td>
                        <td className="py-3 pr-4">{formatDate(award.award_date)}</td>
                        <td className="py-3">{statusLabel(award.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section
            aria-labelledby="contratos"
            className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-6"
          >
            <h2 id="contratos" className="text-xl font-bold text-brand-950">
              Contratos
            </h2>
            {detail.contracts.length === 0 ? (
              <p className="mt-3 text-sm leading-6 text-stone-600">
                La fuente no reporta contratos para este proceso.
              </p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <caption className="sr-only">Contratos publicados para el proceso</caption>
                  <thead className="border-b border-stone-200 text-xs uppercase tracking-wide text-stone-500">
                    <tr>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Contrato
                      </th>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Adjudicación
                      </th>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Monto
                      </th>
                      <th scope="col" className="py-2 pr-4 font-semibold">
                        Firmado
                      </th>
                      <th scope="col" className="py-2 font-semibold">
                        Estado
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {detail.contracts.map((contract, index) => (
                      <tr key={contract.contract_id ?? `contract-${index}`}>
                        <td className="py-3 pr-4 font-mono text-xs">
                          {contract.contract_id ?? "No informado"}
                        </td>
                        <td className="py-3 pr-4">
                          {contract.award_linked
                            ? (contract.award_id ?? "No informado")
                            : "Contrato sin adjudicación vinculada."}
                        </td>
                        <td className="py-3 pr-4">{formatPEN(contract.amount_pen)}</td>
                        <td className="py-3 pr-4">{formatDate(contract.signed_date)}</td>
                        <td className="py-3">{statusLabel(contract.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section
            aria-labelledby="explicacion"
            className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-6"
          >
            <h2 id="explicacion" className="text-xl font-bold text-brand-950">
              Cómo leer este proceso
            </h2>
            <p className="mt-2 text-sm leading-6 text-stone-600">{explanation.intro}</p>
            <dl className="mt-5 space-y-5">
              {explanation.points.map((point) => (
                <div key={point.label} data-testid="explainer-point">
                  <dt className="font-semibold text-brand-950">{point.label}</dt>
                  <dd className="mt-1 text-sm leading-6 text-stone-700">{point.text}</dd>
                  <dd className="mt-1 text-xs text-stone-500">
                    Fuente: <code className="rounded bg-stone-100 px-1 py-0.5">{point.source}</code>
                  </dd>
                </div>
              ))}
            </dl>
            <div
              data-testid="explainer-disclaimer"
              className="mt-5 rounded-xl bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950 ring-1 ring-amber-200"
            >
              {explanation.disclaimer}
            </div>
          </section>
        </div>

        <aside className="space-y-4">
          <section
            aria-labelledby="mype"
            className="rounded-2xl border border-teal-200 bg-teal-50/70 p-5"
          >
            <h2 id="mype" className="text-lg font-bold text-brand-950">
              Compatibilidad MYPE
            </h2>
            <div className="mt-3">
              <MypeBadge fit={detail.mype_fit} />
            </div>
            <p className="mt-3 text-sm leading-6 text-stone-700">
              {detail.mype_fit === true
                ? "La base de datos marca este proceso como compatible con MYPE."
                : detail.mype_fit === false
                  ? "La base de datos no marca este proceso como compatible con MYPE."
                  : "La base no tiene una etiqueta de compatibilidad para este proceso."}{" "}
              La regla se calcula en el pipeline con monto, categoría y departamento objetivo; esta
              aplicación no la recalcula.
            </p>
            <p className="mt-3 text-xs font-medium leading-5 text-amber-900">{MYPE_DISCLAIMER}</p>
          </section>

          <section className="rounded-2xl border border-stone-200 bg-white p-5">
            <h2 className="text-lg font-bold text-brand-950">Checklist de participación</h2>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              Revisa los pasos y descarga el PDF para trabajar sin conexión.
            </p>
            <div className="mt-4 flex flex-col gap-2">
              <Link
                href={`/opportunities/${encodeURIComponent(detail.ocid)}/checklist`}
                className="inline-flex justify-center rounded-lg bg-brand-800 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
              >
                Ver checklist
              </Link>
              <a
                href={`/opportunities/${encodeURIComponent(detail.ocid)}/checklist/pdf`}
                className="inline-flex justify-center rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 hover:border-brand-400 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
              >
                Descargar PDF
              </a>
            </div>
          </section>

          <section className="rounded-2xl border border-stone-200 bg-white p-5">
            <h2 className="text-lg font-bold text-brand-950">Fuente</h2>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              Datos publicados por el OECE en el Portal de Contrataciones Abiertas (OCDS), CC BY
              4.0. Esta ficha no modifica los campos oficiales.
            </p>
            <a
              href="https://contratacionesabiertas.oece.gob.pe/"
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-flex text-sm font-semibold text-brand-800 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
            >
              Consultar en el portal oficial ↗
            </a>
          </section>
        </aside>
      </div>
    </main>
  );
}
