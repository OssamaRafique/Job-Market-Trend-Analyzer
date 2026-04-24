import { describe, expect, it } from "vitest"

import {
  formatWeekLabel,
  mostRecentWeek,
  pivotCompanies,
  pivotSkills,
  topCompaniesLatest,
  topSkillsLatest,
  uniqueWeeks,
} from "../aggregations"
import type { CompanyTrendPoint, SkillTrendPoint } from "../types"

const skills: SkillTrendPoint[] = [
  { skill: "python", count: 100, week: "2026-W15" },
  { skill: "react", count: 70, week: "2026-W15" },
  { skill: "python", count: 120, week: "2026-W16" },
  { skill: "react", count: 80, week: "2026-W16" },
  { skill: "kubernetes", count: 40, week: "2026-W16" },
]

const companies: CompanyTrendPoint[] = [
  { company: "Acme", count: 9, week: "2026-W15" },
  { company: "Nebula", count: 4, week: "2026-W15" },
  { company: "Acme", count: 12, week: "2026-W16" },
  { company: "Nebula", count: 6, week: "2026-W16" },
]

describe("uniqueWeeks", () => {
  it("returns sorted distinct weeks", () => {
    expect(uniqueWeeks(skills)).toEqual(["2026-W15", "2026-W16"])
  })
})

describe("mostRecentWeek", () => {
  it("returns the largest week lexicographically", () => {
    expect(mostRecentWeek(skills)).toBe("2026-W16")
  })
  it("returns undefined for empty input", () => {
    expect(mostRecentWeek([])).toBeUndefined()
  })
})

describe("topSkillsLatest", () => {
  it("returns the top-N skills from the most recent week", () => {
    expect(topSkillsLatest(skills, 2)).toEqual(["python", "react"])
  })
})

describe("topCompaniesLatest", () => {
  it("returns companies sorted by count desc, scoped to latest week", () => {
    const result = topCompaniesLatest(companies, 3)
    expect(result).toHaveLength(2)
    expect(result[0].company).toBe("Acme")
    expect(result[0].count).toBe(12)
  })
})

describe("pivotSkills", () => {
  it("produces one row per week with a column per requested skill", () => {
    const rows = pivotSkills(skills, ["python", "react"])
    expect(rows).toHaveLength(2)
    expect(rows[0]).toEqual({ week: "2026-W15", python: 100, react: 70 })
    expect(rows[1]).toEqual({ week: "2026-W16", python: 120, react: 80 })
  })

  it("defaults missing skill/week combinations to 0", () => {
    const rows = pivotSkills(skills, ["kubernetes"])
    expect(rows[0]).toEqual({ week: "2026-W15", kubernetes: 0 })
    expect(rows[1]).toEqual({ week: "2026-W16", kubernetes: 40 })
  })
})

describe("pivotCompanies", () => {
  it("produces one row per week with a column per requested company", () => {
    const rows = pivotCompanies(companies, ["Acme"])
    expect(rows).toEqual([
      { week: "2026-W15", Acme: 9 },
      { week: "2026-W16", Acme: 12 },
    ])
  })
})

describe("formatWeekLabel", () => {
  it("returns the week number portion", () => {
    expect(formatWeekLabel("2026-W16")).toBe("W16")
  })
  it("is resilient to malformed input", () => {
    expect(formatWeekLabel("garbage")).toBe("garbage")
  })
})
