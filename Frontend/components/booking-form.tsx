"use client"

import * as React from "react"
import { useState, useMemo } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@clerk/nextjs"
import { ChevronRight, CreditCard, Luggage, User, Users, AlertCircle, CheckCircle } from "lucide-react"

import { cn } from "@/utils/cn"
import { Button, LoadingButton } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { PassengerForm } from "@/components/passenger-form"
import { SeatSelection } from "@/components/seat-selection"
import { BaggageOptions } from "@/components/baggage-options"
import { MealOptions } from "@/components/meal-options"

interface ContactInfoState {
  email?: string;
  phone?: string | { countryCode?: string; formatted?: string; number?: string };
  phoneCountryCode?: string;
  street?: string;
  postalCode?: string;
  city?: string;
  countryCode?: string;
}

// Validation interfaces
interface PassengerValidation {
  isValid: boolean;
  missingFields: string[];
}

interface ValidationState {
  passengers: PassengerValidation[];
  contactInfo: {
    isValid: boolean;
    missingFields: string[];
  };
  termsAccepted: boolean;
}

interface BookingFormProps {
  adults?: number;
  children?: number;
  infants?: number;
}

export function BookingForm({ adults = 1, children = 0, infants = 0 }: BookingFormProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { isSignedIn } = useAuth()
  const [currentStep, setCurrentStep] = useState(1)
  const [isNavigating, setIsNavigating] = useState(false)
  
  // Calculate total passenger count from props
  const totalPassengers = adults + children + infants
  const [passengerCount, setPassengerCount] = useState(totalPassengers)

  // Generate passenger types based on counts
  const generatePassengerTypes = () => {
    const types = [];
    for (let i = 0; i < adults; i++) {
      types.push({ type: 'adult', label: `Adult ${i + 1}` });
    }
    for (let i = 0; i < children; i++) {
      types.push({ type: 'child', label: `Child ${i + 1}` });
    }
    for (let i = 0; i < infants; i++) {
      types.push({ type: 'infant', label: `Infant ${i + 1}` });
    }
    return types;
  };

  const passengerTypes = generatePassengerTypes();

  // --- Add State Variables Start ---
  const [passengers, setPassengers] = useState<any[]>(() => {
    // Initialize passengers with their types
    return passengerTypes.map((passengerType, index) => ({
      type: passengerType.type,
      passengerLabel: passengerType.label
    }));
  }); // State for passenger details
  const [contactInfo, setContactInfo] = useState<ContactInfoState>({}); // State for contact info
  const [selectedSeats, setSelectedSeats] = useState<any>({}); // State for seat selection
  const [selectedBaggage, setSelectedBaggage] = useState<any>({}); // State for baggage options
  const [selectedMeals, setSelectedMeals] = useState<any>({}); // State for meal options
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>('PAYMENTCARD');
  const [pricingDetails, setPricingDetails] = useState<any>({}); // State for pricing details
  const [termsAccepted, setTermsAccepted] = useState(false); // State for terms acceptance
  // --- Add State Variables End ---

  // Validation functions
  const validatePassenger = (passenger: any): PassengerValidation => {
    const missingFields: string[] = [];
    
    if (!passenger?.type) missingFields.push('Passenger Type');
    if (!passenger?.title) missingFields.push('Title');
    if (!passenger?.firstName?.trim()) missingFields.push('First Name');
    if (!passenger?.lastName?.trim()) missingFields.push('Last Name');
    if (!passenger?.gender) missingFields.push('Gender');
    if (!passenger?.nationality) missingFields.push('Nationality');
    if (!passenger?.documentType) missingFields.push('Document Type');
    if (!passenger?.documentNumber?.trim()) missingFields.push('Document Number');
    if (!passenger?.issuingCountry) missingFields.push('Issuing Country');
    
    // Date of birth validation
    if (!passenger?.dob?.day || !passenger?.dob?.month || !passenger?.dob?.year) {
      missingFields.push('Date of Birth');
    }
    
    // Expiry date validation
    if (!passenger?.expiryDate?.day || !passenger?.expiryDate?.month || !passenger?.expiryDate?.year) {
      missingFields.push('Document Expiry Date');
    }
    
    return {
      isValid: missingFields.length === 0,
      missingFields
    };
  };

  const validateContactInfo = (): { isValid: boolean; missingFields: string[] } => {
    const missingFields: string[] = [];
    
    if (!contactInfo.email?.trim()) missingFields.push('Email Address');
    const phoneValue = typeof contactInfo.phone === 'string' ? contactInfo.phone : contactInfo.phone?.formatted || contactInfo.phone?.number || '';
    if (!phoneValue?.trim()) missingFields.push('Phone Number');
    if (!contactInfo.phoneCountryCode?.trim()) missingFields.push('Phone Country Code');
    if (!contactInfo.street?.trim()) missingFields.push('Street Address');
    if (!contactInfo.postalCode?.trim()) missingFields.push('Postal Code');
    if (!contactInfo.city?.trim()) missingFields.push('City');
    if (!contactInfo.countryCode?.trim()) missingFields.push('Country');
    
    // Basic email validation
    if (contactInfo.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactInfo.email)) {
      missingFields.push('Valid Email Address');
    }
    
    return {
      isValid: missingFields.length === 0,
      missingFields
    };
  };

  // Compute validation state
  const validationState: ValidationState = useMemo(() => {
    const passengerValidations: PassengerValidation[] = [];
    
    for (let i = 0; i < passengerCount; i++) {
      passengerValidations.push(validatePassenger(passengers[i] || {}));
    }
    
    return {
      passengers: passengerValidations,
      contactInfo: validateContactInfo(),
      termsAccepted
    };
  }, [passengers, passengerCount, contactInfo, termsAccepted]);

  // Check if current step is valid
  const isCurrentStepValid = useMemo(() => {
    switch (currentStep) {
      case 1: // Passenger Details
        return validationState.passengers.every(p => p.isValid) && validationState.contactInfo.isValid;
      case 2: // Seat Selection (optional)
        return true;
      case 3: // Extras (optional)
        return true;
      case 4: // Payment Method
        return true; // Payment method selection is optional with default value
      case 5: // Review
        return validationState.passengers.every(p => p.isValid) && 
               validationState.contactInfo.isValid && 
               validationState.termsAccepted;
      default:
        return false;
    }
  }, [currentStep, validationState]);

  // Get completion percentage for passengers
  const getPassengerCompletionPercentage = (index: number): number => {
    const passenger = passengers[index] || {};
    const validation = validatePassenger(passenger);
    const totalFields = 11; // Total required fields
    const completedFields = totalFields - validation.missingFields.length;
    return Math.round((completedFields / totalFields) * 100);
  };

  // --- Add Handler for Passenger Changes ---
  const handlePassengerChange = (index: number, updatedData: any) => {
    setPassengers(prev => {
      const newPassengers = [...prev];
      // Ensure the array is long enough
      while (newPassengers.length <= index) {
        newPassengers.push({});
      }
      newPassengers[index] = updatedData;
      return newPassengers;
    });
  };

  // --- Add Handler for Contact Info Changes ---
  const handleContactInfoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setContactInfo((prev: ContactInfoState) => ({ ...prev, [id]: value }));
  };

  // --- Add Handler for Contact Info Select Changes ---
  const handleContactInfoSelectChange = (field: string, value: string) => {
    setContactInfo((prev: ContactInfoState) => ({ ...prev, [field]: value }));
  };

  // --- Add Handler for Seat Selection Changes ---
  const handleSeatChange = (flightType: 'outbound' | 'return', updatedSeats: any) => {
    setSelectedSeats((prev: any) => ({ ...prev, [flightType]: updatedSeats }));
  };

  // --- Add Handler for Baggage Changes ---
  const handleBaggageChange = (updatedBaggage: any) => {
    setSelectedBaggage(updatedBaggage);
  };

  // --- Add Handler for Meal Changes ---
  const handleMealChange = (updatedMeals: any) => {
    setSelectedMeals(updatedMeals);
  };

  // Handle passenger count changes with validation
  const handlePassengerCountChange = (newCount: number) => {
    // Check if reducing count would lose data
    if (newCount < passengerCount) {
      const hasDataInRemovedSlots = passengers.slice(newCount).some(passenger => {
        return passenger && Object.keys(passenger).length > 0;
      });
      
      if (hasDataInRemovedSlots) {
        const confirmed = window.confirm(
          `Reducing passenger count will remove data for passengers ${newCount + 1} to ${passengerCount}. Continue?`
        );
        if (!confirmed) return;
      }
    }
    
    setPassengerCount(newCount);
  };
  // --- End Handlers ---

  const steps = [
    { id: 1, name: "Passenger Details" },
    { id: 2, name: "Seat Selection" },
    { id: 3, name: "Extras" },
    { id: 4, name: "Payment Method" },
    { id: 5, name: "Review" },
  ]

  const nextStep = () => {
    if (currentStep < steps.length && isCurrentStepValid) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleContinueToPayment = async () => {
    console.log('[DEBUG] Continue to Payment button clicked')
    console.log('[DEBUG] isCurrentStepValid:', isCurrentStepValid)

    // Final validation before payment
    if (!isCurrentStepValid) {
      console.log('[DEBUG] Current step is not valid, returning early')
      return;
    }

    setIsNavigating(true);

    const flightId = pathname.split("/")[2]

    // Prepare booking data for backend API
    const bookingData = {
      flightId: flightId,
      passengers: passengers.slice(0, passengerCount), // Only include actual passenger count
      contactInfo: contactInfo,
      extras: {
        seats: selectedSeats,
        baggage: selectedBaggage,
        meals: selectedMeals,
        additionalServices: []
      },
      paymentMethod: selectedPaymentMethod,
      pricing: pricingDetails
    }

    // Store booking data in session storage for payment page
    sessionStorage.setItem("pendingBookingData", JSON.stringify(bookingData))

    // Get the flight price response data and prepare complete flight offer for order creation
    try {
      const storedFlightPriceResponse = sessionStorage.getItem('flightPriceResponseForBooking')
      if (!storedFlightPriceResponse) {
        console.error('No flight price response found for booking - proceeding anyway')
        // Don't return - continue to payment page
      }

      let flightPriceData = null;
      if (storedFlightPriceResponse) {
        flightPriceData = JSON.parse(storedFlightPriceResponse)
      }

      // Get the raw flight price response that the backend needs for order creation
      const storedRawFlightPriceResponse = sessionStorage.getItem('rawFlightPriceResponse')
      if (!storedRawFlightPriceResponse) {
        console.warn('No raw flight price response found for booking - will use fallback approach')
        // Don't return - continue to payment page with available data
      }

      let rawFlightPriceResponse = null;
      if (storedRawFlightPriceResponse) {
        rawFlightPriceResponse = JSON.parse(storedRawFlightPriceResponse)
        console.log('[DEBUG] Using raw flight price response for order creation:', {
          hasShoppingResponseID: !!rawFlightPriceResponse.ShoppingResponseID,
          hasPricedFlightOffers: !!rawFlightPriceResponse.PricedFlightOffers,
          topLevelKeys: Object.keys(rawFlightPriceResponse)
        })
      }

      // Extract shopping response ID from the raw flight price response
      let shoppingResponseId = '';
      let orderId = '';

      if (rawFlightPriceResponse) {
        if (rawFlightPriceResponse?.ShoppingResponseID?.ResponseID?.value) {
          shoppingResponseId = rawFlightPriceResponse.ShoppingResponseID.ResponseID.value;
        }

        // Extract order ID from the raw flight price response
        if (rawFlightPriceResponse?.PricedFlightOffers?.PricedFlightOffer?.[0]?.OfferID?.value) {
          orderId = rawFlightPriceResponse.PricedFlightOffers.PricedFlightOffer[0].OfferID.value;
        }

        console.log('[DEBUG] Extracted IDs from raw flight price response:', {
          shoppingResponseId,
          orderId,
          hasShoppingResponseID: !!shoppingResponseId,
          hasOrderID: !!orderId
        })
      } else {
        console.log('[DEBUG] No raw flight price response available - using fallback approach')
      }

      // Prepare complete flight offer data for order creation
      const flightOfferWithRawResponse = {
        ...(flightPriceData || {}),
        raw_flight_price_response: rawFlightPriceResponse,  // May be null - payment page will handle
        shopping_response_id: shoppingResponseId,
        order_id: orderId
      }

      // Store the complete flight offer data that the payment page expects
      sessionStorage.setItem("selectedFlightOffer", JSON.stringify(flightOfferWithRawResponse))

      console.log('[DEBUG] Stored complete flight offer data for payment page:', {
        hasRawResponse: !!flightOfferWithRawResponse.raw_flight_price_response,
        hasFlightPriceData: !!flightPriceData,
        shoppingResponseId: shoppingResponseId,
        orderId: orderId,
        flightOfferKeys: Object.keys(flightOfferWithRawResponse)
      })

    } catch (error) {
      console.error('Error preparing flight offer data for payment:', error)
      // Store minimal data so payment page doesn't crash
      sessionStorage.setItem("selectedFlightOffer", JSON.stringify({
        error: 'Failed to prepare flight data',
        timestamp: Date.now()
      }))
      // Continue anyway - the payment page will handle missing data
    }

    console.log('[DEBUG] Attempting navigation to payment page')
    console.log('[DEBUG] isSignedIn:', isSignedIn)
    console.log('[DEBUG] flightId:', flightId)

    try {
      if (isSignedIn) {
        const paymentUrl = `/flights/${encodeURIComponent(flightId)}/payment`
        console.log('[DEBUG] Navigating to payment URL:', paymentUrl)
        router.push(paymentUrl)
      } else {
        // Store the redirect URL in session storage
        const redirectUrl = `/flights/${flightId}/payment`
        const signInUrl = `/sign-in?redirect_url=${encodeURIComponent(redirectUrl)}`
        console.log('[DEBUG] Navigating to sign-in URL:', signInUrl)
        router.push(signInUrl)
      }
    } finally {
      // Reset loading state after a delay to allow navigation
      setTimeout(() => setIsNavigating(false), 1000);
    }
  }

  return (
    <div className="p-3 sm:p-4 md:p-6">

        {/* Mobile Progress Indicator */}
        <div className="mt-3 sm:hidden">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Step {currentStep} of {steps.length}</span>
            <span className="font-medium">{steps[currentStep - 1]?.name}</span>
          </div>
          <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${(currentStep / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Desktop Progress Steps */}
        <div className="mt-4 hidden sm:block">
          <div className="flex items-center overflow-x-auto pb-2">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className="flex items-center flex-shrink-0">
                  <div
                    className={cn(
                      "flex h-7 w-7 md:h-8 md:w-8 items-center justify-center rounded-full border text-xs font-medium",
                      currentStep >= step.id
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-muted-foreground/30 text-muted-foreground",
                    )}
                  >
                    {step.id}
                  </div>
                  <span
                    className={cn(
                      "ml-2 text-xs md:text-sm font-medium whitespace-nowrap",
                      currentStep >= step.id ? "text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {step.name}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={cn("mx-2 h-0.5 w-8 md:w-10 bg-muted-foreground/30 flex-shrink-0", currentStep > step.id && "bg-primary")}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Validation Summary */}
        {!isCurrentStepValid && (
          <Alert className="mt-3 sm:mt-4">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <AlertDescription className="text-sm">
              Please complete all required fields before continuing.
              {currentStep === 1 && (
                <div className="mt-2 space-y-1">
                  {validationState.passengers.map((validation, index) => (
                    !validation.isValid && (
                      <div key={index} className="text-xs sm:text-sm">
                        <span className="font-medium">Passenger {index + 1}:</span> {validation.missingFields.join(', ')}
                      </div>
                    )
                  ))}
                  {!validationState.contactInfo.isValid && (
                    <div className="text-xs sm:text-sm">
                      <span className="font-medium">Contact Info:</span> {validationState.contactInfo.missingFields.join(', ')}
                    </div>
                  )}
                </div>
              )}
              {currentStep === 5 && !validationState.termsAccepted && (
                <div className="mt-2 text-xs sm:text-sm">
                  Please accept the Terms and Conditions
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}

        <div className="mt-4 sm:mt-6">
          {/* Step 1: Passenger Details */}
          {currentStep === 1 && (
            <div className="space-y-4 sm:space-y-6">
              <div className="space-y-3 sm:space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <h3 className="text-base sm:text-lg font-medium">Passenger Information</h3>
                  <div className="text-xs sm:text-sm text-muted-foreground">
                    {adults} Adult{adults !== 1 ? 's' : ''}
                    {children > 0 && `, ${children} Child${children !== 1 ? 'ren' : ''}`}
                    {infants > 0 && `, ${infants} Infant${infants !== 1 ? 's' : ''}`}
                  </div>
                </div>

                <Tabs defaultValue="passenger-1" className="w-full">
                  <TabsList className="grid w-full grid-cols-1 gap-1 sm:grid-cols-2 md:w-auto md:grid-cols-none md:auto-cols-auto md:flex md:gap-0">
                    {passengerTypes.map((passengerType, index) => {
                      const validation = validationState.passengers[index];
                      const completionPercentage = getPassengerCompletionPercentage(index);

                      return (
                        <TabsTrigger key={index} value={`passenger-${index + 1}`} className="relative text-xs sm:text-sm">
                          <div className="flex items-center gap-1 sm:gap-2">
                            <span className="truncate">{passengerType.label}</span>
                            {validation?.isValid ? (
                              <CheckCircle className="h-3 w-3 text-green-500 flex-shrink-0" />
                            ) : completionPercentage > 0 ? (
                              <div className="h-3 w-3 rounded-full border border-orange-500 bg-orange-100 text-[8px] flex items-center justify-center text-orange-600 flex-shrink-0">
                                {Math.round(completionPercentage / 10)}
                              </div>
                            ) : (
                              <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />
                            )}
                          </div>
                        </TabsTrigger>
                      );
                    })}
                  </TabsList>

                  {passengerTypes.map((passengerType, index) => (
                    <TabsContent key={index} value={`passenger-${index + 1}`}>
                      <PassengerForm
                        passengerNumber={index + 1}
                        passengerLabel={passengerType.label}
                        passengerType={passengerType.type}
                        passengerData={passengers[index] || {}} // Pass current data or empty object
                        onPassengerChange={(updatedData) => handlePassengerChange(index, updatedData)} // Pass update handler
                      />
                      
                      {/* Progress indicator */}
                      <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-muted/50 rounded-md">
                        <div className="flex items-center justify-between text-xs sm:text-sm">
                          <span>Form Completion</span>
                          <span className={cn(
                            "font-medium",
                            validationState.passengers[index]?.isValid ? "text-green-600" : "text-orange-600"
                          )}>
                            {getPassengerCompletionPercentage(index)}%
                          </span>
                        </div>
                        <div className="mt-2 h-1.5 sm:h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className={cn(
                              "h-full transition-all duration-300",
                              validationState.passengers[index]?.isValid ? "bg-green-500" : "bg-orange-500"
                            )}
                            style={{ width: `${getPassengerCompletionPercentage(index)}%` }}
                          />
                        </div>
                        {!validationState.passengers[index]?.isValid && validationState.passengers[index]?.missingFields.length > 0 && (
                          <div className="mt-2 text-xs text-muted-foreground">
                            Missing: {validationState.passengers[index].missingFields.join(', ')}
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  ))}
                </Tabs>
              </div>

              <div className="space-y-3 sm:space-y-4">
                <h3 className="text-base sm:text-lg font-medium">Contact Information</h3>

                {/* Email and Phone Section */}
                <div className="grid gap-3 sm:gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm">Email Address *</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="your.email@example.com"
                      value={contactInfo.email || ''}
                      onChange={handleContactInfoChange}
                      className={cn(
                        "text-sm",
                        contactInfo.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactInfo.email) && "border-red-500"
                      )}
                    />
                    <p className="text-xs text-muted-foreground">
                      Your booking confirmation will be sent to this email
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm">Phone Number *</Label>
                    <div className="flex gap-2">
                      <Select
                        value={contactInfo.phoneCountryCode || ''}
                        onValueChange={(value) => handleContactInfoSelectChange('phoneCountryCode', value)}
                      >
                        <SelectTrigger className="w-20 sm:w-24 text-sm">
                          <SelectValue placeholder="+1" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">+1</SelectItem>
                          <SelectItem value="44">+44</SelectItem>
                          <SelectItem value="49">+49</SelectItem>
                          <SelectItem value="33">+33</SelectItem>
                          <SelectItem value="39">+39</SelectItem>
                          <SelectItem value="34">+34</SelectItem>
                          <SelectItem value="31">+31</SelectItem>
                          <SelectItem value="46">+46</SelectItem>
                          <SelectItem value="47">+47</SelectItem>
                          <SelectItem value="45">+45</SelectItem>
                          <SelectItem value="358">+358</SelectItem>
                          <SelectItem value="254">+254</SelectItem>
                          <SelectItem value="27">+27</SelectItem>
                          <SelectItem value="234">+234</SelectItem>
                          <SelectItem value="91">+91</SelectItem>
                          <SelectItem value="86">+86</SelectItem>
                          <SelectItem value="81">+81</SelectItem>
                          <SelectItem value="82">+82</SelectItem>
                          <SelectItem value="61">+61</SelectItem>
                          <SelectItem value="64">+64</SelectItem>
                        </SelectContent>
                      </Select>
                      <Input
                        id="phone"
                        type="tel"
                        placeholder="123-456-7890"
                        value={typeof contactInfo.phone === 'string' ? contactInfo.phone : contactInfo.phone?.formatted || contactInfo.phone?.number || ''}
                        onChange={handleContactInfoChange}
                        className="flex-1 text-sm"
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">For urgent notifications about your flight</p>
                  </div>
                </div>

                {/* Address Section */}
                <div className="space-y-3 sm:space-y-4">
                  <h4 className="text-sm sm:text-base font-medium">Address Information</h4>
                  <div className="grid gap-3 sm:gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="street" className="text-sm">Street Address *</Label>
                      <Input
                        id="street"
                        type="text"
                        placeholder="123 Main Street, Apt 4B"
                        value={contactInfo.street || ''}
                        onChange={handleContactInfoChange}
                        className="text-sm"
                      />
                    </div>
                    <div className="grid gap-3 sm:gap-4 sm:grid-cols-3">
                      <div className="space-y-2">
                        <Label htmlFor="city" className="text-sm">City *</Label>
                        <Input
                          id="city"
                          type="text"
                          placeholder="New York"
                          value={contactInfo.city || ''}
                          onChange={handleContactInfoChange}
                          className="text-sm"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="postalCode" className="text-sm">Postal Code *</Label>
                        <Input
                          id="postalCode"
                          type="text"
                          placeholder="10001"
                          value={contactInfo.postalCode || ''}
                          onChange={handleContactInfoChange}
                          className="text-sm"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm">Country *</Label>
                        <Select
                          value={contactInfo.countryCode || ''}
                          onValueChange={(value) => handleContactInfoSelectChange('countryCode', value)}
                        >
                          <SelectTrigger className="text-sm">
                            <SelectValue placeholder="Select country" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="US">United States</SelectItem>
                            <SelectItem value="GB">United Kingdom</SelectItem>
                            <SelectItem value="DE">Germany</SelectItem>
                            <SelectItem value="FR">France</SelectItem>
                            <SelectItem value="IT">Italy</SelectItem>
                            <SelectItem value="ES">Spain</SelectItem>
                            <SelectItem value="NL">Netherlands</SelectItem>
                            <SelectItem value="SE">Sweden</SelectItem>
                            <SelectItem value="NO">Norway</SelectItem>
                            <SelectItem value="DK">Denmark</SelectItem>
                            <SelectItem value="FI">Finland</SelectItem>
                            <SelectItem value="KE">Kenya</SelectItem>
                            <SelectItem value="ZA">South Africa</SelectItem>
                            <SelectItem value="NG">Nigeria</SelectItem>
                            <SelectItem value="IN">India</SelectItem>
                            <SelectItem value="CN">China</SelectItem>
                            <SelectItem value="JP">Japan</SelectItem>
                            <SelectItem value="KR">South Korea</SelectItem>
                            <SelectItem value="AU">Australia</SelectItem>
                            <SelectItem value="NZ">New Zealand</SelectItem>
                            <SelectItem value="CA">Canada</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Seat Selection */}
          {currentStep === 2 && (
            <div className="space-y-4 sm:space-y-6">
              <div>
                <h3 className="text-base sm:text-lg font-medium">Seat Selection</h3>
                <p className="text-xs sm:text-sm text-muted-foreground">Choose your preferred seats for your flights</p>
              </div>

              <div className="space-y-4 sm:space-y-6">
                <div>
                  <h4 className="mb-2 text-sm sm:text-base font-medium">Outbound Flight</h4>
                  <SeatSelection
                    flightType="outbound"
                    selectedSeats={selectedSeats.outbound || []}
                    onSeatChange={handleSeatChange}
                  />
                </div>

                <Separator />

                <div>
                  <h4 className="mb-2 text-sm sm:text-base font-medium">Return Flight</h4>
                  <SeatSelection
                    flightType="return"
                    selectedSeats={selectedSeats.return || []}
                    onSeatChange={handleSeatChange}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Extras */}
          {currentStep === 3 && (
            <div className="space-y-4 sm:space-y-6">
              <div>
                <h3 className="text-base sm:text-lg font-medium">Optional Extras</h3>
                <p className="text-xs sm:text-sm text-muted-foreground">Enhance your journey with additional services</p>
              </div>

              <div className="space-y-4 sm:space-y-6">
                <div>
                  <h4 className="mb-2 text-sm sm:text-base font-medium">Baggage Options</h4>
                  <BaggageOptions
                    selectedBaggage={selectedBaggage}
                    onBaggageChange={handleBaggageChange}
                  />
                </div>

                <Separator />

                <div>
                  <h4 className="mb-2 text-base font-medium">Meal Preferences</h4>
                  <MealOptions 
                    selectedMeals={selectedMeals} 
                    onMealChange={handleMealChange} 
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Payment Method */}
          {currentStep === 4 && (
            <div className="space-y-4 sm:space-y-6">
              <div>
                <h3 className="text-base sm:text-lg font-medium">Payment Method</h3>
                <p className="text-xs sm:text-sm text-muted-foreground">Choose your preferred payment method</p>
              </div>

              <div className="space-y-3 sm:space-y-4">
                <div className="grid grid-cols-1 gap-3 sm:gap-4">
                  {/* Cash Payment */}
                  <div
                    className={cn(
                      "p-3 sm:p-4 border rounded-lg cursor-pointer transition-all",
                      selectedPaymentMethod === 'CASH'
                        ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setSelectedPaymentMethod('CASH')}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={cn(
                        "w-4 h-4 rounded-full border-2 flex-shrink-0",
                        selectedPaymentMethod === 'CASH'
                          ? "border-primary bg-primary"
                          : "border-gray-300"
                      )}>
                        {selectedPaymentMethod === 'CASH' && (
                          <div className="w-full h-full rounded-full bg-white scale-50"></div>
                        )}
                      </div>
                      <div className="min-w-0">
                        <h4 className="font-medium text-sm sm:text-base">Cash Payment</h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">Pay with cash at the airport</p>
                      </div>
                    </div>
                  </div>

                  {/* Card Payment */}
                  <div
                    className={cn(
                      "p-3 sm:p-4 border rounded-lg cursor-pointer transition-all",
                      selectedPaymentMethod === 'PAYMENTCARD'
                        ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setSelectedPaymentMethod('PAYMENTCARD')}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={cn(
                        "w-4 h-4 rounded-full border-2 flex-shrink-0",
                        selectedPaymentMethod === 'PAYMENTCARD'
                          ? "border-primary bg-primary"
                          : "border-gray-300"
                      )}>
                        {selectedPaymentMethod === 'PAYMENTCARD' && (
                          <div className="w-full h-full rounded-full bg-white scale-50"></div>
                        )}
                      </div>
                      <div className="min-w-0">
                        <h4 className="font-medium text-sm sm:text-base">Credit/Debit Card</h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">Pay securely with your card</p>
                      </div>
                    </div>
                  </div>

                  {/* EasyPay */}
                  <div
                    className={cn(
                      "p-3 sm:p-4 border rounded-lg cursor-pointer transition-all",
                      selectedPaymentMethod === 'EASYPAY'
                        ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setSelectedPaymentMethod('EASYPAY')}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={cn(
                        "w-4 h-4 rounded-full border-2 flex-shrink-0",
                        selectedPaymentMethod === 'EASYPAY'
                          ? "border-primary bg-primary"
                          : "border-gray-300"
                      )}>
                        {selectedPaymentMethod === 'EASYPAY' && (
                          <div className="w-full h-full rounded-full bg-white scale-50"></div>
                        )}
                      </div>
                      <div className="min-w-0">
                        <h4 className="font-medium text-sm sm:text-base">EasyPay</h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">Quick payment with EasyPay account</p>
                      </div>
                    </div>
                  </div>

                  {/* Other Payment */}
                  <div
                    className={cn(
                      "p-3 sm:p-4 border rounded-lg cursor-pointer transition-all",
                      selectedPaymentMethod === 'OTHER'
                        ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                        : "border-border hover:border-primary/50"
                    )}
                    onClick={() => setSelectedPaymentMethod('OTHER')}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={cn(
                        "w-4 h-4 rounded-full border-2 flex-shrink-0",
                        selectedPaymentMethod === 'OTHER'
                          ? "border-primary bg-primary"
                          : "border-gray-300"
                      )}>
                        {selectedPaymentMethod === 'OTHER' && (
                          <div className="w-full h-full rounded-full bg-white scale-50"></div>
                        )}
                      </div>
                      <div className="min-w-0">
                        <h4 className="font-medium text-sm sm:text-base">Other Payment</h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">Alternative payment methods</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Selected Payment Method Info */}
                <div className="p-3 sm:p-4 bg-muted/50 rounded-lg">
                  <h4 className="font-medium mb-2 text-sm sm:text-base">Selected Payment Method</h4>
                  <p className="text-xs sm:text-sm text-muted-foreground">
                    {selectedPaymentMethod === 'CASH' && 'You will pay with cash at the airport counter.'}
                    {selectedPaymentMethod === 'PAYMENTCARD' && 'You will be redirected to secure card payment processing.'}
                    {selectedPaymentMethod === 'EASYPAY' && 'You will use your EasyPay account for quick payment.'}
                    {selectedPaymentMethod === 'OTHER' && 'Alternative payment method will be processed.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Review */}
          {currentStep === 5 && (
            <div className="space-y-4 sm:space-y-6">
              <div>
                <h3 className="text-base sm:text-lg font-medium">Review Your Booking</h3>
                <p className="text-xs sm:text-sm text-muted-foreground">Please review all details before proceeding to payment</p>
              </div>

              {/* Passenger Summary */}
              <div className="space-y-3 sm:space-y-4">
                <h4 className="text-sm sm:text-base font-medium">Passengers ({passengerCount})</h4>
                {passengers.slice(0, passengerCount).map((passenger, index) => (
                  <div key={index} className="flex items-center justify-between p-2 sm:p-3 border rounded-md">
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-sm sm:text-base truncate">
                        {passenger?.title} {passenger?.firstName} {passenger?.lastName}
                      </div>
                      <div className="text-xs sm:text-sm text-muted-foreground">
                        {passenger?.type} • {passenger?.nationality}
                      </div>
                    </div>
                    {validationState.passengers[index]?.isValid ? (
                      <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 flex-shrink-0 ml-2" />
                    ) : (
                      <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-red-500 flex-shrink-0 ml-2" />
                    )}
                  </div>
                ))}
              </div>

              {/* Contact Info Summary */}
              <div className="space-y-2">
                <h4 className="text-sm sm:text-base font-medium">Contact Information</h4>
                <div className="p-2 sm:p-3 border rounded-md">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm sm:text-base truncate">{contactInfo.email}</div>
                      <div className="text-xs sm:text-sm text-muted-foreground">{typeof contactInfo.phone === 'object' && contactInfo.phone?.formatted
                        ? contactInfo.phone.formatted
                        : typeof contactInfo.phone === 'string' ? contactInfo.phone : 'N/A'}</div>
                    </div>
                    {validationState.contactInfo.isValid ? (
                      <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 flex-shrink-0 ml-2" />
                    ) : (
                      <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-red-500 flex-shrink-0 ml-2" />
                    )}
                  </div>
                </div>
              </div>

              {/* Payment Method Summary */}
              <div className="space-y-2">
                <h4 className="text-sm sm:text-base font-medium">Payment Method</h4>
                <div className="p-2 sm:p-3 border rounded-md">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-sm sm:text-base">
                        {selectedPaymentMethod === 'CASH' && 'Cash Payment'}
                        {selectedPaymentMethod === 'PAYMENTCARD' && 'Credit/Debit Card'}
                        {selectedPaymentMethod === 'EASYPAY' && 'EasyPay'}
                        {selectedPaymentMethod === 'OTHER' && 'Other Payment Method'}
                      </div>
                      <div className="text-xs sm:text-sm text-muted-foreground">
                        {selectedPaymentMethod === 'CASH' && 'Pay with cash at the airport counter'}
                        {selectedPaymentMethod === 'PAYMENTCARD' && 'Secure card payment processing'}
                        {selectedPaymentMethod === 'EASYPAY' && 'Quick payment with EasyPay account'}
                        {selectedPaymentMethod === 'OTHER' && 'Alternative payment method'}
                      </div>
                    </div>
                    <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 flex-shrink-0 ml-2" />
                  </div>
                </div>
              </div>

              {/* Terms and Conditions */}
              <div className="space-y-3 sm:space-y-4">
                <div className="flex items-start space-x-2 sm:space-x-3">
                  <Checkbox
                    id="terms"
                    checked={termsAccepted}
                    onCheckedChange={(checked) => setTermsAccepted(checked as boolean)}
                    className="mt-0.5"
                  />
                  <div className="min-w-0 flex-1">
                    <label
                      htmlFor="terms"
                      className="text-xs sm:text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      I agree to the Terms and Conditions *
                    </label>
                    <p className="mt-1 text-xs text-muted-foreground">
                      By checking this box, you agree to our{" "}
                      <a href="#" className="text-primary underline">
                        Terms of Service
                      </a>{" "}
                      and{" "}
                      <a href="#" className="text-primary underline">
                        Privacy Policy
                      </a>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="mt-6 sm:mt-8 flex flex-col sm:flex-row gap-3 sm:gap-0 sm:justify-between">
            <Button
              variant="outline"
              onClick={prevStep}
              disabled={currentStep === 1}
              className="w-full sm:w-auto text-sm"
            >
              Back
            </Button>

            {currentStep < steps.length ? (
              <LoadingButton
                onClick={nextStep}
                disabled={!isCurrentStepValid}
                loading={isNavigating}
                loadingText="Processing..."
                className={cn(
                  "w-full sm:w-auto text-sm",
                  !isCurrentStepValid && "opacity-50 cursor-not-allowed"
                )}
              >
                Continue
                <ChevronRight className="ml-1 h-4 w-4" />
              </LoadingButton>
            ) : (
              <LoadingButton
                onClick={handleContinueToPayment}
                disabled={!isCurrentStepValid}
                loading={isNavigating}
                loadingText="Redirecting..."
                className={cn(
                  "w-full sm:w-auto text-sm",
                  !isCurrentStepValid && "opacity-50 cursor-not-allowed"
                )}
                aria-label="Continue to payment page"
              >
                <span className="hidden sm:inline">Continue to Payment</span>
                <span className="sm:hidden">Continue</span>
                <ChevronRight className="ml-1 h-4 w-4" />
              </LoadingButton>
            )}
          </div>
        </div>
    </div>
  )
}
