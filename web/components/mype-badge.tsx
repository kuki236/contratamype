import { MYPE_DISCLAIMER } from "@/lib/explainer";

type Fit = boolean | null | undefined;

const CONFIG = {
  yes: {
    label: "Compatible MYPE",
    className: "border-teal-300 bg-teal-50 text-teal-900",
    dot: "bg-teal-600",
  },
  no: {
    label: "No marcada compatible",
    className: "border-slate-300 bg-slate-100 text-slate-700",
    dot: "bg-slate-400",
  },
  unknown: {
    label: "Sin clasificar",
    className: "border-amber-300 bg-amber-50 text-amber-900",
    dot: "bg-amber-500",
  },
};

export function MypeBadge({ fit }: { fit: Fit }) {
  const key = fit === true ? "yes" : fit === false ? "no" : "unknown";
  const config = CONFIG[key];
  return (
    <span
      data-testid="mype-badge"
      title={MYPE_DISCLAIMER}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${config.className}`}
    >
      <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}
