import { useState, useCallback } from "react"
import { api } from "@/utils/api-client"
import { useLoading } from "@/utils/loading-state"
import type { FlightOffer } from "@/types/flight-api"
import type { FlightSearchFormData, SearchFormErrors, FlightSegment } from "./flight-search-form.types"

const initialFormData: FlightSearchFormData = {
  tripType: 'round-trip',
  origin: '',
  destination: '',
  departDate: undefined,
  returnDate: undefined,
  passengers: {
    adults: 1,
    children: 0,
    infants: 0
  },
  cabinType: 'ECONOMY',
  segments: [{ origin: '', destination: '', departureDate: undefined }]
}

interface UseFlightSearchReturn {
  formData: FlightSearchFormData
  errors: SearchFormErrors
  loading: boolean
  results: FlightOffer[]
  meta: any
  setFormData: (data: Partial<FlightSearchFormData>) => void
  setErrors: (errors: SearchFormErrors) => void
  addSegment: () => void
  removeSegment: (index: number) => void
  updateSegment: (index: number, segment: Partial<FlightSegment>) => void
  validateForm: () => boolean
  handleSearch: () => Promise<void>
  reset: () => void
}

export function useFlightSearch(
  initialValues?: Partial<FlightSearchFormData>,
  onSearch?: (results: FlightOffer[], meta: any, formData?: FlightSearchFormData) => void,
  onError?: (error: string) => void,
  onSearchStart?: (formData: FlightSearchFormData) => boolean
): UseFlightSearchReturn {
  const [formData, setFormDataState] = useState<FlightSearchFormData>({
    ...initialFormData,
    ...initialValues
  })
  
  const [errors, setErrors] = useState<SearchFormErrors>({})
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<FlightOffer[]>([])
  const [meta, setMeta] = useState<any>(null)
  const { setLoadingState } = useLoading()

  const setFormData = useCallback((data: Partial<FlightSearchFormData>) => {
    setFormDataState(prev => ({ ...prev, ...data }))
    // Clear related errors when field changes
    setErrors(prev => {
      const newErrors = { ...prev }
      Object.keys(data).forEach(key => {
        delete newErrors[key as keyof SearchFormErrors]
      })
      return newErrors
    })
  }, [])

  const addSegment = useCallback(() => {
    setFormData({
      segments: [...formData.segments, { origin: '', destination: '', departureDate: undefined }]
    })
  }, [formData.segments, setFormData])

  const removeSegment = useCallback((index: number) => {
    if (formData.segments.length > 1) {
      const newSegments = formData.segments.filter((_, i) => i !== index)
      setFormData({ segments: newSegments })
    }
  }, [formData.segments, setFormData])

  const updateSegment = useCallback((index: number, segment: Partial<FlightSegment>) => {
    const newSegments = [...formData.segments]
    newSegments[index] = { ...newSegments[index], ...segment }
    setFormData({ segments: newSegments })
  }, [formData.segments, setFormData])

  const validateForm = useCallback((): boolean => {
    const newErrors: SearchFormErrors = {}

    // Validate origin and destination
    if (!formData.origin.trim()) {
      newErrors.origin = 'Origin is required'
    }
    if (!formData.destination.trim()) {
      newErrors.destination = 'Destination is required'
    }
    if (formData.origin === formData.destination && formData.origin) {
      newErrors.destination = 'Destination must be different from origin'
    }

    // Validate dates
    if (!formData.departDate) {
      newErrors.departDate = 'Departure date is required'
    }
    if (formData.tripType === 'round-trip' && !formData.returnDate) {
      newErrors.returnDate = 'Return date is required for round-trip'
    }
    if (formData.departDate && formData.returnDate && formData.returnDate <= formData.departDate) {
      newErrors.returnDate = 'Return date must be after departure date'
    }

    // Validate passengers
    if (formData.passengers.adults < 1) {
      newErrors.passengers = 'At least one adult passenger is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [formData])

  const handleSearch = useCallback(async () => {
    if (!validateForm()) {
      return
    }

    // If we have onSearchStart callback, call it for immediate redirection
    if (onSearchStart) {
      const shouldRedirect = onSearchStart(formData)
      if (shouldRedirect) {
        // User is being redirected to results page
        // The results page will handle the actual search API call
        return
      }
    }

    // Fallback: If no onSearchStart or it returns false, continue with the search here
    // This maintains backward compatibility for components that don't use the new flow
    setLoading(true)
    setLoadingState({ isLoading: true })
    
    try {
      // Map trip type to API format
      const tripTypeMapping = {
        'round-trip': 'ROUND_TRIP',
        'one-way': 'ONE_WAY',
        'multi-city': 'MULTI_CITY'
      } as const

      const searchRequest = {
        tripType: tripTypeMapping[formData.tripType as keyof typeof tripTypeMapping],
        odSegments: [{
          origin: formData.origin,
          destination: formData.destination,
          departureDate: formData.departDate?.toISOString().split('T')[0] || ''
        }],
        numAdults: formData.passengers.adults,
        numChildren: formData.passengers.children,
        numInfants: formData.passengers.infants,
        cabinPreference: formData.cabinType,
        directOnly: false
      }

      // Add return segment for round-trip
      if (formData.tripType === 'round-trip' && formData.returnDate) {
        searchRequest.odSegments.push({
          origin: formData.destination,
          destination: formData.origin,
          departureDate: formData.returnDate.toISOString().split('T')[0]
        })
      }

      const response = await api.searchFlights(searchRequest)
      
      if (response?.data?.data?.offers) {
        setResults(response.data.data.offers)
        setMeta(response.data.data.metadata || null)
        onSearch?.(response.data.data.offers, response.data.data.metadata || null, formData)
      } else {
        throw new Error('No flight results received')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Search failed'
      setErrors({ general: errorMessage })
      onError?.(errorMessage)
      setResults([])
      setMeta(null)
    } finally {
      setLoading(false)
      setLoadingState({ isLoading: false })
    }
  }, [formData, validateForm, onSearch, onError, onSearchStart, setLoadingState])

  const reset = useCallback(() => {
    setFormDataState({ ...initialFormData, ...initialValues })
    setErrors({})
    setResults([])
    setMeta(null)
  }, [initialValues])

  return {
    formData,
    errors,
    loading,
    results,
    meta,
    setFormData,
    setErrors,
    addSegment,
    removeSegment,
    updateSegment,
    validateForm,
    handleSearch,
    reset
  }
}