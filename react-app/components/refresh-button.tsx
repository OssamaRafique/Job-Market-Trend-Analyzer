"use client"

import { useState, useTransition } from "react"
import { RefreshCw } from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "https://job-market-trend-analyzer.fly.dev"

export function RefreshButton() {
  const router = useRouter()
  const [isSending, setIsSending] = useState(false)
  const [isPending, startTransition] = useTransition()

  const onClick = async () => {
    setIsSending(true)
    try {
      const res = await fetch(`${API_BASE}/api/refresh`, { method: "POST" })
      if (res.status === 202 || res.ok) {
        toast.success("Refresh queued", {
          description: "A new collection job has been enqueued. New data will appear shortly.",
        })
        startTransition(() => router.refresh())
        return
      }
      if (res.status === 503) {
        toast.error("Message broker unavailable", {
          description: "The API could not reach RabbitMQ. Try again in a moment.",
        })
        return
      }
      throw new Error(`Request failed: ${res.status}`)
    } catch (err) {
      toast.error("Could not queue refresh", {
        description: err instanceof Error ? err.message : "Unknown error",
      })
    } finally {
      setIsSending(false)
    }
  }

  const busy = isSending || isPending

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      disabled={busy}
      className="gap-1.5"
      aria-label="Fetch new jobs"
      title="Fetch new jobs from The Muse"
    >
      <RefreshCw className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} aria-hidden />
      <span className="hidden sm:inline">{busy ? "Fetching…" : "Fetch new data"}</span>
    </Button>
  )
}
