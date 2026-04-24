import {
  FIXTURE_CATEGORIES,
  buildAllJobs,
  buildCompanyTrends,
  buildSkillTrends,
} from "./fixtures"
import type {
  ApiResult,
  Category,
  CompanyTrendPoint,
  JobsQuery,
  JobsResponse,
  SkillTrendPoint,
  TrendsQuery,
} from "./types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? ""

export function isRefreshEnabled(): boolean {
  return process.env.NEXT_PUBLIC_ENABLE_REFRESH === "true"
}

export function hasBackend(): boolean {
  return Boolean(API_URL)
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    next: { revalidate: 60 },
    headers: { Accept: "application/json" },
  })
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with ${res.status}`)
  }
  return (await res.json()) as T
}

async function withFallback<T>(path: string, fixture: () => T): Promise<ApiResult<T>> {
  if (!API_URL) {
    return { data: fixture(), fromFixtures: true }
  }
  try {
    const data = await fetchJson<T>(path)
    return { data, fromFixtures: false }
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error"
    return { data: fixture(), fromFixtures: true, error: message }
  }
}

function toQuery(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue
    sp.set(k, String(v))
  }
  const q = sp.toString()
  return q ? `?${q}` : ""
}

export async function getCategories(): Promise<ApiResult<Category[]>> {
  return withFallback<Category[]>("/api/categories", () => FIXTURE_CATEGORIES)
}

export async function getSkillTrends(q: TrendsQuery = {}): Promise<ApiResult<SkillTrendPoint[]>> {
  const weeks = clampWeeks(q.weeks ?? 4)
  const path = `/api/trends/skills${toQuery({ weeks, category: q.category })}`
  return withFallback<SkillTrendPoint[]>(path, () => buildSkillTrends(weeks, q.category))
}

export async function getCompanyTrends(
  q: TrendsQuery = {},
): Promise<ApiResult<CompanyTrendPoint[]>> {
  const weeks = clampWeeks(q.weeks ?? 4)
  const path = `/api/trends/companies${toQuery({ weeks, category: q.category })}`
  return withFallback<CompanyTrendPoint[]>(path, () => buildCompanyTrends(weeks, q.category))
}

export async function getJobs(q: JobsQuery = {}): Promise<ApiResult<JobsResponse>> {
  const limit = q.limit ?? 25
  const offset = q.offset ?? 0
  const path = `/api/jobs${toQuery({
    category: q.category,
    level: q.level,
    location: q.location,
    limit,
    offset,
  })}`
  return withFallback<JobsResponse>(path, () => filterFixtureJobs({ ...q, limit, offset }))
}

function clampWeeks(w: number): number {
  if (!Number.isFinite(w) || w < 1) return 1
  if (w > 12) return 12
  return Math.floor(w)
}

function filterFixtureJobs(q: JobsQuery): JobsResponse {
  let items = buildAllJobs()
  if (q.category) items = items.filter((j) => j.category === q.category)
  if (q.level) items = items.filter((j) => j.level === q.level)
  if (q.location) {
    const needle = q.location.toLowerCase()
    items = items.filter((j) => j.location.toLowerCase().includes(needle))
  }
  const total = items.length
  const start = q.offset ?? 0
  const end = start + (q.limit ?? 25)
  return { total, items: items.slice(start, end) }
}
