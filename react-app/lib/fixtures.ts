// Local fixtures used when the backend is unreachable or NEXT_PUBLIC_API_URL is unset.
// Shapes match the API contract documented in section 5 of the UI specification.

import type { Category, CompanyTrendPoint, JobPosting, SkillTrendPoint } from "./types"

export const FIXTURE_CATEGORIES: Category[] = [
  "Software Engineer",
  "Data and Analytics",
  "Data Science",
  "DevOps and Sysadmin",
  "Product",
  "Design and UX",
]

// Returns an ISO-week string (e.g. "2026-W16") for `weeksAgo` weeks before now.
function weekKey(weeksAgo: number): string {
  const now = new Date()
  const target = new Date(now.getTime() - weeksAgo * 7 * 24 * 60 * 60 * 1000)
  // ISO week calculation
  const tmp = new Date(Date.UTC(target.getUTCFullYear(), target.getUTCMonth(), target.getUTCDate()))
  const dayNum = tmp.getUTCDay() || 7
  tmp.setUTCDate(tmp.getUTCDate() + 4 - dayNum)
  const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1))
  const weekNum = Math.ceil(((tmp.getTime() - yearStart.getTime()) / 86400000 + 1) / 7)
  return `${tmp.getUTCFullYear()}-W${String(weekNum).padStart(2, "0")}`
}

const SKILL_SEED: Record<string, { base: number; drift: number; category: string }> = {
  python: { base: 148, drift: 6, category: "Software Engineer" },
  typescript: { base: 132, drift: 4, category: "Software Engineer" },
  kubernetes: { base: 96, drift: 8, category: "DevOps and Sysadmin" },
  react: { base: 118, drift: 3, category: "Software Engineer" },
  aws: { base: 104, drift: 5, category: "DevOps and Sysadmin" },
  sql: { base: 142, drift: 2, category: "Data and Analytics" },
  pytorch: { base: 62, drift: 7, category: "Data Science" },
  tensorflow: { base: 48, drift: -2, category: "Data Science" },
  go: { base: 54, drift: 6, category: "Software Engineer" },
  rust: { base: 34, drift: 9, category: "Software Engineer" },
  snowflake: { base: 58, drift: 4, category: "Data and Analytics" },
  airflow: { base: 44, drift: 3, category: "Data and Analytics" },
}

const COMPANY_SEED: Record<string, { base: number; drift: number; category: string }> = {
  Stripe: { base: 36, drift: 2, category: "Software Engineer" },
  Datadog: { base: 24, drift: 3, category: "DevOps and Sysadmin" },
  Vercel: { base: 18, drift: 1, category: "Software Engineer" },
  Snowflake: { base: 22, drift: 2, category: "Data and Analytics" },
  Databricks: { base: 28, drift: 3, category: "Data Science" },
  Airbnb: { base: 20, drift: 1, category: "Software Engineer" },
  Shopify: { base: 16, drift: 2, category: "Software Engineer" },
  Cloudflare: { base: 19, drift: 2, category: "DevOps and Sysadmin" },
  Notion: { base: 12, drift: 1, category: "Product" },
  Figma: { base: 14, drift: 2, category: "Design and UX" },
  Plaid: { base: 11, drift: 1, category: "Software Engineer" },
  Linear: { base: 9, drift: 1, category: "Product" },
}

export function buildSkillTrends(weeks: number, category?: string): SkillTrendPoint[] {
  const rows: SkillTrendPoint[] = []
  const entries = Object.entries(SKILL_SEED).filter(
    ([, meta]) => !category || meta.category === category,
  )
  // Always produce at least something if the category filter zeros results.
  const source = entries.length ? entries : Object.entries(SKILL_SEED)

  for (let w = weeks - 1; w >= 0; w--) {
    const week = weekKey(w)
    for (const [skill, meta] of source) {
      // Deterministic, slightly noisy trend.
      const noise = Math.round(Math.sin((w + skill.length) * 1.3) * 5)
      const count = Math.max(1, meta.base + meta.drift * (weeks - 1 - w) + noise)
      rows.push({ skill, count, week })
    }
  }
  return rows
}

export function buildCompanyTrends(weeks: number, category?: string): CompanyTrendPoint[] {
  const rows: CompanyTrendPoint[] = []
  const entries = Object.entries(COMPANY_SEED).filter(
    ([, meta]) => !category || meta.category === category,
  )
  const source = entries.length ? entries : Object.entries(COMPANY_SEED)

  for (let w = weeks - 1; w >= 0; w--) {
    const week = weekKey(w)
    for (const [company, meta] of source) {
      const noise = Math.round(Math.cos((w + company.length) * 1.1) * 3)
      const count = Math.max(1, meta.base + meta.drift * (weeks - 1 - w) + noise)
      rows.push({ company, count, week })
    }
  }
  return rows
}

const LEVELS = ["Entry", "Mid", "Senior", "Staff", "Principal"]
const LOCATIONS = [
  "Remote",
  "San Francisco, CA",
  "New York, NY",
  "Austin, TX",
  "London, UK",
  "Berlin, DE",
  "Toronto, CA",
  "Seattle, WA",
]
const TITLE_PREFIX: Record<string, string[]> = {
  "Software Engineer": ["Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Engineer"],
  "Data and Analytics": ["Data Engineer", "Analytics Engineer", "Business Intelligence Analyst"],
  "Data Science": ["Data Scientist", "Machine Learning Engineer", "Applied Scientist"],
  "DevOps and Sysadmin": ["DevOps Engineer", "Site Reliability Engineer", "Platform Engineer"],
  Product: ["Product Manager", "Technical Product Manager", "Associate Product Manager"],
  "Design and UX": ["Product Designer", "UX Researcher", "Design Engineer"],
}

// Generate a deterministic set of 240 job postings.
export function buildAllJobs(): JobPosting[] {
  const jobs: JobPosting[] = []
  const companies = Object.keys(COMPANY_SEED)
  const categories = FIXTURE_CATEGORIES
  let id = 1
  for (let i = 0; i < 240; i++) {
    const category = categories[i % categories.length]
    const titles = TITLE_PREFIX[category] ?? ["Engineer"]
    const title = titles[i % titles.length]
    const company = companies[(i * 3) % companies.length]
    const level = LEVELS[(i * 5) % LEVELS.length]
    const location = LOCATIONS[(i * 7) % LOCATIONS.length]
    const daysAgo = i % 28
    const date = new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000)
    const levelTitle = level === "Entry" || level === "Mid" ? title : `${level} ${title}`
    jobs.push({
      id: id++,
      title: levelTitle,
      company,
      category,
      level,
      location,
      date_collected: date.toISOString(),
    })
  }
  return jobs
}
