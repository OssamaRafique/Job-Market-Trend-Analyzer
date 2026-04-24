"use client"

import { useMemo, useState } from "react"
import {
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
import { formatWeekLabel, pivotSkills, topSkillsLatest } from "@/lib/aggregations"
import type { SkillTrendPoint } from "@/lib/types"
import { cn } from "@/lib/utils"

const PALETTE = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
]

function colorFor(index: number): string {
  return PALETTE[index % PALETTE.length]
}

export function SkillTrendsChart({
  points,
  topN,
  className,
}: {
  points: SkillTrendPoint[]
  topN: number
  className?: string
}) {
  const skills = useMemo(() => topSkillsLatest(points, topN), [points, topN])
  const data = useMemo(() => pivotSkills(points, skills), [points, skills])
  const [hidden, setHidden] = useState<Set<string>>(new Set())

  const config = useMemo<ChartConfig>(() => {
    const cfg: ChartConfig = {}
    skills.forEach((s, idx) => {
      cfg[s] = { label: s, color: colorFor(idx) }
    })
    return cfg
  }, [skills])

  const toggle = (skill: string) => {
    setHidden((prev) => {
      const next = new Set(prev)
      if (next.has(skill)) next.delete(skill)
      else next.add(skill)
      return next
    })
  }

  if (!skills.length) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-border bg-card text-sm text-muted-foreground">
        No skill trends available for this filter.
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col gap-4 rounded-lg border border-border bg-card p-4 sm:p-6", className)}>
      <ChartContainer
        config={config}
        className="aspect-auto h-[340px] w-full"
        aria-label="Skill trends over time"
      >
        <LineChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 4 }}>
          <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            dataKey="week"
            tickFormatter={formatWeekLabel}
            tickLine={false}
            axisLine={false}
            stroke="var(--color-muted-foreground)"
            fontSize={12}
            tickMargin={8}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            stroke="var(--color-muted-foreground)"
            fontSize={12}
            width={36}
          />
          <ChartTooltip
            cursor={{ stroke: "var(--color-border)" }}
            content={
              <ChartTooltipContent
                labelFormatter={(v) => `Week ${formatWeekLabel(String(v))}`}
              />
            }
          />
          {skills.map((skill, idx) => (
            <Line
              key={skill}
              dataKey={skill}
              type="monotone"
              stroke={colorFor(idx)}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              hide={hidden.has(skill)}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ChartContainer>

      <div
        role="group"
        aria-label="Toggle skills"
        className="flex flex-wrap gap-1.5"
      >
        {skills.map((skill, idx) => {
          const isHidden = hidden.has(skill)
          return (
            <button
              key={skill}
              type="button"
              onClick={() => toggle(skill)}
              aria-pressed={!isHidden}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors",
                isHidden
                  ? "border-border text-muted-foreground opacity-50 hover:opacity-100"
                  : "border-border text-foreground hover:bg-muted",
              )}
            >
              <span
                aria-hidden
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: colorFor(idx) }}
              />
              {skill}
            </button>
          )
        })}
      </div>
    </div>
  )
}
