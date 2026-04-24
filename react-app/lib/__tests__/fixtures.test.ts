import { describe, expect, it } from "vitest"

import {
  buildAllJobs,
  buildCompanyTrends,
  buildSkillTrends,
  FIXTURE_CATEGORIES,
} from "../fixtures"

describe("buildSkillTrends", () => {
  it("produces one entry per (skill, week) pair", () => {
    const weeks = 3
    const rows = buildSkillTrends(weeks)
    const uniqueSkills = new Set(rows.map((r) => r.skill))
    const uniqueWeeks = new Set(rows.map((r) => r.week))
    expect(uniqueWeeks.size).toBe(weeks)
    expect(rows.length).toBe(uniqueSkills.size * weeks)
    expect(rows.every((r) => r.count > 0)).toBe(true)
  })

  it("filters by category when provided", () => {
    const rows = buildSkillTrends(2, "Data Science")
    expect(rows.length).toBeGreaterThan(0)
    // Every skill in the rollup should belong to Data Science in the seed.
    const dataScienceSkills = new Set(["pytorch", "tensorflow"])
    for (const row of rows) {
      expect(dataScienceSkills.has(row.skill)).toBe(true)
    }
  })
})

describe("buildCompanyTrends", () => {
  it("produces entries for each company across the requested weeks", () => {
    const rows = buildCompanyTrends(4)
    const uniqueWeeks = new Set(rows.map((r) => r.week))
    expect(uniqueWeeks.size).toBe(4)
    expect(rows.every((r) => r.count > 0)).toBe(true)
  })
})

describe("buildAllJobs", () => {
  it("returns a deterministic batch of postings", () => {
    const first = buildAllJobs()
    const second = buildAllJobs()
    expect(first).toHaveLength(240)
    expect(first[0].title).toBe(second[0].title)
  })

  it("assigns a category from the canonical list to every job", () => {
    const allowed = new Set(FIXTURE_CATEGORIES)
    for (const job of buildAllJobs()) {
      expect(allowed.has(job.category)).toBe(true)
    }
  })
})
