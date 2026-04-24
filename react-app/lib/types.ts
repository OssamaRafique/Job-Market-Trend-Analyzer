// Shared types that mirror the backend API contract (section 5 of the spec).

export type Category = string

export interface SkillTrendPoint {
  skill: string
  count: number
  week: string // e.g. "2026-W16"
}

export interface CompanyTrendPoint {
  company: string
  count: number
  week: string
}

export interface JobPosting {
  id: number
  title: string
  company: string
  category: string
  level: string
  location: string
  date_collected: string // ISO 8601
}

export interface JobsResponse {
  total: number
  items: JobPosting[]
}

export interface JobsQuery {
  category?: string
  level?: string
  location?: string
  limit?: number
  offset?: number
}

export interface TrendsQuery {
  weeks?: number
  category?: string
}

export interface ApiError {
  error: string
  details?: string
}

export interface ApiResult<T> {
  data: T
  // when true, data came from local fixtures because the backend was unreachable
  fromFixtures: boolean
  // populated when the network call failed
  error?: string
}
