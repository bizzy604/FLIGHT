"use client"

import * as React from "react"
import { Check, ChevronsUpDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { COUNTRY_CODES, CountryCode, searchCountryCodes } from "@/utils/country-codes"

interface PhoneCountrySelectorProps {
  value?: string
  onValueChange: (value: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
  showMostCommon?: boolean
  maxCommonItems?: number
}

export function PhoneCountrySelector({ 
  value, 
  onValueChange, 
  placeholder = "Select country code...",
  className,
  disabled = false,
  showMostCommon = true,
  maxCommonItems = 20
}: PhoneCountrySelectorProps) {
  const [open, setOpen] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")

  // Filter country codes based on search query
  const filteredCountryCodes = React.useMemo(() => {
    if (!searchQuery.trim()) {
      // Show most common countries first, then all others
      if (showMostCommon) {
        const mostCommon = COUNTRY_CODES
          .filter(cc => (cc.priority || 0) >= 50)
          .sort((a, b) => (b.priority || 0) - (a.priority || 0))
          .slice(0, maxCommonItems)
        
        const others = COUNTRY_CODES
          .filter(cc => (cc.priority || 0) < 50)
          .sort((a, b) => a.name.localeCompare(b.name))
        
        return [...mostCommon, ...others]
      }
      return COUNTRY_CODES.sort((a, b) => a.name.localeCompare(b.name))
    }
    return searchCountryCodes(searchQuery)
  }, [searchQuery, showMostCommon, maxCommonItems])

  // Get selected country code
  const selectedCountryCode = React.useMemo(() => {
    if (!value) return null
    return COUNTRY_CODES.find(countryCode => countryCode.dialCode === value)
  }, [value])

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn(
            "w-full justify-between text-left font-normal",
            !selectedCountryCode && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          {selectedCountryCode ? (
            <div className="flex items-center gap-2">
              <span className="text-lg">{selectedCountryCode.flag}</span>
              <span className="font-mono text-sm">{selectedCountryCode.dialCode}</span>
            </div>
          ) : (
            placeholder
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0" align="start">
        <Command>
          <CommandInput 
            placeholder="Search country codes..." 
            value={searchQuery}
            onValueChange={setSearchQuery}
          />
          <CommandList>
            <CommandEmpty>No country code found.</CommandEmpty>
            <CommandGroup>
              {filteredCountryCodes.map((countryCode) => (
                <CommandItem
                  key={`${countryCode.dialCode}-${countryCode.code}`}
                  value={countryCode.dialCode}
                  onSelect={(currentValue) => {
                    onValueChange(currentValue === value ? "" : currentValue)
                    setOpen(false)
                    setSearchQuery("")
                  }}
                  className="flex items-center gap-2"
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === countryCode.dialCode ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <span className="text-lg">{countryCode.flag}</span>
                  <span className="font-mono text-sm">{countryCode.dialCode}</span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {countryCode.name}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
