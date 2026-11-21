import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { MypeBadge } from "@/components/mype-badge";
import { PrintButton } from "@/components/print-button";
import { ApiError, getChecklist } from "@/lib/api";
import { formatAmount, formatDate } from "@/lib/format";
import { categoryLabel, methodLabel } from "@/lib/labels";
import type { Checklist } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Checklist de participación",
};

async function loadChecklist(ocid: string): Promise<Checklist | null> {
  try {
    return await getChecklist(ocid);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export default async function ChecklistPage({ params }: { params: Promise<{ ocid: string }> }) {
  const { ocid } = await params;
  const checklist = await loadChecklist(ocid);
  if (!checklist) notFound();

  const title = checklist.process.title?.trim() || "Proceso sin título";
  const pdfHref = `/opportunities/${encodeURIComponent(checklist.ocid)}/checklist/pdf`;

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 print:hidden">
        <Link
          href={`/opportunities/${encodeURIComponent(checklist.ocid)}`}
          className="inline-flex items-center gap-2 rounded-md text-sm font-semibold text-brand-800 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
        >
          <span aria-hidden="true">←</span> Volver a la ficha
        </Link>
        <div className="flex flex-wrap gap-2">
          <PrintButton />
          <a
            href={pdfHref}
            className="inline-flex items-center justify-center rounded-lg bg-brand-800 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
          >
            Descargar PDF
          </a>
        </div>
      </div>

      <article className="print-sheet rounded-2xl border border-stone-200 bg-white p-6 shadow-sm sm:p-10">
        <header className="border-b border-stone-200 pb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-700">
            ContrataMYPE · Checklist de participación
          </p>
          <h1 className="mt-2 text-3xl font-bold leading-tight tracking-tight text-brand-950">
            Checklist de participación
          </h1>
          <p className="mt-2 text-lg font-semibold text-stone-800">{title}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-stone-300 bg-stone-50 px-2.5 py-1 font-mono text-xs text-stone-700">
              {checklist.ocid}
            </span>
            <MypeBadge fit={checklist.process.mype_fit} />
          </div>
        </header>

        <section aria-labelledby="datos-clave" className="mt-6">
          <h2 id="datos-clave" className="text-lg font-bold text-brand-950">
            Datos clave de la fuente
          </h2>
          <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-3 rounded-xl bg-stone-50 p-4 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">
                Entidad compradora
              </dt>
              <dd className="mt-0.5 font-medium text-stone-900">
                {checklist.process.buyer_name ?? "Entidad compradora no informada"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">
                Departamento
              </dt>
              <dd className="mt-0.5 font-medium text-stone-900">
                {checklist.process.department ?? "No informado"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">
                Monto
              </dt>
              <dd className="mt-0.5 font-medium text-stone-900">
                {formatAmount(checklist.process.amount_pen)}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">
                Categoría y método
              </dt>
              <dd className="mt-0.5 font-medium text-stone-900">
                {categoryLabel(checklist.process.category)} ·{" "}
                {methodLabel(checklist.process.method)}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">
                Publicación
              </dt>
              <dd className="mt-0.5 font-medium text-stone-900">
                {formatDate(checklist.process.published_date)}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">
                Período registrado
              </dt>
              <dd className="mt-0.5 font-medium text-stone-900">
                {formatDate(checklist.process.tender_start)} a{" "}
                {formatDate(checklist.process.tender_end)}
              </dd>
            </div>
          </dl>
        </section>

        {checklist.warnings.length > 0 ? (
          <section aria-labelledby="advertencias" className="mt-6">
            <h2 id="advertencias" className="text-lg font-bold text-brand-950">
              Datos incompletos en la fuente
            </h2>
            <ul
              data-testid="checklist-warnings"
              className="mt-2 list-inside list-disc space-y-1 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950"
            >
              {checklist.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <section aria-labelledby="pasos" className="mt-7">
          <h2 id="pasos" className="text-lg font-bold text-brand-950">
            Pasos para revisar este proceso
          </h2>
          <ol className="mt-4 space-y-5">
            {checklist.items.map((item, index) => (
              <li key={item.id} className="flex gap-3">
                <span
                  aria-hidden="true"
                  className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border-2 border-brand-300 text-xs font-bold text-brand-800"
                >
                  {index + 1}
                </span>
                <div>
                  <h3 className="font-semibold text-stone-900">{item.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-stone-700">{item.detail}</p>
                  <p className="mt-1 text-xs text-stone-500">
                    Fuente: <code className="rounded bg-stone-100 px-1 py-0.5">{item.source}</code>
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <footer className="mt-8 border-t border-stone-200 pt-5 text-sm leading-6 text-stone-600">
          <p className="font-semibold text-stone-800">Fuente y límites</p>
          <p className="mt-1">
            Fuente:{" "}
            <a
              href={checklist.source.url}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-brand-800 underline-offset-4 hover:underline"
            >
              {checklist.source.name}
            </a>
            , licencia {checklist.source.license}. ContrataMYPE no está afiliado al OECE.
          </p>
          <p
            data-testid="disclaimer"
            className="mt-3 rounded-xl bg-amber-50 px-4 py-3 text-amber-950 ring-1 ring-amber-200"
          >
            {checklist.disclaimer}
          </p>
          <p className="mt-3 text-xs text-stone-500">
            Las bases del proceso y el cronograma publicado en el portal oficial prevalecen sobre
            este checklist.
          </p>
        </footer>
      </article>
    </main>
  );
}
