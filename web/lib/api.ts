import type { Checklist, Meta, OpportunityDetail, OpportunityPage, Stats } from "./types";
import type { OpportunityQuery } from "./filters";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function apiBaseUrl(): string {
  return (process.env.CONTRATAMYPE_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    let message = `La API respondió ${response.status}.`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the status-based message when the body is not JSON.
    }
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as T;
}

function buildQueryString(query: OpportunityQuery): string {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.department) params.set("department", query.department);
  if (query.category) params.set("category", query.category);
  if (query.method) params.set("method", query.method);
  if (query.min_amount !== undefined) params.set("min_amount", String(query.min_amount));
  if (query.max_amount !== undefined) params.set("max_amount", String(query.max_amount));
  if (query.status) params.set("status", query.status);
  params.set("year", String(query.year));
  params.set("mype_only", String(query.mype_only));
  params.set("page", String(query.page));
  params.set("page_size", String(query.page_size));
  return params.toString();
}

export function searchOpportunities(query: OpportunityQuery): Promise<OpportunityPage> {
  return getJson<OpportunityPage>(`/opportunities?${buildQueryString(query)}`);
}

export function getMeta(year: number): Promise<Meta> {
  return getJson<Meta>(`/meta?year=${year}`);
}

export function getStats(year: number): Promise<Stats> {
  return getJson<Stats>(`/stats?year=${year}`);
}

export function getOpportunity(ocid: string): Promise<OpportunityDetail> {
  return getJson<OpportunityDetail>(`/opportunities/${encodeURIComponent(ocid)}`);
}

export function getChecklist(ocid: string): Promise<Checklist> {
  return getJson<Checklist>(`/checklist/${encodeURIComponent(ocid)}`);
}

export function getChecklistResponse(ocid: string): Promise<Response> {
  return fetch(`${apiBaseUrl()}/checklist/${encodeURIComponent(ocid)}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
}
