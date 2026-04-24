import { Building2 } from "lucide-react"
import {
  CategoryFilter,
  ClearFiltersButton,
  WeeksSelector,
} from "@/components/filters"
import { CompanyRanking } from "@/components/company-ranking"
import { EmptyState } from "@/components/empty-state"
import { FixturesBanner } from "@/components/fixtures-banner"
import { PageHeader } from "@/components/page-header"
import { getCategories, getCompanyTrends } from "@/lib/api"

export const dynamic = "force-dynamic"

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>

function parseNumber(value: string | string[] | undefined, fallback: number, allowed: number[]) {
  if (typeof value !== "string") return fallback
  const n = Number.parseInt(value, 10)
  return allowed.includes(n) ? n : fallback
}

export default async function CompaniesPage({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams
  const category = typeof sp.category === "string" ? sp.category : undefined
  const weeks = parseNumber(sp.weeks, 4, [1, 4, 12])

  const [categoriesRes, companiesRes] = await Promise.all([
    getCategories(),
    getCompanyTrends({ weeks, category }),
  ])

  const usingFixtures = categoriesRes.fromFixtures || companiesRes.fromFixtures
  const firstError = categoriesRes.error ?? companiesRes.error

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        title="Companies"
        description="Who is hiring the most right now, and how their posting volume has moved week over week."
      />

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-border bg-card p-4">
        <WeeksSelector value={weeks} />
        <CategoryFilter categories={categoriesRes.data} value={category} />
        <ClearFiltersButton keys={["category", "weeks"]} className="mb-0.5" />
      </div>

      {usingFixtures ? <FixturesBanner error={firstError} /> : null}

      {companiesRes.data.length ? (
        <CompanyRanking points={companiesRes.data} topN={10} enableDetail />
      ) : (
        <EmptyState
          title="No company data available"
          description="Try widening the time window or clearing the category filter."
          icon={Building2}
        />
      )}
    </div>
  )
}
