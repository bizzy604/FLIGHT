"use client"

import { memo, useState, useMemo, useCallback } from "react"
import { MapPin, Plane } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { cn } from "@/utils/cn"
import type { AirportSelectorProps, Airport } from "./airport-selector.types"
import { DEFAULT_AIRPORTS, POPULAR_AIRPORTS } from "./airport-selector.types"

export const AirportSelector = memo(function AirportSelector({
  label,
  value,
  onChange,
  placeholder = "Search airport...",
  disabled = false,
  airports = DEFAULT_AIRPORTS,
  className,
  error,
  icon = <Plane className="h-4 w-4" />,
  compact = false,
  inline = false,
}: AirportSelectorProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  // Find selected airport for display
  const selectedAirport = useMemo(() => 
    airports.find(airport => airport.code === value),
    [airports, value]
  )

  // Performance optimization: Show popular airports initially, search all when user types
  const displayedAirports = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2) {
      // Show popular airports when no search or search too short
      return POPULAR_AIRPORTS
    }
    
    const query = searchQuery.toLowerCase()
    const filtered = airports.filter(airport => 
      airport.code.toLowerCase().includes(query) ||
      airport.name.toLowerCase().includes(query) ||
      airport.city.toLowerCase().includes(query)
    )
    
    // Limit results to 50 for performance
    return filtered.slice(0, 50)
  }, [airports, searchQuery])

  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query)
  }, [])

  const handleSelect = (airportCode: string) => {
    onChange(airportCode)
    setOpen(false)
    setSearchQuery("")
  }

  const displayValue = selectedAirport 
    ? `${selectedAirport.city} (${selectedAirport.code})`
    : value || ""

  // Inline layout for horizontal form
  if (inline) {
    return (
      <div className={className}>
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={open}
              className={cn(
                "w-full justify-start font-medium text-left p-2 h-auto min-h-[40px] border border-border hover:bg-secondary/50 rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                !value && "text-muted-foreground",
                error && "text-destructive border-destructive"
              )}
              disabled={disabled}
            >
              <span className="truncate text-base">
                {displayValue || placeholder}
              </span>
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-0" align="start">
            <Command>
              <CommandInput 
                placeholder="Type 2+ characters to search all airports..."
                value={searchQuery}
                onValueChange={handleSearchChange}
              />
              <CommandList className="max-h-64 overflow-auto">
                <CommandEmpty>
                  {searchQuery.length < 2 
                    ? "Type at least 2 characters to search all airports"
                    : "No airport found."
                  }
                </CommandEmpty>
                <CommandGroup>
                  {searchQuery.length < 2 && (
                    <div className="px-2 py-1 text-xs text-muted-foreground border-b">
                      Popular Airports
                    </div>
                  )}
                  {displayedAirports.map((airport) => (
                    <CommandItem
                      key={airport.code}
                      value={airport.code}
                      onSelect={() => handleSelect(airport.code)}
                    >
                      <MapPin className="mr-2 h-4 w-4" />
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {airport.city} ({airport.code})
                        </span>
                        <span className="text-xs text-muted-foreground truncate">
                          {airport.name}
                        </span>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
                {searchQuery.length >= 2 && displayedAirports.length === 50 && (
                  <div className="px-2 py-1 text-xs text-muted-foreground border-t">
                    Showing first 50 results. Type more to narrow search.
                  </div>
                )}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
        {error && (
          <p className="text-xs text-destructive mt-1">{error}</p>
        )}
      </div>
    )
  }

  // Default layout
  return (
    <div className={cn("space-y-2", className)}>
      <Label className={cn("text-sm font-medium", error && "text-destructive")}>
        {label}
      </Label>
      
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn(
              "w-full justify-between font-normal",
              !value && "text-muted-foreground",
              error && "border-destructive"
            )}
            disabled={disabled}
          >
            <div className="flex items-center">
              {icon && <span className="mr-2">{icon}</span>}
              <span className="truncate">
                {displayValue || placeholder}
              </span>
            </div>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0" align="start">
          <Command>
            <CommandInput 
              placeholder="Type 2+ characters to search all airports..."
              value={searchQuery}
              onValueChange={handleSearchChange}
            />
            <CommandList className="max-h-64 overflow-auto">
              <CommandEmpty>
                {searchQuery.length < 2 
                  ? "Type at least 2 characters to search all airports"
                  : "No airport found."
                }
              </CommandEmpty>
              <CommandGroup>
                {searchQuery.length < 2 && (
                  <div className="px-2 py-1 text-xs text-muted-foreground border-b">
                    Popular Airports
                  </div>
                )}
                {displayedAirports.map((airport) => (
                  <CommandItem
                    key={airport.code}
                    value={airport.code}
                    onSelect={() => handleSelect(airport.code)}
                  >
                    <MapPin className="mr-2 h-4 w-4" />
                    <div className="flex flex-col">
                      <span className="font-medium">
                        {airport.city} ({airport.code})
                      </span>
                      <span className="text-xs text-muted-foreground truncate">
                        {airport.name}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
              {searchQuery.length >= 2 && displayedAirports.length === 50 && (
                <div className="px-2 py-1 text-xs text-muted-foreground border-t">
                  Showing first 50 results. Type more to narrow search.
                </div>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  )
})

AirportSelector.displayName = "AirportSelector"