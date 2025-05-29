import { AlertCircle, Check, X } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FareRules } from "@/types/flight-api"

interface FareRulesComponentProps {
  fareRules: FareRules
  fareName?: string
  fareBasisCode?: string
}

export function FareRulesComponent({ 
  fareRules, 
  fareName, 
  fareBasisCode 
}: FareRulesComponentProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Fare Rules</CardTitle>
        {fareName && (
          <p className="text-sm text-muted-foreground">
            {fareName} {fareBasisCode && `(${fareBasisCode})`}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Change Rules */}
          <div className="rounded-md border p-3">
            <h3 className="text-sm font-medium">Ticket Changes</h3>
            
            <div className="mt-2 space-y-3">
              {/* Change before departure */}
              {fareRules.changeBeforeDeparture !== undefined && (
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm">Changes before departure</p>
                    {fareRules.changeBeforeDeparture.conditions && (
                      <p className="text-xs text-muted-foreground">{fareRules.changeBeforeDeparture.conditions}</p>
                    )}
                  </div>
                  <div className="flex items-center">
                    {fareRules.changeBeforeDeparture.allowed ? (
                      <Badge 
                        variant="outline" 
                        className={`ml-2 ${fareRules.changeBeforeDeparture.fee === 0 ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}`}
                      >
                        {fareRules.changeBeforeDeparture.fee === 0 ? 
                          'Free' : 
                          `${fareRules.changeBeforeDeparture.fee} ${fareRules.changeBeforeDeparture.currency}`}
                      </Badge>
                    ) : (
                      <Badge variant="destructive">Not allowed</Badge>
                    )}
                  </div>
                </div>
              )}
              
              {/* Change after departure */}
              {fareRules.changeAfterDeparture !== undefined && (
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm">Changes after departure</p>
                    {fareRules.changeAfterDeparture.conditions && (
                      <p className="text-xs text-muted-foreground">{fareRules.changeAfterDeparture.conditions}</p>
                    )}
                  </div>
                  <div className="flex items-center">
                    {fareRules.changeAfterDeparture.allowed ? (
                      <Badge 
                        variant="outline" 
                        className={`ml-2 ${fareRules.changeAfterDeparture.fee === 0 ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}`}
                      >
                        {fareRules.changeAfterDeparture.fee === 0 ? 
                          'Free' : 
                          `${fareRules.changeAfterDeparture.fee} ${fareRules.changeAfterDeparture.currency}`}
                      </Badge>
                    ) : (
                      <Badge variant="destructive">Not allowed</Badge>
                    )}
                  </div>
                </div>
              )}
              
              {/* Change fee general indicator if specific cases aren't provided */}
              {fareRules.changeFee !== undefined && 
                fareRules.changeBeforeDeparture === undefined && 
                fareRules.changeAfterDeparture === undefined && (
                <div className="flex items-center justify-between">
                  <p className="text-sm">Change fee applies</p>
                  <div className="ml-2">
                    {fareRules.changeFee ? (
                      <Badge variant="outline">Yes</Badge>
                    ) : (
                      <Badge variant="outline" className="bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400">No</Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Cancellation Rules */}
          <div className="rounded-md border p-3">
            <h3 className="text-sm font-medium">Cancellation & Refunds</h3>
            
            <div className="mt-2 space-y-3">
              {/* Refundability general indicator */}
              {fareRules.refundable !== undefined && (
                <div className="flex items-center justify-between">
                  <p className="text-sm">Refundable ticket</p>
                  <div className="ml-2">
                    {fareRules.refundable ? (
                      <Badge variant="outline" className="bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                        <Check className="mr-1 h-3 w-3" />
                        Yes
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                        <X className="mr-1 h-3 w-3" />
                        No
                      </Badge>
                    )}
                  </div>
                </div>
              )}
              
              {/* Cancellation before departure */}
              {fareRules.cancelBeforeDeparture !== undefined && (
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm">Cancellation before departure</p>
                    {fareRules.cancelBeforeDeparture.conditions && (
                      <p className="text-xs text-muted-foreground">{fareRules.cancelBeforeDeparture.conditions}</p>
                    )}
                  </div>
                  <div className="flex items-center">
                    {fareRules.cancelBeforeDeparture.allowed ? (
                      <Badge 
                        variant="outline" 
                        className={`ml-2 ${fareRules.cancelBeforeDeparture.fee === 0 ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}`}
                      >
                        {fareRules.cancelBeforeDeparture.refundPercentage ? 
                          `${fareRules.cancelBeforeDeparture.refundPercentage}% refund` : 
                          (fareRules.cancelBeforeDeparture.fee === 0 ? 
                            'Free' : 
                            `${fareRules.cancelBeforeDeparture.fee} ${fareRules.cancelBeforeDeparture.currency}`)}
                      </Badge>
                    ) : (
                      <Badge variant="destructive">Not allowed</Badge>
                    )}
                  </div>
                </div>
              )}
              
              {/* Cancellation after departure */}
              {fareRules.cancelAfterDeparture !== undefined && (
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm">Cancellation after departure</p>
                    {fareRules.cancelAfterDeparture.conditions && (
                      <p className="text-xs text-muted-foreground">{fareRules.cancelAfterDeparture.conditions}</p>
                    )}
                  </div>
                  <div className="flex items-center">
                    {fareRules.cancelAfterDeparture.allowed ? (
                      <Badge 
                        variant="outline" 
                        className={`ml-2 ${fareRules.cancelAfterDeparture.fee === 0 ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}`}
                      >
                        {fareRules.cancelAfterDeparture.refundPercentage ? 
                          `${fareRules.cancelAfterDeparture.refundPercentage}% refund` : 
                          (fareRules.cancelAfterDeparture.fee === 0 ? 
                            'Free' : 
                            `${fareRules.cancelAfterDeparture.fee} ${fareRules.cancelAfterDeparture.currency}`)}
                      </Badge>
                    ) : (
                      <Badge variant="destructive">Not allowed</Badge>
                    )}
                  </div>
                </div>
              )}
              
              {/* No-show policy */}
              {fareRules.noShow !== undefined && (
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm">No-show policy</p>
                    {fareRules.noShow.conditions && (
                      <p className="text-xs text-muted-foreground">{fareRules.noShow.conditions}</p>
                    )}
                  </div>
                  <div className="flex items-center">
                    {fareRules.noShow.refundable ? (
                      <Badge 
                        variant="outline" 
                        className={fareRules.noShow.fee === 0 ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}
                      >
                        {fareRules.noShow.refundPercentage ? 
                          `${fareRules.noShow.refundPercentage}% refund` : 
                          (fareRules.noShow.fee === 0 ? 
                            'Refundable' : 
                            `Fee: ${fareRules.noShow.fee} ${fareRules.noShow.currency}`)}
                      </Badge>
                    ) : (
                      <Badge variant="destructive">Non-refundable</Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Additional Notes/Restrictions */}
          {fareRules.additionalRestrictions && fareRules.additionalRestrictions.length > 0 && (
            <div className="rounded-md border p-3">
              <h3 className="flex items-center text-sm font-medium">
                <AlertCircle className="mr-2 h-4 w-4" />
                Additional Restrictions
              </h3>
              
              <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
                {fareRules.additionalRestrictions.map((restriction, index) => (
                  <li key={index}>{restriction}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
