"use client"

import { ChevronLeft, ChevronRight } from "lucide-react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useCallback } from "react"
import { Button } from "@/components/ui/button"

export function PaginationControls({
  total,
  limit,
  offset,
}: {
  total: number
  limit: number
  offset: number
}) {
  const router = useRouter()
  const pathname = usePathname()
  const params = useSearchParams()

  const go = useCallback(
    (nextOffset: number) => {
      const sp = new URLSearchParams(params.toString())
      if (nextOffset <= 0) sp.delete("offset")
      else sp.set("offset", String(nextOffset))
      const qs = sp.toString()
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    },
    [params, pathname, router],
  )

  const start = total === 0 ? 0 : offset + 1
  const end = Math.min(offset + limit, total)
  const atStart = offset <= 0
  const atEnd = offset + limit >= total

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-muted-foreground tabular-nums">
        Showing <span className="font-medium text-foreground">{start}</span>–
        <span className="font-medium text-foreground">{end}</span> of{" "}
        <span className="font-medium text-foreground">{total.toLocaleString()}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => go(Math.max(0, offset - limit))}
          disabled={atStart}
          className="gap-1"
        >
          <ChevronLeft className="h-3.5 w-3.5" aria-hidden />
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => go(offset + limit)}
          disabled={atEnd}
          className="gap-1"
        >
          Next
          <ChevronRight className="h-3.5 w-3.5" aria-hidden />
        </Button>
      </div>
    </div>
  )
}
