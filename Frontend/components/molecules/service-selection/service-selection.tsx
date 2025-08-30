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
import { seatServiceCache } from "@/utils/seat-service-cache-manager"
import { logger } from "@/utils/logger"
import { formatCurrency, formatCurrencyForDisplay } from "@/utils/currency-formatter"
import { BaggageOptions, type BaggageSelection } from "@/components/molecules/baggage-options"

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
  onServicesUpdate?: (services: any[]) => void // New callback for services data
  onPricingUpdate?: (totalPrice: number, servicesCount: number, currency: string) => void // Direct pricing callback
  selectedBaggage?: BaggageSelection
  onBaggageChange?: (baggage: BaggageSelection) => void
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
  onServicesUpdate,
  onPricingUpdate,
  selectedBaggage = { checkedBags: 0, specialEquipment: 'none' },
  onBaggageChange,
  passengers,
  className 
}: ServiceSelectionProps) {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [servicesByCategory, setServicesByCategory] = useState<Record<string, Service[]>>({})
  const [activeTab, setActiveTab] = useState('meals')

  // Load services from backend with intelligent caching
  useEffect(() => {
    const loadServices = async () => {
      if (!flightPriceResponse) return

      setLoading(true)
      setError(null)

      try {
        logger.info('🛎️ Loading service list data...')
        
        // 🚀 STEP 1: Check proactive loading cache first (from simple-api-manager)
        const sessionId = localStorage.getItem('flight_session_id')
        if (sessionId) {
          // Check simple cache manager first (populated by proactive loading)
          const simpleCacheManager = await import('@/utils/simple-cache-manager')
          const proactiveCacheResult = simpleCacheManager.simpleCacheManager.getServiceList(sessionId)
          
          if (proactiveCacheResult.success && proactiveCacheResult.data) {
            logger.info('⚡ Using proactively loaded service list data!')
            processServiceListData(proactiveCacheResult.data)
            setLoading(false)
            return
          }
        }

        // 🚀 STEP 2: Check our pre-loaded cache as fallback
        const cachedResult = seatServiceCache.getCachedServiceList(flightPriceResponse)
        
        if (cachedResult.data) {
          logger.info('⚡ Using pre-loaded service list data from cache!')
          const servicesData = cachedResult.data
          
          // Process cached data
          processServiceListData(servicesData)
          setLoading(false)
          return
        } 
        
        if (cachedResult.isLoading) {
          logger.info('🔄 Service list data is still loading in background, waiting with exponential backoff...')
          // Use exponential backoff to wait for global preloading to complete
          await waitForCacheWithBackoff(flightPriceResponse, 5, 1000) // 5 retries, starting with 1 second
          return
        }

        if (cachedResult.error) {
          logger.warn('⚠️ Service pre-loading failed with error:', cachedResult.error)
        }

        // 🚀 STEP 2: Fall back to direct API call
        logger.info('💻 No pre-loaded service data available, using direct API call')
        await fallbackToApiCall()

      } catch (err) {
        logger.error("❌ Error loading services:", err)
        setError("Failed to load services. Please try again.")
        setServices([])
        setServicesByCategory({})
      } finally {
        setLoading(false)
      }
    }

    // 🚀 ENHANCED: Wait for cache with exponential backoff to prevent redundant API calls
    const waitForCacheWithBackoff = async (flightPriceResponse: any, maxRetries: number, initialDelay: number) => {
      let delay = initialDelay
      
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        logger.info(`🔄 Service cache wait attempt ${attempt}/${maxRetries}, delay: ${delay}ms`)
        
        await new Promise(resolve => setTimeout(resolve, delay))
        
        const retryResult = seatServiceCache.getCachedServiceList(flightPriceResponse)
        
        if (retryResult.data) {
          logger.info(`✅ Got pre-loaded service list data after ${attempt} attempts!`)
          processServiceListData(retryResult.data)
          setLoading(false)
          return
        }
        
        if (!retryResult.isLoading) {
          logger.info(`🚫 Global loading completed but no service data available after ${attempt} attempts`)
          break
        }
        
        // Exponential backoff with jitter
        delay = Math.min(delay * 2, 10000) + Math.random() * 1000
      }
      
      // If we reach here, fall back to API call as last resort
      logger.warn(`⚠️ Service cache wait timeout after ${maxRetries} attempts, falling back to API call`)
      await fallbackToApiCall()
      setLoading(false)
    }

    // Helper function to process service list data
    const processServiceListData = (servicesData: any) => {
      logger.info('🔍 Processing service list data structure:', Object.keys(servicesData || {}))
      
      // Handle the backend transformer response structure
      let actualData = servicesData
      
      // If it's wrapped in a status response, extract the data
      if (servicesData?.status === 'success' && servicesData?.data) {
        actualData = servicesData.data
        logger.info('✅ Extracted services data from status wrapper')
      }
      
      // Look for services in multiple possible locations
      let servicesList = null
      
      if (actualData?.services?.service) {
        servicesList = actualData.services.service
        logger.info(`✅ Found ${servicesList.length} services in services.service`)
      } else if (actualData?.services) {
        servicesList = actualData.services
        logger.info(`✅ Found ${servicesList.length} services in top-level services`)
      } else if (actualData?.service) {
        servicesList = actualData.service
        logger.info(`✅ Found ${servicesList.length} services in service array`)
      }
      
      if (servicesList && servicesList.length > 0) {
        setServices(servicesList)
        
        // Categorize services
        const categorized = categorizeServices(servicesList)
        setServicesByCategory(categorized)
        
        // Set active tab to first available category
        const categories = Object.keys(categorized)
        if (categories.length > 0 && !categories.includes(activeTab)) {
          setActiveTab(categories[0])
        }
        
        logger.info(`✅ Successfully processed ${servicesList.length} services into ${categories.length} categories`)
      } else {
        logger.warn('⚠️ No services found in response')
        setServices([])
        setServicesByCategory({})
      }
    }

    // Fallback function for direct API calls (original logic)
    const fallbackToApiCall = async () => {
      try {
        // Check backend cache first
        const cacheResponse = await api.checkServiceListCache(flightPriceResponse)
        
        let servicesData = null
        
        if (cacheResponse.data?.cache_hit) {
          logger.info("🎯 Backend service list cache hit")
          servicesData = cacheResponse.data.data
        } else {
          logger.info("📞 Backend cache miss, making fresh API call")
          const response = await api.getServiceList(flightPriceResponse)
          servicesData = response.data
        }

        processServiceListData(servicesData)
      } catch (apiError) {
        logger.error("❌ Service API fallback failed:", apiError)
        throw apiError
      }
    }

    loadServices()
  }, [flightPriceResponse]) // Remove onServicesUpdate from dependencies since it's optional

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
    logger.info(`🛎️ Service ${serviceObjectKey} clicked`)
    
    const service = services.find(s => s.objectKey === serviceObjectKey)
    const isSelected = selectedServices.includes(serviceObjectKey)
    
    logger.info(`🛎️ Service ${serviceObjectKey} - Currently selected: ${isSelected}, Service exists: ${!!service}`)
    
    let updatedServices: string[]
    if (isSelected) {
      // Remove service
      updatedServices = selectedServices.filter(s => s !== serviceObjectKey)
      logger.info(`✅ Deselected service ${serviceObjectKey}`)
    } else {
      // Add service
      updatedServices = [...selectedServices, serviceObjectKey]
      logger.info(`✅ Selected service ${serviceObjectKey}`)
    }
    
    logger.info(`🛎️ Service selection changed from [${selectedServices.join(', ')}] to [${updatedServices.join(', ')}]`)
    onServiceChange(updatedServices)
    
    // Send direct pricing data to parent for Price Summary
    const totalPrice = updatedServices.reduce((total, serviceObjectKey) => {
      const service = services.find(s => s.objectKey === serviceObjectKey)
      return total + (service ? getSelectedServicePrice(service) : 0)
    }, 0)
    const currency = getCurrency()
    onPricingUpdate?.(totalPrice, updatedServices.length, currency)
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
      <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-6 bg-primary rounded-full"></div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Add Services</h2>
        </div>
        
        {/* Service Tabs */}
        <div className="flex gap-2 mb-6 border-b-2 border-gray-200 dark:border-gray-600">
          {Object.keys(servicesByCategory).map((categoryKey) => (
            <button
              key={categoryKey}
              className={cn(
                "px-5 py-3 font-semibold transition-all duration-300 relative",
                activeTab === categoryKey
                  ? "text-primary after:absolute after:bottom-0 after:left-0 after:right-0 after:h-1 after:bg-primary after:rounded-t-md"
                  : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
              )}
              onClick={() => setActiveTab(categoryKey)}
            >
              {getCategoryName(categoryKey)}
            </button>
          ))}
        </div>

        {/* Service Content */}
        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
          {/* Special handling for baggage tab */}
          {activeTab === 'baggage' ? (
            <div className="space-y-4">
              {/* Baggage quantity selection */}
              <BaggageOptions
                selectedBaggage={selectedBaggage}
                onBaggageChange={onBaggageChange || (() => {})}
                flightBaggageAllowance={{
                  carryOn: 'As per airline policy',
                  checked: 'As per airline policy',
                  additionalBagPrice: (() => {
                    // Find the most appropriate baggage service price from actual API data
                    const baggageServices = servicesByCategory[activeTab] || [];
                    const weightSystemService = baggageServices.find(s => s.name?.value?.toLowerCase().includes('weight system'));
                    const bagService = baggageServices.find(s => s.name?.value?.toLowerCase().includes('bag'));
                    const firstBaggageService = baggageServices[0];
                    
                    // Priority: weight system > bag > first service > 0 (no hardcoded fallback)
                    const selectedService = weightSystemService || bagService || firstBaggageService;
                    return selectedService?.price?.[0]?.total?.value || 0;
                  })(),
                  currency: getCurrency()
                }}
                currency={getCurrency()}
              />
              
              {/* Additional baggage services from API */}
              {servicesByCategory[activeTab]?.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-gray-900 dark:text-white border-t pt-4">Additional Baggage Services</h4>
                  {servicesByCategory[activeTab].map((service) => {
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
                            ? "border-primary bg-gradient-to-r from-primary/10 to-primary/20" 
                            : "border-gray-200 dark:border-gray-600 hover:border-primary/50 hover:shadow-md hover:-translate-y-1"
                        )}
                        onClick={() => handleServiceToggle(service.objectKey)}
                      >
                        {/* Selection checkmark */}
                        {isSelected && (
                          <div className="absolute top-3 right-3 w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                            <Check className="h-4 w-4 text-white font-bold" />
                          </div>
                        )}

                        <div className="flex justify-between items-start">
                          <div className="flex-1 pr-10">
                            <div className="flex items-center gap-3 mb-2">
                              <h4 className="font-semibold text-gray-900 dark:text-white">{service.name?.value}</h4>
                              {service.bookingInstructions?.ssrCode && (
                                <Badge variant="secondary" className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                                  {service.bookingInstructions.ssrCode[0]}
                                </Badge>
                              )}
                            </div>
                            
                            {service.descriptions?.description?.[0]?.text?.value && (
                              <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                                {service.descriptions.description[0].text.value}
                              </p>
                            )}
                          </div>

                          <div className="text-right">
                            {isFree ? (
                              <span className="inline-block px-3 py-1 bg-primary/20 text-primary text-sm font-semibold rounded-lg">
                                FREE
                              </span>
                            ) : (
                              <div className="text-lg font-bold text-primary">
                                {formatCurrency(price, currency)}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            /* Regular service grid for other tabs */
            servicesByCategory[activeTab]?.map((service) => {
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
                    ? "border-primary bg-gradient-to-r from-primary/10 to-primary/20" 
                    : "border-gray-200 dark:border-gray-600 hover:border-primary/50 hover:shadow-md hover:-translate-y-1"
                )}
                onClick={() => handleServiceToggle(service.objectKey)}
              >
                {/* Selection checkmark */}
                {isSelected && (
                  <div className="absolute top-3 right-3 w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                    <Check className="h-4 w-4 text-white font-bold" />
                  </div>
                )}

                <div className="flex justify-between items-start">
                  <div className="flex-1 pr-10">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold text-gray-900 dark:text-white">{service.name?.value}</h4>
                      {service.bookingInstructions?.ssrCode && (
                        <Badge variant="secondary" className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                          {service.bookingInstructions.ssrCode[0]}
                        </Badge>
                      )}
                    </div>
                    
                    {service.descriptions?.description?.[0]?.text?.value && (
                      <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                        {service.descriptions.description[0].text.value}
                      </p>
                    )}
                  </div>

                  <div className="text-right">
                    {isFree ? (
                      <span className="inline-block px-3 py-1 bg-primary/20 text-primary text-sm font-semibold rounded-lg">
                        FREE
                      </span>
                    ) : (
                      <div className="text-lg font-bold text-primary">
                        {formatCurrency(price, currency)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
            })
          )}
          
          {/* No services message */}
          {activeTab !== 'baggage' && (!servicesByCategory[activeTab] || servicesByCategory[activeTab].length === 0) && (
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
                {formatCurrency(getTotalPrice(), getCurrency())}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}