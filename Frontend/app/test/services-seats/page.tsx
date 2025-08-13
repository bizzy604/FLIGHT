"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { ServiceSelection, SeatSelection } from "@/components/molecules"
import { Badge } from "@/components/ui/badge"

// Mock FlightPriceRS data for testing
const mockFlightPriceResponse = {
  "ShoppingResponseID": {
    "ResponseID": {
      "value": "test-shopping-response-123"
    }
  },
  "PricedFlightOffers": {
    "PricedFlightOffer": [
      {
        "OfferID": {
          "value": "test-offer-123",
          "Owner": "SN",
          "Channel": "NDC"
        },
        "OfferPrice": [
          {
            "RequestedDate": {
              "PriceDetail": {
                "TotalAmount": {
                  "SimpleCurrencyPrice": {
                    "value": 750.00,
                    "Code": "USD"
                  }
                },
                "BaseAmount": {
                  "value": 600.00,
                  "Code": "USD"
                },
                "Taxes": {
                  "Total": {
                    "value": 150.00,
                    "Code": "USD"
                  }
                }
              },
              "Associations": [
                {
                  "AssociatedTraveler": {
                    "TravelerReferences": ["PAX1"]
                  }
                }
              ]
            },
            "OfferItemID": "test-offer-item-123"
          }
        ]
      }
    ]
  },
  "DataLists": {
    "AnonymousTravelerList": {
      "AnonymousTraveler": [
        {
          "ObjectKey": "PAX1",
          "PTC": {
            "value": "ADT"
          }
        }
      ]
    },
    "FlightSegmentList": {
      "FlightSegment": [
        {
          "SegmentKey": "SEG1",
          "Departure": {
            "AirportCode": {"value": "JFK"},
            "Date": "2025-12-01",
            "Time": "10:00"
          },
          "Arrival": {
            "AirportCode": {"value": "LAX"},
            "Date": "2025-12-01", 
            "Time": "13:00"
          },
          "MarketingCarrier": {
            "AirlineID": {"value": "SN"},
            "FlightNumber": {"value": "123"}
          }
        }
      ]
    }
  }
}

// Mock passengers for testing
const mockPassengers = [
  {
    objectKey: "PAX1",
    name: "John Doe",
    type: "adult"
  }
]

