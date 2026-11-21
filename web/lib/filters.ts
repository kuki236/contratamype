import type { OpportunityPage } from "./types";

export const COHORT_YEAR = 2025;
export const PAGE_SIZE = 20;

export interface SearchFilters {
  q: string;
  department: string;
  category: string;
  method: string;
  min_amount: string;
  max_amount: string;
  status: string;
  mype_only: boolean;
  page: number;
}

type RawSearchParams = Record<string, string | string[] | undefined>;

function first(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

function optionalNumber(value: string): number | undefined {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}

export function parseFilters(raw: RawSearchParams): SearchFilters {
  const pageValue = Number.parseInt(first(raw.page), 10);
  return {
    q: first(raw.q).trim(),
    department: first(raw.department),
    category: first(raw.category),
    method: first(raw.method),
    min_amount: first(raw.min_amount),
    max_amount: first(raw.max_amount),
    status: first(raw.status),
    mype_only: first(raw.mype_only) !== "0",
    page: Number.isFinite(pageValue) && pageValue > 0 ? pageValue : 1,
  };
}

export interface OpportunityQuery {
  q?: string;
  department?: string;
  category?: string;
  method?: string;
  min_amount?: number;
  max_amount?: number;
  status?: string;
  year: number;
  mype_only: boolean;
  page: number;
  page_size: number;
}

export function toOpportunityQuery(filters: SearchFilters): OpportunityQuery {
  return {
    q: filters.q || undefined,
    department: filters.department || undefined,
    category: filters.category || undefined,
    method: filters.method || undefined,
    min_amount: optionalNumber(filters.min_amount),
    max_amount: optionalNumber(filters.max_amount),
    status: filters.status || undefined,
    year: COHORT_YEAR,
    mype_only: filters.mype_only,
    page: filters.page,
    page_size: PAGE_SIZE,
  };
}

export function toSearchParams(
  filters: SearchFilters,
  overrides: Partial<SearchFilters> = {},
): URLSearchParams {
  const merged = { ...filters, ...overrides };
  const params = new URLSearchParams();
  if (merged.q) params.set("q", merged.q);
  if (merged.department) params.set("department", merged.department);
  if (merged.category) params.set("category", merged.category);
  if (merged.method) params.set("method", merged.method);
  if (merged.min_amount) params.set("min_amount", merged.min_amount);
  if (merged.max_amount) params.set("max_amount", merged.max_amount);
  if (merged.status) params.set("status", merged.status);
  params.set("mype_only", merged.mype_only ? "1" : "0");
  if (merged.page > 1) params.set("page", String(merged.page));
  return params;
}

export function hasActiveFilters(filters: SearchFilters): boolean {
  return Boolean(
    filters.q ||
    filters.department ||
    filters.category ||
    filters.method ||
    filters.min_amount ||
    filters.max_amount ||
    filters.status ||
    !filters.mype_only,
  );
}

export function pageLabel(results: OpportunityPage): string {
  if (results.total === 0) return "0 resultados";
  const start = (results.page - 1) * results.page_size + 1;
  const end = Math.min(results.page * results.page_size, results.total);
  return `${start}–${end} de ${results.total}`;
}
