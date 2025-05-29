import { useState } from 'react'
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
  Briefcase
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { FlightOffer } from "@/types/flight-api"

interface EnhancedFlightCardProps {
  flight: FlightOffer
  showExtendedDetails?: boolean
}

export function EnhancedFlightCard({ flight, showExtendedDetails = false }: EnhancedFlightCardProps) {
  const [expanded, setExpanded] = useState(showExtendedDetails)
  
  // Helper to format datetime (extract only time part)
  const formatTime = (datetime: string) => {
    try {
      // Handle the unusual format with T in the middle
      if (datetime.includes('T')) {
        return datetime.split('T')[1].substring(0, 5);
      }
      return new Date(datetime).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    } catch (e) {
      return datetime;
    }
  };

  // Extract airport city name from airportName if available
  const getCity = (airportName?: string, airport?: string) => {
    if (!airportName) return airport || '';
    
    // Try to extract city from format like "New York J F Kennedy International Apt, US"
    const parts = airportName.split(',');
    if (parts.length > 0) {
      // Further extract just the city name (not the airport name)
      const cityAndAirport = parts[0].trim();
      const cityMatch = cityAndAirport.match(/^([A-Za-z\s]+)/);
      return cityMatch ? cityMatch[1].trim() : cityAndAirport;
    }
    
    return airportName;
  };

  return (
    <Card className="overflow-hidden transition-all hover:shadow-md">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto]">
          {/* Flight Details */}
          <div className="p-4 md:p-6">
            <div className="mb-4 flex items-center">
              <div className="flex items-center">
                <Image
                  src={flight.airline.logo || "/placeholder.svg"}
                  alt={flight.airline.name}
                  width={40}
                  height={40}
                  className="mr-3 rounded-full"
                />
                <div>
                  <p className="font-medium">{flight.airline.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {flight.airline.code} {flight.airline.flightNumber}
                  </p>
                </div>
              </div>

              {flight.stops === 0 && (
                <Badge variant="outline" className="ml-auto">
                  Direct
                </Badge>
              )}

              {flight.stops > 0 && (
                <Badge variant="outline" className="ml-auto">
                  {flight.stops} {flight.stops === 1 ? "stop" : "stops"}
                </Badge>
              )}
            </div>

            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
              {/* Departure */}
              <div>
                <p className="text-2xl font-bold">{formatTime(flight.departure.datetime)}</p>
                <p className="text-sm font-medium">{flight.departure.airport}</p>
                <p className="text-xs text-muted-foreground">{getCity(flight.departure.airportName, flight.departure.airport)}</p>
                {flight.departure.terminal && (
                  <p className="text-xs text-muted-foreground">Terminal {flight.departure.terminal}</p>
                )}
              </div>

              {/* Flight Path Visualization */}
              <div className="flex flex-col items-center">
                <p className="text-xs font-medium text-muted-foreground">{flight.duration}</p>
                <div className="relative my-2 w-full">
                  <Separator className="absolute top-1/2 h-[2px] w-full -translate-y-1/2" />

                  {flight.stops === 0 && <ArrowRight className="relative mx-auto h-4 w-4 bg-background" />}

                  {flight.stops > 0 && flight.stopDetails && (
                    <div className="relative flex w-full items-center justify-center space-x-1">
                      <div className="h-2 w-2 rounded-full bg-primary"></div>
                      {flight.stopDetails.map((stop, index) => (
                        <div key={index} className="flex items-center">
                          <div className="text-xs font-medium text-muted-foreground">{stop}</div>
                          <div className="h-2 w-2 rounded-full bg-primary"></div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Arrival */}
              <div className="text-right">
                <p className="text-2xl font-bold">{formatTime(flight.arrival.datetime)}</p>
                <p className="text-sm font-medium">{flight.arrival.airport}</p>
                <p className="text-xs text-muted-foreground">{getCity(flight.arrival.airportName, flight.arrival.airport)}</p>
                {flight.arrival.terminal && (
                  <p className="text-xs text-muted-foreground">Terminal {flight.arrival.terminal}</p>
                )}
              </div>
            </div>

            {/* Stop Details */}
            {flight.stops > 0 && flight.stopDetails && (
              <div className="mt-3 rounded-md bg-muted p-2 text-xs">
                <p className="font-medium">
                  {flight.stops === 1 ? "Connection" : "Connections"}:
                  {flight.stopDetails.map((stop, index) => (
                    <span key={index}>
                      {" "}
                      {stop} {index < flight.stopDetails!.length - 1 ? "," : ""}
                    </span>
                  ))}
                </p>
              </div>
            )}

            {/* Enhanced Aircraft Information */}
            {flight.aircraft && (
              <div className="mt-2 text-xs text-muted-foreground">
                <span className="font-medium">Aircraft:</span> {flight.aircraft.name} ({flight.aircraft.code})
              </div>
            )}

            {/* Fare Family Information */}
            {flight.fare && (
              <div className="mt-2">
                <Badge variant="secondary" className="font-medium">
                  {flight.fare.fareFamily || flight.fare.fareName || flight.fare.fareClass}
                </Badge>
              </div>
            )}

            {/* Additional Info */}
            <div className="mt-4 flex items-center text-xs text-muted-foreground">
              <div className="flex items-center">
                <Luggage className="mr-1 h-3 w-3" />
                <span>{flight.baggage?.carryOn?.description || "Carry-on included"}</span>
              </div>
              <div className="ml-4 flex items-center">
                <Clock className="mr-1 h-3 w-3" />
                <span>On-time performance: 92%</span>
              </div>
              <div className="ml-auto">
                <span className="font-medium text-foreground">{flight.seatsAvailable} seats left</span>
              </div>
            </div>
            
            {/* Additional Services Icons */}
            {flight.additionalServices && (
              <div className="mt-2 flex space-x-3 text-xs text-muted-foreground">
                {flight.additionalServices.wifiAvailable && (
                  <div className="flex items-center">
                    <Wifi className="mr-1 h-3 w-3" />
                    <span>WiFi</span>
                  </div>
                )}
                {flight.additionalServices.powerOutlets && (
                  <div className="flex items-center">
                    <Power className="mr-1 h-3 w-3" />
                    <span>Power</span>
                  </div>
                )}
                {flight.additionalServices.entertainmentSystem && (
                  <div className="flex items-center">
                    <Tv className="mr-1 h-3 w-3" />
                    <span>Entertainment</span>
                  </div>
                )}
                {flight.additionalServices.meals?.available && (
                  <div className="flex items-center">
                    <Utensils className="mr-1 h-3 w-3" />
                    <span>{flight.additionalServices.meals.complimentary ? "Meals included" : "Meals for purchase"}</span>
                  </div>
                )}
              </div>
            )}
            
            {/* Toggle for expanded view */}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setExpanded(!expanded)} 
              className="mt-4 w-full justify-between"
            >
              {expanded ? "Hide details" : "Show more details"}
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            
            {/* Expanded Details Section */}
            {expanded && (
              <div className="mt-4 border-t pt-4">
                <Tabs defaultValue="segments">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="segments">Segments</TabsTrigger>
                    <TabsTrigger value="fare">Fare Details</TabsTrigger>
                    <TabsTrigger value="baggage">Baggage</TabsTrigger>
                    <TabsTrigger value="services">Services</TabsTrigger>
                  </TabsList>
                  
                  {/* Segments Tab */}
                  <TabsContent value="segments" className="mt-4">
                    {flight.segments?.map((segment, index) => (
                      <div key={index} className="mb-4 rounded-md border p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Image
                              src={segment.airline.logo || `/airlines/${segment.airline.code.toLowerCase()}.png`}
                              alt={segment.airline.name}
                              width={24}
                              height={24}
                              className="mr-2 rounded-full"
                            />
                            <span className="text-sm font-medium">
                              {segment.airline.name} {segment.airline.flightNumber}
                            </span>
                          </div>
                          <span className="text-xs text-muted-foreground">{segment.duration}</span>
                        </div>
                        
                        <div className="mt-2 grid grid-cols-2 gap-2">
                          <div>
                            <p className="text-sm font-bold">{formatTime(segment.departure.datetime)}</p>
                            <p className="text-xs">{segment.departure.airport} {segment.departure.terminal && `Terminal ${segment.departure.terminal}`}</p>
                            <p className="text-xs text-muted-foreground">{getCity(segment.departure.airportName, segment.departure.airport)}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-bold">{formatTime(segment.arrival.datetime)}</p>
                            <p className="text-xs">{segment.arrival.airport} {segment.arrival.terminal && `Terminal ${segment.arrival.terminal}`}</p>
                            <p className="text-xs text-muted-foreground">{getCity(segment.arrival.airportName, segment.arrival.airport)}</p>
                          </div>
                        </div>
                        
                        {segment.aircraft && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            Aircraft: {segment.aircraft.name} ({segment.aircraft.code})
                          </p>
                        )}
                        
                        {segment.operatingAirline && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            Operated by: {segment.operatingAirline.name}
                          </p>
                        )}
                      </div>
                    ))}
                  </TabsContent>
                  
                  {/* Fare Details Tab */}
                  <TabsContent value="fare" className="mt-4">
                    <div className="space-y-4">
                      {flight.fare && (
                        <div>
                          <h4 className="text-sm font-medium">Fare Information</h4>
                          <div className="mt-2 rounded-md border p-3">
                            <p className="text-sm">
                              <span className="font-medium">Fare Type:</span> {flight.fare.fareName || flight.fare.fareFamily || flight.fare.fareClass}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Fare Basis Code: {flight.fare.fareBasisCode}
                            </p>
                            
                            {flight.fare.rules && (
                              <div className="mt-2 space-y-2">
                                <h5 className="text-xs font-medium">Change & Cancellation Rules</h5>
                                
                                {flight.fare.rules.changeBeforeDeparture && (
                                  <div className="flex items-center justify-between text-xs">
                                    <span>Change before departure:</span>
                                    <span className={flight.fare.rules.changeBeforeDeparture.fee === 0 ? "text-green-600" : ""}>
                                      {flight.fare.rules.changeBeforeDeparture.allowed ? 
                                        (flight.fare.rules.changeBeforeDeparture.fee === 0 ? 
                                          "Allowed (free)" : 
                                          `${flight.fare.rules.changeBeforeDeparture.fee} ${flight.fare.rules.changeBeforeDeparture.currency}`) : 
                                        "Not allowed"}
                                    </span>
                                  </div>
                                )}
                                
                                {flight.fare.rules.changeAfterDeparture && (
                                  <div className="flex items-center justify-between text-xs">
                                    <span>Change after departure:</span>
                                    <span>
                                      {flight.fare.rules.changeAfterDeparture.allowed ? 
                                        (flight.fare.rules.changeAfterDeparture.fee === 0 ? 
                                          "Allowed (free)" : 
                                          `${flight.fare.rules.changeAfterDeparture.fee} ${flight.fare.rules.changeAfterDeparture.currency}`) : 
                                        "Not allowed"}
                                    </span>
                                  </div>
                                )}
                                
                                {flight.fare.rules.refundable !== undefined && (
                                  <div className="flex items-center justify-between text-xs">
                                    <span>Refundable:</span>
                                    <span className={flight.fare.rules.refundable ? "text-green-600" : ""}>
                                      {flight.fare.rules.refundable ? "Yes" : "No"}
                                    </span>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {flight.priceBreakdown && (
                        <div>
                          <h4 className="text-sm font-medium">Price Breakdown</h4>
                          <div className="mt-2 rounded-md border p-3">
                            <div className="space-y-1 text-sm">
                              <div className="flex justify-between">
                                <span>Base fare</span>
                                <span>{flight.priceBreakdown.baseFare} {flight.priceBreakdown.currency}</span>
                              </div>
                              <div className="flex justify-between text-muted-foreground">
                                <span>Taxes</span>
                                <span>{flight.priceBreakdown.taxes} {flight.priceBreakdown.currency}</span>
                              </div>
                              <div className="flex justify-between text-muted-foreground">
                                <span>Fees</span>
                                <span>{flight.priceBreakdown.fees} {flight.priceBreakdown.currency}</span>
                              </div>
                              {flight.priceBreakdown.surcharges && flight.priceBreakdown.surcharges > 0 && (
                                <div className="flex justify-between text-muted-foreground">
                                  <span>Surcharges</span>
                                  <span>{flight.priceBreakdown.surcharges} {flight.priceBreakdown.currency}</span>
                                </div>
                              )}
                              {flight.priceBreakdown.discounts && flight.priceBreakdown.discounts > 0 && (
                                <div className="flex justify-between text-green-600">
                                  <span>Discounts</span>
                                  <span>-{flight.priceBreakdown.discounts} {flight.priceBreakdown.currency}</span>
                                </div>
                              )}
                              <Separator className="my-2" />
                              <div className="flex justify-between font-medium">
                                <span>Total price</span>
                                <span>{flight.priceBreakdown.totalPrice} {flight.priceBreakdown.currency}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                  
                  {/* Baggage Tab */}
                  <TabsContent value="baggage" className="mt-4">
                    <div className="rounded-md border p-3">
                      <h4 className="text-sm font-medium">Baggage Allowance</h4>
                      
                      <div className="mt-2 space-y-3">
                        <div>
                          <h5 className="text-xs font-medium flex items-center">
                            <Briefcase className="mr-1 h-3 w-3" />
                            Carry-on Baggage
                          </h5>
                          <p className="text-xs text-muted-foreground mt-1">
                            {flight.baggage?.carryOn?.description || "Standard carry-on allowance"}
                          </p>
                          {flight.baggage?.carryOn?.weight && (
                            <p className="text-xs">
                              Weight: {flight.baggage.carryOn.weight.value} {flight.baggage.carryOn.weight.unit}
                            </p>
                          )}
                        </div>
                        
                        {flight.baggage?.checkedBaggage && (
                          <div>
                            <h5 className="text-xs font-medium flex items-center">
                              <Luggage className="mr-1 h-3 w-3" />
                              Checked Baggage
                            </h5>
                            <p className="text-xs text-muted-foreground mt-1">
                              {flight.baggage.checkedBaggage.description || "Standard checked baggage allowance"}
                            </p>
                            {flight.baggage.checkedBaggage.pieces && (
                              <p className="text-xs">
                                Pieces: {flight.baggage.checkedBaggage.pieces}
                              </p>
                            )}
                            {flight.baggage.checkedBaggage.weight && (
                              <p className="text-xs">
                                Weight: {flight.baggage.checkedBaggage.weight.value} {flight.baggage.checkedBaggage.weight.unit}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </TabsContent>
                  
                  {/* Additional Services Tab */}
                  <TabsContent value="services" className="mt-4">
                    {flight.additionalServices && (
                      <div className="rounded-md border p-3 space-y-3">
                        {flight.additionalServices.seatSelection && (
                          <div>
                            <h5 className="text-xs font-medium">Seat Selection</h5>
                            <p className="text-xs mt-1">
                              {flight.additionalServices.seatSelection.description || 
                                (flight.additionalServices.seatSelection.complimentary ? 
                                  "Complimentary seat selection included" : 
                                  `Available for ${flight.additionalServices.seatSelection.cost} ${flight.additionalServices.seatSelection.currency}`)}
                            </p>
                          </div>
                        )}
                        
                        {flight.additionalServices.meals && (
                          <div>
                            <h5 className="text-xs font-medium">Meals</h5>
                            <p className="text-xs mt-1">
                              {flight.additionalServices.meals.description ||
                                (flight.additionalServices.meals.complimentary ? 
                                  "Complimentary meals included" : 
                                  "Meals available for purchase onboard")}
                            </p>
                            {flight.additionalServices.meals.options && flight.additionalServices.meals.options.length > 0 && (
                              <p className="text-xs text-muted-foreground">
                                Options: {flight.additionalServices.meals.options.join(", ")}
                              </p>
                            )}
                          </div>
                        )}
                        
                        {flight.additionalServices.priorityBoarding && (
                          <div>
                            <h5 className="text-xs font-medium">Priority Boarding</h5>
                            <p className="text-xs mt-1">
                              {flight.additionalServices.priorityBoarding.complimentary ? 
                                "Complimentary priority boarding" : 
                                `Available for ${flight.additionalServices.priorityBoarding.cost} ${flight.additionalServices.priorityBoarding.currency}`}
                            </p>
                          </div>
                        )}
                        
                        <div>
                          <h5 className="text-xs font-medium">Onboard Amenities</h5>
                          <div className="mt-1 grid grid-cols-3 gap-2 text-xs">
                            <div className={`flex items-center ${flight.additionalServices.wifiAvailable ? 'text-foreground' : 'text-muted-foreground line-through'}`}>
                              <Wifi className="mr-1 h-3 w-3" />
                              <span>WiFi</span>
                            </div>
                            <div className={`flex items-center ${flight.additionalServices.powerOutlets ? 'text-foreground' : 'text-muted-foreground line-through'}`}>
                              <Power className="mr-1 h-3 w-3" />
                              <span>Power</span>
                            </div>
                            <div className={`flex items-center ${flight.additionalServices.entertainmentSystem ? 'text-foreground' : 'text-muted-foreground line-through'}`}>
                              <Tv className="mr-1 h-3 w-3" />
                              <span>Entertainment</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            )}
          </div>

          {/* Price and CTA */}
          <div className="flex flex-col justify-between border-t bg-muted p-4 md:border-l md:border-t-0">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Price per person</p>
              <p className="text-3xl font-bold">{flight.price} {flight.currency}</p>
              <p className="text-xs text-muted-foreground">Round trip, all taxes included</p>
            </div>

            <div className="mt-4 flex flex-col space-y-2">
              <Link href={`/flights/${flight.id}`}>
                <Button className="w-full">Select</Button>
              </Link>
              <Link href={`/flights/${flight.id}/details`}>
                <Button variant="outline" className="w-full">
                  View Details
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
