export const CATEGORY_LABELS: Record<string, string> = {
  goods: "Bienes",
  services: "Servicios",
  works: "Obras",
};

export const CATEGORY_STYLES: Record<string, string> = {
  goods: "border-sky-200 bg-sky-50 text-sky-900",
  services: "border-violet-200 bg-violet-50 text-violet-900",
  works: "border-orange-200 bg-orange-50 text-orange-900",
};

export function categoryLabel(value: string | null | undefined): string {
  if (!value) return "Categoría no informada";
  return CATEGORY_LABELS[value] ?? value;
}

const STATUS_LABELS: Record<string, string> = {
  active: "Vigente",
  cancelled: "Cancelado",
  terminated: "Terminado",
  complete: "Terminado",
  completed: "Terminado",
  pending: "Pendiente",
};

export function statusLabel(value: string | null | undefined): string {
  const raw = value?.trim();
  if (!raw) return "No informado";
  return STATUS_LABELS[raw.toLowerCase()] ?? `${raw} (fuente)`;
}

export function methodLabel(value: string | null | undefined): string {
  return value && value.trim() ? value : "No informado";
}
