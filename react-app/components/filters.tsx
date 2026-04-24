"use client"

import { Search } from "lucide-react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useCallback, useEffect, useState } from "react"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// All filter controls write to the URL query string so the state is shareable,
// matching section 7 of the UI specification.
function useUrlSetter() {
  const router = useRouter()
  const pathname = usePathname()
  const params = useSearchParams()

  return useCallback(
    (updates: Record<string, string | null>) => {
      const sp = new URLSearchParams(params.toString())
      for (const [k, v] of Object.entries(updates)) {
        if (v === null || v === "") sp.delete(k)
        else sp.set(k, v)
      }
      // Reset offset-based pagination whenever a filter changes.
      if (Object.keys(updates).some((k) => k !== "offset")) {
        sp.delete("offset")
      }
      const qs = sp.toString()
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    },
    [params, pathname, router],
  )
}

const ALL_VALUE = "__all__"

export function CategoryFilter({
  categories,
  value,
  className,
}: {
  categories: string[]
  value?: string
  className?: string
}) {
  const setUrl = useUrlSetter()
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor="category-filter" className="text-xs text-muted-foreground">
        Category
      </Label>
      <Select
        value={value ?? ALL_VALUE}
        onValueChange={(v) => setUrl({ category: v === ALL_VALUE ? null : v })}
      >
        <SelectTrigger id="category-filter" className="w-full sm:w-[220px]">
          <SelectValue placeholder="All categories" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_VALUE}>All categories</SelectItem>
          {categories.map((c) => (
            <SelectItem key={c} value={c}>
              {c}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export function WeeksSelector({
  value,
  options = [1, 4, 12],
  className,
}: {
  value: number
  options?: number[]
  className?: string
}) {
  const setUrl = useUrlSetter()
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label className="text-xs text-muted-foreground">Time window</Label>
      <div role="group" aria-label="Weeks" className="inline-flex rounded-md border border-border p-0.5">
        {options.map((w) => {
          const active = w === value
          return (
            <button
              key={w}
              type="button"
              onClick={() => setUrl({ weeks: String(w) })}
              aria-pressed={active}
              className={cn(
                "rounded px-3 py-1 text-sm transition-colors",
                active
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {w === 1 ? "1w" : `${w}w`}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function TopNSelector({
  value,
  options = [5, 10, 20],
  className,
}: {
  value: number
  options?: number[]
  className?: string
}) {
  const setUrl = useUrlSetter()
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label className="text-xs text-muted-foreground">Top skills</Label>
      <div role="group" aria-label="Top N" className="inline-flex rounded-md border border-border p-0.5">
        {options.map((n) => {
          const active = n === value
          return (
            <button
              key={n}
              type="button"
              onClick={() => setUrl({ top: String(n) })}
              aria-pressed={active}
              className={cn(
                "rounded px-3 py-1 text-sm transition-colors",
                active
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {n}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function LevelFilter({
  value,
  className,
}: {
  value?: string
  className?: string
}) {
  const setUrl = useUrlSetter()
  const levels = ["Entry", "Mid", "Senior", "Staff", "Principal"]
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor="level-filter" className="text-xs text-muted-foreground">
        Level
      </Label>
      <Select
        value={value ?? ALL_VALUE}
        onValueChange={(v) => setUrl({ level: v === ALL_VALUE ? null : v })}
      >
        <SelectTrigger id="level-filter" className="w-full sm:w-[160px]">
          <SelectValue placeholder="All levels" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_VALUE}>All levels</SelectItem>
          {levels.map((l) => (
            <SelectItem key={l} value={l}>
              {l}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

// 300ms debounced free-text input per section 7 of the spec.
export function LocationSearch({
  value,
  className,
}: {
  value?: string
  className?: string
}) {
  const setUrl = useUrlSetter()
  const [local, setLocal] = useState(value ?? "")

  useEffect(() => {
    setLocal(value ?? "")
  }, [value])

  useEffect(() => {
    const current = value ?? ""
    if (local === current) return
    const id = setTimeout(() => {
      setUrl({ location: local.trim() === "" ? null : local.trim() })
    }, 300)
    return () => clearTimeout(id)
  }, [local, setUrl, value])

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor="location-filter" className="text-xs text-muted-foreground">
        Location
      </Label>
      <InputGroup className="w-full sm:w-[240px]">
        <InputGroupAddon>
          <Search className="h-3.5 w-3.5" aria-hidden />
        </InputGroupAddon>
        <InputGroupInput
          id="location-filter"
          placeholder="Remote, San Francisco, …"
          value={local}
          onChange={(e) => setLocal(e.target.value)}
        />
      </InputGroup>
    </div>
  )
}

export function ClearFiltersButton({
  keys,
  className,
}: {
  keys: string[]
  className?: string
}) {
  const setUrl = useUrlSetter()
  const params = useSearchParams()
  const hasAny = keys.some((k) => params.get(k))
  if (!hasAny) return null
  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("text-muted-foreground", className)}
      onClick={() => setUrl(Object.fromEntries(keys.map((k) => [k, null])))}
    >
      Clear filters
    </Button>
  )
}
