import { Briefcase } from "lucide-react"
import {
  CategoryFilter,
  ClearFiltersButton,
  LevelFilter,
  LocationSearch,
} from "@/components/filters"
import { EmptyState } from "@/components/empty-state"
import { FixturesBanner } from "@/components/fixtures-banner"
import { JobsTable } from "@/components/jobs-table"
import { PageHeader } from "@/components/page-header"
import { PaginationControls } from "@/components/pagination-controls"
import { getCategories, getJobs } from "@/lib/api"

export const dynamic = "force-dynamic"

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>

function asString(v: string | string[] | undefined): string | undefined {
  return typeof v === "string" && v.length ? v : undefined
}

function parseOffset(v: string | string[] | undefined): number {
  if (typeof v !== "string") return 0
  const n = Number.parseInt(v, 10)
  return Number.isFinite(n) && n > 0 ? n : 0
}

export default async function JobsPage({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams
  const category = asString(sp.category)
  const level = asString(sp.level)
  const location = asString(sp.location)
  const offset = parseOffset(sp.offset)
  const limit = 25

  const [categoriesRes, jobsRes] = await Promise.all([
    getCategories(),
    getJobs({ category, level, location, offset, limit }),
  ])

  const usingFixtures = categoriesRes.fromFixtures || jobsRes.fromFixtures
  const firstError = categoriesRes.error ?? jobsRes.error

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        title="Jobs browser"
        description="Search the raw job postings collected from The Muse. Filters update the URL so results stay shareable."
      />

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-border bg-card p-4">
        <CategoryFilter categories={categoriesRes.data} value={category} />
        <LevelFilter value={level} />
        <LocationSearch value={location} />
        <ClearFiltersButton keys={["category", "level", "location", "offset"]} className="mb-0.5" />
      </div>

      {usingFixtures ? <FixturesBanner error={firstError} /> : null}

      {jobsRes.data.items.length ? (
        <div className="flex flex-col gap-4">
          <JobsTable items={jobsRes.data.items} />
          <PaginationControls
            total={jobsRes.data.total}
            limit={limit}
            offset={offset}
          />
        </div>
      ) : (
        <EmptyState
          title="No jobs match these filters"
          description="Try clearing the filters or broadening the location search."
          icon={Briefcase}
        />
      )}
    </div>
  )
}
