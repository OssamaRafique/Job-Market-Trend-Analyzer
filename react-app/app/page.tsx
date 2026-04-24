import { Suspense } from "react"
import { Briefcase, Building2, TrendingUp } from "lucide-react"
import { CategoryFilter, ClearFiltersButton } from "@/components/filters"
import { CompanyRanking } from "@/components/company-ranking"
import { EmptyState } from "@/components/empty-state"
import { FixturesBanner } from "@/components/fixtures-banner"
import { PageHeader, SectionHeader } from "@/components/page-header"
import { SkillTrendsChart } from "@/components/skill-trends-chart"
import { SummaryTile } from "@/components/summary-tile"
import { getCategories, getCompanyTrends, getJobs, getSkillTrends } from "@/lib/api"
import { mostRecentWeek, topCompaniesLatest, topSkillsLatest } from "@/lib/aggregations"

export const dynamic = "force-dynamic"

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>

export default async function OverviewPage({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams
  const category = typeof sp.category === "string" ? sp.category : undefined

  const [categoriesRes, skillsRes, companiesThisWeek, companiesTrendRes, jobsRes] =
    await Promise.all([
      getCategories(),
      getSkillTrends({ weeks: 4, category }),
      getCompanyTrends({ weeks: 1, category }),
      getCompanyTrends({ weeks: 4, category }),
      getJobs({ category, limit: 1, offset: 0 }),
    ])

  const usingFixtures =
    categoriesRes.fromFixtures ||
    skillsRes.fromFixtures ||
    companiesThisWeek.fromFixtures ||
    companiesTrendRes.fromFixtures ||
    jobsRes.fromFixtures
  const firstError =
    categoriesRes.error ??
    skillsRes.error ??
    companiesThisWeek.error ??
    companiesTrendRes.error ??
    jobsRes.error

  const totalJobs = jobsRes.data.total
  const topSkill = topSkillsLatest(skillsRes.data, 1)[0]
  const topCompany = topCompaniesLatest(companiesThisWeek.data, 1)[0]
  const latestWeek = mostRecentWeek(skillsRes.data) ?? "—"

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        title="Overview"
        description="What's hot in the job market this week — aggregated across postings collected daily from The Muse."
      >
        <CategoryFilter categories={categoriesRes.data} value={category} />
        <ClearFiltersButton keys={["category"]} />
      </PageHeader>

      {usingFixtures ? <FixturesBanner error={firstError} /> : null}

      <section aria-labelledby="summary-heading" className="flex flex-col gap-4">
        <h2 id="summary-heading" className="sr-only">
          Summary
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <SummaryTile
            label="Jobs in view"
            value={totalJobs.toLocaleString()}
            hint={category ? `Filtered to ${category}` : "Across all categories"}
            icon={Briefcase}
          />
          <SummaryTile
            label="Top skill this week"
            value={topSkill ?? "—"}
            hint={topSkill ? `Week ${latestWeek}` : "No data available"}
            icon={TrendingUp}
            tone="accent"
          />
          <SummaryTile
            label="Top company this week"
            value={topCompany?.company ?? "—"}
            hint={
              topCompany
                ? `${topCompany.count.toLocaleString()} postings this week`
                : "No data available"
            }
            icon={Building2}
          />
        </div>
      </section>

      <section aria-labelledby="skills-heading" className="flex flex-col gap-3">
        <SectionHeader
          title="Skill trends"
          description="Top 5 skills over the last 4 weeks."
        />
        <Suspense fallback={null}>
          {skillsRes.data.length ? (
            <SkillTrendsChart points={skillsRes.data} topN={5} />
          ) : (
            <EmptyState
              title="No skill trends yet"
              description="The backend has not returned any skill data for this filter."
              icon={TrendingUp}
            />
          )}
        </Suspense>
      </section>

      <section aria-labelledby="companies-heading" className="flex flex-col gap-3">
        <SectionHeader
          title="Top hiring companies"
          description="Most postings this week, filtered by category."
        />
        {companiesThisWeek.data.length ? (
          <CompanyRanking points={companiesThisWeek.data} topN={10} />
        ) : (
          <EmptyState
            title="No company data yet"
            description="Try clearing the category filter."
            icon={Building2}
          />
        )}
      </section>
    </div>
  )
}
