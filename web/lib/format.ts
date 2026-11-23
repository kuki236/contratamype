const moneyFormatter = new Intl.NumberFormat("es-PE", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const compactMoneyFormatter = new Intl.NumberFormat("es-PE", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const longDateFormatter = new Intl.DateTimeFormat("es-PE", {
  day: "2-digit",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

const shortDateFormatter = new Intl.DateTimeFormat("es-PE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

function parseDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatPEN(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Monto no informado";
  return `S/ ${moneyFormatter.format(value)}`;
}

export function formatPENCompact(value: number | null | undefined): string {
  if (value === null || value === undefined) return "No informado";
  return `S/ ${compactMoneyFormatter.format(value)}`;
}

export function formatAmountUseful(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Monto no informado";
  if (value === 0) return "S/ 0.00 (no informado útil)";
  return formatPEN(value);
}

export function formatDate(value: string | null | undefined): string {
  const date = parseDate(value);
  return date ? longDateFormatter.format(date) : "No informada";
}

export function formatDateShort(value: string | null | undefined): string {
  const date = parseDate(value);
  return date ? shortDateFormatter.format(date) : "No informada";
}

export function formatDateRange(
  start: string | null | undefined,
  end: string | null | undefined,
): string {
  if (!start && !end) return "Fechas no informadas";
  if (start && end && start === end) return `${formatDateShort(start)} (fecha única)`;
  if (!start) return `Cierre: ${formatDateShort(end)}`;
  if (!end) return `Inicio: ${formatDateShort(start)}`;
  return `${formatDateShort(start)} – ${formatDateShort(end)}`;
}

export function cohortLabel(years: number[]): string {
  const sorted = Array.from(new Set(years)).sort((a, b) => a - b);
  if (sorted.length === 0) return "sin cohortes";
  if (sorted.length === 1) return String(sorted[0]);
  const contiguous = sorted.every((year, index) => index === 0 || year === sorted[index - 1] + 1);
  return contiguous ? `${sorted[0]}–${sorted[sorted.length - 1]}` : sorted.join(", ");
}
