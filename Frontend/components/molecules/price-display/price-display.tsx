"use client"

import { memo } from "react"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/utils/cn"
import type { PriceDisplayProps, TaxDetail, FeeDetail } from "./price-display.types"

export const PriceDisplay = memo(function PriceDisplay({ 
  priceBreakdown, 
  detailed = false,
  compact = false,
  className 
}: PriceDisplayProps) {
  const {
    baseFare,
    taxes,
    fees,
    surcharges,
    discounts,
    totalPrice,
    currency,
    taxDetails,
    feeDetails
  } = priceBreakdown

  if (compact) {
    return (
      <div className={cn("space-y-1", className)}>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Base fare</span>
          <span>{baseFare} {currency}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Taxes & fees</span>
          <span>{(taxes + fees)} {currency}</span>
        </div>
        <Separator className="my-1" />
        <div className="flex justify-between font-medium">
          <span>Total</span>
          <span className="font-bold">{totalPrice} {currency}</span>
        </div>
      </div>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Fare Details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          <div className="flex justify-between">
            <span>Base fare</span>
            <span>{baseFare} {currency}</span>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <span>Taxes</span>
            <span>{taxes} {currency}</span>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <span>Fees</span>
            <span>{fees} {currency}</span>
          </div>
          
          {surcharges && surcharges > 0 && (
            <div className="flex justify-between text-muted-foreground">
              <span>Surcharges</span>
              <span>{surcharges} {currency}</span>
            </div>
          )}
          
          {discounts && discounts > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discounts</span>
              <span>-{discounts} {currency}</span>
            </div>
          )}
          
          <Separator className="my-2" />
          
          <div className="flex justify-between font-medium">
            <span>Total price</span>
            <span className="font-bold text-lg">{totalPrice} {currency}</span>
          </div>
        </div>
        
        {/* Detailed breakdown section */}
        {detailed && taxDetails && taxDetails.length > 0 && (
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-medium">Tax Breakdown</h4>
            <div className="space-y-1 text-xs">
              {taxDetails.map((tax: TaxDetail, index: number) => (
                <div key={index} className="flex justify-between">
                  <span>{tax.description || tax.code}</span>
                  <span>{tax.amount} {currency}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {detailed && feeDetails && feeDetails.length > 0 && (
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-medium">Fee Breakdown</h4>
            <div className="space-y-1 text-xs">
              {feeDetails.map((fee: FeeDetail, index: number) => (
                <div key={index} className="flex justify-between">
                  <span>{fee.description || fee.code}</span>
                  <span>{fee.amount} {currency}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
})

PriceDisplay.displayName = "PriceDisplay"