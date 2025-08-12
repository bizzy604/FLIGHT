"use client"

import { memo } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { cn } from "@/utils/cn"
import type { CabinSelectorProps } from "./cabin-selector.types"
import { DEFAULT_CABIN_TYPES } from "./cabin-selector.types"

export const CabinSelector = memo(function CabinSelector({
  value,
  onChange,
  cabinTypes = DEFAULT_CABIN_TYPES,
  disabled = false,
  className,
  error,
  label = "Cabin Class",
}: CabinSelectorProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <Label className={cn("text-sm font-medium", error && "text-destructive")}>
          {label}
        </Label>
      )}
      <Select 
        value={value} 
        onValueChange={onChange}
        disabled={disabled}
      >
        <SelectTrigger 
          className={cn(
            "w-full",
            error && "border-destructive"
          )}
        >
          <SelectValue placeholder="Select cabin class" />
        </SelectTrigger>
        <SelectContent>
          {cabinTypes.map((cabin) => (
            <SelectItem key={cabin.value} value={cabin.value}>
              <div className="flex flex-col">
                <span className="font-medium">{cabin.label}</span>
                {cabin.description && (
                  <span className="text-xs text-muted-foreground">
                    {cabin.description}
                  </span>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  )
})

CabinSelector.displayName = "CabinSelector"