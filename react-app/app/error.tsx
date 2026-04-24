"use client"

import { AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-4 px-4 py-16 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-chart-4/10 text-chart-4">
        <AlertTriangle className="h-5 w-5" aria-hidden />
      </span>
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">Something went wrong</h1>
        <p className="text-sm text-muted-foreground">
          {error.message || "An unexpected error occurred while rendering this view."}
        </p>
      </div>
      <Button onClick={() => reset()}>Try again</Button>
    </div>
  )
}
