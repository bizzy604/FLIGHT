import type React from "react"
import { cn } from "@/lib/utils"

interface DataPlaceholderProps {
  children: React.ReactNode
  isLoading?: boolean
  isEmpty?: boolean
  emptyMessage?: string
  className?: string
}

export function DataPlaceholder({
  children,
  isLoading = false,
  isEmpty = false,
  emptyMessage = "No data available",
  className,
}: DataPlaceholderProps) {
  if (isLoading) {
    return (
      <div
        className={cn("flex min-h-[100px] items-center justify-center rounded-md border border-dashed p-8", className)}
      >
        <p className="text-sm text-muted-foreground">Loading data...</p>
      </div>
    )
  }

  if (isEmpty) {
    return (
      <div
        className={cn("flex min-h-[100px] items-center justify-center rounded-md border border-dashed p-8", className)}
      >
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      </div>
    )
  }

  return <>{children}</>
}

