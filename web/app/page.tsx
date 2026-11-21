import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState } from "@/components/empty-state";
import { OpportunityCard } from "@/components/opportunity-card";
import { Pagination } from "@/components/pagination";
import { SearchForm } from "@/components/search-form";
import { getMeta, getStats, searchOpportunities } from "@/lib/api";
import {
  COHORT_YEAR,
  pageLabel,
  parseFilters,
  toOpportunityQuery,
  toSearchParams,
} from "@/lib/filters";
import { formatPENCompact } from "@/lib/format";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Buscar oportunidades",
};

type RawSearchParams = Record<string, string | string[] | undefined>;

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<RawSearchParams>;
}) {
  const filters = parseFilters(await searchParams);
  const query = toOpportunityQuery(filters);
  const [meta, stats, results] = await Promise.all([
    getMeta(COHORT_YEAR),
    getStats(COHORT_YEAR),
    searchOpportunities(query),
  ]);
  const outOfRange =
    results.items.length === 0 && results.pages > 0 && filters.page > results.pages;
  let hasNonMypeResults = false;
  if (!outOfRange && results.total === 0 && filters.mype_only) {
    const allResults = await searchOpportunities({ ...query, mype_only: false, page: 1 });
    hasNonMypeResults = allResults.total > 0;
  }
  const firstPageParams = toSearchParams(filters, { page: 1 });

  return (
    <main className="flex-1 pb-4">
      <section className="relative overflow-hidden bg-brand-950 text-white">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(20,184,166,0.18),transparent_35%),radial-gradient(circle_at_85%_0%,rgba(59,130,246,0.16),transparent_40%)]"
        />
        <div className="relative mx-auto max-w-6xl px-4 pb-24 pt-12 sm:px-6 sm:pt-16">
          <p className="inline-flex items-center gap-2 rounded-full border border-teal-300/30 bg-teal-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-teal-200">
            <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-teal-300" />
            Datos abiertos OECE · Cohorte {COHORT_YEAR}
          </p>
          <h1 className="mt-5 max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
            Encuentra oportunidades para tu MYPE
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
            Busca procesos de compras públicas en Perú, entiende los datos oficiales y descarga un
            checklist para revisar antes de postular.
          </p>
          <dl className="mt-8 grid max-w-2xl grid-cols-1 gap-3 text-sm sm:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              <dt className="text-xs uppercase tracking-wide text-slate-400">Procesos 2025</dt>
              <dd className="mt-1 text-xl font-semibold">{stats.total.toLocaleString("es-PE")}</dd>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              <dt className="text-xs uppercase tracking-wide text-slate-400">Compatibles MYPE</dt>
              <dd className="mt-1 text-xl font-semibold">
                {stats.mype_opportunities.toLocaleString("es-PE")}
              </dd>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              <dt className="text-xs uppercase tracking-wide text-slate-400">Monto mediano</dt>
              <dd className="mt-1 text-xl font-semibold">
                {formatPENCompact(stats.amount.median)}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section
        aria-label="Filtros de búsqueda"
        className="relative z-10 mx-auto -mt-14 max-w-6xl px-4 sm:px-6"
      >
        <SearchForm meta={meta} filters={filters} />
      </section>

      <section aria-labelledby="resultados" className="mx-auto mt-10 max-w-6xl px-4 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-stone-200 pb-4">
          <div>
            <h2 id="resultados" className="text-2xl font-bold tracking-tight text-brand-950">
              {results.total.toLocaleString("es-PE")}{" "}
              {results.total === 1 ? "oportunidad" : "oportunidades"}
            </h2>
            <p className="mt-1 text-sm text-stone-600">
              {pageLabel(results)} · {filters.mype_only ? "Solo compatibles MYPE" : "Todas"} ·
              Cohorte {COHORT_YEAR}
            </p>
          </div>
          <a
            href="#como-funciona"
            className="text-sm font-semibold text-brand-800 underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
          >
            Cómo leer los resultados
          </a>
        </div>

        {outOfRange ? (
          <div
            data-testid="page-out-of-range"
            className="mt-8 rounded-2xl border border-dashed border-amber-300 bg-amber-50 px-6 py-14 text-center"
          >
            <h2 className="text-xl font-semibold text-brand-950">Página fuera de rango</h2>
            <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-stone-700">
              La página {filters.page.toLocaleString("es-PE")} no existe para esta búsqueda: hay{" "}
              {results.pages.toLocaleString("es-PE")} página
              {results.pages === 1 ? "" : "s"} con {results.total.toLocaleString("es-PE")} resultado
              {results.total === 1 ? "" : "s"}.
            </p>
            <Link
              href={`/?${firstPageParams.toString()}`}
              className="mt-5 inline-flex rounded-lg bg-brand-800 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
            >
              Ir a la página 1
            </Link>
          </div>
        ) : results.items.length === 0 ? (
          <div className="mt-8">
            <EmptyState filters={filters} hasNonMypeResults={hasNonMypeResults} />
          </div>
        ) : (
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {results.items.map((opportunity) => (
              <OpportunityCard key={opportunity.ocid} opportunity={opportunity} />
            ))}
          </div>
        )}

        <Pagination filters={filters} results={results} />
      </section>

      <section id="como-funciona" className="mx-auto mt-16 max-w-6xl scroll-mt-8 px-4 sm:px-6">
        <div className="rounded-3xl border border-stone-200 bg-white p-6 sm:p-10">
          <h2 className="text-2xl font-bold tracking-tight text-brand-950">
            Cómo leer una oportunidad
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">
            La ficha muestra solo campos publicados en la fuente OCDS. Cuando un dato falta, se
            indica explícitamente: no se completa con supuestos.
          </p>
          <ol className="mt-8 grid gap-6 md:grid-cols-3">
            <li>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 font-bold text-brand-800">
                1
              </span>
              <h3 className="mt-3 font-semibold text-brand-950">Filtra lo relevante</h3>
              <p className="mt-1 text-sm leading-6 text-stone-600">
                Departamento, categoría, método y monto. La etiqueta MYPE es una heurística de
                compatibilidad MYPE, no elegibilidad legal.
              </p>
            </li>
            <li>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 font-bold text-brand-800">
                2
              </span>
              <h3 className="mt-3 font-semibold text-brand-950">Revisa la ficha y las bases</h3>
              <p className="mt-1 text-sm leading-6 text-stone-600">
                La explicación usa plantillas y cita el campo de origen. Las bases del proceso son
                la fuente vinculante para requisitos y plazos.
              </p>
            </li>
            <li>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 font-bold text-brand-800">
                3
              </span>
              <h3 className="mt-3 font-semibold text-brand-950">Descarga el checklist</h3>
              <p className="mt-1 text-sm leading-6 text-stone-600">
                Imprímelo o descárgalo en PDF. No enumera requisitos específicos que no estén en los
                campos oficiales.
              </p>
            </li>
          </ol>
          <div className="mt-8 rounded-xl bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950 ring-1 ring-amber-200">
            <strong>Importante:</strong> ContrataMYPE no es asesoría legal y no determina
            elegibilidad. La etiqueta de compatibilidad es una heurística de compatibilidad MYPE, no
            elegibilidad legal.
          </div>
        </div>
      </section>
    </main>
  );
}
