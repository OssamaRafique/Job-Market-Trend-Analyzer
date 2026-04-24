import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

export function SummaryTile({
  label,
  value,
  hint,
  icon: Icon,
  tone = "default",
}: {
  label: string
  value: string | number
  hint?: string
  icon?: LucideIcon
  tone?: "default" | "accent"
}) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        {Icon ? (
          <span
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-md",
              tone === "accent"
                ? "bg-chart-1/10 text-chart-1"
                : "bg-muted text-muted-foreground",
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden />
          </span>
        ) : null}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-semibold tracking-tight tabular-nums">{value}</span>
      </div>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  )
}
