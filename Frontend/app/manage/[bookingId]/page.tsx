'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useUser } from '@clerk/nextjs'
import { useToast } from '@/hooks/use-toast'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { 
  ArrowLeft, 
  Download, 
  Phone, 
  Mail, 
  Calendar, 
  Clock, 
  MapPin, 
  Plane,
  User,
  CreditCard,
  FileText,
  AlertCircle
} from 'lucide-react'
import { OfficialItinerary } from '@/components/organisms/official-itinerary/official-itinerary'
import { generatePDFFromComponent } from '@/utils/download-utils'

interface Booking {
  id: string
  bookingReference: string
  status: string
  totalAmount?: number
  currency?: string
  pricing?: {
    total?: {
      amount?: number
      currency?: string
    }
  }
  createdAt: string
  contactInfo?: {
    email?: string
    phone?: string | {
      countryCode?: string
      number?: string
      formatted?: string
    }
  }
  passengers?: Array<{
    firstName: string
    lastName: string
    title?: string
    dateOfBirth?: string
    gender?: string
    passportNumber?: string
    passportExpiry?: string
    nationality?: string
  }>
  flightDetails?: {
    outbound?: {
      departure?: {
        city?: string
        airport?: string
        code?: string
        date?: string
        fullDate?: string
        time?: string
        terminal?: string
      }
      arrival?: {
        city?: string
        airport?: string
        code?: string
        date?: string
        fullDate?: string
        time?: string
        terminal?: string
      }
      flightNumber?: string
      airline?: {
        code?: string
        name?: string
        flightNumber?: string
        logo?: string
      }
      duration?: string
      classOfService?: string
      aircraft?: {
        type?: string
        model?: string
      }
    }
    return?: {
      departure?: {
        city?: string
        airport?: string
        code?: string
        date?: string
        fullDate?: string
        time?: string
        terminal?: string
      }
      arrival?: {
        city?: string
        airport?: string
        code?: string
        date?: string
        fullDate?: string
        time?: string
        terminal?: string
      }
      flightNumber?: string
      airline?: {
        code?: string
        name?: string
        flightNumber?: string
        logo?: string
      }
      duration?: string
      classOfService?: string
      aircraft?: {
        type?: string
        model?: string
      }
    }
  }
  baggageAllowance?: {
    carryOnAllowance?: {
      pieces?: number | string
      weight?: string
      description?: string
    }
    checkedBagAllowance?: {
      pieces?: number | string
      weight?: string
      description?: string
    }
  }
}

