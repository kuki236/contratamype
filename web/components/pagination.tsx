import Link from "next/link";
import type { SearchFilters } from "@/lib/filters";
import { toSearchParams } from "@/lib/filters";
import type { OpportunityPage } from "@/lib/types";

function href(filters: SearchFilters, page: number): string {
  const params = toSearchParams(filters, { page });
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

export function Pagination({
  filters,
  results,
}: {
  filters: SearchFilters;
  results: OpportunityPage;
}) {
  if (results.pages <= 1 || results.page > results.pages) return null;

  return (
    <nav
      aria-label="Paginación de resultados"
      className="mt-8 flex items-center justify-between gap-4"
    >
      {results.page > 1 ? (
        <Link
          href={href(filters, results.page - 1)}
          rel="prev"
          className="rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 hover:border-brand-400 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
        >
          ← Anterior
        </Link>
      ) : (
        <span aria-hidden="true" />
      )}
      <p className="text-sm text-stone-600">
        Página <strong>{results.page.toLocaleString("es-PE")}</strong> de{" "}
        <strong>{results.pages.toLocaleString("es-PE")}</strong>
      </p>
      {results.page < results.pages ? (
        <Link
          href={href(filters, results.page + 1)}
          rel="next"
          className="rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 hover:border-brand-400 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
        >
          Siguiente →
        </Link>
      ) : (
        <span aria-hidden="true" />
      )}
    </nav>
  );
}