export default function ServicesSeatsTestPage() {
  const [selectedServices, setSelectedServices] = useState<string[]>([])
  const [selectedOutboundSeats, setSelectedOutboundSeats] = useState<string[]>([])
  const [selectedReturnSeats, setSelectedReturnSeats] = useState<string[]>([])
  const [testResults, setTestResults] = useState<string[]>([])
  const [apiTestStatus, setApiTestStatus] = useState<string>("")

  const addTestResult = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setTestResults(prev => [`[${timestamp}] ${message}`, ...prev.slice(0, 9)]) // Keep last 10 results
  }

  const clearTestResults = () => {
    setTestResults([])
  }

  const resetSelections = () => {
    setSelectedServices([])
    setSelectedOutboundSeats([])
    setSelectedReturnSeats([])
    addTestResult("All selections reset")
  }

  // Store real flight price data in sessionStorage on component mount
  useEffect(() => {
    // Store flight price response for components to use
    sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(mockFlightPriceResponse))
    addTestResult("Flight price data stored in sessionStorage")
  }, [])

  // Test API endpoints directly
  const testServiceListAPI = async () => {
    try {
      setApiTestStatus("Testing ServiceList API...")
      addTestResult("🔄 Testing ServiceList API call...")
      
      const response = await fetch('/api/verteil/service-list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          flight_price_response: mockFlightPriceResponse,
          selected_offer_index: 0
        })
      })

      if (response.ok) {
        const data = await response.json()
        setApiTestStatus("✅ ServiceList API call successful")
        addTestResult(`✅ ServiceList API success: Found ${Object.keys(data?.services || {}).length} service categories`)
        console.log('ServiceList Response:', data)
      } else {
        const error = await response.text()
        setApiTestStatus(`❌ ServiceList API failed: ${response.status}`)
        addTestResult(`❌ ServiceList API failed: ${error}`)
      }
    } catch (error) {
      setApiTestStatus(`❌ ServiceList API error: ${error}`)
      addTestResult(`❌ ServiceList API error: ${error}`)
    }
  }

  const testSeatAvailabilityAPI = async () => {
    try {
      setApiTestStatus("Testing SeatAvailability API...")
      addTestResult("🔄 Testing SeatAvailability API call...")
      
      const response = await fetch('/api/verteil/seat-availability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          flight_price_response: mockFlightPriceResponse,
          selected_offer_index: 0
        })
      })

      if (response.ok) {
        const data = await response.json()
        setApiTestStatus("✅ SeatAvailability API call successful")
        addTestResult(`✅ SeatAvailability API success: Found ${data?.seatMaps?.length || 0} seat maps`)
        console.log('SeatAvailability Response:', data)
      } else {
        const error = await response.text()
        setApiTestStatus(`❌ SeatAvailability API failed: ${response.status}`)
        addTestResult(`❌ SeatAvailability API failed: ${error}`)
      }
    } catch (error) {
      setApiTestStatus(`❌ SeatAvailability API error: ${error}`)
      addTestResult(`❌ SeatAvailability API error: ${error}`)
    }
  }

  const handleServiceChange = (updatedServices: string[]) => {
    setSelectedServices(updatedServices)
    addTestResult(`Services updated: ${updatedServices.join(", ") || "None selected"}`)
  }

  const handleSeatChange = (flightType: 'outbound' | 'return', updatedSeats: string[]) => {
    if (flightType === 'outbound') {
      setSelectedOutboundSeats(updatedSeats)
      addTestResult(`Outbound seats updated: ${updatedSeats.join(", ") || "None selected"}`)
    } else {
      setSelectedReturnSeats(updatedSeats)
      addTestResult(`Return seats updated: ${updatedSeats.join(", ") || "None selected"}`)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Services & Seats Test Page</h1>
          <p className="text-muted-foreground">
            Test the ServiceSelection and SeatSelection components with real backend integration
          </p>
        </div>

        {/* Control Panel */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Test Controls</CardTitle>
            <CardDescription>Manage test state and view results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4 items-center mb-4">
              <Button onClick={resetSelections} variant="outline">
                Reset All Selections
              </Button>
              <Button onClick={clearTestResults} variant="outline">
                Clear Test Results
              </Button>
              <Button onClick={testServiceListAPI} variant="default">
                Test ServiceList API
              </Button>
              <Button onClick={testSeatAvailabilityAPI} variant="default">
                Test SeatAvailability API
              </Button>
            </div>
            <div className="mb-4">
              {apiTestStatus && (
                <div className="p-2 bg-muted rounded text-sm">
                  <strong>API Test Status:</strong> {apiTestStatus}
                </div>
              )}
            </div>
            <div className="flex gap-2 items-center">
              <span className="text-sm font-medium">Selections:</span>
              <Badge variant="secondary">
                Services: {selectedServices.length}
              </Badge>
              <Badge variant="secondary">
                Outbound Seats: {selectedOutboundSeats.length}
              </Badge>
              <Badge variant="secondary">
                Return Seats: {selectedReturnSeats.length}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Test Results Panel */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Test Results Log</CardTitle>
            <CardDescription>Real-time results from component interactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 max-h-48 overflow-y-auto bg-muted p-3 rounded font-mono text-sm">
              {testResults.length > 0 ? (
                testResults.map((result, index) => (
                  <div key={index} className="text-xs">
                    {result}
                  </div>
                ))
              ) : (
                <div className="text-muted-foreground text-xs">
                  No test results yet. Interact with the components below to see results.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Main Testing Components */}
        <Tabs defaultValue="services" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="services">Service Selection</TabsTrigger>
            <TabsTrigger value="seats">Seat Selection</TabsTrigger>
            <TabsTrigger value="combined">Combined Test</TabsTrigger>
          </TabsList>

          {/* Service Selection Tab */}
          <TabsContent value="services">
            <Card>
              <CardHeader>
                <CardTitle>Service Selection Testing</CardTitle>
                <CardDescription>
                  Test the ServiceSelection component with mock flight data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ServiceSelection
                  flightPriceResponse={mockFlightPriceResponse}
                  selectedServices={selectedServices}
                  onServiceChange={handleServiceChange}
                  passengers={mockPassengers}
                />
              </CardContent>
            </Card>
          </TabsContent>

          {/* Seat Selection Tab */}
          <TabsContent value="seats">
            <Card>
              <CardHeader>
                <CardTitle>Seat Selection Testing</CardTitle>
                <CardDescription>
                  Test the SeatSelection component with mock flight data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="text-sm font-medium mb-3">Outbound Flight</h4>
                  <SeatSelection
                    flightPriceResponse={mockFlightPriceResponse}
                    flightType="outbound"
                    segmentKey="SEG1"
                    selectedSeats={selectedOutboundSeats}
                    onSeatChange={handleSeatChange}
                    passengers={mockPassengers}
                  />
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="text-sm font-medium mb-3">Return Flight</h4>
                  <SeatSelection
                    flightPriceResponse={mockFlightPriceResponse}
                    flightType="return"
                    segmentKey="SEG2"
                    selectedSeats={selectedReturnSeats}
                    onSeatChange={handleSeatChange}
                    passengers={mockPassengers}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Combined Testing Tab */}
          <TabsContent value="combined">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Combined Services & Seats Testing</CardTitle>
                  <CardDescription>
                    Test both components together as they would appear in the booking flow
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h4 className="text-lg font-medium mb-3">Additional Services</h4>
                    <ServiceSelection
                      flightPriceResponse={mockFlightPriceResponse}
                      selectedServices={selectedServices}
                      onServiceChange={handleServiceChange}
                      passengers={mockPassengers}
                    />
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h4 className="text-lg font-medium mb-3">Seat Selection</h4>
                    <div className="space-y-4">
                      <div>
                        <h5 className="text-sm font-medium mb-2">Outbound Flight</h5>
                        <SeatSelection
                          flightPriceResponse={mockFlightPriceResponse}
                          flightType="outbound"
                          segmentKey="SEG1"
                          selectedSeats={selectedOutboundSeats}
                          onSeatChange={handleSeatChange}
                          passengers={mockPassengers}
                        />
                      </div>
                      
                      <div>
                        <h5 className="text-sm font-medium mb-2">Return Flight</h5>
                        <SeatSelection
                          flightPriceResponse={mockFlightPriceResponse}
                          flightType="return"
                          segmentKey="SEG2"
                          selectedSeats={selectedReturnSeats}
                          onSeatChange={handleSeatChange}
                          passengers={mockPassengers}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}