export default function BookingDetailsPage() {
  const router = useRouter()
  const params = useParams()
  const bookingId = params.bookingId as string
  const { isLoaded, isSignedIn } = useUser()
  const { toast } = useToast()

  const [isLoading, setIsLoading] = useState(true)
  const [booking, setBooking] = useState<Booking | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  useEffect(() => {
    const fetchBookingDetails = async () => {
      if (!isLoaded) return

      if (!isSignedIn) {
        router.push('/sign-in')
        return
      }

      try {
        setIsLoading(true)
        const response = await fetch(`/api/bookings/${bookingId}`)
        
        if (!response.ok) {
          throw new Error('Failed to fetch booking details')
        }

        const data = await response.json()
        setBooking(data)
      } catch (error) {
        console.error('Error fetching booking details:', error)
        toast({
          title: 'Error',
          description: 'Failed to load booking details. Please try again.',
          variant: 'destructive',
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookingDetails()
  }, [isLoaded, isSignedIn, bookingId, router, toast])

  const handleDownloadItinerary = async () => {
    if (!booking) return

    try {
      setIsDownloading(true)
      
      // Create itinerary data for the PDF
      const itineraryData = {
        bookingInfo: {
          bookingReference: booking.bookingReference,
          orderId: booking.id,
          status: booking.status,
          issueDateFormatted: new Date(booking.createdAt).toLocaleDateString()
        },
        passengers: booking.passengers || [],
        baggageAllowance: booking.baggageAllowance,
        outboundFlight: booking.flightDetails?.outbound,
        returnFlight: booking.flightDetails?.return,
        contactInfo: booking.contactInfo,
        additionalServices: [],
        fareRules: []
      }

      // Create a temporary element for PDF generation
      const tempElement = document.createElement('div')
      tempElement.id = 'manage-itinerary-component'
      tempElement.style.display = 'none'
      document.body.appendChild(tempElement)
      
      // Render the component temporarily
      const { createRoot } = await import('react-dom/client')
      const root = createRoot(tempElement)
      root.render(<OfficialItinerary data={itineraryData} />)
      
      // Wait for rendering to complete
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // Generate PDF
      await generatePDFFromComponent(
        'manage-itinerary-component',
        `flight-itinerary-${booking.bookingReference}.pdf`
      )
      
      // Clean up
      root.unmount()
      document.body.removeChild(tempElement)

      toast({
        title: 'Success',
        description: 'Itinerary downloaded successfully!',
      })
    } catch (error) {
      console.error('Error downloading itinerary:', error)
      toast({
        title: 'Error',
        description: 'Failed to download itinerary. Please try again.',
        variant: 'destructive',
      })
    } finally {
      setIsDownloading(false)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    } catch {
      return dateString
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      confirmed: { variant: 'default' as const, label: 'Confirmed' },
      pending: { variant: 'secondary' as const, label: 'Pending' },
      cancelled: { variant: 'destructive' as const, label: 'Cancelled' },
      completed: { variant: 'outline' as const, label: 'Completed' }
    }

    const config = statusConfig[status.toLowerCase() as keyof typeof statusConfig] || 
                  { variant: 'secondary' as const, label: status }

    return (
      <Badge variant={config.variant}>
        {config.label}
      </Badge>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!booking) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card>
          <CardContent className="p-8 text-center">
            <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Booking Not Found</h2>
            <p className="text-muted-foreground mb-4">
              The booking you're looking for doesn't exist or you don't have permission to view it.
            </p>
            <Button onClick={() => router.push('/manage')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Manage Bookings
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/manage')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Booking Details</h1>
            <p className="text-muted-foreground">Reference: {booking.bookingReference}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge(booking.status)}
        </div>
      </div>

      {/* Booking Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Booking Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Booking Reference</p>
              <p className="font-semibold">{booking.bookingReference}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Amount</p>
              <p className="font-semibold">
                {booking.pricing?.total?.currency || booking.currency || 'N/A'} {booking.pricing?.total?.amount?.toLocaleString() || booking.totalAmount?.toLocaleString() || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Booking Date</p>
              <p className="font-semibold">{formatDate(booking.createdAt)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Flight Information */}
      {booking.flightDetails && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plane className="w-5 h-5" />
              Flight Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Outbound Flight */}
            {booking.flightDetails.outbound && (
              <div>
                <h3 className="font-semibold mb-4 text-primary-600">Outbound Flight</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Departure</p>
                    <p className="font-semibold">
                      {booking.flightDetails.outbound.departure?.city || 'N/A'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {booking.flightDetails.outbound.departure?.airport || 'N/A'}
                    </p>
                    {booking.flightDetails.outbound.departure?.fullDate && (
                      <p className="text-sm">
                        {formatDate(booking.flightDetails.outbound.departure.fullDate)}
                      </p>
                    )}
                    {booking.flightDetails.outbound.departure?.time && (
                      <p className="text-sm">
                        {booking.flightDetails.outbound.departure.time}
                      </p>
                    )}
                    {booking.flightDetails.outbound.departure?.terminal && (
                      <p className="text-xs text-blue-600">
                        Terminal: {booking.flightDetails.outbound.departure.terminal}
                      </p>
                    )}
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">Duration</p>
                    <p className="font-semibold">
                      {booking.flightDetails.outbound.duration || 'N/A'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {booking.flightDetails.outbound.airline?.flightNumber || booking.flightDetails.outbound.flightNumber || 'N/A'}
                    </p>
                    {booking.flightDetails.outbound.airline && (
                      <p className="text-sm">
                        {booking.flightDetails.outbound.airline.name || booking.flightDetails.outbound.airline.code || 'N/A'}
                      </p>
                    )}
                    {booking.flightDetails.outbound.aircraft && (
                      <p className="text-xs text-blue-600">
                        Aircraft: {booking.flightDetails.outbound.aircraft.type || booking.flightDetails.outbound.aircraft.model || 'N/A'}
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Arrival</p>
                    <p className="font-semibold">
                      {booking.flightDetails.outbound.arrival?.city || 'N/A'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {booking.flightDetails.outbound.arrival?.airport || 'N/A'}
                    </p>
                    {booking.flightDetails.outbound.arrival?.fullDate && (
                      <p className="text-sm">
                        {formatDate(booking.flightDetails.outbound.arrival.fullDate)}
                      </p>
                    )}
                    {booking.flightDetails.outbound.arrival?.time && (
                      <p className="text-sm">
                        {booking.flightDetails.outbound.arrival.time}
                      </p>
                    )}
                    {booking.flightDetails.outbound.arrival?.terminal && (
                      <p className="text-xs text-blue-600">
                        Terminal: {booking.flightDetails.outbound.arrival.terminal}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Return Flight */}
            {booking.flightDetails.return && (
              <>
                <Separator />
                <div>
                  <h3 className="font-semibold mb-4 text-primary-600">Return Flight</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Departure</p>
                      <p className="font-semibold">
                        {booking.flightDetails.return.departure?.city || 'N/A'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {booking.flightDetails.return.departure?.airport || 'N/A'}
                      </p>
                      {booking.flightDetails.return.departure?.fullDate && (
                        <p className="text-sm">
                          {formatDate(booking.flightDetails.return.departure.fullDate)}
                        </p>
                      )}
                      {booking.flightDetails.return.departure?.time && (
                        <p className="text-sm">
                          {booking.flightDetails.return.departure.time}
                        </p>
                      )}
                      {booking.flightDetails.return.departure?.terminal && (
                        <p className="text-xs text-blue-600">
                          Terminal: {booking.flightDetails.return.departure.terminal}
                        </p>
                      )}
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Duration</p>
                      <p className="font-semibold">
                        {booking.flightDetails.return.duration || 'N/A'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {booking.flightDetails.return.airline?.flightNumber || booking.flightDetails.return.flightNumber || 'N/A'}
                      </p>
                      {booking.flightDetails.return.airline && (
                        <p className="text-sm">
                          {booking.flightDetails.return.airline.name || booking.flightDetails.return.airline.code || 'N/A'}
                        </p>
                      )}
                      {booking.flightDetails.return.aircraft && (
                        <p className="text-xs text-blue-600">
                          Aircraft: {booking.flightDetails.return.aircraft.type || booking.flightDetails.return.aircraft.model || 'N/A'}
                        </p>
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Arrival</p>
                      <p className="font-semibold">
                        {booking.flightDetails.return.arrival?.city || 'N/A'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {booking.flightDetails.return.arrival?.airport || 'N/A'}
                      </p>
                      {booking.flightDetails.return.arrival?.fullDate && (
                        <p className="text-sm">
                          {formatDate(booking.flightDetails.return.arrival.fullDate)}
                        </p>
                      )}
                      {booking.flightDetails.return.arrival?.time && (
                        <p className="text-sm">
                          {booking.flightDetails.return.arrival.time}
                        </p>
                      )}
                      {booking.flightDetails.return.arrival?.terminal && (
                        <p className="text-xs text-blue-600">
                          Terminal: {booking.flightDetails.return.arrival.terminal}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Passenger Information */}
      {booking.passengers && booking.passengers.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Passenger Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {booking.passengers.map((passenger, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Name</p>
                      <p className="font-semibold">
                        {passenger.title && `${passenger.title} `}
                        {passenger.firstName} {passenger.lastName}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Date of Birth</p>
                      <p className="font-semibold">
                        {passenger.dateOfBirth ? formatDate(passenger.dateOfBirth) : 'N/A'}
                      </p>
                    </div>
                    {passenger.passportNumber && (
                      <div>
                        <p className="text-sm text-muted-foreground">Passport Number</p>
                        <p className="font-semibold font-mono">{passenger.passportNumber}</p>
                      </div>
                    )}
                    {passenger.nationality && (
                      <div>
                        <p className="text-sm text-muted-foreground">Nationality</p>
                        <p className="font-semibold">{passenger.nationality}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Baggage Allowance */}
      {booking.baggageAllowance && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Baggage Allowance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {booking.baggageAllowance.carryOnAllowance && (
                <div>
                  <h3 className="font-semibold mb-2">Carry-On Baggage</h3>
                  <div className="space-y-2">
                    {booking.baggageAllowance.carryOnAllowance.pieces && (
                      <p className="text-sm">
                        <span className="font-medium">Pieces:</span> {booking.baggageAllowance.carryOnAllowance.pieces}
                      </p>
                    )}
                    {booking.baggageAllowance.carryOnAllowance.weight && (
                      <p className="text-sm">
                        <span className="font-medium">Weight:</span> {booking.baggageAllowance.carryOnAllowance.weight}
                      </p>
                    )}
                    {booking.baggageAllowance.carryOnAllowance.description && (
                      <p className="text-sm text-muted-foreground">
                        {booking.baggageAllowance.carryOnAllowance.description}
                      </p>
                    )}
                  </div>
                </div>
              )}
              {booking.baggageAllowance.checkedBagAllowance && (
                <div>
                  <h3 className="font-semibold mb-2">Checked Baggage</h3>
                  <div className="space-y-2">
                    {booking.baggageAllowance.checkedBagAllowance.pieces && (
                      <p className="text-sm">
                        <span className="font-medium">Pieces:</span> {booking.baggageAllowance.checkedBagAllowance.pieces}
                      </p>
                    )}
                    {booking.baggageAllowance.checkedBagAllowance.weight && (
                      <p className="text-sm">
                        <span className="font-medium">Weight:</span> {booking.baggageAllowance.checkedBagAllowance.weight}
                      </p>
                    )}
                    {booking.baggageAllowance.checkedBagAllowance.description && (
                      <p className="text-sm text-muted-foreground">
                        {booking.baggageAllowance.checkedBagAllowance.description}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Contact Information */}
      {booking.contactInfo && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Contact Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {booking.contactInfo.email && (
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-semibold">{booking.contactInfo.email}</p>
                </div>
              )}
              {booking.contactInfo.phone && (
                <div>
                  <p className="text-sm text-muted-foreground">Phone</p>
                  <p className="font-semibold">
                    {typeof booking.contactInfo.phone === 'string' 
                      ? booking.contactInfo.phone 
                      : booking.contactInfo.phone.formatted || 
                        `${booking.contactInfo.phone.countryCode || ''} ${booking.contactInfo.phone.number || ''}`.trim()
                    }
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button 
              onClick={handleDownloadItinerary}
              disabled={isDownloading}
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              {isDownloading ? 'Downloading...' : 'Download Itinerary'}
            </Button>
            
            <Button variant="outline" className="flex items-center gap-2">
              <Phone className="w-4 h-4" />
              Contact Support
            </Button>
            
            <Button variant="outline" className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Email Support
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
