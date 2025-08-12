"use client"

import { useState } from "react"
import { flightStorageManager } from "@/utils/flight-storage-manager"
import Link from "next/link"
import Image from "next/image"
import { Check, Download, Mail, Printer, Share2 } from "lucide-react"
import { OfficialItinerary, BoardingPassItinerary } from "@/components/organisms";
import { transformOrderCreateToItinerary } from "@/utils/itinerary-data-transformer";
import { Button, LoadingButton } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import { generatePDFFromComponent } from "@/utils/download-utils"

interface PaymentConfirmationProps {
  booking: any // Using any for brevity, but would use a proper type in a real app
}

export function PaymentConfirmation({ booking }: PaymentConfirmationProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const [isEmailing, setIsEmailing] = useState(false)



  // Debug function to log robust storage contents
  const debugRobustStorage = async () => {
    if (typeof window !== 'undefined') {
      console.log('=== ROBUST STORAGE DEBUG ===')

      try {
        // Check robust storage health
        const health = await flightStorageManager.healthCheck()
        console.log('Storage health:', health)

        // Check storage stats
        const stats = flightStorageManager.getStorageStats()
        console.log('Storage stats:', stats)

        // Try to get booking data
        const bookingResult = await flightStorageManager.getBookingData()
        console.log('Booking data result:', bookingResult)

        // Check for legacy session storage keys
        const possibleKeys = ['dev_completedBooking', 'booking-storage', 'booking', 'bookingData', 'hybridStorage', 'booking-data']

        possibleKeys.forEach(key => {
          const data = sessionStorage.getItem(key)
          if (data) {
            console.log(`Legacy ${key} content:`, data)
            try {
              const parsed = JSON.parse(data)
              console.log(`Legacy ${key} parsed:`, parsed)

              // Check if this looks like our booking data structure
              if (parsed.bookingReference || parsed.contactInfo || parsed.flightDetails) {
                console.log(`*** Legacy ${key} contains booking data structure! ***`)
              }
            } catch (e) {
              console.log(`Legacy ${key} parse error:`, e)
            }
          }
        })

      } catch (error) {
        console.error('Robust storage debug error:', error)
      }

      console.log('=== END ROBUST STORAGE DEBUG ===')
    }
  }

  // Helper function to safely convert values to numbers and format them
  const formatPrice = (value: any, currency?: string): string => {
    if (value === null || value === undefined) return '0.00'
    
    // If it's already a number, use it directly
    if (typeof value === 'number') {
      return value.toFixed(2)
    }
    
    // If it's a string, try to parse it
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      return isNaN(parsed) ? '0.00' : parsed.toFixed(2)
    }
    
    // For any other type, try to convert to string then parse
    const parsed = parseFloat(String(value))
    return isNaN(parsed) ? '0.00' : parsed.toFixed(2)
  }

  // Get currency from pricing data
  const getCurrency = (): string => {
    const pricing = getPricingInfo(booking)
    return pricing?.baseFare?.currency || 
           pricing?.total?.currency || 
           pricing?.currency || 
           'USD'
  }

  // Helper function to get passenger data from either format
  const getPassengerData = (bookingData: any) => {
    console.log('🔍 Getting passenger data from booking data:', bookingData);

    // Priority 1: Check if we have the rawData.data.passengers structure (from confirmation page)
    if (bookingData.rawData?.data?.passengers && Array.isArray(bookingData.rawData.data.passengers)) {
      console.log('✅ Using rawData.data.passengers array:', bookingData.rawData.data.passengers);
      return bookingData.rawData.data.passengers;
    }

    // Priority 2: Check if we have the database booking structure with passengers from backend response
    if (bookingData.passengers && Array.isArray(bookingData.passengers)) {
      console.log('✅ Using database passengers array');
      return bookingData.passengers;
    }

    // Priority 3: Check if we have passengers in the passengerDetails JSON column with passengers array
    if (bookingData.passengerDetails?.passengers && Array.isArray(bookingData.passengerDetails.passengers)) {
      console.log('✅ Using database passengerDetails.passengers array');
      return bookingData.passengerDetails.passengers;
    }

    // Priority 3: Try to get data from session storage if available
    if (typeof window !== 'undefined') {
      try {
        const possibleKeys = ['dev_completedBooking', 'booking-storage', 'booking', 'bookingData', 'hybridStorage', 'booking-data']

        for (const key of possibleKeys) {
          const sessionData = sessionStorage.getItem(key)
          if (sessionData) {
            try {
              const parsed = JSON.parse(sessionData)
              console.log(`Passenger Data - Session storage data from key '${key}':`, parsed)

              // Check if we have the booking data directly at root level
              if (parsed.passengers && Array.isArray(parsed.passengers)) {
                console.log('Using session storage passenger data:', parsed.passengers)
                return parsed.passengers
              }

              // Check nested structure
              if (parsed.state?.booking?.passengers && Array.isArray(parsed.state.booking.passengers)) {
                console.log('Using nested session storage passenger data:', parsed.state.booking.passengers)
                return parsed.state.booking.passengers
              }
            } catch (parseError) {
              console.warn(`Could not parse session storage passenger data from key '${key}':`, parseError)
            }
          }
        }
      } catch (error) {
        console.warn('Could not access session storage passenger data:', error)
      }
    }

    // Priority 4: Check legacy API format with names/types/documents arrays
    if (bookingData.passengerDetails) {
      const { names, types, documents } = bookingData.passengerDetails

      // If names is a string, split it
      if (typeof names === 'string') {
        const nameArray = names.split(' ')
        const firstName = nameArray[0] || 'N/A'
        const lastName = nameArray.slice(1).join(' ') || 'N/A'

        return [{
          firstName,
          lastName,
          type: types?.[0] || 'adult',
          documentType: 'passport',
          documentNumber: documents?.[0] || 'N/A'
        }]
      }

      // If names is already an array
      if (Array.isArray(names)) {
        return names.map((name: string, index: number) => {
          const nameArray = name.split(' ')
          return {
            firstName: nameArray[0] || 'N/A',
            lastName: nameArray.slice(1).join(' ') || 'N/A',
            type: types?.[index] || 'adult',
            documentType: 'passport',
            documentNumber: documents?.[index] || 'N/A'
          }
        })
      }
    }

    console.warn('⚠️ No passenger data found in booking data');
    return []
  }

  // Helper function to get flight details using robust storage
  const getFlightDetails = (bookingData: any) => {
    console.log('🔍 Getting flight details from booking data:', bookingData);

    // Priority 1: Check if we have the database booking structure with flightDetails JSON column
    if (bookingData.flightDetails?.outbound) {
      console.log('✅ Using database flightDetails JSON column');
      return bookingData.flightDetails;
    }

    // Priority 2: Use originalFlightOffer for confirmation (most reliable for database bookings)
    if (bookingData.originalFlightOffer) {
      console.log('✅ Using originalFlightOffer for confirmation data')
      const offer = bookingData.originalFlightOffer
      const flight = offer.flight_segments?.[0] || {}
      const pricing = offer.total_price || {}

      return {
        outbound: {
          airline: {
            name: flight.airline_name || 'Unknown Airline',
            code: flight.airline_code || 'Unknown',
            flightNumber: flight.flight_number || 'Unknown',
            logo: `/airlines/${flight.airline_code || 'Unknown'}.svg`
          },
          departure: {
            airport: flight.departure_airport || 'Unknown',
            time: flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
            fullDate: flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'Unknown',
            terminal: flight.departure_terminal || 'TBD'
          },
          arrival: {
            airport: flight.arrival_airport || 'Unknown',
            time: flight.arrival_datetime ? new Date(flight.arrival_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
            fullDate: flight.arrival_datetime ? new Date(flight.arrival_datetime).toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'Unknown',
            terminal: flight.arrival_terminal || 'TBD'
          },
          duration: flight.duration || 'Unknown',
          class: offer.fare_family || 'Economy',
          stops: 0
        },
        return: null,
        pricing: {
          total: pricing.amount || 0,
          currency: pricing.currency || 'USD'
        },
        passengers: offer.passengers || [],
        fareFamily: offer.fare_family || 'Standard'
      }
    }

    // Priority 3: Try to get data from session storage if available
    if (typeof window !== 'undefined') {
      try {
        const possibleKeys = ['dev_completedBooking', 'booking-storage', 'booking', 'bookingData', 'hybridStorage', 'booking-data']

          for (const key of possibleKeys) {
            const sessionData = sessionStorage.getItem(key)
            if (sessionData) {
              try {
                const parsed = JSON.parse(sessionData)
                console.log(`Flight Details - Session storage data from key '${key}':`, parsed)

              // Check if we have the booking data directly at root level
              if (parsed.flightDetails?.outbound) {
                console.log('Using session storage flight details:', parsed.flightDetails)
                return parsed.flightDetails
              }

              // Check nested structure
              if (parsed.state?.booking?.flightDetails?.outbound) {
                console.log('Using nested session storage flight details:', parsed.state.booking.flightDetails)
                return parsed.state.booking.flightDetails
              }
            } catch (parseError) {
              console.warn(`Could not parse session storage data from key '${key}':`, parseError)
            }
          }
        }
      } catch (error) {
        console.warn('Could not access session storage:', error)
      }
    }

    // Priority 4: Check API format as fallback
    if (bookingData.routeSegments) {
      const segments = bookingData.routeSegments || {}

      return {
        outbound: {
          airline: {
            name: bookingData.airlineCode || 'N/A',
            code: bookingData.airlineCode || 'N/A',
            flightNumber: bookingData.flightNumbers?.[0] || 'N/A',
            logo: `/airlines/${bookingData.airlineCode || 'Unknown'}.svg`
          },
          departure: {
            airport: segments.origin || 'N/A',
            time: segments.departureTime ? new Date(segments.departureTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A',
            fullDate: segments.departureTime ? new Date(segments.departureTime).toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'
          },
          arrival: {
            airport: segments.destination || 'N/A',
            time: segments.arrivalTime ? new Date(segments.arrivalTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A',
            fullDate: segments.arrivalTime ? new Date(segments.arrivalTime).toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'
          },
          duration: 'N/A',
          stops: 0
        },
        return: null
      }
    }

    console.warn('⚠️ No flight details found in booking data');
    // Return a safe fallback structure instead of null
    return {
      outbound: {
        airline: { name: 'N/A', code: 'N/A', flightNumber: 'N/A', logo: '/placeholder.svg' },
        departure: { airport: 'N/A', time: 'N/A', fullDate: 'N/A', terminal: 'N/A' },
        arrival: { airport: 'N/A', time: 'N/A', fullDate: 'N/A', terminal: 'N/A' },
        duration: 'N/A',
        stops: 0
      },
      return: null,
      pricing: { total: 0, currency: 'USD' },
      passengers: [],
      fareFamily: 'N/A'
    }
  }

  // Helper function to get contact info from either format
  const getContactInfo = (bookingData: any) => {
    console.log('🔍 Getting contact info from booking data:', bookingData);

    // Priority 1: Check if we have the rawData.data.contactInfo structure (from confirmation page)
    if (bookingData.rawData?.data?.contactInfo?.email) {
      console.log('✅ Using rawData.data.contactInfo:', bookingData.rawData.data.contactInfo);
      const contact = bookingData.rawData.data.contactInfo;

      // Handle different phone formats
      let phoneDisplay = 'N/A'
      if (contact.phone) {
        if (typeof contact.phone === 'string') {
          phoneDisplay = contact.phone
        } else if (contact.phone.formatted) {
          phoneDisplay = contact.phone.formatted
        } else if (contact.phone.countryCode && contact.phone.number) {
          phoneDisplay = `${contact.phone.countryCode} ${contact.phone.number}`
        }
      }

      return {
        email: contact.email || 'N/A',
        phone: phoneDisplay
      }
    }

    // Priority 2: Check if we have the database booking structure with contactInfo JSON column
    if (bookingData.contactInfo?.email) {
      console.log('✅ Using database contactInfo JSON column');
      const contact = bookingData.contactInfo;

      // Handle different phone formats
      let phoneDisplay = 'N/A'
      if (contact.phone) {
        if (typeof contact.phone === 'string') {
          phoneDisplay = contact.phone
        } else if (contact.phone.formatted) {
          phoneDisplay = contact.phone.formatted
        } else if (contact.phone.countryCode && contact.phone.number) {
          phoneDisplay = `${contact.phone.countryCode} ${contact.phone.number}`
        }
      }

      return {
        email: contact.email || 'N/A',
        phone: phoneDisplay
      }
    }

    // Priority 3: Try to get data from session storage if available
    if (typeof window !== 'undefined') {
      try {
        const possibleKeys = ['dev_completedBooking', 'booking-storage', 'booking', 'bookingData', 'hybridStorage', 'booking-data']
          
          for (const key of possibleKeys) {
            const sessionData = sessionStorage.getItem(key)
            if (sessionData) {
              try {
                const parsed = JSON.parse(sessionData)
                console.log(`Contact Info - Session storage data from key '${key}':`, parsed)
              
              // Check if we have the booking data directly at root level
              if (parsed.contactInfo?.email) {
                console.log('Using session storage contact info:', parsed.contactInfo)
                return parsed.contactInfo
              }
              
              // Check nested structure
              if (parsed.state?.booking?.contactInfo?.email) {
                console.log('Using nested session storage contact info:', parsed.state.booking.contactInfo)
                return parsed.state.booking.contactInfo
              }
            } catch (parseError) {
              console.warn(`Could not parse session storage contact data from key '${key}':`, parseError)
            }
          }
        }
      } catch (error) {
        console.warn('Could not access session storage contact data:', error)
      }
    }
    
    // Check session storage format in booking data
    if (bookingData.contactInfo?.email) {
      return bookingData.contactInfo
    }
    
    // Check API format
    if (bookingData.contactInfo) {
      // Handle phone number object or string
      let phoneValue = 'N/A';
      if (bookingData.contactInfo.phone) {
        if (typeof bookingData.contactInfo.phone === 'object') {
          phoneValue = bookingData.contactInfo.phone.formatted ||
                      bookingData.contactInfo.phone.number ||
                      `${bookingData.contactInfo.phone.countryCode || ''}${bookingData.contactInfo.phone.number || ''}` ||
                      'N/A';
        } else {
          phoneValue = bookingData.contactInfo.phone;
        }
      }

      return {
        email: bookingData.contactInfo.email || 'N/A',
        phone: phoneValue
      }
    }
    
    return { email: 'N/A', phone: 'N/A' }
  }

  // Helper function to get pricing info
  const getPricingInfo = (bookingData: any) => {
    console.log('🔍 Getting pricing info from booking data:', bookingData);

    // Priority 1: Check if we have the rawData.data.pricing structure (from confirmation page)
    if (bookingData.rawData?.data?.pricing?.baseFare?.amount !== undefined) {
      console.log('✅ Using rawData.data.pricing structure:', bookingData.rawData.data.pricing);
      return bookingData.rawData.data.pricing;
    }

    // Priority 2: Check if we have the database booking structure with pricing from backend response
    if (bookingData.pricing?.baseFare?.amount !== undefined) {
      console.log('✅ Using database pricing structure');
      return bookingData.pricing;
    }

    // Priority 3: Try to get data from session storage if available
    if (typeof window !== 'undefined') {
      try {
        const possibleKeys = ['dev_completedBooking', 'booking-storage', 'booking', 'bookingData', 'hybridStorage', 'booking-data']

        for (const key of possibleKeys) {
          const sessionData = sessionStorage.getItem(key)
          if (sessionData) {
            try {
              const parsed = JSON.parse(sessionData)
              console.log(`Pricing Info - Session storage data from key '${key}':`, parsed)

              // Check if we have the booking data directly at root level
              if (parsed.pricing?.baseFare?.amount !== undefined) {
                console.log('Using session storage pricing info:', parsed.pricing)
                return parsed.pricing
              }

              // Check nested structure
              if (parsed.state?.booking?.pricing?.baseFare?.amount !== undefined) {
                console.log('Using nested session storage pricing info:', parsed.state.booking.pricing)
                return parsed.state.booking.pricing
              }
            } catch (parseError) {
              console.warn(`Could not parse session storage pricing data from key '${key}':`, parseError)
            }
          }
        }
      } catch (error) {
        console.warn('Could not access session storage pricing data:', error)
      }
    }

    // Priority 4: For API format, create a basic pricing structure using totalAmount
    const totalAmount = bookingData.totalAmount || 0;
    console.log(`⚠️ Using fallback pricing with totalAmount: ${totalAmount}`);

    return {
      baseFare: { amount: totalAmount, currency: 'USD' },
      taxes: { amount: 0, currency: 'USD' },
      total: { amount: totalAmount, currency: 'USD' }
    }
  }

  // Helper function to get extras info from either format
  const getExtrasInfo = (bookingData: any) => {
    // First, try to get data from session storage if available
    if (typeof window !== 'undefined') {
      try {
        const sessionData = sessionStorage.getItem('booking-storage')
        if (sessionData) {
          const parsed = JSON.parse(sessionData)
          // Check if we have the booking data directly at root level
          if (parsed.extras) {
            return parsed.extras
          }
          // Also check nested structure just in case
          if (parsed.state?.booking?.extras) {
            return parsed.state.booking.extras
          }
        }
      } catch (error) {
        console.warn('Could not parse session storage extras data:', error)
      }
    }
    
    // Return booking data extras or empty array
    return bookingData.extras || []
  }



  // Helper function to parse potentially malformed date strings
  const parseDate = (dateString: string | undefined | null): Date | null => {
    if (!dateString) return null;
    
    // Handle malformed dates like "2025-06-25T00:35:00.000T00:35:00"
    // Extract only the valid portion before any duplicate time
    let cleanDateString = dateString;
    const duplicateTimePattern = /T\d{2}:\d{2}:\d{2}(\.\d{3})?T\d{2}:\d{2}:\d{2}/;
    if (duplicateTimePattern.test(dateString)) {
      // Extract everything before the second 'T'
      const firstTIndex = dateString.indexOf('T');
      const secondTIndex = dateString.indexOf('T', firstTIndex + 1);
      if (secondTIndex > -1) {
        cleanDateString = dateString.substring(0, secondTIndex);
      }
    }
    
    const date = new Date(cleanDateString);
    return !isNaN(date.getTime()) ? date : null;
  };

  const handleDownloadOfficialItinerary = async (isCompact = false) => {
    setIsDownloading(true);
    try {
      console.log('🔍 Looking for OrderCreate response in booking data:', booking);

      // Priority 1: Try to get OrderCreate response from rawData (confirmation page)
      let orderCreateResponse = booking?.rawData?.raw_order_create_response;

      // Priority 2: Try to get from database orderCreateResponse column
      if (!orderCreateResponse) {
        orderCreateResponse = booking?.orderCreateResponse;
      }

      // Fallback to session storage if not in booking data
      if (!orderCreateResponse) {
        // First try the dedicated orderCreateResponse key
        const sessionData = sessionStorage.getItem('orderCreateResponse');
        if (sessionData) {
          orderCreateResponse = JSON.parse(sessionData);
        } else {
          // Then try the raw_order_create_response from dev_completedBooking
          const completedBookingData = sessionStorage.getItem('dev_completedBooking');
          if (completedBookingData) {
            const parsedBooking = JSON.parse(completedBookingData);
            if (parsedBooking.raw_order_create_response) {
              orderCreateResponse = parsedBooking.raw_order_create_response;
              console.log('✅ Found raw OrderCreate response in dev_completedBooking session storage');
            }
          }
        }
      }

      console.log('🔍 OrderCreate response found:', !!orderCreateResponse);
      console.log('🔍 Original flight offer found:', !!booking?.originalFlightOffer);

      // Check if we have OrderCreate response or originalFlightOffer for fallback
      if (!orderCreateResponse && !booking?.originalFlightOffer) {
        console.error('❌ No OrderCreate response or originalFlightOffer available');
        throw new Error('OrderCreate response is null or undefined and no originalFlightOffer fallback available');
      }

      console.log('🔄 Transforming OrderCreate response to itinerary data...');
      // Transform the OrderCreate response to itinerary data
      const itineraryData = transformOrderCreateToItinerary(orderCreateResponse, booking?.originalFlightOffer);

      // Generate PDF from the appropriate itinerary component with timeout
      const componentId = isCompact ? 'compact-itinerary' : 'boarding-pass-itinerary';
      const filenameSuffix = isCompact ? 'compact' : 'boarding-pass';

      console.log(`🚀 Starting PDF generation for ${componentId}`);

      // Small delay to ensure component is fully rendered
      await new Promise(resolve => setTimeout(resolve, 100));

      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('PDF generation timed out after 30 seconds')), 30000);
      });

      await Promise.race([
        generatePDFFromComponent(componentId, `flight-itinerary-${filenameSuffix}-${itineraryData.bookingInfo.bookingReference}.pdf`),
        timeoutPromise
      ]);

    } catch (error) {
      console.error('Error generating official itinerary:', error);
      alert(error instanceof Error ? error.message : 'Failed to generate itinerary. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  // Old boarding pass function removed - now using official itinerary system

  const handleEmailItinerary = async () => {
    setIsEmailing(true);
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      // In a real app, this would trigger an API call to send an email
      const contactInfo = getContactInfo(booking);
      alert(`Itinerary sent to ${contactInfo.email || 'your email'}`);
    } finally {
      setIsEmailing(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-8 rounded-lg border bg-green-50 p-6 text-center dark:bg-green-950">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
          <Check className="h-6 w-6 text-green-600 dark:text-green-400" />
        </div>
        <h1 className="mb-2 text-2xl font-bold text-green-800 dark:text-green-300">Booking Confirmed!</h1>
        <p className="text-green-700 dark:text-green-400">
          Your payment has been processed successfully and your booking is confirmed.
        </p>
      </div>

      <div className="mb-6 rounded-lg border p-6">
        <div className="mb-4 flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div>
            <h2 className="text-xl font-bold">Booking Reference: {booking.bookingReference || booking.id || 'N/A'}</h2>
            <p className="text-sm font-medium text-muted-foreground">Order ID: {booking.order_id || booking.orderId || booking.OrderID || 'N/A'}</p>
            <p className="text-sm text-muted-foreground">Please save these reference numbers for future inquiries</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <LoadingButton
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={handleEmailItinerary}
              loading={isEmailing}
              loadingText="Sending..."
              aria-label="Email itinerary"
            >
              <Mail className="h-4 w-4" />
              <span>Email</span>
            </LoadingButton>
            <LoadingButton
              variant="outline"
              size="sm"
              className="flex items-center gap-1 bg-blue-50 hover:bg-blue-100 border-blue-200"
              onClick={() => handleDownloadOfficialItinerary(true)} // Compact version
              loading={isDownloading}
              loadingText="Generating..."
              aria-label="Download compact itinerary (2 pages)"
            >
              <Download className="h-4 w-4" />
              <span>Compact (2 pages)</span>
            </LoadingButton>
            <LoadingButton
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={() => handleDownloadOfficialItinerary(false)} // Detailed version
              loading={isDownloading}
              loadingText="Generating..."
              aria-label="Download detailed itinerary"
            >
              <Download className="h-4 w-4" />
              <span>Detailed</span>
            </LoadingButton>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={() => window.print()}
              aria-label="Print itinerary"
            >
              <Printer className="h-4 w-4" />
              <span>Print</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={() => {
                if (navigator.share) {
                  navigator.share({
                    title: `Flight Booking - ${booking.id}`,
                    text: `My flight from ${(() => {
                       const flightDetails = getFlightDetails(booking);
                       return flightDetails?.outbound?.departure?.city || 'departure city';
                     })()} to ${(() => {
                       const flightDetails = getFlightDetails(booking);
                       return flightDetails?.outbound?.arrival?.city || 'arrival city';
                     })()} is confirmed!`,
                    url: window.location.href,
                  })
                } else {
                  alert("Sharing is not supported on this browser")
                }
              }}
              aria-label="Share booking details"
            >
              <Share2 className="h-4 w-4" />
              <span>Share</span>
            </Button>
          </div>
        </div>

        <Separator className="my-4" />

        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-lg font-medium">Flight Details</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardContent className="p-4">
                  {(() => {
                    const flightDetails = getFlightDetails(booking);
                    
                    // Check if outbound flight details exist
                    if (!flightDetails?.outbound) {
                      return (
                        <div className="text-center py-4">
                          <h4 className="font-medium mb-2">Outbound Flight</h4>
                          <p className="text-muted-foreground">Flight details not available</p>
                        </div>
                      )
                    }

                    const outboundDepartureDateTime = parseDate(flightDetails?.outbound?.departure?.datetime) ||
                      parseDate(flightDetails?.outbound?.departure?.date) ||
                      parseDate(flightDetails?.outbound?.departure?.fullDate);
                    const outboundDepartureTime = flightDetails?.outbound?.departure?.time || (outboundDepartureDateTime ? outboundDepartureDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                    const outboundDepartureAirportDisplay = flightDetails?.outbound?.departure?.airportName || flightDetails?.outbound?.departure?.airport || 'N/A';
                    const outboundDepartureFullDate = outboundDepartureDateTime ? outboundDepartureDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                    const outboundArrivalDateTime = parseDate(flightDetails?.outbound?.arrival?.datetime) ||
                      parseDate(flightDetails?.outbound?.arrival?.date) ||
                      parseDate(flightDetails?.outbound?.arrival?.fullDate);
                    const outboundArrivalTime = flightDetails?.outbound?.arrival?.time || (outboundArrivalDateTime ? outboundArrivalDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                    const outboundArrivalAirportDisplay = flightDetails?.outbound?.arrival?.airportName || flightDetails?.outbound?.arrival?.airport || 'N/A';
                    const outboundArrivalFullDate = outboundArrivalDateTime ? outboundArrivalDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                    return (
                      <>
                        <div className="mb-2 flex items-center justify-between">
                          <h4 className="font-medium">Outbound Flight</h4>
                          <span className="text-sm text-muted-foreground">{flightDetails?.outbound?.duration || 'N/A'}</span>
                        </div>
                        <div className="mb-2 flex items-center">
                          <Image
                            src={flightDetails?.outbound?.airline?.logo || "/placeholder.svg"}
                            alt={flightDetails?.outbound?.airline?.name || 'Airline'}
                            width={24}
                            height={24}
                            className="mr-2 rounded-full"
                          />
                          <span className="text-sm">
                            {flightDetails?.outbound?.airline?.name || 'N/A'} {flightDetails?.outbound?.airline?.code || ''}
                            {typeof flightDetails?.outbound?.airline?.flightNumber === 'object' && flightDetails?.outbound?.airline?.flightNumber?.value
                              ? flightDetails?.outbound?.airline?.flightNumber.value
                              : flightDetails?.outbound?.airline?.flightNumber || ''}
                          </span>
                        </div>
                        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                          <div>
                            <p className="text-lg font-bold">{outboundDepartureTime}</p>
                            <p className="text-sm">{outboundDepartureAirportDisplay}</p>
                            <p className="text-xs text-muted-foreground">
                              {outboundDepartureFullDate}
                            </p>
                          </div>
                          <div className="text-center text-xs text-muted-foreground">
                            <div className="relative h-0.5 w-16 bg-muted">
                              <div className="absolute -right-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                              <div className="absolute -left-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                            </div>
                            <p className="mt-1">{(flightDetails?.outbound?.stops || 0) > 0 ? `${flightDetails?.outbound?.stops} Stop(s)` : 'Direct'}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold">{outboundArrivalTime}</p>
                            <p className="text-sm">{outboundArrivalAirportDisplay}</p>
                            <p className="text-xs text-muted-foreground">{outboundArrivalFullDate}</p>
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </CardContent>
              </Card>

              {(() => {
                 const flightDetails = getFlightDetails(booking);
                 return flightDetails?.return;
               })() && (
                <Card>
                  <CardContent className="p-4">
                    {(() => {
                      const flightDetails = getFlightDetails(booking);
                      const returnDepartureDateTime = parseDate(flightDetails?.return?.departure?.datetime) ||
                        parseDate(flightDetails?.return?.departure?.date) ||
                        parseDate(flightDetails?.return?.departure?.fullDate);
                      const returnDepartureTime = flightDetails?.return?.departure?.time || (returnDepartureDateTime ? returnDepartureDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                      const returnDepartureAirportDisplay = flightDetails?.return?.departure?.airportName || flightDetails?.return?.departure?.airport || 'N/A';
                      const returnDepartureFullDate = returnDepartureDateTime ? returnDepartureDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                      const returnArrivalDateTime = parseDate(flightDetails?.return?.arrival?.datetime) ||
                        parseDate(flightDetails?.return?.arrival?.date) ||
                        parseDate(flightDetails?.return?.arrival?.fullDate);
                      const returnArrivalTime = flightDetails?.return?.arrival?.time || (returnArrivalDateTime ? returnArrivalDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                      const returnArrivalAirportDisplay = flightDetails?.return?.arrival?.airportName || flightDetails?.return?.arrival?.airport || 'N/A';
                      const returnArrivalFullDate = returnArrivalDateTime ? returnArrivalDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                      return (
                        <>
                          <div className="mb-2 flex items-center justify-between">
                            <h4 className="font-medium">Return Flight</h4>
                            <span className="text-sm text-muted-foreground">
                              {flightDetails?.return?.duration || 'N/A'}
                            </span>
                          </div>
                          <div className="mb-2 flex items-center">
                            <Image
                              src={flightDetails?.return?.airline?.logo || "/placeholder.svg"}
                              alt={flightDetails?.return?.airline?.name || 'Airline'}
                              width={24}
                              height={24}
                              className="mr-2 rounded-full"
                            />
                            <span className="text-sm">
                              {flightDetails?.return?.airline?.name || 'N/A'} {flightDetails?.return?.airline?.code || ''}
                              {typeof flightDetails?.return?.airline?.flightNumber === 'object' && flightDetails?.return?.airline?.flightNumber?.value
                                ? flightDetails?.return?.airline?.flightNumber.value
                                : flightDetails?.return?.airline?.flightNumber || ''}
                            </span>
                          </div>
                          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                            <div>
                              <p className="text-lg font-bold">{returnDepartureTime}</p>
                              <p className="text-sm">{returnDepartureAirportDisplay}</p>
                              <p className="text-xs text-muted-foreground">
                                {returnDepartureFullDate}
                              </p>
                            </div>
                            <div className="text-center text-xs text-muted-foreground">
                              <div className="relative h-0.5 w-16 bg-muted">
                                <div className="absolute -right-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                                <div className="absolute -left-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                              </div>
                              <p className="mt-1">{(flightDetails?.return?.stops || 0) > 0 ? `${flightDetails?.return?.stops} Stop(s)` : 'Direct'}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold">{returnArrivalTime}</p>
                              <p className="text-sm">{returnArrivalAirportDisplay}</p>
                              <p className="text-xs text-muted-foreground">
                                {returnArrivalFullDate}
                              </p>
                            </div>
                          </div>
                        </>
                      );
                    })()}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-medium">Passenger Information</h3>
            <div className="rounded-md border p-4">
              {(() => {
                const passengers = getPassengerData(booking);
                
                if (passengers.length > 0) {
                  return passengers.map((passenger: any, index: number) => (
                    <div key={index} className="mb-2 last:mb-0">
                      <p className="font-medium">
                        {passenger.firstName} {passenger.lastName}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {passenger.type} • {passenger.documentType}: {passenger.documentNumber}
                      </p>
                    </div>
                  ));
                }
                
                return <p>No passenger information available</p>;
              })()}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-medium">Contact Information</h3>
            <div className="rounded-md border p-4">
              {(() => {
                const contactInfo = getContactInfo(booking);
                return (
                  <>
                    <p className="mb-1">
                      <span className="font-medium">Email:</span> {contactInfo.email}
                    </p>
                    <p>
                      <span className="font-medium">Phone:</span> {(() => {
                        if (typeof contactInfo.phone === 'object' && contactInfo.phone !== null) {
                          // Handle phone object with different possible structures
                          return contactInfo.phone.formatted ||
                                 contactInfo.phone.number ||
                                 `${contactInfo.phone.countryCode || ''}${contactInfo.phone.number || ''}` ||
                                 'N/A';
                        }
                        // Handle string phone numbers
                        return contactInfo.phone || 'N/A';
                      })()}
                    </p>
                  </>
                );
              })()}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-medium">Selected Extras</h3>
            <div className="rounded-md border p-4">
              {(() => {
                const extras = getExtrasInfo(booking);
                
                if (Array.isArray(extras) && extras.length > 0) {
                  return (
                    <div className="space-y-2">
                      {extras.map((extra: any, index: number) => (
                        <div key={index} className="flex justify-between">
                          <span className="font-medium">{extra.description || extra.type || 'Extra Service'}</span>
                          <span>
                            {extra.price ? 
                              `${extra.price.currency || getCurrency()} ${formatPrice(extra.price.amount || extra.price)}` : 
                              'Included'
                            }
                          </span>
                        </div>
                      ))}
                    </div>
                  );
                }
                
                // Fallback to old structure if extras is an object
                if (booking.extras && typeof booking.extras === 'object' && !Array.isArray(booking.extras)) {
                  return (
                    <>
                      <div className="mb-2">
                        <p className="font-medium">Seats</p>
                        <p className="text-sm">Outbound: {booking.extras.seats?.outbound || 'Not selected'}</p>
                        {(() => {
                           const flightDetails = getFlightDetails(booking);
                           return flightDetails?.return && booking.extras?.seats?.return && (
                             <p className="text-sm">Return: {booking.extras.seats.return}</p>
                           );
                         })()}
                      </div>
                      <div className="mb-2">
                        <p className="font-medium">Baggage</p>
                        <p className="text-sm">Included: {booking.extras.baggage?.included || 'Standard'}</p>
                        <p className="text-sm">Additional: {booking.extras.baggage?.additional || 'None'}</p>
                      </div>
                      <div className="mb-2">
                        <p className="font-medium">Meals</p>
                        <p className="text-sm">Outbound: {booking.extras.meals?.outbound || 'Not selected'}</p>
                        {(() => {
                           const flightDetails = getFlightDetails(booking);
                           return flightDetails?.return && booking.extras?.meals?.return && (
                             <p className="text-sm">Return: {booking.extras.meals.return}</p>
                           );
                         })()}
                      </div>
                      <div>
                        <p className="font-medium">Additional Services</p>
                        <p className="text-sm">
                          {booking.extras.additionalServices && booking.extras.additionalServices.length > 0
                            ? booking.extras.additionalServices.join(", ")
                            : 'None'}
                        </p>
                      </div>
                    </>
                  );
                }
                
                return <p>No extras selected or information unavailable.</p>;
              })()}
            </div>
          </div>

          {/* <div>
            <h3 className="mb-2 text-lg font-medium">Payment Summary</h3>
            <div className="rounded-md border p-4">
              {(() => {
                const pricing = getPricingInfo(booking);
                return (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Base fare ({(() => {
                        const passengers = getPassengerData(booking);
                        return passengers.length || 1;
                      })()} passenger{(() => {
                        const passengers = getPassengerData(booking);
                        return (passengers.length || 1) > 1 ? 's' : '';
                      })()})</span>
                      <span>{pricing.baseFare?.currency || getCurrency()} {formatPrice(pricing.baseFare?.amount || pricing.baseFare)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Taxes and fees</span>
                      <span>{pricing.taxes?.currency || getCurrency()} {formatPrice(pricing.taxes?.amount || pricing.taxes)}</span>
                    </div>
                    {(pricing.fees?.amount || pricing.fees) !== undefined && (
                      <div className="flex justify-between">
                        <span>Fees</span>
                        <span>{pricing.fees?.currency || getCurrency()} {formatPrice(pricing.fees?.amount || pricing.fees)}</span>
                      </div>
                    )}
                    {(pricing.seatSelection?.amount || pricing.seatSelection) !== undefined && (
                      <div className="flex justify-between">
                        <span>Seat selection</span>
                        <span>{pricing.seatSelection?.currency || getCurrency()} {formatPrice(pricing.seatSelection?.amount || pricing.seatSelection)}</span>
                      </div>
                    )}
                    {(pricing.extraBaggage?.amount || pricing.extraBaggage) !== undefined && (
                      <div className="flex justify-between">
                        <span>Extra baggage</span>
                        <span>{pricing.extraBaggage?.currency || getCurrency()} {formatPrice(pricing.extraBaggage?.amount || pricing.extraBaggage)}</span>
                      </div>
                    )}
                    {(pricing.priorityBoarding?.amount || pricing.priorityBoarding) !== undefined && (
                      <div className="flex justify-between">
                        <span>Priority boarding</span>
                        <span>{pricing.priorityBoarding?.currency || getCurrency()} {formatPrice(pricing.priorityBoarding?.amount || pricing.priorityBoarding)}</span>
                      </div>
                    )}
                    {(pricing.travelInsurance?.amount || pricing.travelInsurance) !== undefined && (
                      <div className="flex justify-between">
                        <span>Travel insurance</span>
                        <span>{pricing.travelInsurance?.currency || getCurrency()} {formatPrice(pricing.travelInsurance?.amount || pricing.travelInsurance)}</span>
                      </div>
                    )}
                    <Separator />
                    <div className="flex justify-between font-bold">
                      <span>Total paid</span>
                      <span>{pricing.total?.currency || getCurrency()} {formatPrice(pricing.total?.amount || pricing.total || booking.totalAmount)}</span>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div> */}
        </div>
      </div>

      {/* Official Itinerary Section */}
      {(() => {
        try {
          console.log('🔍 Looking for OrderCreate response for itinerary display in booking data:', booking);

          // Priority 1: Try to get OrderCreate response from rawData (confirmation page)
          let orderCreateResponse = booking?.rawData?.raw_order_create_response;

          // Priority 2: Try to get from database orderCreateResponse column
          if (!orderCreateResponse) {
            orderCreateResponse = booking?.orderCreateResponse;
          }

          // Priority 3: Fallback to session storage if not in booking data
          if (!orderCreateResponse) {
            // First try the dedicated orderCreateResponse key
            const sessionData = sessionStorage.getItem('orderCreateResponse');
            if (sessionData) {
              orderCreateResponse = JSON.parse(sessionData);
            } else {
              // Then try the raw_order_create_response from dev_completedBooking
              const completedBookingData = sessionStorage.getItem('dev_completedBooking');
              if (completedBookingData) {
                const parsedBooking = JSON.parse(completedBookingData);
                if (parsedBooking.raw_order_create_response) {
                  orderCreateResponse = parsedBooking.raw_order_create_response;
                  console.log('✅ Found raw OrderCreate response in dev_completedBooking session storage for display');
                }
              }
            }
          }

          if (orderCreateResponse) {
            console.log('📋 Rendering itinerary with OrderCreate response from:', booking?.rawData?.raw_order_create_response ? 'rawData' : booking?.orderCreateResponse ? 'database' : 'session storage');
            console.log('📋 OrderCreate response data:', orderCreateResponse);
            const itineraryData = transformOrderCreateToItinerary(orderCreateResponse, booking?.originalFlightOffer);
            console.log('📋 Transformed itinerary data:', itineraryData);

            return (
              <div className="mb-8">
                {/* Visible original itinerary */}
                <div id="official-itinerary">
                  <OfficialItinerary data={itineraryData} />
                </div>

                {/* Hidden compact version for PDF generation */}
                <div id="compact-itinerary" className="hidden">
                  <OfficialItinerary data={itineraryData} className="compact-mode" />
                </div>

                {/* Hidden boarding pass version for future use */}
                <div id="boarding-pass-itinerary" className="hidden">
                  <BoardingPassItinerary data={itineraryData} />
                </div>
              </div>
            );
          } else if (booking?.originalFlightOffer) {
            console.log('📋 No OrderCreate response, using originalFlightOffer for itinerary');
            console.log('📋 Original flight offer data:', booking.originalFlightOffer);

            // Use the originalFlightOffer directly with the transformer
            const itineraryData = transformOrderCreateToItinerary(null, booking.originalFlightOffer, booking);
            console.log('📋 Transformed itinerary data from originalFlightOffer:', itineraryData);

            return (
              <div className="mb-8">
                {/* Visible original itinerary */}
                <div id="official-itinerary">
                  <OfficialItinerary data={itineraryData} />
                </div>

                {/* Hidden compact version for PDF generation */}
                <div id="compact-itinerary" className="hidden">
                  <OfficialItinerary data={itineraryData} className="compact-mode" />
                </div>

                {/* Hidden boarding pass version for future use */}
                <div id="boarding-pass-itinerary" className="hidden">
                  <BoardingPassItinerary data={itineraryData} />
                </div>
              </div>
            );
          } else {
            console.warn('⚠️ No OrderCreate response or originalFlightOffer found in booking data');
            // Fallback: Try to show something if we have booking data
            if (booking) {
              return (
                <div className="mb-8 p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <h3 className="text-lg font-semibold text-yellow-800 mb-2">Itinerary Temporarily Unavailable</h3>
                  <p className="text-yellow-700 mb-4">
                    We're having trouble loading your detailed itinerary. Your booking is confirmed with reference:
                    <span className="font-bold ml-1">{booking.bookingReference || booking.id}</span>
                  </p>
                  <p className="text-sm text-yellow-600">
                    Please refresh the page or contact support if this issue persists.
                  </p>
                </div>
              );
            }
          }
        } catch (error) {
          console.error('Error rendering boarding pass itinerary:', error);
          // Fallback: Show error message with booking reference
          return (
            <div className="mb-8 p-6 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Itinerary</h3>
              <p className="text-red-700 mb-4">
                There was an error loading your itinerary. Your booking is still confirmed.
              </p>
              <p className="text-sm text-red-600">
                Error: {error instanceof Error ? error.message : 'Unknown error'}
              </p>
              {booking && (
                <p className="text-sm text-red-600 mt-2">
                  Booking Reference: <span className="font-bold">{booking.bookingReference || booking.id}</span>
                </p>
              )}
            </div>
          );
        }
        return null;
      })()}
    </div>
  )
}
