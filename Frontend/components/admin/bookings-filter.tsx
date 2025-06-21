"use client"

import { useState } from "react"
import { CalendarIcon, Check, ChevronsUpDown, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/utils/cn"

const statuses = [
  { value: "confirmed", label: "Confirmed" },
  { value: "pending", label: "Pending" },
  { value: "cancelled", label: "Cancelled" },
  { value: "refunded", label: "Refunded" },
]

const paymentMethods = [
  { value: "credit-card", label: "Credit Card" },
  { value: "paypal", label: "PayPal" },
  { value: "apple-pay", label: "Apple Pay" },
  { value: "bank-transfer", label: "Bank Transfer" },
]

export function BookingsFilter() {
  const [open, setOpen] = useState(false)
  const [statusValue, setStatusValue] = useState<string[]>([])
  const [paymentValue, setPaymentValue] = useState<string[]>([])
  const [dateRange, setDateRange] = useState<{
    from: Date | undefined
    to: Date | undefined
  }>({
    from: undefined,
    to: undefined,
  })
  const [minAmount, setMinAmount] = useState("")
  const [maxAmount, setMaxAmount] = useState("")

  const handleStatusSelect = (value: string) => {
    setStatusValue((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value],
    )
  }

  const handlePaymentSelect = (value: string) => {
    setPaymentValue((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value],
    )
  }

  const clearFilters = () => {
    setStatusValue([])
    setPaymentValue([])
    setDateRange({ from: undefined, to: undefined })
    setMinAmount("")
    setMaxAmount("")
  }

  const hasActiveFilters =
    statusValue.length > 0 ||
    paymentValue.length > 0 ||
    dateRange.from !== undefined ||
    minAmount !== "" ||
    maxAmount !== ""

  return (
    <div className="rounded-md border p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">Filters</h2>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="mr-2 h-4 w-4" />
            Clear all
          </Button>
        )}
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="space-y-2">
          <Label>Booking Status</Label>
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" role="combobox" className="w-full justify-between">
                {statusValue.length > 0 ? `${statusValue.length} selected` : "Select status"}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-full p-0">
              <Command>
                <CommandInput placeholder="Search status..." />
                <CommandList>
                  <CommandEmpty>No status found.</CommandEmpty>
                  <CommandGroup>
                    {statuses.map((status) => (
                      <CommandItem
                        key={status.value}
                        value={status.value}
                        onSelect={() => handleStatusSelect(status.value)}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            statusValue.includes(status.value) ? "opacity-100" : "opacity-0",
                          )}
                        />
                        {status.label}
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
          {statusValue.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {statusValue.map((value) => {
                const status = statuses.find((s) => s.value === value)
                return (
                  <Badge key={value} variant="secondary" className="gap-1">
                    {status?.label}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-3 w-3 p-0"
                      onClick={() => handleStatusSelect(value)}
                    >
                      <X className="h-3 w-3" />
                      <span className="sr-only">Remove {status?.label}</span>
                    </Button>
                  </Badge>
                )
              })}
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label>Payment Method</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" role="combobox" className="w-full justify-between">
                {paymentValue.length > 0 ? `${paymentValue.length} selected` : "Select payment method"}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-full p-0">
              <Command>
                <CommandInput placeholder="Search payment method..." />
                <CommandList>
                  <CommandEmpty>No payment method found.</CommandEmpty>
                  <CommandGroup>
                    {paymentMethods.map((method) => (
                      <CommandItem
                        key={method.value}
                        value={method.value}
                        onSelect={() => handlePaymentSelect(method.value)}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            paymentValue.includes(method.value) ? "opacity-100" : "opacity-0",
                          )}
                        />
                        {method.label}
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>

        <div className="space-y-2">
          <Label>Date Range</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn("w-full justify-start text-left font-normal", !dateRange.from && "text-muted-foreground")}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {dateRange.from ? (
                  dateRange.to ? (
                    <>
                      {dateRange.from.toLocaleDateString()} - {dateRange.to.toLocaleDateString()}
                    </>
                  ) : (
                    dateRange.from.toLocaleDateString()
                  )
                ) : (
                  "Select date range"
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar 
                mode="range" 
                selected={{
                  from: dateRange?.from,
                  to: dateRange?.to
                }} 
                onSelect={(range) => {
                  if (range?.from) {
                    setDateRange({
                      from: range.from,
                      to: range.to || range.from
                    });
                  }
                }} 
                initialFocus 
              />
            </PopoverContent>
          </Popover>
        </div>

        <div className="space-y-2">
          <Label>Amount Range</Label>
          <div className="flex items-center space-x-2">
            <Input
              type="number"
              placeholder="Min"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              className="w-full"
            />
            <span>-</span>
            <Input
              type="number"
              placeholder="Max"
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              className="w-full"
            />
          </div>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button>Apply Filters</Button>
      </div>
    </div>
  )
}

