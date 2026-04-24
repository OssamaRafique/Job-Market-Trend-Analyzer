"use client"

import { useState, useTransition } from "react"
import { RefreshCw } from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"

// Gated behind NEXT_PUBLIC_ENABLE_REFRESH. Matches section 5.6 of the UI spec.
export function RefreshButton() {
  const router = useRouter()
  const [isSending, setIsSending] = useState(false)
  const [isPending, startTransition] = useTransition()
  const enabled = process.env.NEXT_PUBLIC_ENABLE_REFRESH === "true"
  const base = process.env.NEXT_PUBLIC_API_URL

  if (!enabled) return null

  const onClick = async () => {
    if (!base) {
      toast.error("Refresh unavailable", {
        description: "NEXT_PUBLIC_API_URL is not configured.",
      })
      return
    }
    setIsSending(true)
    try {
      const res = await fetch(`${base}/api/refresh`, { method: "POST" })
      if (!res.ok && res.status !== 202) {
        throw new Error(`Request failed: ${res.status}`)
      }
      toast.success("Refresh queued", {
        description: "A new collection job has been enqueued.",
      })
      startTransition(() => router.refresh())
    } catch (err) {
      toast.error("Could not queue refresh", {
        description: err instanceof Error ? err.message : "Unknown error",
      })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      disabled={isSending || isPending}
      className="gap-1.5"
    >
      <RefreshCw className={`h-3.5 w-3.5 ${isSending ? "animate-spin" : ""}`} aria-hidden />
      <span className="hidden sm:inline">Refresh data</span>
    </Button>
  )
}
