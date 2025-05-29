import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PriceBreakdown } from "@/types/flight-api"

interface PriceBreakdownComponentProps {
  priceBreakdown: PriceBreakdown
  detailed?: boolean
}

export function PriceBreakdownComponent({ 
  priceBreakdown, 
  detailed = false 
}: PriceBreakdownComponentProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Fare Details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          <div className="flex justify-between">
            <span>Base fare</span>
            <span>{priceBreakdown.baseFare} {priceBreakdown.currency}</span>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <span>Taxes</span>
            <span>{priceBreakdown.taxes} {priceBreakdown.currency}</span>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <span>Fees</span>
            <span>{priceBreakdown.fees} {priceBreakdown.currency}</span>
          </div>
          
          {priceBreakdown.surcharges && priceBreakdown.surcharges > 0 && (
            <div className="flex justify-between text-muted-foreground">
              <span>Surcharges</span>
              <span>{priceBreakdown.surcharges} {priceBreakdown.currency}</span>
            </div>
          )}
          
          {priceBreakdown.discounts && priceBreakdown.discounts > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discounts</span>
              <span>-{priceBreakdown.discounts} {priceBreakdown.currency}</span>
            </div>
          )}
          
          <Separator className="my-2" />
          
          <div className="flex justify-between font-medium">
            <span>Total price</span>
            <span>{priceBreakdown.totalPrice} {priceBreakdown.currency}</span>
          </div>
        </div>
        
        {/* Additional detailed breakdown if available and requested */}
        {detailed && priceBreakdown.taxBreakdown && priceBreakdown.taxBreakdown.length > 0 && (
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-medium">Tax Breakdown</h4>
            <div className="space-y-1 text-xs">
              {priceBreakdown.taxBreakdown.map((tax, index) => (
                <div key={index} className="flex justify-between">
                  <span>{tax.description || tax.code}</span>
                  <span>{tax.amount} {priceBreakdown.currency}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {detailed && priceBreakdown.feeBreakdown && priceBreakdown.feeBreakdown.length > 0 && (
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-medium">Fee Breakdown</h4>
            <div className="space-y-1 text-xs">
              {priceBreakdown.feeBreakdown.map((fee, index) => (
                <div key={index} className="flex justify-between">
                  <span>{fee.description || fee.code}</span>
                  <span>{fee.amount} {priceBreakdown.currency}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
