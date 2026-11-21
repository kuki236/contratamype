import type { ReactNode } from "react";

export function Notice({
  tone = "warning",
  title,
  children,
}: {
  tone?: "warning" | "info";
  title?: string;
  children: ReactNode;
}) {
  const styles =
    tone === "warning"
      ? "border-amber-300 bg-amber-50 text-amber-950"
      : "border-sky-200 bg-sky-50 text-sky-950";
  return (
    <div role="note" className={`rounded-xl border px-4 py-3 text-sm leading-6 ${styles}`}>
      {title ? <p className="font-semibold">{title}</p> : null}
      <div className={title ? "mt-1" : ""}>{children}</div>
    </div>
  );
}
