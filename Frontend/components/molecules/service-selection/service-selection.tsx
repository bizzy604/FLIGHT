"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { Check, Plus, Minus, Utensils, Luggage, UserPlus, Wifi, Star } from "lucide-react"

import { cn } from "@/utils/cn"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { LoadingSpinner } from "@/components/atoms"
import { api } from "@/utils/api-client"

interface Service {
  objectKey: string
  serviceId: {
    objectKey: string
    value: string
    owner: string
  }
  name: {
    value: string
  }
  descriptions?: {
    description: Array<{
      text: {
        value: string
      }
    }>
  }
  price: Array<{
    total: {
      value: number
      code: string
    }
  }>
  associations: Array<{
    traveler?: {
      travelerReferences: string[]
    }
    flight?: {
      originDestinationReferencesOrSegmentReferences: Array<{
        segmentReferences: {
          value: string[]
        }
      }>
    }
  }>
  pricedInd: boolean
  category?: string
  bookingInstructions?: {
    ssrCode?: string[]
    method?: string
  }
}

interface ServiceListResponse {
  services: {
    service: Service[]
  }
  shoppingResponseId: {
    responseId: {
      value: string
    }
  }
}

interface ServiceSelectionProps {
  flightPriceResponse: any
  selectedServices: string[]
  onServiceChange: (updatedServices: string[]) => void
  passengers: Array<{
    objectKey: string
    name: string
    type: string
  }>
  className?: string
}

