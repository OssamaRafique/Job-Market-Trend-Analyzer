"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { BarChart3, Briefcase, LineChart, Menu, TrendingUp, X } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { RefreshButton } from "@/components/refresh-button"
import { Button } from "@/components/ui/button"

const NAV = [
  { href: "/", label: "Overview", icon: LineChart },
  { href: "/skills", label: "Skills", icon: TrendingUp },
  { href: "/companies", label: "Companies", icon: BarChart3 },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
]

export function SiteHeader() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`)

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span
            aria-hidden
            className="flex h-7 w-7 items-center justify-center rounded-md bg-foreground text-background"
          >
            <LineChart className="h-4 w-4" />
          </span>
          <span className="text-sm sm:text-base">Job Trend Analyser</span>
        </Link>

        <nav
          aria-label="Primary"
          className="ml-6 hidden items-center gap-1 md:flex"
        >
          {NAV.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  active && "bg-muted text-foreground",
                )}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <RefreshButton />
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {open ? (
        <div className="border-t border-border md:hidden">
          <nav aria-label="Mobile" className="mx-auto flex max-w-7xl flex-col px-4 py-2">
            {NAV.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground",
                    active && "bg-muted text-foreground",
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
      ) : null}
    </header>
  )
}
