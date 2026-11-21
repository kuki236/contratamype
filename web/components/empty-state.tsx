import Link from "next/link";

export function EmptyState({ hasFilters }: { hasFilters: boolean }) {
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
      <h2 className="mt-4 text-xl font-semibold text-brand-950">No encontramos oportunidades</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-stone-600">
        {hasFilters
          ? "Prueba con menos filtros, otro departamento o un monto más amplio. La cohorte 2025 solo incluye los procesos publicados en la fuente."
          : "La cohorte consultada no tiene procesos cargados. Revisa que el pipeline haya generado la base de datos."}
      </p>
      <Link
        href="/"
        className="mt-5 inline-flex rounded-lg bg-brand-800 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
      >
        Limpiar filtros
      </Link>
    </div>
  );
}
