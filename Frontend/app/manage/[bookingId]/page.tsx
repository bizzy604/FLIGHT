"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import { format } from "date-fns"
import Image from "next/image"
import {
  ArrowLeft,
  Calendar,
  Clock,
  Plane,
  MapPin,
  Users,
  CreditCard,
  Download,
  Edit,
  Phone,
  Mail,
  CheckCircle,
  XCircle,
  AlertCircle,
  Luggage,
  FileText,
  Info,
  Shield,
  Building,
  Timer,
  Ticket,
  Globe,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/hooks/use-toast"
import Link from "next/link"
import { transformOrderCreateToItinerary, type ItineraryData } from "@/utils/itinerary-data-transformer"
import { generatePDFFromComponent } from "@/utils/download-utils"
import { OfficialItinerary } from "@/components/organisms"

interface Booking {
  id: number
  bookingReference: string
  status: string
  createdAt: string
  totalAmount: number

  // New database fields (primary source)
  airlineCode?: string
  flightNumbers?: string[]
  routeSegments?: {
    origin?: string
    destination?: string
    departureTime?: string
    arrivalTime?: string
    segments?: any[]
  }
  orderItemId?: string
  passengerTypes?: string[]
  documentNumbers?: string[]
  classOfService?: string
  cabinClass?: string
  orderCreateResponse?: any
  originalFlightOffer?: any

  // Legacy fields (for backwards compatibility)
  flightDetails: {
    // Database structure - flat format
    airlineCode?: string
    outboundFlightNumber?: string
    returnFlightNumber?: string
    origin?: string
    destination?: string
    departureTime?: string
    arrivalTime?: string
    classOfService?: string
    cabinClass?: string
    segments?: any[]
    // Legacy structure - nested format (for backwards compatibility)
    outbound?: FlightDetail
    return?: FlightDetail
  }
  passengerDetails: {
    // Database structure - flat format
    names?: string[]
    types?: string[]
    documents?: string[]
    // Legacy structure - array format (for backwards compatibility)
    0?: {
      firstName: string
      lastName: string
      email?: string
      phone?: string
      dateOfBirth?: string
      passportNumber?: string
    }
  } | Array<{
    firstName: string
    lastName: string
    email?: string
    phone?: string
    dateOfBirth?: string
    passportNumber?: string
  }>
  contactInfo: {
    email: string
    phone: string
  }
  payments?: Array<{
    id: number
    status: string
    amount: number
    paymentMethod?: string
    createdAt: string
  }>
}

interface FlightDetail {
  departure: {
    time: string
    date: string
    city: string
    airport: string
    terminal?: string
  }
  arrival: {
    time: string
    date: string
    city: string
    airport: string
    terminal?: string
  }
  duration: string
  airline?: {
    name: string
    code: string
  }
  flightNumber?: string
  aircraft?: string
  classOfService?: string
}

export default function BookingDetailsPage() {
  const router = useRouter()
  const params = useParams()
  const bookingId = params.bookingId as string
  const { isLoaded, isSignedIn } = useUser()
  const { toast } = useToast()

  const [isLoading, setIsLoading] = useState(true)
  const [booking, setBooking] = useState<Booking | null>(null)
  const [itineraryData, setItineraryData] = useState<ItineraryData | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  useEffect(() => {
    const fetchBookingDetails = async () => {
      if (!isLoaded) return

      try {
        setIsLoading(true)

        const response = await fetch(`/api/bookings/${bookingId}`)

        if (!response.ok) {
          if (response.status === 404) {
            toast({
              title: "Booking not found",
              description: "The booking you're looking for doesn't exist.",
              variant: "destructive",
            })
            router.push("/manage")
          } else if (response.status === 401) {
            toast({
              title: "Unauthorized",
              description: "Please sign in to view your bookings.",
              variant: "destructive",
            })
            router.push("/sign-in")
          } else {
            throw new Error("Failed to fetch booking details")
          }
          return
        }

        const data = await response.json()
        setBooking(data)

        // Transform OrderCreate response using the dual-column strategy
        console.log('📋 Booking data structure:', {
          hasOrderCreateResponse: !!data.orderCreateResponse,
          hasOriginalFlightOffer: !!data.originalFlightOffer,
          orderCreateType: typeof data.orderCreateResponse,
          originalOfferType: typeof data.originalFlightOffer
        })

        // Parse JSON data if needed
        let parsedOrderCreate = data.orderCreateResponse
        if (typeof parsedOrderCreate === 'string') {
          try {
            parsedOrderCreate = JSON.parse(parsedOrderCreate)
          } catch (parseError) {
            console.error('Error parsing orderCreateResponse:', parseError)
            parsedOrderCreate = null
          }
        }

        let originalFlightOffer = data.originalFlightOffer
        if (typeof originalFlightOffer === 'string') {
          try {
            originalFlightOffer = JSON.parse(originalFlightOffer)
          } catch (parseError) {
            console.error('Error parsing originalFlightOffer:', parseError)
            originalFlightOffer = null
          }
        }

        // Prepare basic booking data for fallback
        const basicBookingData = {
          bookingReference: data.bookingReference,
          createdAt: data.createdAt,
          passengerDetails: data.passengerDetails,
          contactInfo: data.contactInfo,
          documentNumbers: data.documentNumbers
        }

        // Try to transform itinerary data
        if (parsedOrderCreate || originalFlightOffer) {
          try {
            const transformedData = transformOrderCreateToItinerary(parsedOrderCreate, originalFlightOffer, basicBookingData)
            setItineraryData(transformedData)
            console.log("✅ Successfully transformed itinerary data:", transformedData)
          } catch (error) {
            console.error("❌ Error transforming itinerary data:", error)
            console.log("⚠️ Continuing without transformed data - using fallback display")
          }
        } else {
          console.log("⚠️ No OrderCreate response or originalFlightOffer found for transformation")
        }
      } catch (error) {
        console.error("Error fetching booking:", error)
        toast({
          title: "Error",
          description: "Failed to load booking details. Please try again.",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookingDetails()
  }, [bookingId, isLoaded, router, toast])

  // Handle itinerary download
  const handleDownloadItinerary = async () => {
    if (!itineraryData || !booking) {
      toast({
        title: "Download Failed",
        description: "Itinerary data is not available for download.",
        variant: "destructive",
      })
      return
    }

    setIsDownloading(true)
    try {
      await generatePDFFromComponent(
        'manage-itinerary-component',
        `flight-itinerary-${booking.bookingReference}.pdf`
      )
      toast({
        title: "Download Successful",
        description: "PDF has been generated successfully.",
        variant: "default",
      })
    } catch (error) {
      console.error('Error generating PDF:', error)
      toast({
        title: "Download Failed",
        description: "Unable to generate PDF. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsDownloading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "confirmed":
        return (
          <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            <CheckCircle className="w-3 h-3 mr-1" />
            Confirmed
          </Badge>
        )
      case "pending":
        return (
          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
            <AlertCircle className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        )
      case "cancelled":
        return (
          <Badge className="bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
            <XCircle className="w-3 h-3 mr-1" />
            Cancelled
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM d, yyyy")
    } catch (e) {
      return dateString
    }
  }

  const formatDateTime = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM d, yyyy 'at' h:mm a")
    } catch (e) {
      return dateString
    }
  }

  // Helper function to get formatted price from booking data
  const getFormattedPrice = (booking: Booking) => {
    // Try to get price from originalFlightOffer first
    if (booking.originalFlightOffer && booking.originalFlightOffer.total_price) {
      const price = booking.originalFlightOffer.total_price
      const amount = price.amount || 0
      const currency = price.currency || 'USD'

      // Convert currency symbols
      const currencySymbol = currency === 'INR' ? '₹' :
                           currency === 'USD' ? '$' :
                           currency === 'EUR' ? '€' :
                           currency === 'GBP' ? '£' : currency

      return `${currencySymbol}${amount.toLocaleString()}`
    }

    // Fallback to totalAmount from booking
    if (booking.totalAmount && booking.totalAmount > 0) {
      return `$${booking.totalAmount}`
    }

    // Default fallback
    return 'Price not available'
  }

  // Helper function to normalize flight data structure
  const getFlightInfo = (booking: Booking) => {
    // Helper function to clean up "Unknown" values
    const cleanValue = (value: string | undefined | null, fallback: string = 'N/A') => {
      if (!value || value === 'Unknown' || value === 'undefined' || value === 'null') {
        return fallback
      }
      return value
    }

    // Helper function to format time from ISO string or time string
    const formatTimeFromString = (timeString: string | undefined) => {
      if (!timeString || timeString === 'N/A' || timeString === 'Unknown') return 'N/A'

      try {
        // If it's an ISO string, extract time
        if (timeString.includes('T')) {
          const date = new Date(timeString)
          return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          })
        }
        // If it's already a time string, return as is
        return timeString
      } catch {
        return 'N/A'
      }
    }

    // Helper function to get enhanced flight details from OrderCreate response
    const getEnhancedFlightDetails = () => {
      const detailedInfo = getDetailedBookingInfo(booking)
      if (!detailedInfo) return null

      const { orderItems } = detailedInfo
      if (orderItems.length === 0) return null

      const flightItem = orderItems[0].FlightItem
      if (!flightItem) return null

      const originDestinations = flightItem.OriginDestination || []
      const enhancedDetails = {
        classOfService: booking.classOfService || booking.cabinClass || 'N/A',
        aircraft: 'N/A',
        terminal: {
          departure: 'N/A',
          arrival: 'N/A'
        }
      }

      // Extract aircraft and terminal information
      if (originDestinations.length > 0) {
        const flights = originDestinations[0].Flight || []
        if (flights.length > 0) {
          const flight = flights[0]
          enhancedDetails.aircraft = flight.Equipment?.AircraftCode || 'N/A'
          enhancedDetails.terminal.departure = flight.Departure?.Terminal?.Name || 'N/A'
          enhancedDetails.terminal.arrival = flight.Arrival?.Terminal?.Name || 'N/A'
        }
      }

      return enhancedDetails
    }

    const enhancedDetails = getEnhancedFlightDetails()

    // PRIORITY 1: Extract from database fields (routeSegments, flightNumbers, airlineCode)
    const routeSegments = booking.routeSegments as any
    const flightNumbers = booking.flightNumbers as string[]
    const airlineCode = booking.airlineCode

    // Check if routeSegments has segments array with actual flight data
    if (routeSegments && routeSegments.segments && routeSegments.segments.length > 0) {
      const segment = routeSegments.segments[0] // Get first segment
      const origin = cleanValue(segment.departure_airport, 'Unknown Airport')
      const destination = cleanValue(segment.arrival_airport, 'Unknown Airport')
      const airline = cleanValue(segment.airline_code, 'Unknown')
      const outboundFlightNumber = cleanValue(segment.flight_number, 'N/A')
      const returnFlightNumber = routeSegments.segments[1] ? cleanValue(routeSegments.segments[1].flight_number) : undefined

      return {
        outbound: {
          departure: {
            time: formatTimeFromString(segment.departure_datetime),
            city: origin,
            airport: origin,
            date: segment.departure_datetime || new Date().toISOString(),
            terminal: enhancedDetails?.terminal.departure || 'N/A'
          },
          arrival: {
            time: formatTimeFromString(segment.arrival_datetime),
            city: destination,
            airport: destination,
            date: segment.arrival_datetime || new Date().toISOString(),
            terminal: enhancedDetails?.terminal.arrival || 'N/A'
          },
          duration: cleanValue(segment.duration, 'N/A'),
          flightNumber: outboundFlightNumber,
          airline: {
            code: airline,
            name: cleanValue(segment.airline_name, airline === 'Unknown' ? 'Unknown Airline' : airline)
          },
          aircraft: enhancedDetails?.aircraft || 'N/A',
          classOfService: enhancedDetails?.classOfService || booking.classOfService || booking.cabinClass || 'N/A'
        },
        return: returnFlightNumber && returnFlightNumber !== 'N/A' ? {
          departure: {
            time: formatTimeFromString(routeSegments.segments[1]?.departure_datetime),
            city: destination,
            airport: destination,
            date: routeSegments.segments[1]?.departure_datetime || new Date().toISOString(),
            terminal: enhancedDetails?.terminal.arrival || 'N/A'
          },
          arrival: {
            time: formatTimeFromString(routeSegments.segments[1]?.arrival_datetime),
            city: origin,
            airport: origin,
            date: routeSegments.segments[1]?.arrival_datetime || new Date().toISOString(),
            terminal: enhancedDetails?.terminal.departure || 'N/A'
          },
          duration: cleanValue(routeSegments.segments[1]?.duration, 'N/A'),
          flightNumber: returnFlightNumber,
          airline: {
            code: airline,
            name: cleanValue(routeSegments.segments[1]?.airline_name, airline === 'Unknown' ? 'Unknown Airline' : airline)
          },
          aircraft: enhancedDetails?.aircraft || 'N/A',
          classOfService: enhancedDetails?.classOfService || booking.classOfService || booking.cabinClass || 'N/A'
        } : undefined
      }
    }

    // PRIORITY 1B: Fallback to routeSegments top-level fields if segments array is empty
    if (routeSegments && (routeSegments.origin || routeSegments.destination) &&
        routeSegments.origin !== 'Unknown' && routeSegments.destination !== 'Unknown') {
      const origin = cleanValue(routeSegments.origin, 'Unknown Airport')
      const destination = cleanValue(routeSegments.destination, 'Unknown Airport')
      const airline = cleanValue(airlineCode, 'Unknown')
      const outboundFlightNumber = flightNumbers && flightNumbers[0] ? cleanValue(flightNumbers[0], 'N/A') : 'N/A'
      const returnFlightNumber = flightNumbers && flightNumbers[1] ? cleanValue(flightNumbers[1]) : undefined

      return {
        outbound: {
          departure: {
            time: formatTimeFromString(routeSegments.departureTime),
            city: origin,
            airport: origin,
            date: routeSegments.departureTime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(routeSegments.arrivalTime),
            city: destination,
            airport: destination,
            date: routeSegments.arrivalTime || new Date().toISOString()
          },
          duration: 'N/A',
          flightNumber: outboundFlightNumber,
          airline: {
            code: airline,
            name: airline === 'Unknown' ? 'Unknown Airline' : airline
          }
        },
        return: returnFlightNumber && returnFlightNumber !== 'N/A' ? {
          departure: {
            time: formatTimeFromString(routeSegments.arrivalTime),
            city: destination,
            airport: destination,
            date: routeSegments.arrivalTime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(routeSegments.departureTime),
            city: origin,
            airport: origin,
            date: routeSegments.departureTime || new Date().toISOString()
          },
          duration: 'N/A',
          flightNumber: returnFlightNumber,
          airline: {
            code: airline,
            name: airline === 'Unknown' ? 'Unknown Airline' : airline
          }
        } : undefined
      }
    }

    // PRIORITY 2: Extract from flightDetails (legacy structure)
    const flightDetails = booking.flightDetails
    if (flightDetails && (flightDetails.origin || flightDetails.destination || flightDetails.airlineCode)) {
      const origin = cleanValue(flightDetails.origin, 'Unknown Airport')
      const destination = cleanValue(flightDetails.destination, 'Unknown Airport')
      const airline = cleanValue(flightDetails.airlineCode, 'Unknown')
      const outboundFlightNumber = cleanValue(flightDetails.outboundFlightNumber, 'N/A')
      const returnFlightNumber = cleanValue(flightDetails.returnFlightNumber)

      return {
        outbound: {
          departure: {
            time: formatTimeFromString(flightDetails.departureTime),
            city: origin,
            airport: origin,
            date: flightDetails.departureTime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(flightDetails.arrivalTime),
            city: destination,
            airport: destination,
            date: flightDetails.arrivalTime || new Date().toISOString()
          },
          duration: 'N/A',
          flightNumber: outboundFlightNumber,
          airline: {
            code: airline,
            name: airline === 'Unknown' ? 'Unknown Airline' : airline
          }
        },
        return: returnFlightNumber && returnFlightNumber !== 'N/A' ? {
          departure: {
            time: formatTimeFromString(flightDetails.arrivalTime),
            city: destination,
            airport: destination,
            date: flightDetails.arrivalTime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(flightDetails.departureTime),
            city: origin,
            airport: origin,
            date: flightDetails.departureTime || new Date().toISOString()
          },
          duration: 'N/A',
          flightNumber: returnFlightNumber,
          airline: {
            code: airline,
            name: airline === 'Unknown' ? 'Unknown Airline' : airline
          }
        } : undefined
      }
    }

    // PRIORITY 3: Fallback to nested structure if available
    if (flightDetails && flightDetails.outbound) {
      return {
        outbound: flightDetails.outbound,
        return: flightDetails.return
      }
    }

    // Default fallback with better messaging
    return {
      outbound: {
        departure: {
          time: 'N/A',
          city: 'Flight details not available',
          airport: 'N/A',
          date: new Date().toISOString()
        },
        arrival: {
          time: 'N/A',
          city: 'Flight details not available',
          airport: 'N/A',
          date: new Date().toISOString()
        },
        duration: 'N/A',
        flightNumber: 'N/A',
        airline: { code: 'N/A', name: 'Flight details not available' }
      }
    }
  }

  // Helper function to normalize passenger data
  const getPassengerInfo = (booking: Booking) => {
    const passengerDetails = booking.passengerDetails

    // Helper function to clean up passenger data
    const cleanPassengerValue = (value: string | undefined | null, fallback: string = 'N/A') => {
      if (!value || value === 'Unknown' || value === 'undefined' || value === 'null' || value.trim() === '') {
        return fallback
      }
      return value.trim()
    }

    // Check if we have the new flat structure with names string
    if (!Array.isArray(passengerDetails) && 'names' in passengerDetails && typeof passengerDetails.names === 'string') {
      const namesString = cleanPassengerValue(passengerDetails.names, '')
      const names = namesString ? namesString.split(', ').filter(n => n.trim()) : []

      if (names.length > 0) {
        return names.map((name: string, index: number) => ({
          firstName: cleanPassengerValue(name.split(' ')[0], `Passenger ${index + 1}`),
          lastName: cleanPassengerValue(name.split(' ').slice(1).join(' '), ''),
          email: booking.contactInfo.email,
          phone: booking.contactInfo.phone
        }))
      }
    }

    // Check if we have the new flat structure with names array
    if (!Array.isArray(passengerDetails) && 'names' in passengerDetails && Array.isArray(passengerDetails.names)) {
      return passengerDetails.names.map((name: string, index: number) => ({
        firstName: cleanPassengerValue(name.split(' ')[0], `Passenger ${index + 1}`),
        lastName: cleanPassengerValue(name.split(' ').slice(1).join(' '), ''),
        email: booking.contactInfo.email,
        phone: booking.contactInfo.phone
      }))
    }

    // Check if we have array structure
    if (Array.isArray(passengerDetails)) {
      return passengerDetails.map((passenger: any, index: number) => ({
        firstName: cleanPassengerValue(passenger.firstName || (passenger.name ? passenger.name.split(' ')[0] : ''), `Passenger ${index + 1}`),
        lastName: cleanPassengerValue(passenger.lastName || (passenger.name ? passenger.name.split(' ').slice(1).join(' ') : ''), ''),
        email: passenger.email || booking.contactInfo.email,
        phone: passenger.phone || booking.contactInfo.phone
      }))
    }

    // Fallback to single passenger from contact info
    return [{
      firstName: 'Passenger 1',
      lastName: '',
      email: booking.contactInfo.email,
      phone: booking.contactInfo.phone
    }]
  }

  // Helper function to extract detailed information from OrderCreate response
  const getDetailedBookingInfo = (booking: Booking) => {
    const orderCreateResponse = booking.orderCreateResponse
    if (!orderCreateResponse || !orderCreateResponse.Response) {
      return null
    }

    const response = orderCreateResponse.Response

    // Extract passengers with detailed information
    const passengers = response.Passengers?.Passenger || []

    // Extract order items for flight details
    const orderItems = response.Order?.[0]?.OrderItems?.OrderItem || []

    // Extract data lists for baggage and penalties
    const dataLists = response.DataLists || {}
    const penaltyList = dataLists.PenaltyList?.Penalty || []
    const carryOnAllowanceList = dataLists.CarryOnAllowanceList?.CarryOnAllowance || []
    const checkedBagAllowanceList = dataLists.CheckedBagAllowanceList?.CheckedBagAllowance || []
    const serviceList = dataLists.ServiceList?.Service || []

    return {
      passengers,
      orderItems,
      penaltyList,
      carryOnAllowanceList,
      checkedBagAllowanceList,
      serviceList
    }
  }

  // Helper function to get baggage information
  const getBaggageInfo = (booking: Booking) => {
    const detailedInfo = getDetailedBookingInfo(booking)
    if (!detailedInfo) return null

    const { carryOnAllowanceList, checkedBagAllowanceList, serviceList } = detailedInfo

    // Extract carry-on baggage info
    const carryOnInfo = carryOnAllowanceList.map((allowance: any) => ({
      type: 'Carry-on',
      description: allowance.AllowanceDescription?.ApplicableParty || 'Traveler',
      pieces: allowance.PieceAllowance?.[0]?.TotalNumber || 'N/A',
      weight: allowance.WeightAllowance?.[0]?.MaxWeight || 'N/A',
      dimensions: allowance.DimensionAllowance?.[0] ?
        `${allowance.DimensionAllowance[0].Length || 'N/A'} x ${allowance.DimensionAllowance[0].Width || 'N/A'} x ${allowance.DimensionAllowance[0].Height || 'N/A'}` : 'N/A'
    }))

    // Extract checked baggage info
    const checkedBagInfo = checkedBagAllowanceList.map((allowance: any) => ({
      type: 'Checked',
      description: allowance.AllowanceDescription?.ApplicableParty || 'Traveler',
      pieces: allowance.PieceAllowance?.[0]?.TotalNumber || 'N/A',
      weight: allowance.WeightAllowance?.[0]?.MaxWeight || 'N/A',
      dimensions: allowance.DimensionAllowance?.[0] ?
        `${allowance.DimensionAllowance[0].Length || 'N/A'} x ${allowance.DimensionAllowance[0].Width || 'N/A'} x ${allowance.DimensionAllowance[0].Height || 'N/A'}` : 'N/A'
    }))

    return [...carryOnInfo, ...checkedBagInfo]
  }

  // Helper function to get fare rules and penalties
  const getFareRules = (booking: Booking) => {
    const detailedInfo = getDetailedBookingInfo(booking)
    if (!detailedInfo) return null

    const { penaltyList } = detailedInfo

    return penaltyList.map((penalty: any) => ({
      type: penalty.Details?.Detail?.[0]?.SubType || 'General',
      description: penalty.Details?.Detail?.[0]?.Description?.Text || 'No description available',
      amount: penalty.Details?.Detail?.[0]?.Amount ?
        `${penalty.Details.Detail[0].Amount.value} ${penalty.Details.Detail[0].Amount.Code}` : 'N/A',
      conditions: penalty.Details?.Detail?.[0]?.Remarks?.Remark || []
    }))
  }

  // Helper function to get detailed passenger information from OrderCreate
  const getDetailedPassengerInfo = (booking: Booking) => {
    const detailedInfo = getDetailedBookingInfo(booking)
    if (!detailedInfo) return getPassengerInfo(booking) // Fallback to basic info

    const { passengers } = detailedInfo

    if (passengers.length > 0) {
      return passengers.map((passenger: any, index: number) => ({
        firstName: passenger.Individual?.GivenName || `Passenger ${index + 1}`,
        lastName: passenger.Individual?.Surname || '',
        title: passenger.Individual?.NameTitle || '',
        dateOfBirth: passenger.Individual?.Birthdate || '',
        gender: passenger.Individual?.Gender || '',
        email: booking.contactInfo?.email || '',
        phone: booking.contactInfo?.phone || '',
        passportNumber: passenger.IdentityDocument?.IdentityDocumentNumber || '',
        passportExpiry: passenger.IdentityDocument?.ExpiryDate || '',
        nationality: passenger.IdentityDocument?.IssuingCountryCode || '',
        passengerType: passenger.PTC || 'ADT'
      }))
    }

    return getPassengerInfo(booking) // Fallback to basic info
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!booking) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Booking Not Found</h1>
          <p className="text-muted-foreground mb-6">
            The booking you're looking for doesn't exist or you don't have access to it.
          </p>
          <Button onClick={() => router.push("/manage")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Bookings
          </Button>
        </div>
      </div>
    )
  }

  // Safety check for booking data
  if (!booking.flightDetails || !booking.contactInfo) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Invalid Booking Data</h1>
          <p className="text-muted-foreground mb-6">
            This booking has incomplete data. Please contact support for assistance.
          </p>
          <Button onClick={() => router.push("/manage")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Bookings
          </Button>
        </div>
      </div>
    )
  }

  // Get normalized data - use transformed data when available
  const flightInfo = getFlightInfo(booking)
  const passengerInfo = itineraryData ? itineraryData.passengers : getDetailedPassengerInfo(booking)
  const baggageInfo = itineraryData ? itineraryData.baggageAllowance : getBaggageInfo(booking)
  const fareRules = itineraryData ? itineraryData.fareRules : getFareRules(booking)

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push("/manage")}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Bookings
        </Button>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Booking Details</h1>
            <p className="text-muted-foreground">
              Reference: {booking.bookingReference}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {getStatusBadge(booking.status)}
          </div>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Flight Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plane className="w-5 h-5" />
              Flight Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Outbound Flight */}
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                Outbound Flight
                {flightInfo.outbound.flightNumber && (
                  <span className="text-sm text-muted-foreground">
                    ({flightInfo.outbound.airline?.code} {flightInfo.outbound.flightNumber})
                  </span>
                )}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
                <div>
                  <p className="text-sm text-muted-foreground">Departure</p>
                  <p className="font-semibold">{flightInfo.outbound.departure.time}</p>
                  <p className="text-sm">{flightInfo.outbound.departure.city}</p>
                  <p className="text-xs text-muted-foreground">
                    {flightInfo.outbound.departure.airport}
                  </p>
                  {flightInfo.outbound.departure.terminal && flightInfo.outbound.departure.terminal !== 'N/A' && (
                    <p className="text-xs text-blue-600">Terminal: {flightInfo.outbound.departure.terminal}</p>
                  )}
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Duration</p>
                  <p className="font-semibold">{flightInfo.outbound.duration}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(flightInfo.outbound.departure.date)}
                  </p>
                  {flightInfo.outbound.aircraft && flightInfo.outbound.aircraft !== 'N/A' && (
                    <p className="text-xs text-blue-600">Aircraft: {flightInfo.outbound.aircraft}</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Arrival</p>
                  <p className="font-semibold">{flightInfo.outbound.arrival.time}</p>
                  <p className="text-sm">{flightInfo.outbound.arrival.city}</p>
                  <p className="text-xs text-muted-foreground">
                    {flightInfo.outbound.arrival.airport}
                  </p>
                  {flightInfo.outbound.arrival.terminal && flightInfo.outbound.arrival.terminal !== 'N/A' && (
                    <p className="text-xs text-blue-600">Terminal: {flightInfo.outbound.arrival.terminal}</p>
                  )}
                </div>
              </div>
              {flightInfo.outbound.classOfService && flightInfo.outbound.classOfService !== 'N/A' && (
                <div className="mt-2 p-2 bg-blue-50 rounded text-center">
                  <p className="text-sm text-blue-700">
                    <Building className="w-4 h-4 inline mr-1" />
                    Class of Service: <span className="font-semibold">{flightInfo.outbound.classOfService}</span>
                  </p>
                </div>
              )}
            </div>

            {/* Return Flight */}
            {flightInfo.return && (
              <div>
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Return Flight
                  {flightInfo.return.flightNumber && (
                    <span className="text-sm text-muted-foreground">
                      ({flightInfo.return.airline?.code} {flightInfo.return.flightNumber})
                    </span>
                  )}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
                  <div>
                    <p className="text-sm text-muted-foreground">Departure</p>
                    <p className="font-semibold">{flightInfo.return.departure.time}</p>
                    <p className="text-sm">{flightInfo.return.departure.city}</p>
                    <p className="text-xs text-muted-foreground">
                      {flightInfo.return.departure.airport}
                    </p>
                    {flightInfo.return.departure.terminal && flightInfo.return.departure.terminal !== 'N/A' && (
                      <p className="text-xs text-blue-600">Terminal: {flightInfo.return.departure.terminal}</p>
                    )}
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">Duration</p>
                    <p className="font-semibold">{flightInfo.return.duration}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(flightInfo.return.departure.date)}
                    </p>
                    {flightInfo.return.aircraft && flightInfo.return.aircraft !== 'N/A' && (
                      <p className="text-xs text-blue-600">Aircraft: {flightInfo.return.aircraft}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Arrival</p>
                    <p className="font-semibold">{flightInfo.return.arrival.time}</p>
                    <p className="text-sm">{flightInfo.return.arrival.city}</p>
                    <p className="text-xs text-muted-foreground">
                      {flightInfo.return.arrival.airport}
                    </p>
                    {flightInfo.return.arrival.terminal && flightInfo.return.arrival.terminal !== 'N/A' && (
                      <p className="text-xs text-blue-600">Terminal: {flightInfo.return.arrival.terminal}</p>
                    )}
                  </div>
                </div>
                {flightInfo.return.classOfService && flightInfo.return.classOfService !== 'N/A' && (
                  <div className="mt-2 p-2 bg-blue-50 rounded text-center">
                    <p className="text-sm text-blue-700">
                      <Building className="w-4 h-4 inline mr-1" />
                      Class of Service: <span className="font-semibold">{flightInfo.return.classOfService}</span>
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Passenger Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Passenger Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.isArray(passengerInfo) && passengerInfo.map((passenger: any, index: number) => (
                <div key={index} className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold">
                        {/* Handle both transformed data and legacy data */}
                        {itineraryData ? (
                          `${passenger.title || ''} ${passenger.firstName || ''} ${passenger.lastName || ''}`.trim()
                        ) : (
                          `${passenger.title || ''} ${passenger.firstName || ''} ${passenger.lastName || ''}`.trim()
                        )}
                      </h3>
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {itineraryData ? (passenger.passengerTypeLabel || 'Passenger') : (
                          passenger.passengerType === 'ADT' ? 'Adult' :
                          passenger.passengerType === 'CHD' ? 'Child' :
                          passenger.passengerType === 'INF' ? 'Infant' : (passenger.passengerType || 'Passenger')
                        )}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Ticket Number</p>
                      <p className="font-semibold text-blue-600">
                        {itineraryData ? passenger.ticketNumber : `TKT-${booking.bookingReference}-${index + 1}`}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Personal Information */}
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Personal Details</h4>
                      {(itineraryData ? passenger.birthDate : passenger.dateOfBirth) && (
                        <div className="mb-2">
                          <p className="text-sm text-muted-foreground">Date of Birth</p>
                          <p className="font-semibold">
                            {formatDate(itineraryData ? passenger.birthDate : passenger.dateOfBirth)}
                          </p>
                        </div>
                      )}
                      {itineraryData && passenger.age && (
                        <div>
                          <p className="text-sm text-muted-foreground">Age</p>
                          <p className="font-semibold">{passenger.age} years</p>
                        </div>
                      )}
                      {passenger.gender && (
                        <div>
                          <p className="text-sm text-muted-foreground">Gender</p>
                          <p className="font-semibold">{passenger.gender}</p>
                        </div>
                      )}
                    </div>

                    {/* Document Information */}
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Travel Document</h4>
                      <div className="mb-2">
                        <p className="text-sm text-muted-foreground">Document Type</p>
                        <p className="font-semibold">
                          {itineraryData ? (passenger.documentType === 'PT' ? 'Passport' : passenger.documentType) : 'Passport'}
                        </p>
                      </div>
                      {(itineraryData ? passenger.documentNumber : passenger.passportNumber) && (
                        <div className="mb-2">
                          <p className="text-sm text-muted-foreground">Document Number</p>
                          <p className="font-semibold font-mono">
                            {itineraryData ? passenger.documentNumber : passenger.passportNumber}
                          </p>
                        </div>
                      )}
                      {(itineraryData ? passenger.documentExpiry : passenger.passportExpiry) && (
                        <div className="mb-2">
                          <p className="text-sm text-muted-foreground">Document Expiry</p>
                          <p className="font-semibold">
                            {formatDate(itineraryData ? passenger.documentExpiry : passenger.passportExpiry)}
                          </p>
                        </div>
                      )}
                      {(itineraryData ? passenger.countryOfIssuance : passenger.nationality) && (
                        <div>
                          <p className="text-sm text-muted-foreground">Issuing Country</p>
                          <p className="font-semibold">
                            {itineraryData ? passenger.countryOfIssuance : passenger.nationality}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Additional Information */}
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Additional Info</h4>
                      <div className="mb-2">
                        <p className="text-sm text-muted-foreground">Passenger ID</p>
                        <p className="font-semibold font-mono">
                          {itineraryData ? passenger.objectKey : `PAX-${index + 1}`}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Passenger Type</p>
                        <p className="font-semibold">{passenger.passengerType}</p>
                      </div>
                      {itineraryData && passenger.email && (
                        <div className="mt-2">
                          <p className="text-sm text-muted-foreground">Email</p>
                          <p className="font-semibold text-xs">{passenger.email}</p>
                        </div>
                      )}
                      {itineraryData && passenger.phone && (
                        <div className="mt-2">
                          <p className="text-sm text-muted-foreground">Phone</p>
                          <p className="font-semibold text-xs">{passenger.phone}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Important Notice */}
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-xs text-yellow-800">
                      <span className="font-semibold">⚠️ Important:</span> Please ensure your travel document is valid for at least 6 months from the date of travel and has sufficient blank pages for entry stamps.
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold text-blue-800">
                  Total Passengers: {passengerInfo.length}
                </span>
                <div className="flex space-x-4">
                  {['ADT', 'CHD', 'INF'].map(type => {
                    const count = passengerInfo.filter((p: any) => p.passengerType === type).length;
                    if (count > 0) {
                      return (
                        <span key={type} className="text-blue-600">
                          {type}: {count}
                        </span>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Baggage Information */}
        {baggageInfo && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Luggage className="w-5 h-5" />
                Baggage Allowance
              </CardTitle>
            </CardHeader>
            <CardContent>
              {itineraryData && !Array.isArray(baggageInfo) && 'carryOnBags' in baggageInfo ? (
                // Use transformed baggage data
                <div className="space-y-4">
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                          <Luggage className="w-4 h-4" />
                          Carry-On Baggage
                        </h4>
                        <div className="space-y-2">
                          <p className="text-sm">
                            <span className="font-medium">Pieces:</span> {baggageInfo.carryOnBags}
                          </p>
                          {baggageInfo.carryOnAllowance?.weight && (
                            <p className="text-sm">
                              <span className="font-medium">Weight:</span> {baggageInfo.carryOnAllowance.weight.value} {baggageInfo.carryOnAllowance.weight.unit}
                            </p>
                          )}
                          {baggageInfo.carryOnAllowance?.description && (
                            <p className="text-sm text-muted-foreground">{baggageInfo.carryOnAllowance.description}</p>
                          )}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                          <Luggage className="w-4 h-4" />
                          Checked Baggage
                        </h4>
                        <div className="space-y-2">
                          <p className="text-sm">
                            <span className="font-medium">Pieces:</span> {baggageInfo.checkedBags}
                          </p>
                          {baggageInfo.checkedBagAllowance?.weight && (
                            <p className="text-sm">
                              <span className="font-medium">Weight:</span> {baggageInfo.checkedBagAllowance.weight.value} {baggageInfo.checkedBagAllowance.weight.unit}
                            </p>
                          )}
                          {baggageInfo.checkedBagAllowance?.description && (
                            <p className="text-sm text-muted-foreground">{baggageInfo.checkedBagAllowance.description}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                // Use legacy baggage data
                Array.isArray(baggageInfo) && baggageInfo.length > 0 && (
                  <div className="space-y-4">
                    {baggageInfo.map((baggage: any, index: number) => (
                      <div key={index} className="p-4 bg-muted/50 rounded-lg">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <div>
                            <p className="text-sm text-muted-foreground">Type</p>
                            <p className="font-semibold">{baggage.type}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Pieces</p>
                            <p className="font-semibold">{baggage.pieces}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Weight</p>
                            <p className="font-semibold">{baggage.weight}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Dimensions</p>
                            <p className="font-semibold text-xs">{baggage.dimensions}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              )}
            </CardContent>
          </Card>
        )}

        {/* Fare Rules and Penalties */}
        {fareRules && Array.isArray(fareRules) && fareRules.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Fare Rules & Penalties
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {fareRules.map((rule: any, index: number) => (
                  <div key={index} className="p-4 bg-muted/50 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Rule Type</p>
                        <p className="font-semibold">{itineraryData ? rule.category : rule.type}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Penalty Amount</p>
                        <p className="font-semibold">
                          {itineraryData ? (
                            rule.penalty ? `${rule.penalty.amount} ${rule.penalty.currency}` : 'N/A'
                          ) : (
                            rule.amount
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Description</p>
                        <p className="text-sm">{rule.description}</p>
                      </div>
                    </div>
                    {itineraryData && rule.interpretation && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-sm text-muted-foreground mb-2">Interpretation:</p>
                        <p className="text-sm bg-blue-50 p-2 rounded border-l-4 border-blue-200">
                          {rule.interpretation}
                        </p>
                      </div>
                    )}
                    {!itineraryData && rule.conditions && rule.conditions.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-sm text-muted-foreground mb-2">Conditions:</p>
                        <ul className="text-xs space-y-1">
                          {rule.conditions.map((condition: string, condIndex: number) => (
                            <li key={condIndex} className="flex items-start gap-2">
                              <span className="text-muted-foreground">•</span>
                              <span>{condition}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Booking Reference & Order Details */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ticket className="w-5 h-5" />
              Booking Reference & Order Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Info className="w-4 h-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Booking Reference</p>
                </div>
                <p className="font-bold text-lg">{booking.bookingReference}</p>
              </div>
              {booking.orderItemId && (
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Globe className="w-4 h-4 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">Order ID</p>
                  </div>
                  <p className="font-semibold">{booking.orderItemId}</p>
                </div>
              )}
              <div className="p-4 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Booking Date</p>
                </div>
                <p className="font-semibold">{formatDateTime(booking.createdAt)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        {booking.contactInfo && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Phone className="w-5 h-5" />
                Contact Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <Mail className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Email</p>
                    <p className="font-semibold">{booking.contactInfo?.email || 'Not provided'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Phone className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Phone</p>
                    <p className="font-semibold">{booking.contactInfo?.phone || 'Not provided'}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Payment Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="w-5 h-5" />
              Payment Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <CreditCard className="w-4 h-4 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">Total Amount</p>
                  </div>
                  <p className="text-2xl font-bold">{getFormattedPrice(booking)}</p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">Payment Status</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(booking.status)}
                  </div>
                </div>
              </div>

              {booking.payments && booking.payments.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Timer className="w-4 h-4" />
                    Payment History
                  </h4>
                  {booking.payments.map((payment) => (
                    <div key={payment.id} className="flex justify-between items-center p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">${payment.amount}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatDateTime(payment.createdAt)}
                        </p>
                      </div>
                      <Badge
                        className={
                          payment.status === "succeeded"
                            ? "bg-green-100 text-green-800"
                            : payment.status === "pending"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-red-100 text-red-800"
                        }
                      >
                        {payment.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Important Travel Information */}
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700">
              <Info className="w-5 h-5" />
              Important Travel Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                <span>Please arrive at the airport at least 2 hours before domestic flights and 3 hours before international flights.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                <span>Ensure your passport is valid for at least 6 months from your travel date for international flights.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                <span>Check visa requirements for your destination country before traveling.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                <span>Review baggage restrictions and prohibited items before packing.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                <span>Web check-in is available 24 hours before departure for most airlines.</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                className="flex-1"
                variant="outline"
                onClick={handleDownloadItinerary}
                disabled={isDownloading || !itineraryData}
              >
                <Download className="w-4 h-4 mr-2" />
                {isDownloading ? "Generating PDF..." : "Download Itinerary"}
              </Button>

              {booking.status !== "cancelled" && (
                <Link href={`/manage/${booking.bookingReference}/edit`} className="flex-1">
                  <Button variant="outline" className="w-full">
                    <Edit className="w-4 h-4 mr-2" />
                    Modify Booking
                  </Button>
                </Link>
              )}

              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  toast({
                    title: "Contact Support",
                    description: "Please call +1-800-FLIGHTS or email support@reatravels.com for assistance.",
                  })
                }}
              >
                <Phone className="w-4 h-4 mr-2" />
                Contact Support
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Hidden Official Itinerary Component for PDF Generation */}
      {itineraryData && (
        <div id="manage-itinerary-component" style={{ position: 'absolute', left: '-9999px', top: '-9999px' }}>
          <OfficialItinerary data={itineraryData} />
        </div>
      )}
    </div>
  )
}
