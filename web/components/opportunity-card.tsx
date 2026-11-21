import Link from "next/link";
import { formatAmount, formatDateRange } from "@/lib/format";
import { CATEGORY_STYLES, categoryLabel, methodLabel } from "@/lib/labels";
import type { OpportunitySummary } from "@/lib/types";
import { MypeBadge } from "./mype-badge";

export function OpportunityCard({ opportunity }: { opportunity: OpportunitySummary }) {
  const title = opportunity.title?.trim() || "Proceso sin título";
  const description = opportunity.description?.trim();
  const department = opportunity.department?.trim() || "No informado";

  return (
    <article
      data-testid="opportunity-card"
      className="group flex flex-col rounded-2xl border border-stone-200 bg-white p-5 shadow-sm transition hover:border-brand-300 hover:shadow-md focus-within:ring-2 focus-within:ring-brand-600 focus-within:ring-offset-2"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
            CATEGORY_STYLES[opportunity.category ?? ""] ??
            "border-stone-300 bg-stone-100 text-stone-700"
          }`}
        >
          {categoryLabel(opportunity.category)}
        </span>
        <MypeBadge fit={opportunity.mype_fit} />
      </div>

      <h3 className="mt-3 text-lg font-semibold leading-snug text-brand-950">
        <Link
          href={`/opportunities/${encodeURIComponent(opportunity.ocid)}`}
          className="rounded-sm hover:text-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
        >
          {title}
        </Link>
      </h3>

      <p className="mt-1 text-sm font-medium text-stone-600">
        {opportunity.buyer_name?.trim() || "Entidad no informada"}
      </p>

      <p
        className={`mt-2 text-sm leading-6 ${description ? "text-stone-600" : "text-stone-500 italic"}`}
      >
        {description
          ? description.length > 180
            ? `${description.slice(0, 177)}…`
            : description
          : "Descripción no informada en la fuente."}
      </p>

      <dl className="mt-4 grid grid-cols-1 gap-2 border-t border-stone-100 pt-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">
            Departamento
          </dt>
          <dd className="mt-0.5 font-medium text-stone-800">{department}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">Monto</dt>
          <dd className="mt-0.5 font-medium text-stone-800">
            {formatAmount(opportunity.amount_pen)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-stone-500">Fechas</dt>
          <dd className="mt-0.5 font-medium text-stone-800">
            {formatDateRange(opportunity.tender_start, opportunity.tender_end)}
          </dd>
        </div>
      </dl>

      <p className="mt-3 text-xs text-stone-500">
        {methodLabel(opportunity.method)} · OCID {opportunity.ocid}
      </p>
    </article>
  );
}
