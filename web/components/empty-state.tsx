import Link from "next/link";
import { hasActiveFilters, toSearchParams, type SearchFilters } from "@/lib/filters";

function hrefFor(filters: SearchFilters, mypeOnly: boolean): string {
  const params = toSearchParams({ ...filters, mype_only: mypeOnly }, { page: 1 });
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

export function EmptyState({
  filters,
  hasNonMypeResults,
}: {
  filters: SearchFilters;
  hasNonMypeResults: boolean;
}) {
  const active = hasActiveFilters(filters);
  const offerAll = filters.mype_only && hasNonMypeResults;
  const primaryClass =
    "inline-flex rounded-lg bg-brand-800 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";
  const secondaryClass =
    "inline-flex rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 hover:border-brand-400 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600";

  return (
    <div
      data-testid="empty-state"
      className="rounded-2xl border border-dashed border-stone-300 bg-white px-6 py-14 text-center"
    >
      <div
        aria-hidden="true"
        className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-stone-100 text-2xl"
      >
        ⌕
      </div>
      <h2 className="mt-4 text-xl font-semibold text-brand-950">
        {offerAll ? "No hay coincidencias solo entre MYPE" : "No encontramos oportunidades"}
      </h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-stone-600">
        {offerAll
          ? "Tu búsqueda no coincide con las oportunidades marcadas como compatibles MYPE, pero sí hay resultados en toda la cohorte."
          : active
            ? "Prueba con menos filtros, otro departamento o un monto más amplio. La cohorte 2025 solo incluye los procesos publicados en la fuente."
            : "La cohorte consultada no tiene procesos cargados. Revisa que el pipeline haya generado la base de datos."}
      </p>
      <div className="mt-5 flex flex-wrap justify-center gap-3">
        {offerAll ? (
          <Link href={hrefFor(filters, false)} className={primaryClass}>
            Ver todas las oportunidades
          </Link>
        ) : null}
        {active ? (
          <Link href="/" className={offerAll ? secondaryClass : primaryClass}>
            Limpiar filtros
          </Link>
        ) : null}
      </div>
    </div>
  );
}
