import Link from "next/link";
import { MAX_QUERY_LENGTH, type SearchFilters } from "@/lib/filters";
import { cohortLabel } from "@/lib/format";
import { CATEGORY_LABELS } from "@/lib/labels";
import type { Meta } from "@/lib/types";

const inputClass =
  "mt-1 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 shadow-sm outline-none transition focus:border-brand-600 focus:ring-2 focus:ring-brand-600/20";
const labelClass = "block text-sm font-semibold text-stone-800";

function SelectOptions({
  values,
  labels,
  includeEmpty = "Todos",
  current,
}: {
  values: string[];
  labels?: Record<string, string>;
  includeEmpty?: string;
  current?: string;
}) {
  const missing = current && !values.includes(current) ? current : null;
  return (
    <>
      <option value="">{includeEmpty}</option>
      {missing ? <option value={missing}>{labels?.[missing] ?? missing}</option> : null}
      {values.map((value) => (
        <option key={value} value={value}>
          {labels?.[value] ?? value}
        </option>
      ))}
    </>
  );
}

export function SearchForm({ meta, filters }: { meta: Meta; filters: SearchFilters }) {
  const hasFilters =
    filters.q ||
    filters.department ||
    filters.category ||
    filters.method ||
    filters.min_amount ||
    filters.max_amount ||
    filters.status ||
    filters.year ||
    !filters.mype_only;
  const years = [...meta.years].sort((a, b) => b - a).map(String);
  const cohortText =
    meta.years.length === 1 ? `Cohorte ${meta.years[0]}` : `Cohortes ${cohortLabel(meta.years)}`;

  return (
    <form
      method="get"
      action="/"
      role="search"
      aria-label="Buscar oportunidades"
      className="rounded-2xl border border-stone-200 bg-white p-5 shadow-lg shadow-stone-900/5 sm:p-6"
    >
      <div>
        <label htmlFor="q" className={labelClass}>
          Buscar por texto
        </label>
        <p id="q-help" className="mt-0.5 text-xs text-stone-500">
          Busca en el título, la descripción, la entidad o el OCID.
        </p>
        <input
          id="q"
          name="q"
          type="search"
          defaultValue={filters.q}
          maxLength={MAX_QUERY_LENGTH}
          placeholder="Ej.: laptops, limpieza, municipalidad"
          aria-describedby="q-help"
          className={`${inputClass} mt-2 py-3 text-base`}
        />
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label htmlFor="year" className={labelClass}>
            Año
          </label>
          <select id="year" name="year" defaultValue={filters.year} className={inputClass}>
            <SelectOptions values={years} current={filters.year} />
          </select>
        </div>

        <div>
          <label htmlFor="department" className={labelClass}>
            Departamento
          </label>
          <select
            id="department"
            name="department"
            defaultValue={filters.department}
            className={inputClass}
          >
            <SelectOptions values={meta.departments} current={filters.department} />
          </select>
        </div>

        <div>
          <label htmlFor="category" className={labelClass}>
            Categoría
          </label>
          <select
            id="category"
            name="category"
            defaultValue={filters.category}
            className={inputClass}
          >
            <SelectOptions
              values={meta.categories}
              labels={CATEGORY_LABELS}
              current={filters.category}
            />
          </select>
        </div>

        <div>
          <label htmlFor="method" className={labelClass}>
            Método de contratación
          </label>
          <select id="method" name="method" defaultValue={filters.method} className={inputClass}>
            <SelectOptions values={meta.methods} current={filters.method} />
          </select>
        </div>

        <div>
          <label htmlFor="min_amount" className={labelClass}>
            Monto mínimo (S/)
          </label>
          <input
            id="min_amount"
            name="min_amount"
            type="number"
            inputMode="decimal"
            min="0"
            step="0.01"
            defaultValue={filters.min_amount}
            placeholder="0.00"
            className={inputClass}
          />
        </div>

        <div>
          <label htmlFor="max_amount" className={labelClass}>
            Monto máximo (S/)
          </label>
          <input
            id="max_amount"
            name="max_amount"
            type="number"
            inputMode="decimal"
            min="0"
            step="0.01"
            defaultValue={filters.max_amount}
            placeholder="200000.00"
            className={inputClass}
          />
        </div>

        <div>
          <label htmlFor="mype_only" className={labelClass}>
            Compatibilidad MYPE
          </label>
          <select
            id="mype_only"
            name="mype_only"
            defaultValue={filters.mype_only ? "1" : "0"}
            aria-describedby="mype-help"
            className={inputClass}
          >
            <option value="1">Solo compatibles MYPE</option>
            <option value="0">Todas las oportunidades</option>
          </select>
          <p id="mype-help" className="mt-1 text-xs text-stone-500">
            Es una heurística de compatibilidad, no elegibilidad legal.
          </p>
        </div>

        <div>
          <label htmlFor="status" className={labelClass}>
            Estado
          </label>
          <select
            id="status"
            name="status"
            defaultValue={filters.status}
            disabled={meta.statuses.length === 0}
            className={`${inputClass} disabled:cursor-not-allowed disabled:bg-stone-100 disabled:text-stone-500`}
          >
            {meta.statuses.length > 0 ? (
              <SelectOptions values={meta.statuses} current={filters.status} />
            ) : (
              <option value="">Sin estados en la fuente</option>
            )}
          </select>
          {meta.statuses.length === 0 ? (
            <p className="mt-1 text-xs text-stone-500">
              La cohorte no informa estados de proceso; el filtro queda deshabilitado.
            </p>
          ) : null}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="submit"
          className="inline-flex items-center justify-center rounded-lg bg-brand-800 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
        >
          Buscar oportunidades
        </button>
        {hasFilters ? (
          <Link
            href="/"
            className="rounded-lg px-3 py-2 text-sm font-semibold text-brand-800 underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
          >
            Limpiar filtros
          </Link>
        ) : null}
        <span className="ml-auto text-xs text-stone-500">
          {cohortText} · {meta.departments.length} departamentos en la fuente
        </span>
      </div>
    </form>
  );
}
