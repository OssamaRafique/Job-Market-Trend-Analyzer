// Helpers that turn the flat API responses into chart-ready shapes.

import type { CompanyTrendPoint, SkillTrendPoint } from "./types"

export function uniqueWeeks(points: { week: string }[]): string[] {
  return Array.from(new Set(points.map((p) => p.week))).sort()
}

export function mostRecentWeek(points: { week: string }[]): string | undefined {
  return uniqueWeeks(points).at(-1)
}

// Returns the top-N skills aggregated over the most recent week.
export function topSkillsLatest(points: SkillTrendPoint[], n: number): string[] {
  const latest = mostRecentWeek(points)
  if (!latest) return []
  const latestRows = points.filter((p) => p.week === latest)
  return latestRows
    .sort((a, b) => b.count - a.count)
    .slice(0, n)
    .map((p) => p.skill)
}

export function topCompaniesLatest(points: CompanyTrendPoint[], n: number): CompanyTrendPoint[] {
  const latest = mostRecentWeek(points)
  if (!latest) return []
  return points
    .filter((p) => p.week === latest)
    .sort((a, b) => b.count - a.count)
    .slice(0, n)
}

// Pivots skills into { week, [skill]: count }
export function pivotSkills(
  points: SkillTrendPoint[],
  skills: string[],
): Array<Record<string, number | string>> {
  const weeks = uniqueWeeks(points)
  return weeks.map((week) => {
    const row: Record<string, number | string> = { week }
    for (const skill of skills) {
      const match = points.find((p) => p.week === week && p.skill === skill)
      row[skill] = match?.count ?? 0
    }
    return row
  })
}

export function pivotCompanies(
  points: CompanyTrendPoint[],
  companies: string[],
): Array<Record<string, number | string>> {
  const weeks = uniqueWeeks(points)
  return weeks.map((week) => {
    const row: Record<string, number | string> = { week }
    for (const company of companies) {
      const match = points.find((p) => p.week === week && p.company === company)
      row[company] = match?.count ?? 0
    }
    return row
  })
}

// Formats "2026-W16" into a more human "W16" label.
export function formatWeekLabel(week: string): string {
  const parts = week.split("-")
  return parts.length === 2 ? parts[1] : week
}
