"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plane, Calendar, Users, FileText, MapPin, Clock } from "lucide-react"
import Image from "next/image"

interface OfficialItineraryProps {
  data: any
}

export function OfficialItinerary({ data }: OfficialItineraryProps) {
  if (!data) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground">Itinerary data not available</p>
      </div>
    )
  }

  // Get all flight segments for display
  const flights = data.outboundFlight || data.flights || [];

  return (
    <div className="max-w-4xl mx-auto bg-background print:bg-white" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Professional Header */}
      <div className="border-b-2 border-blue-600 pb-6 mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Image src="/logo1.png" alt="Rea Travel" width={60} height={60} />
            <div>
              <h1 className="text-3xl font-bold text-blue-600">REA TRAVEL</h1>
              <p className="text-muted-foreground text-lg">Flight Itinerary & E-Ticket</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Booking Reference</p>
            <p className="text-2xl font-bold text-blue-600">
              {data.bookingInfo?.bookingReference || data.bookingReference || 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Booking Summary Box */}
      <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="font-semibold text-foreground mb-2">BOOKING DETAILS</h3>
            <p className="text-sm text-foreground"><span className="font-medium">Order ID:</span> {data.bookingInfo?.orderId || 'N/A'}</p>
            <p className="text-sm text-foreground"><span className="font-medium">Status:</span> {data.bookingInfo?.status || 'Confirmed'}</p>
            <p className="text-sm text-foreground"><span className="font-medium">Issue Date:</span> {data.bookingInfo?.issueDateFormatted || 'N/A'}</p>
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-2">PASSENGER</h3>
            {data.passengers?.[0] && (
              <>
                <p className="text-sm font-medium text-foreground">{data.passengers[0].fullName || `${data.passengers[0].firstName || ''} ${data.passengers[0].lastName || ''}`.trim()}</p>
                <p className="text-sm text-foreground">{data.passengers[0].passengerTypeLabel || 'Adult'}</p>
                <p className="text-sm text-foreground">Doc: {data.passengers[0].documentNumber || 'N/A'}</p>
              </>
            )}
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-2">TOTAL FARE</h3>
            <p className="text-xl font-bold text-green-600 dark:text-green-400">{data.pricing?.formattedTotal || 'N/A'}</p>
            <p className="text-sm text-foreground">{data.pricing?.paymentMethodLabel || 'Cash'}</p>
          </div>
        </div>
      </div>

      {/* Flight Details Section */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-foreground mb-4 border-b border-border pb-2">FLIGHT DETAILS</h2>
        
        {flights.length > 0 ? (
          <div className="space-y-6">
            {flights.map((flight: any, index: number) => (
              <div key={index} className="border border-border rounded-lg overflow-hidden">
                {/* Flight Header */}
                <div className="bg-muted/50 px-6 py-3 border-b border-border">
                  <div className="flex justify-between items-center">
                    <h3 className="font-bold text-lg text-foreground">
                      Flight {index + 1}: {flight.flightNumber || 'N/A'}
                    </h3>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">{flight.airline || 'N/A'}</p>
                      <p className="text-xs text-muted-foreground">{flight.aircraft || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                {/* Flight Body */}
                <div className="p-6 bg-card">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                    {/* Departure */}
                    <div className="text-center">
                      <h4 className="text-sm font-semibold text-muted-foreground mb-3">DEPARTURE</h4>
                      <div className="space-y-2">
                        <p className="text-3xl font-bold text-blue-600">{flight.departure?.airport || 'N/A'}</p>
                        <p className="text-sm text-muted-foreground max-w-[200px] mx-auto">
                          {flight.departure?.airportName || 'N/A'}
                        </p>
                        <div className="flex items-center justify-center gap-2 mt-3">
                          <Calendar className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium text-foreground">{flight.departure?.date || 'N/A'}</span>
                        </div>
                        <div className="flex items-center justify-center gap-2">
                          <Clock className="w-4 h-4 text-muted-foreground" />
                          <span className="text-xl font-bold text-foreground">{flight.departure?.time || 'N/A'}</span>
                        </div>
                        {flight.departure?.terminal && (
                          <p className="text-sm bg-muted rounded px-2 py-1 inline-block text-foreground">
                            Terminal {flight.departure.terminal}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Flight Route */}
                    <div className="text-center">
                      <div className="flex flex-col items-center">
                        <Plane className="w-8 h-8 text-blue-500 mb-2" />
                        <div className="w-24 h-px bg-border mb-2"></div>
                        {flight.durationFormatted && (
                          <p className="text-sm font-medium text-muted-foreground">{flight.durationFormatted}</p>
                        )}
                        <p className="text-xs text-muted-foreground mt-1">{flight.classOfService || 'Economy'}</p>
                      </div>
                    </div>

                    {/* Arrival */}
                    <div className="text-center">
                      <h4 className="text-sm font-semibold text-muted-foreground mb-3">ARRIVAL</h4>
                      <div className="space-y-2">
                        <p className="text-3xl font-bold text-blue-600">{flight.arrival?.airport || 'N/A'}</p>
                        <p className="text-sm text-muted-foreground max-w-[200px] mx-auto">
                          {flight.arrival?.airportName || 'N/A'}
                        </p>
                        <div className="flex items-center justify-center gap-2 mt-3">
                          <Calendar className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium text-foreground">{flight.arrival?.date || 'N/A'}</span>
                        </div>
                        <div className="flex items-center justify-center gap-2">
                          <Clock className="w-4 h-4 text-muted-foreground" />
                          <span className="text-xl font-bold text-foreground">{flight.arrival?.time || 'N/A'}</span>
                        </div>
                        {flight.arrival?.terminal && (
                          <p className="text-sm bg-muted rounded px-2 py-1 inline-block text-foreground">
                            Terminal {flight.arrival.terminal}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Connection indicator */}
                  {index < flights.length - 1 && (
                    <div className="mt-6 pt-4 border-t border-dashed border-border">
                      <div className="bg-yellow-50 dark:bg-yellow-950/20 rounded p-3 text-center">
                        <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                          ✈️ Connection at {flight.arrival?.airport || 'N/A'}
                        </p>
                        <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                          Please collect your boarding pass for the next flight
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-8 border border-border rounded-lg">
            <p className="text-muted-foreground">No flight information available</p>
          </div>
        )}
      </div>

      {/* Passenger Information */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-foreground mb-4 border-b border-border pb-2">PASSENGER INFORMATION</h2>
        
        {data.passengers && data.passengers.length > 0 ? (
          <div className="border border-border rounded-lg overflow-hidden">
            <div className="bg-muted/50 grid grid-cols-4 gap-4 p-4 text-sm font-semibold text-foreground border-b border-border">
              <div>PASSENGER NAME</div>
              <div>TYPE</div>
              <div>DOCUMENT</div>
              <div>E-TICKET NUMBER</div>
            </div>
            {data.passengers.map((passenger: any, index: number) => (
              <div key={index} className="grid grid-cols-4 gap-4 p-4 border-b border-border last:border-b-0 bg-card">
                <div>
                  <p className="font-medium text-foreground">
                    {passenger.fullName || `${passenger.firstName || ''} ${passenger.lastName || ''}`.trim()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-foreground">{passenger.passengerTypeLabel || 'Adult'}</p>
                </div>
                <div>
                  <p className="text-sm text-foreground">{passenger.documentNumber || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-mono text-foreground">{passenger.ticketNumber || 'N/A'}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-8 border border-border rounded-lg">
            <p className="text-muted-foreground">No passenger information available</p>
          </div>
        )}
      </div>

      {/* Additional Information Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        
        {/* Baggage Allowance */}
        {data.baggageAllowance && (
          <div>
            <h2 className="text-xl font-bold text-foreground mb-4 border-b border-border pb-2">BAGGAGE ALLOWANCE</h2>
            <div className="space-y-4">
              {data.baggageAllowance.checkedBagAllowance && (
                <div className="border border-border rounded-lg p-4 bg-card">
                  <h3 className="font-semibold mb-2 text-foreground">Checked Baggage</h3>
                  {data.baggageAllowance.checkedBagAllowance.pieces !== null && (
                    <p className="text-sm text-foreground">• Pieces: {data.baggageAllowance.checkedBagAllowance.pieces}</p>
                  )}
                  {data.baggageAllowance.checkedBagAllowance.description && (
                    <p className="text-sm text-muted-foreground">• {data.baggageAllowance.checkedBagAllowance.description}</p>
                  )}
                </div>
              )}
              {data.baggageAllowance.carryOnAllowance && (
                <div className="border border-border rounded-lg p-4 bg-card">
                  <h3 className="font-semibold mb-2 text-foreground">Carry-On Baggage</h3>
                  {data.baggageAllowance.carryOnAllowance.pieces !== null && (
                    <p className="text-sm text-foreground">• Pieces: {data.baggageAllowance.carryOnAllowance.pieces}</p>
                  )}
                  {data.baggageAllowance.carryOnAllowance.description && (
                    <p className="text-sm text-muted-foreground">• {data.baggageAllowance.carryOnAllowance.description}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Contact Information */}
        <div>
          <h2 className="text-xl font-bold text-foreground mb-4 border-b border-border pb-2">CONTACT INFORMATION</h2>
          <div className="border border-border rounded-lg p-4 space-y-3 bg-card">
            <div>
              <p className="font-medium text-foreground">Email Address</p>
              <p className="text-sm text-muted-foreground">{data.contactInfo?.email || 'N/A'}</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Phone Number</p>
              <p className="text-sm text-muted-foreground">
                {(() => {
                  const phone = data.contactInfo?.phone;
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
        </div>
      </div>

      {/* Additional Services */}
      {data.additionalServices && data.additionalServices.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-bold text-foreground mb-4 border-b border-border pb-2">ADDITIONAL SERVICES</h2>
          
          <div className="space-y-4">
            {/* Group services by type */}
            {['MEAL', 'SEAT', 'BAGGAGE', 'OTHER'].map(serviceType => {
              const servicesOfType = data.additionalServices.filter((s: any) => s.serviceType === serviceType);
              if (servicesOfType.length === 0) return null;

              return (
                <div key={serviceType} className="border border-border rounded-lg p-4 bg-card">
                  <h3 className="font-semibold mb-3 text-foreground">
                    {serviceType === 'MEAL' ? '🍽️ Meal Services' : 
                     serviceType === 'SEAT' ? '💺 Seat Services' :
                     serviceType === 'BAGGAGE' ? '🧳 Baggage Services' : 
                     '🔧 Other Services'}
                  </h3>
                  
                  <div className="space-y-3">
                    {servicesOfType.map((service: any, index: number) => (
                      <div key={index} className="flex justify-between items-start p-3 bg-muted/30 rounded border border-border">
                        <div className="flex-1">
                          <p className="font-medium text-foreground">{service.serviceName}</p>
                          <p className="text-sm text-muted-foreground mt-1">{service.description}</p>
                          <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                            <span>Passenger: {service.passengerReference}</span>
                            <span>Flight: {service.segmentReference}</span>
                            <span className="capitalize">Status: {service.status}</span>
                          </div>
                        </div>
                        {service.price && (
                          <div className="text-right ml-4">
                            <p className="font-semibold text-foreground">{service.price.formattedPrice}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Important Travel Information */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-foreground mb-4 border-b border-border pb-2">IMPORTANT TRAVEL INFORMATION</h2>
        <div className="border border-border rounded-lg p-6 bg-card">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3 text-foreground">Check-in Requirements</h3>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Arrive 3 hours before international flights</li>
                <li>• Arrive 2 hours before domestic flights</li>
                <li>• Web check-in available 24 hours before departure</li>
                <li>• Valid passport required for international travel</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-3 text-foreground">Baggage Guidelines</h3>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Check weight and size restrictions</li>
                <li>• Liquid restrictions apply for carry-on</li>
                <li>• Prohibited items not allowed</li>
                <li>• Label all baggage with contact information</li>
              </ul>
            </div>
          </div>
          
          {/* E-Ticket Numbers */}
          {data.ticketNumbers && data.ticketNumbers.length > 0 && (
            <div className="mt-6 pt-6 border-t border-border">
              <h3 className="font-semibold mb-3 text-foreground">E-Ticket Numbers</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {data.ticketNumbers.map((ticketNumber: string, index: number) => (
                  <div key={index} className="bg-muted p-2 rounded font-mono text-sm text-foreground">
                    {ticketNumber}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fare Rules Summary */}
          {data.fareRules && data.fareRules.length > 0 && (
            <div className="mt-6 pt-6 border-t border-border">
              <h3 className="font-semibold mb-3 text-foreground">Fare Rules & Penalties</h3>
              <div className="space-y-2 text-sm">
                {data.fareRules.map((fareRule: any, index: number) => (
                  <div key={index} className="bg-yellow-50 dark:bg-yellow-950/20 p-3 rounded border border-yellow-200 dark:border-yellow-800">
                    <p className="font-medium mb-1 text-foreground">
                      {fareRule.passengerType === 'ADT' ? 'Adult' : fareRule.passengerType === 'CHD' ? 'Child' : fareRule.passengerType === 'INF' ? 'Infant' : fareRule.passengerType} Passenger
                    </p>
                    {fareRule.rules.map((rule: any, ruleIndex: number) => (
                      <div key={ruleIndex} className="flex justify-between text-xs">
                        <span className="text-foreground">{rule.type} Fee ({rule.application})</span>
                        <span className={rule.allowed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                          {rule.allowed ? `${rule.currency} ${rule.minAmount}-${rule.maxAmount}` : 'Not Allowed'}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center border-t border-border pt-6 text-sm text-muted-foreground">
        <p className="font-medium text-foreground">REA TRAVEL</p>
        <p>© {new Date().getFullYear()} Rea Travel. All rights reserved.</p>
        <p className="mt-2">For assistance, contact us at support@reatravels.com | +254 729 582 121</p>
      </div>
    </div>
  )
}