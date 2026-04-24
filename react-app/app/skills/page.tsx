import { TrendingUp } from "lucide-react"
import {
  CategoryFilter,
  ClearFiltersButton,
  TopNSelector,
  WeeksSelector,
} from "@/components/filters"
import { EmptyState } from "@/components/empty-state"
import { FixturesBanner } from "@/components/fixtures-banner"
import { PageHeader } from "@/components/page-header"
import { SkillTrendsChart } from "@/components/skill-trends-chart"
import { getCategories, getSkillTrends } from "@/lib/api"

export const dynamic = "force-dynamic"

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>

function parseNumber(value: string | string[] | undefined, fallback: number, allowed: number[]) {
  if (typeof value !== "string") return fallback
  const n = Number.parseInt(value, 10)
  return allowed.includes(n) ? n : fallback
}

export default async function SkillsPage({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams
  const category = typeof sp.category === "string" ? sp.category : undefined
  const weeks = parseNumber(sp.weeks, 4, [1, 4, 12])
  const topN = parseNumber(sp.top, 10, [5, 10, 20])

  const [categoriesRes, skillsRes] = await Promise.all([
    getCategories(),
    getSkillTrends({ weeks, category }),
  ])

  const usingFixtures = categoriesRes.fromFixtures || skillsRes.fromFixtures
  const firstError = categoriesRes.error ?? skillsRes.error

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        title="Skill trends"
        description="Track which skills are gaining or losing momentum in job postings over time."
      />

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-border bg-card p-4">
        <WeeksSelector value={weeks} />
        <TopNSelector value={topN} />
        <CategoryFilter categories={categoriesRes.data} value={category} />
        <ClearFiltersButton keys={["category", "weeks", "top"]} className="mb-0.5" />
      </div>

      {usingFixtures ? <FixturesBanner error={firstError} /> : null}

      {skillsRes.data.length ? (
        <SkillTrendsChart points={skillsRes.data} topN={topN} />
      ) : (
        <EmptyState
          title="No skill trends available"
          description="Try widening the time window or clearing the category filter."
          icon={TrendingUp}
        />
      )}

      <p className="text-xs text-muted-foreground">
        Tip: click a legend entry to toggle a skill on or off.
      </p>
    </div>
  )
}
