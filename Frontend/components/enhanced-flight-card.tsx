"use client"

import { useState, useEffect } from 'react'
import Link from "next/link"
import Image from "next/image"
import { 
  ArrowRight, 
  Clock, 
  Luggage, 
  ChevronDown, 
  ChevronUp, 
  Wifi, 
  Power, 
  Utensils, 
  Tv, 
  Briefcase,
  MapPin,
  Plane,
  Users,
  CreditCard,
  AlertCircle
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { FlightOffer } from "@/types/flight-api"

interface EnhancedFlightCardProps {
  flight: FlightOffer
  showExtendedDetails?: boolean
  searchParams?: {
    adults?: number
    children?: number
    infants?: number
    tripType?: string
    origin?: string
    destination?: string
    departDate?: string
    returnDate?: string
    cabinClass?: string
  }
}

export function EnhancedFlightCard({ flight, showExtendedDetails = false, searchParams }: EnhancedFlightCardProps) {
  // Build query string with search parameters
  const buildFlightUrl = () => {
    const params = new URLSearchParams({ from: 'search' })
    
    if (searchParams) {
      if (searchParams.adults) params.set('adults', searchParams.adults.toString())
      if (searchParams.children) params.set('children', searchParams.children.toString())
      if (searchParams.infants) params.set('infants', searchParams.infants.toString())
      if (searchParams.tripType) params.set('tripType', searchParams.tripType)
      if (searchParams.origin) params.set('origin', searchParams.origin)
      if (searchParams.destination) params.set('destination', searchParams.destination)
      if (searchParams.departDate) params.set('departDate', searchParams.departDate)
      if (searchParams.returnDate) params.set('returnDate', searchParams.returnDate)
      if (searchParams.cabinClass) params.set('cabinClass', searchParams.cabinClass)
    }
    
    return `/flights/${encodeURIComponent(flight.id)}?${params.toString()}`
  }
  const [expanded, setExpanded] = useState(showExtendedDetails)
  
  useEffect(() => {
  }, [flight]);

  // Note: Data formatting is now handled by the backend
  // Frontend components should use FlightOffer data directly

  return (
    <Card className="overflow-hidden transition-all hover:shadow-md">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto]">
          {/* Flight Details */}
          <div className="p-4 md:p-6">
            <div className="mb-4 flex items-center">
              <div className="flex items-center">
                <Image
                  src={flight.airline?.logo || "/placeholder-logo.svg"}
                  alt={flight.airline?.name || "Airline"}
                  width={32}
                  height={32}
                  className="mr-3 rounded"
                />
                <div>
                  <div className="font-semibold text-sm">{flight.airline?.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {flight.segments?.map((segment, index) => (
                      <span key={`flight-${flight.id}-segment-${index}-${segment.airline?.flightNumber || 'unknown'}`}>
                        {segment.airline?.flightNumber}
                        {index < (flight.segments?.length || 0) - 1 && ", "}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
              {flight.fare?.fareFamily && (
                <Badge variant="secondary" className="ml-auto">
                  {flight.fare.fareFamily}
                </Badge>
              )}
            </div>

            {/* Route and Time */}
            <div className="mb-4">
              <div className="flex items-center justify-between">
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {flight.segments?.[0]?.departure?.time || '--:--'}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {flight.segments?.[0]?.departure?.airportName ||
                      flight.segments?.[0]?.departure?.airport}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {flight.segments?.[0]?.departure?.airport}
                  </div>
                </div>
                
                <div className="flex flex-col items-center px-4">
                  <div className="text-xs text-muted-foreground mb-1">
                    {flight.duration}
                  </div>
                  <div className="flex items-center">
                    <div className="h-px bg-border flex-1 w-16"></div>
                    <ArrowRight className="mx-2 h-4 w-4 text-muted-foreground" />
                    <div className="h-px bg-border flex-1 w-16"></div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {flight.segments && flight.segments.length > 1 ? `${flight.segments.length - 1} stop${flight.segments.length > 2 ? 's' : ''}` : 'Direct'}
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {flight.segments?.[flight.segments.length - 1]?.arrival?.time || '--:--'}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {flight.segments?.[flight.segments.length - 1]?.arrival?.airportName ||
                      flight.segments?.[flight.segments.length - 1]?.arrival?.airport || 'Unknown'}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {flight.segments?.[flight.segments.length - 1]?.arrival?.airport}
                  </div>
                </div>
              </div>
            </div>

            {/* Amenities */}
            {flight.additionalServices?.additionalAmenities && flight.additionalServices.additionalAmenities.length > 0 && (
              <div className="mb-4">
                <div className="flex flex-wrap gap-2">
                  {flight.additionalServices.additionalAmenities.map((amenity: string, index: number) => {
                    const getAmenityIcon = (amenity: string) => {
                      switch (amenity.toLowerCase()) {
                        case 'wifi':
                          return <Wifi className="h-3 w-3" />;
                        case 'power':
                          return <Power className="h-3 w-3" />;
                        case 'meal':
                          return <Utensils className="h-3 w-3" />;
                        case 'entertainment':
                          return <Tv className="h-3 w-3" />;
                        default:
                          return <Briefcase className="h-3 w-3" />;
                      }
                    };
                    
                    return (
                      <Badge key={`${amenity}-${index}`} variant="outline" className="text-xs">
                        {getAmenityIcon(amenity)}
                        <span className="ml-1">{amenity}</span>
                      </Badge>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Expandable Details */}
            {expanded && (
              <div className="space-y-4">
                <Separator />
                
                <Tabs defaultValue="segments" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="segments">Flight Details</TabsTrigger>
                    <TabsTrigger value="baggage">Baggage</TabsTrigger>
                    <TabsTrigger value="fare">Fare Rules</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="segments" className="space-y-4">
                    {flight.segments?.map((segment, index) => (
                      <div key={`flight-${flight.id}-detail-segment-${index}-${segment.airline?.flightNumber || 'unknown'}-${segment.departure?.airport || 'unknown'}`} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <Image
                              src={segment.airline?.logo || "/placeholder-logo.svg"}
                              alt={segment.airline?.name || "Airline"}
                              width={24}
                              height={24}
                              className="mr-2 rounded"
                            />
                            <span className="font-medium">{segment.airline?.flightNumber}</span>
                          </div>
                          <Badge variant="outline">{segment.aircraft?.name || segment.aircraft?.code}</Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="font-medium">Departure</div>
                            <div>{segment.departure?.datetime || '--:--'}</div>
                            <div className="text-muted-foreground">
                              {segment.departure?.airportName || segment.departure?.airport || 'Unknown'} ({segment.departure?.airport})
                            </div>
                          </div>
                          <div>
                            <div className="font-medium">Arrival</div>
                            <div>{segment.arrival?.datetime || '--:--'}</div>
                            <div className="text-muted-foreground">
                              {segment.arrival?.airportName || segment.arrival?.airport || 'Unknown'} ({segment.arrival?.airport})
                            </div>
                          </div>
                        </div>
                        
                        <div className="mt-2 text-sm text-muted-foreground">
                          Duration: {segment.duration}
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                  
                  <TabsContent value="baggage">
                    <div className="space-y-2">
                      <div className="flex items-center">
                        <Luggage className="h-4 w-4 mr-2" />
                        <span className="text-sm">Carry-on: {flight.baggage?.carryOn?.description || 'Included'}</span>
                      </div>
                      <div className="flex items-center">
                        <Luggage className="h-4 w-4 mr-2" />
                        <span className="text-sm">Checked: {flight.baggage?.checkedBaggage?.description || 'See fare rules'}</span>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="fare" className="space-y-4">
                    {/* Basic Fare Rules Cards */}
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <span className="font-medium">Refundable</span>
                        </div>
                        <Badge variant={flight.fareRules?.refundable ? "default" : "destructive"}>
                          {flight.fareRules?.refundable ? "Yes" : "No"}
                        </Badge>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <span className="font-medium">Changeable</span>
                        </div>
                        <Badge variant={flight.fareRules?.exchangeable ? "default" : "destructive"}>
                          {flight.fareRules?.exchangeable ? "Yes" : "No"}
                        </Badge>
                      </div>
                    </div>

                    {flight.fareRules?.changeFee && (
                      <div className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <span className="font-medium">Change Fee</span>
                          </div>
                          <Badge variant="outline">{flight.fareRules.changeFee}</Badge>
                        </div>
                      </div>
                    )}
                    
                    {/* Change Policy Before Departure */}
                    {flight.fareRules?.changeBeforeDeparture && (
                      <div className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <span className="font-medium">Change Before Departure</span>
                          </div>
                          <Badge variant={flight.fareRules.changeBeforeDeparture.allowed ? "default" : "destructive"}>
                            {flight.fareRules.changeBeforeDeparture.allowed ? "Allowed" : "Not Allowed"}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-1 gap-2 text-sm mt-2">
                          {flight.fareRules.changeBeforeDeparture.fee && (
                            <div className="text-muted-foreground">
                              <strong>Fee:</strong> {flight.fareRules.changeBeforeDeparture.fee} {flight.fareRules.changeBeforeDeparture.currency}
                            </div>
                          )}
                          {flight.fareRules.changeBeforeDeparture.conditions && (
                            <div className="text-muted-foreground">
                              <strong>Conditions:</strong> {flight.fareRules.changeBeforeDeparture.conditions}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {/* Cancellation Policy Before Departure */}
                    {flight.fareRules?.cancelBeforeDeparture && (
                      <div className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <span className="font-medium">Cancel Before Departure</span>
                          </div>
                          <Badge variant={flight.fareRules.cancelBeforeDeparture.allowed ? "default" : "destructive"}>
                            {flight.fareRules.cancelBeforeDeparture.allowed ? "Allowed" : "Not Allowed"}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-1 gap-2 text-sm mt-2">
                          {flight.fareRules.cancelBeforeDeparture.fee && (
                            <div className="text-muted-foreground">
                              <strong>Fee:</strong> {flight.fareRules.cancelBeforeDeparture.fee} {flight.fareRules.cancelBeforeDeparture.currency}
                            </div>
                          )}
                          {flight.fareRules.cancelBeforeDeparture.refundPercentage && (
                            <div className="text-muted-foreground">
                              <strong>Refund:</strong> {flight.fareRules.cancelBeforeDeparture.refundPercentage}%
                            </div>
                          )}
                          {flight.fareRules.cancelBeforeDeparture.conditions && (
                            <div className="text-muted-foreground">
                              <strong>Conditions:</strong> {flight.fareRules.cancelBeforeDeparture.conditions}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {/* Additional Restrictions */}
                    {flight.fareRules?.additionalRestrictions && flight.fareRules.additionalRestrictions.length > 0 && (
                      <div className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <span className="font-medium">Additional Restrictions</span>
                          </div>
                          <Badge variant="outline">{flight.fareRules.additionalRestrictions.length} restriction{flight.fareRules.additionalRestrictions.length > 1 ? 's' : ''}</Badge>
                        </div>
                        
                        <div className="mt-2 text-sm text-muted-foreground space-y-1">
                          {flight.fareRules.additionalRestrictions.map((restriction, index) => (
                            <div key={index}>• {restriction}</div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Fare Description */}
                    {flight.fareDescription && (
                      <div className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <span className="font-medium">Fare Description</span>
                          </div>
                        </div>
                        
                        <div className="mt-2 text-sm text-muted-foreground">
                          {flight.fareDescription}
                        </div>
                      </div>
                    )}
                      
                    {/* Detailed Penalty Information (if available) */}
                    {flight.penalties && flight.penalties.length > 0 && (
                      <div className="space-y-4">
                        <div className="font-medium text-base">Detailed Penalty Information</div>
                        {flight.penalties.map((penalty, index) => (
                          <div key={index} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center">
                                <span className="font-medium capitalize">{penalty.type}</span>
                              </div>
                              <Badge variant="outline">{penalty.amount} {penalty.currency}</Badge>
                            </div>
                            
                            <div className="grid grid-cols-1 gap-2 text-sm mt-2">
                              <div className="text-muted-foreground">
                                <strong>Application:</strong> {penalty.application}
                              </div>
                              {penalty.remarks && (
                                <div className="text-muted-foreground">
                                  <strong>Remarks:</strong> {penalty.remarks}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            )}

            {/* Toggle Button */}
            <div className="mt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
                className="w-full"
              >
                {expanded ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-2" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-2" />
                    Show More Details
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Price and Book Button */}
          <div className="bg-muted/50 p-4 md:p-6 flex flex-col justify-between min-w-[200px]">
            <div className="text-center mb-4">
              <div className="text-2xl font-bold">
                {flight.priceBreakdown?.currency} {flight.priceBreakdown?.totalPrice || flight.price}
              </div>
              <div className="text-sm text-muted-foreground">
                per person
              </div>
              {flight.priceBreakdown?.baseFare && flight.priceBreakdown.baseFare !== flight.priceBreakdown.totalPrice && (
                <div className="text-xs text-muted-foreground line-through">
                  {flight.priceBreakdown?.currency} {flight.priceBreakdown.baseFare}
                </div>
              )}
            </div>
            
            <Link href={buildFlightUrl()} className="w-full">
              <Button className="w-full">
                Select Flight
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
