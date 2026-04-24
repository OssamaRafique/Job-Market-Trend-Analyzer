import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { JobPosting } from "@/lib/types"

function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date)
}

export function JobsTable({ items }: { items: JobPosting[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <Table>
        <TableHeader className="bg-muted/40">
          <TableRow>
            <TableHead scope="col">Title</TableHead>
            <TableHead scope="col">Company</TableHead>
            <TableHead scope="col" className="hidden lg:table-cell">
              Category
            </TableHead>
            <TableHead scope="col" className="hidden md:table-cell">
              Level
            </TableHead>
            <TableHead scope="col" className="hidden lg:table-cell">
              Location
            </TableHead>
            <TableHead scope="col" className="text-right">
              Collected
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((job) => (
            <TableRow key={job.id}>
              <TableCell className="font-medium">{job.title}</TableCell>
              <TableCell className="text-muted-foreground">{job.company}</TableCell>
              <TableCell className="hidden text-muted-foreground lg:table-cell">
                {job.category}
              </TableCell>
              <TableCell className="hidden md:table-cell">
                <Badge variant="secondary" className="font-normal">
                  {job.level}
                </Badge>
              </TableCell>
              <TableCell className="hidden text-muted-foreground lg:table-cell">
                {job.location}
              </TableCell>
              <TableCell className="text-right text-muted-foreground tabular-nums">
                {formatDate(job.date_collected)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
