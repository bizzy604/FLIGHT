"use client"

import Link from "next/link"
import Image from "next/image"
import { Check, Download, Mail, Printer, Share2 } from "lucide-react"
import ReactDOMServer from 'react-dom/server'; 
import BoardingPass from "./boarding-pass/BoardingPass"; 
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import { downloadFromDataUrl, componentToDataUrl } from "@/utils/download-utils"

interface PaymentConfirmationProps {
  booking: any // Using any for brevity, but would use a proper type in a real app
}

export function PaymentConfirmation({ booking }: PaymentConfirmationProps) {
  // Function to download booking confirmation
  const downloadBookingConfirmation = async () => {
    try {
      // Extract passenger and flight information from booking
      const passenger = booking.passengers?.[0] || {};
      const flight = booking.flights?.[0] || {};
      const segment = flight.segments?.[0] || {};
      
      // Create boarding pass props from booking data
      const boardingPassProps = {
        passengerName: `${passenger.firstName} ${passenger.lastName}`,
        flightNumber: flight.flightNumber || 'N/A',
        departureCity: segment.departure?.city || 'N/A',
        departureAirport: segment.departure?.airportCode || 'N/A',
        departureTime: segment.departure?.time || '--:--',
        departureDate: segment.departure?.date || '',
        arrivalCity: segment.arrival?.city || 'N/A',
        arrivalAirport: segment.arrival?.airportCode || 'N/A',
        arrivalTime: segment.arrival?.time || '--:--',
        arrivalDate: segment.arrival?.date || '',
        seat: booking.seat || '--',
        boardingTime: segment.boardingTime || '--:--',
        terminal: segment.departure?.terminal || '--',
        gate: segment.departure?.gate || '--',
        confirmation: booking.referenceNumber || 'N/A',
        duration: flight.duration || '--h --m',
        classType: booking.cabinClass || 'ECONOMY',
        amenities: booking.amenities || [],
        isStatic: true
      };
      
      // Convert boarding pass component to data URL
      const boardingPass = <BoardingPass {...boardingPassProps} />;
      const dataUrl = await componentToDataUrl(boardingPass);
      
      // Generate a filename with booking reference
      const fileName = `boarding-pass-${booking.referenceNumber || 'confirmation'}.png`;
      
      // Trigger download
      downloadFromDataUrl(dataUrl, fileName);
    } catch (error) {
      console.error('Error downloading boarding pass:', error);
    }
  };

  // Debug function to log session storage contents
  const debugSessionStorage = () => {
    if (typeof window !== 'undefined') {
      console.log('=== SESSION STORAGE DEBUG ===')
      console.log('All session storage keys:', Object.keys(sessionStorage))
      
      // Check for all possible keys
      const possibleKeys = ['dev_completedBooking', 'booking-storage', 'booking', 'bookingData', 'hybridStorage', 'booking-data']
      
      possibleKeys.forEach(key => {
        const data = sessionStorage.getItem(key)
        if (data) {
          console.log(`${key} content:`, data)
          try {
            const parsed = JSON.parse(data)
            console.log(`${key} parsed:`, parsed)
            
            // Check if this looks like our booking data structure
            if (parsed.bookingReference || parsed.contactInfo || parsed.flightDetails) {
              console.log(`*** ${key} contains booking data structure! ***`)
            }
          } catch (e) {
            console.log(`${key} parse error:`, e)
          }
        }
      })
      
      // Check for any other keys containing 'booking'
      Object.keys(sessionStorage).forEach(key => {
        if (key.toLowerCase().includes('booking') && !possibleKeys.includes(key)) {
          console.log(`Found other booking-related key: ${key}`, sessionStorage.getItem(key))
        }
      })
      
      console.log('=== END SESSION STORAGE DEBUG ===')
    }
  }
  
  // Call debug function
  debugSessionStorage()

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
    // First, try to get data from session storage if available
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
    
    // Check session storage format in booking data
    if (bookingData.passengers && Array.isArray(bookingData.passengers)) {
      return bookingData.passengers
    }
    
    // Check API format
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
    
    return []
  }

  // Helper function to get flight details from either format
  const getFlightDetails = (bookingData: any) => {
    // First, try to get data from session storage if available
    if (typeof window !== 'undefined') {
      try {
        // Try multiple possible session storage keys
        const possibleKeys = ['dev_completedBooking', 'booking-storage', 'booking', 'bookingData', 'hybridStorage', 'booking-data']
          
          for (const key of possibleKeys) {
            const sessionData = sessionStorage.getItem(key)
            if (sessionData) {
              try {
                const parsed = JSON.parse(sessionData)
                console.log(`Pricing Info - Session storage data from key '${key}':`, parsed)
              
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
    
    // Check booking data format (session storage format)
    if (bookingData.flightDetails?.outbound) {
      return bookingData.flightDetails
    }
    
    // Check API format as fallback
    if (bookingData.flightDetails || bookingData.routeSegments) {
      const apiFlightDetails = bookingData.flightDetails || {}
      const segments = bookingData.routeSegments || {}

      // Extract flight information from the correct backend structure
      const outboundFlight = apiFlightDetails.outbound || {}
      const airlineInfo = outboundFlight.airline || {}

      return {
        outbound: {
          airline: {
            name: airlineInfo.name || bookingData.airlineCode || 'N/A',
            code: airlineInfo.code || bookingData.airlineCode || 'N/A',
            flightNumber: airlineInfo.flightNumber || bookingData.flightNumbers?.[0] || 'N/A',
            logo: `/airlines/${airlineInfo.code || bookingData.airlineCode || 'Unknown'}.svg`
          },
          departure: {
            airport: outboundFlight.departure?.airport || segments.origin || 'N/A',
            time: outboundFlight.departure?.time || (segments.departureTime ? new Date(segments.departureTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'),
            fullDate: outboundFlight.departure?.fullDate || (segments.departureTime ? new Date(segments.departureTime).toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A')
          },
          arrival: {
            airport: outboundFlight.arrival?.airport || segments.destination || 'N/A',
            time: outboundFlight.arrival?.time || (segments.arrivalTime ? new Date(segments.arrivalTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'),
            fullDate: outboundFlight.arrival?.fullDate || (segments.arrivalTime ? new Date(segments.arrivalTime).toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A')
          },
          duration: 'N/A',
          stops: 0
        },
        return: null
      }
    }
    
    return null
  }

  // Helper function to get contact info from either format
  const getContactInfo = (bookingData: any) => {
    // First, try to get data from session storage if available
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
      return {
        email: bookingData.contactInfo.email || 'N/A',
        phone: bookingData.contactInfo.phone || 'N/A'
      }
    }
    
    return { email: 'N/A', phone: 'N/A' }
  }

  // Helper function to get pricing info
  const getPricingInfo = (bookingData: any) => {
    // First, try to get data from session storage if available
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
    
    // Check if we have session storage pricing format in booking data
    if (bookingData.pricing?.baseFare?.amount !== undefined) {
      return bookingData.pricing
    }
    
    // For API format, create a basic pricing structure
    const totalAmount = bookingData.totalAmount || '0'
    return {
      baseFare: { amount: totalAmount, currency: 'USD' },
      taxes: { amount: '0', currency: 'USD' },
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

  const handleDownload = () => {
    downloadBookingConfirmation()
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

  const handleDownloadBoardingPass = async () => {
    // Get data from session storage using helper functions
    const flightDetails = getFlightDetails(booking)
    const passengerData = getPassengerData(booking)
    const contactInfo = getContactInfo(booking)
    
    // Use the first passenger for boarding pass
    const passenger = passengerData && passengerData.length > 0 ? passengerData[0] : null
    
    try {
      // Check if this is a round trip flight
      const hasReturnFlight = flightDetails && flightDetails.return;

      // Extract date information for outbound flight
      const outboundDepartureDateTime = parseDate(flightDetails?.outbound?.departure?.datetime) || 
        parseDate(flightDetails?.outbound?.departure?.date) || 
        parseDate(flightDetails?.outbound?.departure?.fullDate);
      const outboundDepartureDate = outboundDepartureDateTime ? 
        outboundDepartureDateTime.toLocaleDateString([], { month: 'short', day: 'numeric' }) : null;
      
      const outboundArrivalDateTime = parseDate(flightDetails?.outbound?.arrival?.datetime) || 
        parseDate(flightDetails?.outbound?.arrival?.date) || 
        parseDate(flightDetails?.outbound?.arrival?.fullDate);
      const outboundArrivalDate = outboundArrivalDateTime ? 
        outboundArrivalDateTime.toLocaleDateString([], { month: 'short', day: 'numeric' }) : null;
      
      // Create outbound boarding pass
      const outboundBoardingPassProps = {
        passengerName: passenger ? `${passenger.firstName || 'N/A'} ${passenger.lastName || 'N/A'}` : 'N/A',
        flightNumber: flightDetails?.outbound?.airline?.flightNumber || 'N/A',
        departureCity: flightDetails?.outbound?.departure?.city || 'N/A',
        departureAirport: flightDetails?.outbound?.departure?.airport || 'N/A',
        departureTime: flightDetails?.outbound?.departure?.time || 'N/A',
        departureDate: outboundDepartureDate || undefined,
        arrivalCity: flightDetails?.outbound?.arrival?.city || 'N/A',
        arrivalAirport: flightDetails?.outbound?.arrival?.airport || 'N/A',
        arrivalTime: flightDetails?.outbound?.arrival?.time || 'N/A',
        arrivalDate: outboundArrivalDate || undefined,
        seat: passenger?.seatNumber || 'N/A',
        boardingTime: flightDetails?.outbound?.boardingTime || 'N/A',
        terminal: flightDetails?.outbound?.departure?.terminal || 'N/A',
        gate: flightDetails?.outbound?.departure?.gate || 'N/A',
        confirmation: booking.bookingReference || booking.id || 'N/A',
        duration: flightDetails?.outbound?.duration || 'N/A',
        classType: flightDetails?.class || 'Economy',
        amenities: booking.extras?.map((extra: any) => extra.description || extra.name) || []
      };
      
      // Create a temporary props object for rendering, excluding interactive elements for static HTML
      const staticOutboundBoardingPassProps = { ...outboundBoardingPassProps, isStatic: true };
      
      const outboundBoardingPassHtml = ReactDOMServer.renderToStaticMarkup(
        <BoardingPass {...staticOutboundBoardingPassProps} />
      );
      
      // Generate HTML for outbound flight
      const outboundHtml = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Outbound Boarding Pass</title><script src="https://cdn.tailwindcss.com"></script><style>
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  display: flex; /* Ensure body can be a flex container */
  flex-direction: column; /* Stack children vertically */
  align-items: center; /* Center children horizontally */
  justify-content: center; /* Center children vertically */
  background-color: #f3f4f6; /* Added a light gray background for better visibility */
}
</style></head><body>${outboundBoardingPassHtml}</body></html>`;
      
      // Create blob and download outbound boarding pass
      const outboundBlob = new Blob([outboundHtml], { type: 'text/html' });
      const outboundUrl = URL.createObjectURL(outboundBlob);
      const outboundLink = document.createElement('a');
      outboundLink.href = outboundUrl;
      outboundLink.download = `boarding-pass-outbound-${booking.bookingReference || booking.id}.html`;
      document.body.appendChild(outboundLink);
      outboundLink.click();
      document.body.removeChild(outboundLink);
      URL.revokeObjectURL(outboundUrl);
      
      // If this is a round trip, also generate return boarding pass
      if (hasReturnFlight) {
        // Extract date information for return flight
        const returnDepartureDateTime = parseDate(flightDetails?.return?.departure?.datetime) || 
          parseDate(flightDetails?.return?.departure?.date) || 
          parseDate(flightDetails?.return?.departure?.fullDate);
        const returnDepartureDate = returnDepartureDateTime ? 
          returnDepartureDateTime.toLocaleDateString([], { month: 'short', day: 'numeric' }) : null;
        
        const returnArrivalDateTime = parseDate(flightDetails?.return?.arrival?.datetime) || 
          parseDate(flightDetails?.return?.arrival?.date) || 
          parseDate(flightDetails?.return?.arrival?.fullDate);
        const returnArrivalDate = returnArrivalDateTime ? 
          returnArrivalDateTime.toLocaleDateString([], { month: 'short', day: 'numeric' }) : null;
        
        // Create return boarding pass props
        const returnBoardingPassProps = {
          passengerName: passenger ? `${passenger.firstName || 'N/A'} ${passenger.lastName || 'N/A'}` : 'N/A',
          flightNumber: flightDetails?.return?.airline?.flightNumber || 'N/A',
          departureCity: flightDetails?.return?.departure?.city || 'N/A',
          departureAirport: flightDetails?.return?.departure?.airport || 'N/A',
          departureTime: flightDetails?.return?.departure?.time || 'N/A',
          departureDate: returnDepartureDate || undefined,
          arrivalCity: flightDetails?.return?.arrival?.city || 'N/A',
          arrivalAirport: flightDetails?.return?.arrival?.airport || 'N/A',
          arrivalTime: flightDetails?.return?.arrival?.time || 'N/A',
          arrivalDate: returnArrivalDate || undefined,
          seat: passenger?.returnSeatNumber || passenger?.seatNumber || 'N/A',
          boardingTime: flightDetails?.return?.boardingTime || 'N/A',
          terminal: flightDetails?.return?.departure?.terminal || 'N/A',
          gate: flightDetails?.return?.departure?.gate || 'N/A',
          confirmation: booking.bookingReference || booking.id || 'N/A',
          duration: flightDetails?.return?.duration || 'N/A',
          classType: flightDetails?.class || 'Economy',
          amenities: booking.extras?.map((extra: any) => extra.description || extra.name) || []
        };
        
        // Create a temporary props object for rendering, excluding interactive elements for static HTML
        const staticReturnBoardingPassProps = { ...returnBoardingPassProps, isStatic: true };
        
        const returnBoardingPassHtml = ReactDOMServer.renderToStaticMarkup(
          <BoardingPass {...staticReturnBoardingPassProps} />
        );
        
        // Generate HTML for return flight
        const returnHtml = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Return Boarding Pass</title><script src="https://cdn.tailwindcss.com"></script><style>
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  display: flex; /* Ensure body can be a flex container */
  flex-direction: column; /* Stack children vertically */
  align-items: center; /* Center children horizontally */
  justify-content: center; /* Center children vertically */
  background-color: #f3f4f6; /* Added a light gray background for better visibility */
}
</style></head><body>${returnBoardingPassHtml}</body></html>`;
        
        // Create blob and download return boarding pass
        const returnBlob = new Blob([returnHtml], { type: 'text/html' });
        const returnUrl = URL.createObjectURL(returnBlob);
        const returnLink = document.createElement('a');
        returnLink.href = returnUrl;
        returnLink.download = `boarding-pass-return-${booking.bookingReference || booking.id}.html`;
        document.body.appendChild(returnLink);
        returnLink.click();
        document.body.removeChild(returnLink);
        URL.revokeObjectURL(returnUrl);
      }
    } catch (error) {
      console.error('Error generating HTML boarding pass:', error);
      alert(error instanceof Error ? error.message : 'Failed to generate HTML boarding pass. Please try again.');
    }
  };

  const handleEmailItinerary = () => {
    // In a real app, this would trigger an API call to send an email
    alert(`Itinerary sent to ${booking.contactInfo?.email || 'your email'}`)
  }

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
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={handleEmailItinerary}
              aria-label="Email itinerary"
            >
              <Mail className="h-4 w-4" />
              <span>Email</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={handleDownloadBoardingPass} // Changed to handleDownloadBoardingPass
              aria-label="Download itinerary"
            >
              <Download className="h-4 w-4" />
              <span>Download</span>
            </Button>
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
                       return flightDetails.outbound.departure?.city || 'departure city';
                     })()} to ${(() => {
                       const flightDetails = getFlightDetails(booking);
                       return flightDetails.outbound.arrival?.city || 'arrival city';
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

                    const outboundDepartureDateTime = parseDate(flightDetails.outbound.departure?.datetime) || 
                      parseDate(flightDetails.outbound.departure?.date) || 
                      parseDate(flightDetails.outbound.departure?.fullDate);
                    const outboundDepartureTime = flightDetails.outbound.departure?.time || (outboundDepartureDateTime ? outboundDepartureDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                    const outboundDepartureAirportDisplay = flightDetails.outbound.departure?.airportName || flightDetails.outbound.departure?.airport || 'N/A';
                    const outboundDepartureFullDate = outboundDepartureDateTime ? outboundDepartureDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                    const outboundArrivalDateTime = parseDate(flightDetails.outbound.arrival?.datetime) || 
                      parseDate(flightDetails.outbound.arrival?.date) || 
                      parseDate(flightDetails.outbound.arrival?.fullDate);
                    const outboundArrivalTime = flightDetails.outbound.arrival?.time || (outboundArrivalDateTime ? outboundArrivalDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                    const outboundArrivalAirportDisplay = flightDetails.outbound.arrival?.airportName || flightDetails.outbound.arrival?.airport || 'N/A';
                    const outboundArrivalFullDate = outboundArrivalDateTime ? outboundArrivalDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                    return (
                      <>
                        <div className="mb-2 flex items-center justify-between">
                          <h4 className="font-medium">Outbound Flight</h4>
                          <span className="text-sm text-muted-foreground">{flightDetails.outbound.duration || 'N/A'}</span>
                        </div>
                        <div className="mb-2 flex items-center">
                          <Image
                            src={flightDetails.outbound.airline?.logo || "/placeholder.svg"}
                            alt={flightDetails.outbound.airline?.name || 'Airline'}
                            width={24}
                            height={24}
                            className="mr-2 rounded-full"
                          />
                          <span className="text-sm">
                            {flightDetails.outbound.airline?.name || 'N/A'} {flightDetails.outbound.airline?.code || ''}
                            {typeof flightDetails.outbound.airline?.flightNumber === 'object' && flightDetails.outbound.airline.flightNumber?.value 
                              ? flightDetails.outbound.airline.flightNumber.value 
                              : flightDetails.outbound.airline?.flightNumber || ''}
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
                            <p className="mt-1">{(flightDetails.outbound.stops || 0) > 0 ? `${flightDetails.outbound.stops} Stop(s)` : 'Direct'}</p>
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
                 return flightDetails.return;
               })() && (
                <Card>
                  <CardContent className="p-4">
                    {(() => {
                      const flightDetails = getFlightDetails(booking);
                      const returnDepartureDateTime = parseDate(flightDetails.return.departure?.datetime) || 
                        parseDate(flightDetails.return.departure?.date) || 
                        parseDate(flightDetails.return.departure?.fullDate);
                      const returnDepartureTime = flightDetails.return.departure?.time || (returnDepartureDateTime ? returnDepartureDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                      const returnDepartureAirportDisplay = flightDetails.return.departure?.airportName || flightDetails.return.departure?.airport || 'N/A';
                      const returnDepartureFullDate = returnDepartureDateTime ? returnDepartureDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                      const returnArrivalDateTime = parseDate(flightDetails.return.arrival?.datetime) || 
                        parseDate(flightDetails.return.arrival?.date) || 
                        parseDate(flightDetails.return.arrival?.fullDate);
                      const returnArrivalTime = flightDetails.return.arrival?.time || (returnArrivalDateTime ? returnArrivalDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A');
                      const returnArrivalAirportDisplay = flightDetails.return.arrival?.airportName || flightDetails.return.arrival?.airport || 'N/A';
                      const returnArrivalFullDate = returnArrivalDateTime ? returnArrivalDateTime.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

                      return (
                        <>
                          <div className="mb-2 flex items-center justify-between">
                            <h4 className="font-medium">Return Flight</h4>
                            <span className="text-sm text-muted-foreground">
                              {flightDetails.return.duration || 'N/A'}
                            </span>
                          </div>
                          <div className="mb-2 flex items-center">
                            <Image
                              src={flightDetails.return.airline?.logo || "/placeholder.svg"}
                              alt={flightDetails.return.airline?.name || 'Airline'}
                              width={24}
                              height={24}
                              className="mr-2 rounded-full"
                            />
                            <span className="text-sm">
                              {flightDetails.return.airline?.name || 'N/A'} {flightDetails.return.airline?.code || ''}
                              {typeof flightDetails.return.airline?.flightNumber === 'object' && flightDetails.return.airline.flightNumber?.value 
                                ? flightDetails.return.airline.flightNumber.value 
                                : flightDetails.return.airline?.flightNumber || ''}
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
                              <p className="mt-1">{(flightDetails.return.stops || 0) > 0 ? `${flightDetails.return.stops} Stop(s)` : 'Direct'}</p>
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
                      <span className="font-medium">Phone:</span> {typeof contactInfo.phone === 'object' && contactInfo.phone?.formatted 
                        ? contactInfo.phone.formatted 
                        : contactInfo.phone}
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
                           return flightDetails.return && booking.extras?.seats?.return && (
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
                           return flightDetails.return && booking.extras?.meals?.return && (
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

          <div>
            <h3 className="mb-2 text-lg font-medium">Payment Summary</h3>
            <div className="rounded-md border p-4">
              {(() => {
                const pricing = getPricingInfo(booking);
                return (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Base fare ({booking.passengers?.length || 1} passenger{(booking.passengers?.length || 1) > 1 ? 's' : ''})</span>
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
          </div>
        </div>
      </div>

      <div className="mb-8 space-y-4 rounded-lg border bg-muted/30 p-6">
        <h3 className="text-lg font-medium">What's Next?</h3>
        <div className="space-y-2">
          <p className="text-sm">
            <span className="font-medium">Check-in:</span> Online check-in opens 24 hours before your flight. You'll
            receive an email reminder.
          </p>
          <p className="text-sm">
            <span className="font-medium">Manage your booking:</span> You can make changes to your booking, select
            seats, or add extras through your account.
          </p>
          <p className="text-sm">
            <span className="font-medium">Need help?:</span> Our customer service team is available 24/7 to assist you
            with any questions.
          </p>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/manage">
            <Button>Manage Booking</Button>
          </Link>
          <Link href="/support">
            <Button variant="outline">Contact Support</Button>
          </Link>
        </div>
      </div>

      <div className="text-center">
        <Link href="/">
          <Button variant="outline">Return to Home</Button>
        </Link>
      </div>
    </div>
  )
}
