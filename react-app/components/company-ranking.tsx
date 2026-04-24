"use client"

import { useMemo, useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  XAxis,
  YAxis,
} from "recharts"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { formatWeekLabel, mostRecentWeek } from "@/lib/aggregations"
import type { CompanyTrendPoint } from "@/lib/types"
import { cn } from "@/lib/utils"

export function CompanyRanking({
  points,
  topN = 10,
  enableDetail = false,
  className,
}: {
  points: CompanyTrendPoint[]
  topN?: number
  enableDetail?: boolean
  className?: string
}) {
  const latestWeek = useMemo(() => mostRecentWeek(points), [points])
  const latest = useMemo(() => {
    if (!latestWeek) return []
    return points
      .filter((p) => p.week === latestWeek)
      .sort((a, b) => b.count - a.count)
      .slice(0, topN)
  }, [points, latestWeek, topN])

  const [selected, setSelected] = useState<string | null>(null)
  const sparkline = useMemo(() => {
    if (!selected) return []
    return points
      .filter((p) => p.company === selected)
      .sort((a, b) => a.week.localeCompare(b.week))
      .map((p) => ({ week: p.week, count: p.count }))
  }, [points, selected])

  const barConfig: ChartConfig = {
    count: { label: "Postings", color: "var(--color-chart-1)" },
  }
  const sparkConfig: ChartConfig = {
    count: { label: "Postings", color: "var(--color-chart-1)" },
  }

  if (!latest.length) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-border bg-card text-sm text-muted-foreground">
        No company data available.
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col gap-6 rounded-lg border border-border bg-card p-4 sm:p-6", className)}>
      <ChartContainer
        config={barConfig}
        className="aspect-auto h-[360px] w-full"
        aria-label="Top hiring companies"
      >
        <BarChart
          data={latest}
          layout="vertical"
          margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
        >
          <CartesianGrid horizontal={false} strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            type="number"
            tickLine={false}
            axisLine={false}
            stroke="var(--color-muted-foreground)"
            fontSize={12}
          />
          <YAxis
            type="category"
            dataKey="company"
            tickLine={false}
            axisLine={false}
            width={120}
            stroke="var(--color-muted-foreground)"
            fontSize={12}
          />
          <ChartTooltip cursor={{ fill: "var(--color-muted)" }} content={<ChartTooltipContent />} />
          <Bar
            dataKey="count"
            fill="var(--color-chart-1)"
            radius={[0, 4, 4, 0]}
            onClick={
              enableDetail
                ? (d) => {
                    const name = (d as unknown as { company?: string }).company
                    if (name) setSelected((prev) => (prev === name ? null : name))
                  }
                : undefined
            }
            cursor={enableDetail ? "pointer" : undefined}
            isAnimationActive={false}
          />
        </BarChart>
      </ChartContainer>

      {enableDetail ? (
        <div className="flex flex-col gap-3 border-t border-border pt-4">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold">Weekly sparkline</h3>
            <div className="flex flex-wrap gap-1.5">
              {latest.map((c) => {
                const active = c.company === selected
                return (
                  <button
                    key={c.company}
                    type="button"
                    onClick={() => setSelected(active ? null : c.company)}
                    className={cn(
                      "rounded-full border px-2.5 py-0.5 text-xs transition-colors",
                      active
                        ? "border-foreground bg-foreground text-background"
                        : "border-border text-muted-foreground hover:text-foreground",
                    )}
                  >
                    {c.company}
                  </button>
                )
              })}
            </div>
          </div>

          {selected && sparkline.length ? (
            <ChartContainer
              config={sparkConfig}
              className="aspect-auto h-[160px] w-full"
              aria-label={`Posting sparkline for ${selected}`}
            >
              <LineChart data={sparkline} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border" />
                <XAxis
                  dataKey="week"
                  tickFormatter={formatWeekLabel}
                  tickLine={false}
                  axisLine={false}
                  stroke="var(--color-muted-foreground)"
                  fontSize={11}
                />
                <YAxis hide />
                <ChartTooltip
                  cursor={{ stroke: "var(--color-border)" }}
                  content={
                    <ChartTooltipContent
                      labelFormatter={(v) => `Week ${formatWeekLabel(String(v))}`}
                    />
                  }
                />
                <Line
                  dataKey="count"
                  type="monotone"
                  stroke="var(--color-chart-1)"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ChartContainer>
          ) : (
            <p className="text-xs text-muted-foreground">
              Select a company above to see its weekly posting volume.
            </p>
          )}
        </div>
      ) : null}
    </div>
  )
}