export function ServiceSelection({ 
  flightPriceResponse, 
  selectedServices, 
  onServiceChange, 
  passengers,
  className 
}: ServiceSelectionProps) {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [servicesByCategory, setServicesByCategory] = useState<Record<string, Service[]>>({})
  const [activeTab, setActiveTab] = useState('meals')

  // Load services from backend
  useEffect(() => {
    const loadServices = async () => {
      if (!flightPriceResponse) return

      setLoading(true)
      setError(null)

      try {
        // Check cache first
        const cacheResponse = await api.checkServiceListCache(flightPriceResponse)
        
        let servicesData = null
        
        if (cacheResponse.data?.cache_hit) {
          console.log("ServiceList cache hit")
          servicesData = cacheResponse.data.data
        } else {
          console.log("ServiceList cache miss, fetching from API")
          const response = await api.getServiceList(flightPriceResponse)
          servicesData = response.data
        }

        if (servicesData?.services?.service) {
          const servicesList = servicesData.services.service
          setServices(servicesList)
          
          // Categorize services
          const categorized = categorizeServices(servicesList)
          setServicesByCategory(categorized)
        } else {
          setServices([])
          setServicesByCategory({})
        }
      } catch (err) {
        console.error("Error loading services:", err)
        setError("Failed to load services. Please try again.")
        setServices([])
        setServicesByCategory({})
      } finally {
        setLoading(false)
      }
    }

    loadServices()
  }, [flightPriceResponse])

  // Categorize services by type - enhanced for better categorization
  const categorizeServices = (servicesList: Service[]): Record<string, Service[]> => {
    const categories: Record<string, Service[]> = {
      meals: [],
      baggage: [],
      assistance: []
    }

    servicesList.forEach(service => {
      const serviceName = service.name?.value?.toLowerCase() || ""
      const serviceCode = service.serviceId?.value?.toLowerCase() || ""

      // Meal services (AVML, BBML, BLML, CHML, etc.)
      if (serviceName.includes("meal") || serviceName.includes("food") || 
          serviceCode.includes("ml") || serviceCode.includes("meal") ||
          ['avml', 'bbml', 'blml', 'chml', 'dbml', 'fpml', 'gfml', 'hnml', 'ksml', 'lcml', 'lfml', 'lsml', 'nlml', 'rvml', 'vjml', 'vlml', 'voml'].includes(serviceCode)) {
        categories.meals.push(service)
      } 
      // Baggage services (XWBG, XBAG, etc.)
      else if (serviceName.includes("bag") || serviceName.includes("luggage") || serviceName.includes("weight") ||
               serviceCode.includes("bag") || serviceCode.includes("xwbg") || serviceCode.includes("wbg")) {
        categories.baggage.push(service)
      } 
      // Assistance services (WCHR, WCHS, etc.)
      else if (serviceName.includes("wheelchair") || serviceName.includes("assistance") || serviceName.includes("help") ||
               serviceCode.includes("wch") || serviceCode.includes("wchr") || serviceCode.includes("wchs")) {
        categories.assistance.push(service)
      }
      // Default to meals if unsure
      else {
        categories.meals.push(service)
      }
    })

    // Remove empty categories
    Object.keys(categories).forEach(key => {
      if (categories[key].length === 0) {
        delete categories[key]
      }
    })

    return categories
  }

  // Get service icon based on category
  const getServiceIcon = (categoryKey: string) => {
    switch (categoryKey) {
      case 'meals':
        return <Utensils className="h-5 w-5" />
      case 'baggage':
        return <Luggage className="h-5 w-5" />
      case 'seats':
        return <UserPlus className="h-5 w-5" />
      case 'priority':
        return <Star className="h-5 w-5" />
      default:
        return <Plus className="h-5 w-5" />
    }
  }

  // Get category display name
  const getCategoryName = (categoryKey: string) => {
    switch (categoryKey) {
      case 'meals':
        return 'Meals'
      case 'baggage':
        return 'Baggage'
      case 'assistance':
        return 'Special Assistance'
      default:
        return 'Other Services'
    }
  }

  const handleServiceToggle = (serviceObjectKey: string) => {
    const isSelected = selectedServices.includes(serviceObjectKey)
    
    let updatedServices: string[]
    if (isSelected) {
      // Remove service
      updatedServices = selectedServices.filter(s => s !== serviceObjectKey)
    } else {
      // Add service
      updatedServices = [...selectedServices, serviceObjectKey]
    }
    
    onServiceChange(updatedServices)
  }

  const getSelectedServicePrice = (service: Service): number => {
    return service.price?.[0]?.total?.value || 0
  }

  const getTotalPrice = (): number => {
    return selectedServices.reduce((total, serviceObjectKey) => {
      const service = services.find(s => s.objectKey === serviceObjectKey)
      return total + (service ? getSelectedServicePrice(service) : 0)
    }, 0)
  }

  const getCurrency = (): string => {
    const firstService = services.find(s => s.price?.[0]?.total?.code)
    return firstService?.price?.[0]?.total?.code || 'USD'
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Additional Services</CardTitle>
          <CardDescription>Loading available services...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner className="h-6 w-6" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Additional Services</CardTitle>
          <CardDescription className="text-red-600">{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Button 
              variant="outline" 
              onClick={() => window.location.reload()}
            >
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (Object.keys(servicesByCategory).length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Additional Services</CardTitle>
          <CardDescription>No additional services are available for this flight.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Services Header */}
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-6 bg-purple-600 rounded-full"></div>
          <h2 className="text-xl font-bold text-gray-900">Add Services</h2>
        </div>
        
        {/* Service Tabs */}
        <div className="flex gap-2 mb-6 border-b-2 border-gray-200">
          {Object.keys(servicesByCategory).map((categoryKey) => (
            <button
              key={categoryKey}
              className={cn(
                "px-5 py-3 font-semibold transition-all duration-300 relative",
                activeTab === categoryKey
                  ? "text-purple-600 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-1 after:bg-purple-600 after:rounded-t-md"
                  : "text-gray-600 hover:text-gray-900"
              )}
              onClick={() => setActiveTab(categoryKey)}
            >
              {getCategoryName(categoryKey)}
            </button>
          ))}
        </div>

        {/* Service Grid */}
        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
          {servicesByCategory[activeTab]?.map((service) => {
            const isSelected = selectedServices.includes(service.objectKey)
            const price = getSelectedServicePrice(service)
            const currency = service.price?.[0]?.total?.code || 'USD'
            const isFree = price === 0

            return (
              <div
                key={service.objectKey}
                className={cn(
                  "border-2 rounded-xl p-4 cursor-pointer transition-all duration-300 relative overflow-hidden",
                  isSelected 
                    ? "border-green-500 bg-gradient-to-r from-green-50 to-green-100" 
                    : "border-gray-200 hover:border-purple-400 hover:shadow-md hover:-translate-y-1"
                )}
                onClick={() => handleServiceToggle(service.objectKey)}
              >
                {/* Selection checkmark */}
                {isSelected && (
                  <div className="absolute top-3 right-3 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <Check className="h-4 w-4 text-white font-bold" />
                  </div>
                )}

                <div className="flex justify-between items-start">
                  <div className="flex-1 pr-10">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold text-gray-900">{service.name?.value}</h4>
                      {service.bookingInstructions?.ssrCode && (
                        <Badge variant="secondary" className="text-xs bg-gray-100 text-gray-600">
                          {service.bookingInstructions.ssrCode[0]}
                        </Badge>
                      )}
                    </div>
                    
                    {service.descriptions?.description?.[0]?.text?.value && (
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {service.descriptions.description[0].text.value}
                      </p>
                    )}
                  </div>

                  <div className="text-right">
                    {isFree ? (
                      <span className="inline-block px-3 py-1 bg-green-100 text-green-700 text-sm font-semibold rounded-lg">
                        FREE
                      </span>
                    ) : (
                      <div className="text-lg font-bold text-purple-600">
                        ₹{price.toLocaleString('en-IN')}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
          
          {(!servicesByCategory[activeTab] || servicesByCategory[activeTab].length === 0) && (
            <div className="text-center py-8 text-gray-500">
              No {getCategoryName(activeTab).toLowerCase()} services available for this flight.
            </div>
          )}
        </div>
      </div>

      {/* Selected Services Summary */}
      {selectedServices.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-green-800">Selected Services ({selectedServices.length})</h4>
              <p className="text-sm text-green-600">
                {selectedServices.map(serviceKey => {
                  const service = services.find(s => s.objectKey === serviceKey)
                  return service?.name?.value
                }).filter(Boolean).join(", ")}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-green-600">Total Additional Services</div>
              <div className="font-bold text-xl text-green-800">
                ₹{getTotalPrice().toLocaleString('en-IN')}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}