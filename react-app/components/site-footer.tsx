"use client"

import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

type Status = "unknown" | "healthy" | "degraded"

export function SiteFooter() {
  const [status, setStatus] = useState<Status>("unknown")
  const base = process.env.NEXT_PUBLIC_API_URL

  useEffect(() => {
    if (!base) {
      setStatus("unknown")
      return
    }
    const controller = new AbortController()
    fetch(`${base}/health`, { signal: controller.signal })
      .then(async (r) => {
        if (!r.ok) throw new Error("not ok")
        const data = (await r.json()) as { status?: string }
        setStatus(data.status === "healthy" ? "healthy" : "degraded")
      })
      .catch(() => setStatus("degraded"))
    return () => controller.abort()
  }, [base])

  const label =
    status === "healthy" ? "API healthy" : status === "degraded" ? "API unreachable" : "Using local fixtures"
  const dotClass =
    status === "healthy"
      ? "bg-chart-1"
      : status === "degraded"
        ? "bg-chart-4"
        : "bg-muted-foreground"

  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className={cn("inline-block h-2 w-2 rounded-full", dotClass)}
          />
          <span>{label}</span>
        </div>
        <p className="text-balance">
          Data sourced from{" "}
          <a
            href="https://www.themuse.com/developers/api/v2"
            target="_blank"
            rel="noreferrer"
            className="underline underline-offset-4 hover:text-foreground"
          >
            The Muse API
          </a>
          . Updated daily.
        </p>
      </div>
    </footer>
  )
}
