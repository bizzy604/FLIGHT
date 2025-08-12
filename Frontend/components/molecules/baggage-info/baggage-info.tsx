import { Briefcase, Luggage, Info } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { BaggageAllowance } from "@/types/flight-api"

interface BaggageInfoComponentProps {
  baggage: BaggageAllowance
}

export function BaggageInfo({ baggage }: BaggageInfoComponentProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Baggage Information</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Carry-On Baggage */}
          {baggage.carryOn && (
            <div>
              <h3 className="flex items-center text-sm font-medium">
                <Briefcase className="mr-2 h-4 w-4" />
                Carry-On Baggage
              </h3>
              
              <div className="mt-2 rounded-md border p-3">
                <p className="text-sm">{baggage.carryOn.description}</p>
                
                <div className="mt-2 space-y-2 text-sm">
                  {baggage.carryOn.quantity !== undefined && (
                    <div className="flex justify-between">
                      <span>Allowed pieces:</span>
                      <span className="font-medium">{baggage.carryOn.quantity}</span>
                    </div>
                  )}
                  
                  {baggage.carryOn.weight && (
                    <div className="flex justify-between">
                      <span>Maximum weight:</span>
                      <span className="font-medium">{baggage.carryOn.weight.value} {baggage.carryOn.weight.unit}</span>
                    </div>
                  )}
                  
                  {baggage.carryOn.dimensions && (
                    <div className="flex justify-between">
                      <span>Maximum dimensions:</span>
                      <span className="font-medium">
                        {baggage.carryOn.dimensions.length?.value && baggage.carryOn.dimensions.width?.value && baggage.carryOn.dimensions.height?.value
                          ? `${baggage.carryOn.dimensions.length.value}x${baggage.carryOn.dimensions.width.value}x${baggage.carryOn.dimensions.height.value} ${baggage.carryOn.dimensions.length.unit || ''}`
                          : baggage.carryOn.dimensions.totalDimensions?.value
                            ? `${baggage.carryOn.dimensions.totalDimensions.value} ${baggage.carryOn.dimensions.totalDimensions.unit || ''}`
                            : 'Standard size'}
                      </span>
                    </div>
                  )}
                </div>
                
                {baggage.carryOn.personalItem && (
                  <div className="mt-3 border-t pt-2">
                    <h4 className="text-xs font-medium">Personal Item</h4>
                    <div className="mt-1 space-y-1 text-xs">
                      {baggage.carryOn.personalItem.description && (
                        <p>{baggage.carryOn.personalItem.description}</p>
                      )}
                      
                      {baggage.carryOn.personalItem.dimensions && (
                        <div className="flex justify-between">
                          <span>Maximum dimensions:</span>
                          <span>
                            {typeof baggage.carryOn.personalItem.dimensions === 'object' && baggage.carryOn.personalItem.dimensions.length?.value
                              ? `${baggage.carryOn.personalItem.dimensions.length.value}x${baggage.carryOn.personalItem.dimensions.width?.value || ''}x${baggage.carryOn.personalItem.dimensions.height?.value || ''} ${baggage.carryOn.personalItem.dimensions.length.unit || ''}`
                              : String(baggage.carryOn.personalItem.dimensions)}
                          </span>
                        </div>
                      )}
                      
                      {baggage.carryOn.personalItem.weight && (
                        <div className="flex justify-between">
                          <span>Maximum weight:</span>
                          <span>{baggage.carryOn.personalItem.weight.value} {baggage.carryOn.personalItem.weight.unit}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Checked Baggage */}
          {baggage.checkedBaggage && (
            <div>
              <h3 className="flex items-center text-sm font-medium">
                <Luggage className="mr-2 h-4 w-4" />
                Checked Baggage
              </h3>
              
              <div className="mt-2 rounded-md border p-3">
                <p className="text-sm">{baggage.checkedBaggage.description}</p>
                
                <div className="mt-2 space-y-2 text-sm">
                  {baggage.checkedBaggage.pieces !== undefined && (
                    <div className="flex justify-between">
                      <span>Free allowance:</span>
                      <span className="font-medium">{baggage.checkedBaggage.pieces} piece{baggage.checkedBaggage.pieces !== 1 ? 's' : ''}</span>
                    </div>
                  )}
                  
                  {baggage.checkedBaggage.weight && (
                    <div className="flex justify-between">
                      <span>Maximum weight per piece:</span>
                      <span className="font-medium">{baggage.checkedBaggage.weight.value} {baggage.checkedBaggage.weight.unit}</span>
                    </div>
                  )}
                  
                  {baggage.checkedBaggage.dimensions && (
                    <div className="flex justify-between">
                      <span>Maximum dimensions:</span>
                      <span className="font-medium">
                        {baggage.checkedBaggage.dimensions.length?.value && baggage.checkedBaggage.dimensions.width?.value && baggage.checkedBaggage.dimensions.height?.value
                          ? `${baggage.checkedBaggage.dimensions.length.value}x${baggage.checkedBaggage.dimensions.width.value}x${baggage.checkedBaggage.dimensions.height.value} ${baggage.checkedBaggage.dimensions.length.unit || ''}`
                          : baggage.checkedBaggage.dimensions.totalDimensions?.value
                            ? `${baggage.checkedBaggage.dimensions.totalDimensions.value} ${baggage.checkedBaggage.dimensions.totalDimensions.unit || ''}`
                            : 'Standard size'}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Overweight/Oversize Charges */}
                {(baggage.checkedBaggage.overweightCharge || baggage.checkedBaggage.oversizeCharge) && (
                  <div className="mt-3 border-t pt-2">
                    <h4 className="flex items-center text-xs font-medium">
                      <Info className="mr-1 h-3 w-3" />
                      Additional Charges
                    </h4>
                    
                    <div className="mt-1 space-y-1 text-xs">
                      {baggage.checkedBaggage.overweightCharge && (
                        <div className="flex justify-between">
                          <span>Overweight fee:</span>
                          <span>{baggage.checkedBaggage.overweightCharge.amount} {baggage.checkedBaggage.overweightCharge.currency}</span>
                        </div>
                      )}
                      
                      {baggage.checkedBaggage.oversizeCharge && (
                        <div className="flex justify-between">
                          <span>Oversize fee:</span>
                          <span>{baggage.checkedBaggage.oversizeCharge.amount} {baggage.checkedBaggage.oversizeCharge.currency}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Additional Baggage Pricing Table */}
                {baggage.checkedBaggage.additionalBaggagePrices && baggage.checkedBaggage.additionalBaggagePrices.length > 0 && (
                  <div className="mt-3 border-t pt-2">
                    <h4 className="text-xs font-medium">Additional Baggage Prices</h4>
                    
                    <div className="mt-1 overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Bag</TableHead>
                            <TableHead>Price</TableHead>
                            <TableHead>Weight</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {baggage.checkedBaggage.additionalBaggagePrices.map((price, index) => (
                            <TableRow key={index}>
                              <TableCell>
                                {index + 1 + (baggage.checkedBaggage?.pieces || 0)}
                                {getOrdinalSuffix(index + 1 + (baggage.checkedBaggage?.pieces || 0))} bag
                              </TableCell>
                              <TableCell>
                                {price.amount} {price.currency}
                              </TableCell>
                              <TableCell>
                                {price.weight ? `${price.weight.value} ${price.weight.unit}` : "Standard"}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                )}
                
                {/* Prepaid Discount Information */}
                {baggage.checkedBaggage.prepaidDiscount && (
                  <div className="mt-3 rounded-md bg-green-50 p-2 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    <h4 className="text-xs font-medium">Prepaid Baggage Discount</h4>
                    <p className="mt-1 text-xs">
                      Save {baggage.checkedBaggage.prepaidDiscount.percentage}% when you add bags during booking
                      {baggage.checkedBaggage.prepaidDiscount.description && ` - ${baggage.checkedBaggage.prepaidDiscount.description}`}
                    </p>
                  </div>
                )}
                
                {/* Special Items */}
                {baggage.checkedBaggage.specialItems && baggage.checkedBaggage.specialItems.length > 0 && (
                  <div className="mt-3 border-t pt-2">
                    <h4 className="text-xs font-medium">Special Items</h4>
                    
                    <div className="mt-1">
                      <TooltipProvider>
                        {baggage.checkedBaggage.specialItems.map((item, index) => (
                          <Tooltip key={index}>
                            <TooltipTrigger asChild>
                              <span className="mr-2 inline-flex cursor-help items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold">
                                {item.type}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="text-xs">{item.description}</p>
                              {item.extraFee && (
                                <p className="text-xs font-medium">
                                  Additional fee may apply
                                </p>
                              )}
                            </TooltipContent>
                          </Tooltip>
                        ))}
                      </TooltipProvider>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Helper function to get the ordinal suffix for a number (1st, 2nd, 3rd, etc.)
function getOrdinalSuffix(num: number): string {
  const j = num % 10;
  const k = num % 100;
  
  if (j === 1 && k !== 11) {
    return 'st';
  }
  if (j === 2 && k !== 12) {
    return 'nd';
  }
  if (j === 3 && k !== 13) {
    return 'rd';
  }
  return 'th';
}
