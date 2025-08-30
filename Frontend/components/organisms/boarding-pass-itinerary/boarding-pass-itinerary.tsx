"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plane, MapPin, Calendar, Clock, Users, FileText, CreditCard, Luggage } from "lucide-react"
import Image from "next/image"

interface BoardingPassItineraryProps {
  data: any
}

export function BoardingPassItinerary({ data }: BoardingPassItineraryProps) {
  if (!data) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground">Boarding pass data not available</p>
      </div>
    )
  }

  // Get all flight segments (outbound and return)
  const allFlights = [
    ...(data.outboundFlight || []),
    ...(data.returnFlight || [])
  ];

  // Fallback to legacy flights structure if new structure not available
  const flights = allFlights.length > 0 ? allFlights : (data.flights || []);

  // Get final destination from last flight segment
  const firstFlight = flights[0];
  const lastFlight = flights[flights.length - 1];

  return (
    <div className="max-w-4xl mx-auto space-y-6 bg-white print:bg-white">
      {/* Header */}
      <div className="text-center mb-8 print:mb-6">
        <div className="flex items-center justify-center mb-4">
          <Image src="/logo1.png" alt="Rea Travel Logo" width={48} height={48} className="mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-blue-600">FLIGHT ITINERARY</h1>
            <p className="text-lg text-gray-600">E-Ticket & Boarding Information</p>
          </div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg inline-block">
          <p className="text-sm font-medium text-gray-600">Booking Reference</p>
          <p className="text-2xl font-bold text-blue-600">
            {data.bookingInfo?.bookingReference || data.bookingReference || 'N/A'}
          </p>
        </div>
      </div>

      {/* Booking Information */}
      {data.bookingInfo && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Booking Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Order ID</p>
                <p className="font-medium">{data.bookingInfo.orderId}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <p className="font-medium capitalize">{data.bookingInfo.status}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Issue Date</p>
                <p className="font-medium">{data.bookingInfo.issueDateFormatted}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Agency</p>
                <p className="font-medium">{data.bookingInfo.agencyName}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Flight Segments */}
      {flights.length > 0 ? (
        <div className="space-y-4">
          {flights.map((flight: any, index: number) => (
            <Card key={index} className="border-2">
              <CardContent className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold flex items-center gap-2">
                    <Plane className="w-5 h-5" />
                    Flight {index + 1}: {flight.flightNumber}
                  </h3>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Aircraft</p>
                    <p className="font-medium">{flight.aircraft || 'N/A'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                  {/* Departure */}
                  <div className="text-center md:text-left">
                    <h4 className="text-sm font-medium text-muted-foreground mb-2">DEPARTURE</h4>
                    <div className="space-y-1">
                      <p className="text-3xl font-bold">{flight.departure?.airport}</p>
                      <p className="text-sm text-muted-foreground">
                        {flight.departure?.airportName}
                      </p>
                      <div className="flex items-center justify-center md:justify-start gap-2 mt-2">
                        <Calendar className="w-4 h-4" />
                        <span className="font-medium">{flight.departure?.date}</span>
                      </div>
                      <div className="flex items-center justify-center md:justify-start gap-2">
                        <Clock className="w-4 h-4" />
                        <span className="text-lg font-bold">{flight.departure?.time}</span>
                      </div>
                      {flight.departure?.terminal && (
                        <p className="text-sm">Terminal {flight.departure.terminal}</p>
                      )}
                    </div>
                  </div>

                  {/* Flight Info */}
                  <div className="text-center">
                    <div className="flex flex-col items-center">
                      <Plane className="w-8 h-8 text-blue-500 mb-2" />
                      <p className="font-bold text-lg">{flight.airline}</p>
                      <p className="text-sm text-muted-foreground">Flight {flight.flightNumber}</p>
                      {flight.durationFormatted && (
                        <p className="text-sm text-muted-foreground mt-1">Duration: {flight.durationFormatted}</p>
                      )}
                      <p className="text-sm font-medium mt-2">{flight.classOfService || 'Economy'}</p>
                    </div>
                  </div>

                  {/* Arrival */}
                  <div className="text-center md:text-right">
                    <h4 className="text-sm font-medium text-muted-foreground mb-2">ARRIVAL</h4>
                    <div className="space-y-1">
                      <p className="text-3xl font-bold">{flight.arrival?.airport}</p>
                      <p className="text-sm text-muted-foreground">
                        {flight.arrival?.airportName}
                      </p>
                      <div className="flex items-center justify-center md:justify-end gap-2 mt-2">
                        <Calendar className="w-4 h-4" />
                        <span className="font-medium">{flight.arrival?.date}</span>
                      </div>
                      <div className="flex items-center justify-center md:justify-end gap-2">
                        <Clock className="w-4 h-4" />
                        <span className="text-lg font-bold">{flight.arrival?.time}</span>
                      </div>
                      {flight.arrival?.terminal && (
                        <p className="text-sm">Terminal {flight.arrival.terminal}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Connection indicator */}
                {index < flights.length - 1 && (
                  <div className="mt-4 pt-4 border-t border-dashed border-gray-300">
                    <p className="text-center text-sm text-muted-foreground">
                      Connection at {flight.arrival?.airport} • Proceed to gate for next flight
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center p-8">
          <p className="text-muted-foreground">No flight information available</p>
        </div>
      )}

      {/* Passenger Information */}
      {data.passengers && data.passengers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Passenger Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.passengers.map((passenger: any, index: number) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Full Name</p>
                      <p className="font-bold text-lg">
                        {passenger.fullName || `${passenger.firstName || ''} ${passenger.lastName || ''}`.trim()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Passenger Type</p>
                      <p className="font-medium">{passenger.passengerTypeLabel || 'Adult'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Document</p>
                      <p className="font-medium">{passenger.documentNumber || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Ticket Number</p>
                      <p className="font-mono text-sm">{passenger.ticketNumber || 'N/A'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pricing Summary */}
      {data.pricing && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="w-5 h-5" />
              Payment Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-lg font-medium">Total Amount Paid</span>
                <span className="text-2xl font-bold text-green-600">
                  {data.pricing.formattedTotal}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Payment Method: {data.pricing.paymentMethodLabel}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Baggage Information */}
      {data.baggageAllowance && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Luggage className="w-5 h-5" />
              Baggage Allowance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.baggageAllowance.checkedBagAllowance && (
                <div className="p-3 border rounded-lg">
                  <h4 className="font-medium mb-2">Checked Baggage</h4>
                  {data.baggageAllowance.checkedBagAllowance.pieces !== null && (
                    <p className="text-sm">Allowed Pieces: {data.baggageAllowance.checkedBagAllowance.pieces}</p>
                  )}
                  {data.baggageAllowance.checkedBagAllowance.description && (
                    <p className="text-sm text-muted-foreground">{data.baggageAllowance.checkedBagAllowance.description}</p>
                  )}
                </div>
              )}
              {data.baggageAllowance.carryOnAllowance && (
                <div className="p-3 border rounded-lg">
                  <h4 className="font-medium mb-2">Carry-On Baggage</h4>
                  {data.baggageAllowance.carryOnAllowance.pieces !== null && (
                    <p className="text-sm">Allowed Pieces: {data.baggageAllowance.carryOnAllowance.pieces}</p>
                  )}
                  {data.baggageAllowance.carryOnAllowance.description && (
                    <p className="text-sm text-muted-foreground">{data.baggageAllowance.carryOnAllowance.description}</p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Additional Services */}
      {data.additionalServices && data.additionalServices.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Additional Services
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.additionalServices.map((service: any, index: number) => (
                <div key={index} className="flex justify-between items-center p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">
                      {service.serviceType === 'MEAL' ? '🍽️' : 
                       service.serviceType === 'SEAT' ? '💺' :
                       service.serviceType === 'BAGGAGE' ? '🧳' : '🔧'} {service.serviceName}
                    </p>
                    <p className="text-sm text-muted-foreground">{service.description}</p>
                    <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                      <span>Passenger: {service.passengerReference}</span>
                      <span>Status: {service.status}</span>
                    </div>
                  </div>
                  {service.price && (
                    <div className="text-right">
                      <p className="font-semibold text-green-600">{service.price.formattedPrice}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Contact Information */}
      {data.contactInfo && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Contact Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Email Address</p>
                <p className="font-medium">{data.contactInfo.email}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Phone Number</p>
                <p className="font-medium">
                  {(() => {
                    const phone = data.contactInfo.phone;
                    if (!phone) return 'N/A';
                    
                    if (typeof phone === 'object' && phone !== null) {
                      if (phone.formatted) {
                        return phone.formatted;
                      }
                      if (phone.countryCode && phone.number) {
                        return `${phone.countryCode} ${phone.number}`;
                      }
                      if (phone.number) {
                        return phone.number;
                      }
                      return 'N/A';
                    }
                    
                    return phone;
                  })()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Important Travel Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Important Travel Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Check-in Requirements</h4>
                <ul className="space-y-1 text-sm">
                  <li>• Arrive 3 hours before international flights</li>
                  <li>• Web check-in available 24 hours before departure</li>
                  <li>• Valid passport required for international travel</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">Baggage Guidelines</h4>
                <ul className="space-y-1 text-sm">
                  <li>• Check weight and size restrictions</li>
                  <li>• Liquid restrictions apply for carry-on</li>
                  <li>• Prohibited items not allowed</li>
                </ul>
              </div>
            </div>
            
            {/* E-Ticket Numbers */}
            {data.ticketNumbers && data.ticketNumbers.length > 0 && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium mb-2">E-Ticket Numbers</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {data.ticketNumbers.map((ticketNumber: string, index: number) => (
                    <p key={index} className="font-mono text-sm bg-white p-2 rounded border">
                      {ticketNumber}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Fare Rules Summary */}
            {data.fareRules && data.fareRules.length > 0 && (
              <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
                <h4 className="font-medium mb-2">Fare Rules Summary</h4>
                <div className="text-xs space-y-1">
                  {data.fareRules.map((fareRule: any, index: number) => (
                    <div key={index}>
                      <span className="font-medium">
                        {fareRule.passengerType === 'ADT' ? 'Adult' : fareRule.passengerType}: 
                      </span>
                      {fareRule.rules.map((rule: any, ruleIndex: number) => (
                        <span key={ruleIndex} className="ml-2">
                          {rule.type}: {rule.currency} {rule.minAmount}-{rule.maxAmount}
                          {ruleIndex < fareRule.rules.length - 1 ? ', ' : ''}
                        </span>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center text-sm text-muted-foreground border-t pt-4 print:mt-8">
        <p>© {new Date().getFullYear()} Rea Travel. All rights reserved.</p>
        <p className="mt-1">For assistance, contact us at support@reatravels.com</p>
      </div>
    </div>
  )
}