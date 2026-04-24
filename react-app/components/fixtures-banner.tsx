import { Info } from "lucide-react"

export function FixturesBanner({ error }: { error?: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/40 px-4 py-3 text-xs text-muted-foreground">
      <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
      <div className="flex flex-col gap-0.5">
        <p className="font-medium text-foreground">Showing sample data</p>
        <p>
          {error
            ? `Backend unreachable (${error}). Displaying local fixtures so the UI remains usable.`
            : "NEXT_PUBLIC_API_URL is not configured. Displaying local fixtures — set the env var to connect to the real API."}
        </p>
      </div>
    </div>
  )
}
