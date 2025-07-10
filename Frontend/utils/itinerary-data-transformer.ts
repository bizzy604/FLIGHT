/**
 * Data transformation service for extracting itinerary information from OrderCreate response
 * Transforms raw airline API response into structured data for official flight itinerary
 */

export interface PassengerInfo {
  objectKey: string;
  fullName: string;
  title: string;
  firstName: string;
  lastName: string;
  passengerType: 'ADT' | 'CHD' | 'INF';
  passengerTypeLabel: string;
  birthDate: string;
  age: number;
  documentType: string;
  documentNumber: string;
  documentExpiry: string;
  countryOfIssuance: string;
  countryOfResidence?: string;
  ticketNumber: string;
  email?: string;
  phone?: string;
}

export interface FlightSegment {
  segmentKey: string;
  flightNumber: string;
  airline: string;
  airlineCode: string;
  airlineLogo?: string;
  aircraft: string;
  aircraftCode: string;
  departure: {
    airport: string;
    airportName: string;
    date: string;
    time: string;
    terminal: string;
    formattedDateTime: string;
  };
  arrival: {
    airport: string;
    airportName: string;
    date: string;
    time: string;
    terminal: string;
    formattedDateTime: string;
  };
  duration: string;
  durationFormatted: string;
  classOfService: string;
  cabinClass: string;
  fareBasisCode: string;
}

export interface BookingInfo {
  orderId: string;
  bookingReference: string;
  alternativeOrderId: string;
  status: string;
  issueDate: string;
  issueDateFormatted: string;
  agencyName: string;
  discountApplied?: {
    name: string;
    percentage: number;
    amount: number;
  };
}

export interface PricingInfo {
  totalAmount: number;
  currency: string;
  formattedTotal: string;
  paymentMethod: string;
  paymentMethodLabel: string;
}

export interface BaggageDetails {
  checkedBags: number | null;
  carryOnBags: number | null;
  checkedBagAllowance?: {
    pieces?: number | null;
    weight?: {
      value: number;
      unit: string;
    };
    description?: string | null;
  };
  carryOnAllowance?: {
    pieces?: number | null;
    weight?: {
      value: number;
      unit: string;
    };
    description?: string | null;
  };
}

export interface FareRule {
  type: 'Cancel' | 'Change';
  application: string;
  timing: string;
  minAmount: number;
  maxAmount: number;
  currency: string;
  description: string;
  allowed: boolean;
}

export interface PassengerFareRules {
  passengerType: string;
  rules: FareRule[];
}

export interface ItineraryData {
  bookingInfo: BookingInfo;
  passengers: PassengerInfo[];
  outboundFlight: FlightSegment[];
  returnFlight: FlightSegment[] | null;
  pricing: PricingInfo;
  contactInfo: {
    email: string;
    phone: string;
  };
  baggageAllowance: BaggageDetails;
  fareRules: PassengerFareRules[];
}

// Airport code to name mapping (extend as needed)
const AIRPORT_NAMES: Record<string, string> = {
  'NBO': 'Jomo Kenyatta International Airport, Nairobi',
  'CDG': 'Charles de Gaulle Airport, Paris',
  'LHR': 'Heathrow Airport, London',
  'DXB': 'Dubai International Airport',
  'JFK': 'John F. Kennedy International Airport, New York',
  'LAX': 'Los Angeles International Airport',
  'BOM': 'Chhatrapati Shivaji Maharaj International Airport, Mumbai',
  'DEL': 'Indira Gandhi International Airport, New Delhi',
  'DOH': 'Hamad International Airport, Doha',
  'AMS': 'Amsterdam Airport Schiphol',
  'FRA': 'Frankfurt Airport',
  'ZUR': 'Zurich Airport',
  'IST': 'Istanbul Airport',
  'CAI': 'Cairo International Airport',
  'ADD': 'Addis Ababa Bole International Airport',
  'CPT': 'Cape Town International Airport',
  'JNB': 'O.R. Tambo International Airport, Johannesburg'
};

// Payment method code to label mapping
const PAYMENT_METHODS: Record<string, string> = {
  'CA': 'Cash',
  'CC': 'Credit Card',
  'DC': 'Debit Card',
  'PP': 'PayPal',
  'BT': 'Bank Transfer',
  'CH': 'Check'
};

// Passenger type labels
const PASSENGER_TYPE_LABELS: Record<string, string> = {
  'ADT': 'Adult',
  'CHD': 'Child',
  'INF': 'Infant'
};

/**
 * Formats date string to readable format
 */
function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
}

/**
 * Formats time string to readable format
 */
function formatTime(timeString: string): string {
  try {
    // Handle both "HH:mm:ss" and "HH:mm" formats
    const timeParts = timeString.split(':');
    const hours = parseInt(timeParts[0]);
    const minutes = timeParts[1];
    return `${hours.toString().padStart(2, '0')}:${minutes}`;
  } catch {
    return timeString;
  }
}

/**
 * Formats duration from ISO 8601 format (PT8H40M) to readable format
 */
function formatDuration(duration: string): string {
  try {
    const match = duration.match(/PT(\d+H)?(\d+M)?/);
    if (!match) return duration;
    
    const hours = match[1] ? parseInt(match[1].replace('H', '')) : 0;
    const minutes = match[2] ? parseInt(match[2].replace('M', '')) : 0;
    
    if (hours > 0 && minutes > 0) {
      return `${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h`;
    } else if (minutes > 0) {
      return `${minutes}m`;
    }
    return duration;
  } catch {
    return duration;
  }
}

/**
 * Calculates age from birth date
 */
function calculateAge(birthDate: string): number {
  try {
    const birth = new Date(birthDate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
  } catch {
    return 0;
  }
}

/**
 * Formats currency amount
 */
function formatCurrency(amount: number, currency: string): string {
  try {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
    return formatter.format(amount);
  } catch {
    return `${currency} ${amount.toLocaleString()}`;
  }
}

/**
 * Gets airport name from code
 */
function getAirportName(code: string): string {
  return AIRPORT_NAMES[code] || `${code} Airport`;
}

/**
 * Formats date and time from ISO string
 */
function formatDateTimeFromISO(isoString: string): string {
  try {
    if (!isoString) return 'N/A';
    const dateObj = new Date(isoString);
    const formattedDate = dateObj.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
    const formattedTime = dateObj.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
    return `${formattedDate} ${formattedTime}`;
  } catch {
    return isoString;
  }
}

/**
 * Extracts date only from ISO string
 */
function formatDateOnly(isoString: string): string {
  try {
    if (!isoString) return '';
    const dateObj = new Date(isoString);
    return dateObj.toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch {
    return isoString;
  }
}

/**
 * Extracts time only from ISO string
 */
function formatTimeOnly(isoString: string): string {
  try {
    if (!isoString) return '';
    const dateObj = new Date(isoString);
    return dateObj.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch {
    return isoString;
  }
}

/**
 * Combines date and time for display (legacy function)
 */
function formatDateTime(date: string, time: string): string {
  try {
    const dateObj = new Date(date);
    const formattedDate = dateObj.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
    const formattedTime = formatTime(time);
    return `${formattedDate} ${formattedTime}`;
  } catch {
    return `${date} ${time}`;
  }
}

/**
 * Airline mapping for proper airline names (FALLBACK ONLY)
 * Note: This is now used as fallback only. API-provided names are prioritized.
 * The backend now uses a centralized airline mapping service.
 */
const AIRLINE_NAMES_FALLBACK: { [key: string]: string } = {
  'AF': 'Air France',
  'KL': 'KLM Royal Dutch Airlines',
  'EK': 'Emirates',
  'QR': 'Qatar Airways',
  'KQ': 'Kenya Airways',
  'ET': 'Ethiopian Airlines',
  'LH': 'Lufthansa',
  'BA': 'British Airways',
  'SQ': 'Singapore Airlines',
  'EY': 'Etihad Airways',
  'TK': 'Turkish Airlines',
  'CX': 'Cathay Pacific',
  'QF': 'Qantas',
  'DL': 'Delta Air Lines',
  'UA': 'United Airlines',
  'AA': 'American Airlines',
  '6E': 'IndiGo',
  'AI': 'Air India',
  'IX': 'Air India Express',
  'SU': 'Aeroflot',
  'WN': 'Southwest Airlines',
  'NH': 'ANA All Nippon Airways',
  'JL': 'Japan Airlines',
  'CA': 'Air China',
  'CZ': 'China Southern Airlines',
  'MU': 'China Eastern Airlines',
  'GF': 'Gulf Air'  // Added missing Gulf Air
};

/**
 * Get airline name from airline code (FALLBACK ONLY)
 * Note: This should only be used when API doesn't provide airline name.
 * The backend now provides airline names through centralized mapping service.
 */
function getAirlineName(airlineCode: string): string {
  if (!airlineCode) {
    console.log('🔍 getAirlineName: No airline code provided');
    return 'Unknown Airline';
  }
  const code = airlineCode.trim().toUpperCase();
  const airlineName = AIRLINE_NAMES_FALLBACK[code];
  console.log(`🔍 getAirlineName: Using FALLBACK mapping for code "${code}" -> Name "${airlineName || `Airline ${code}`}"`);
  return airlineName || `Airline ${code}`;
}

// Helper function to extract detailed baggage information
function extractBaggageDetails(orderCreateResponse: any): BaggageDetails {
  const response = orderCreateResponse.Response || orderCreateResponse;
  const dataLists = response.DataLists;

  // Extract checked bag allowance
  const checkedBagAllowance = dataLists?.CheckedBagAllowanceList?.CheckedBagAllowance || [];
  const carryOnAllowance = dataLists?.CarryOnAllowanceList?.CarryOnAllowance || [];

  // Get basic baggage info from ticket documents
  const baggageInfo = response.TicketDocInfos?.TicketDocInfo?.[0]?.TicketDocument?.[0]?.CouponInfo?.[0]?.AddlBaggageInfo;

  let checkedBagDetails = null;
  let carryOnDetails = null;

  // Process checked bag allowance
  if (checkedBagAllowance.length > 0) {
    const checkedBag = checkedBagAllowance[0];
    if (checkedBag.PieceAllowance) {
      checkedBagDetails = {
        pieces: checkedBag.PieceAllowance[0]?.TotalQuantity || 0,
        description: 'Checked Bag Allowance'
      };
    } else if (checkedBag.WeightAllowance) {
      checkedBagDetails = {
        weight: {
          value: checkedBag.WeightAllowance.MaximumWeight[0]?.Value || 0,
          unit: checkedBag.WeightAllowance.MaximumWeight[0]?.UOM || 'Kilogram'
        },
        description: 'Checked Bag Weight Allowance'
      };
    }
  }

  // Process carry-on allowance
  if (carryOnAllowance.length > 0) {
    const carryOn = carryOnAllowance[0];
    if (carryOn.PieceAllowance) {
      const totalQuantity = carryOn.PieceAllowance[0]?.TotalQuantity;
      carryOnDetails = {
        pieces: totalQuantity !== undefined ? totalQuantity : null,
        description: carryOn.AllowanceDescription?.Descriptions?.Description?.[0]?.Text?.value || null
      };
    }
  }

  // Extract actual values from API response without hardcoded fallbacks
  const checkedBagsCount = baggageInfo?.AllowableBag?.[0]?.Number || checkedBagDetails?.pieces || null;
  const carryOnBagsCount = carryOnDetails?.pieces !== null ? carryOnDetails?.pieces : null;

  return {
    checkedBags: checkedBagsCount,
    carryOnBags: carryOnBagsCount,
    checkedBagAllowance: checkedBagDetails || undefined,
    carryOnAllowance: carryOnDetails || undefined
  };
}

// Helper function to extract fare rules
function extractFareRules(orderCreateResponse: any): PassengerFareRules[] {
  const response = orderCreateResponse.Response || orderCreateResponse;

  console.log('🔍 extractFareRules - Response structure:', {
    hasDataLists: !!response.DataLists,
    hasPenaltyList: !!response.DataLists?.PenaltyList,
    penaltyCount: response.DataLists?.PenaltyList?.Penalty?.length || 0,
    hasPassengers: !!response.Passengers,
    passengerCount: response.Passengers?.Passenger?.length || 0,
    responseKeys: Object.keys(response || {})
  });

  const penalties = response.DataLists?.PenaltyList?.Penalty || [];
  const passengers = response.Passengers?.Passenger || [];

  console.log('🔍 Penalty details:', penalties.map((p: any, i: number) => ({
    index: i,
    objectKey: p.ObjectKey,
    hasDetails: !!p.Details,
    detailCount: p.Details?.Detail?.length || 0,
    cancelFeeInd: p.CancelFeeInd,
    refundableInd: p.RefundableInd
  })));

  console.log('🔍 Passenger details:', passengers.map((p: any, i: number) => ({
    index: i,
    objectKey: p.ObjectKey,
    ptc: p.PTC?.value
  })));

  const fareRulesByPassenger: Record<string, FareRule[]> = {};

  // Process penalties
  penalties.forEach((penalty: any, penaltyIndex: number) => {
    console.log(`🔍 Processing penalty ${penaltyIndex}:`, {
      objectKey: penalty.ObjectKey,
      hasDetails: !!penalty.Details,
      detailsStructure: penalty.Details ? Object.keys(penalty.Details) : []
    });

    const details = penalty.Details?.Detail?.[0];
    if (!details) {
      console.log(`⚠️ Penalty ${penaltyIndex} has no details, skipping`);
      return;
    }

    const rule: FareRule = {
      type: details.Type as 'Cancel' | 'Change',
      application: getApplicationDescription(details.Application?.Code),
      timing: getTimingDescription(details.Application?.Code),
      minAmount: details.Amounts?.Amount?.[0]?.CurrencyAmountValue?.value || 0,
      maxAmount: details.Amounts?.Amount?.[1]?.CurrencyAmountValue?.value || 0,
      currency: details.Amounts?.Amount?.[0]?.CurrencyAmountValue?.Code || 'USD',
      description: details.Amounts?.Amount?.[0]?.ApplicableFeeRemarks?.Remark?.[0]?.value || '',
      allowed: penalty.CancelFeeInd !== false || penalty.ChangeFeeInd !== false || penalty.RefundableInd !== false || penalty.ChangeAllowedInd !== false
    };

    // Extract passenger reference from penalty ObjectKey
    const objectKey = penalty.ObjectKey || '';
    console.log(`🔍 Penalty ${penaltyIndex} ObjectKey: "${objectKey}"`);

    const passengerMatch = objectKey.match(/PAX(\d+)/);
    console.log(`🔍 Passenger match result:`, passengerMatch);

    if (passengerMatch) {
      const passengerKey = `PAX${passengerMatch[1]}`;
      console.log(`🔍 Adding rule to passenger: ${passengerKey}`);
      if (!fareRulesByPassenger[passengerKey]) {
        fareRulesByPassenger[passengerKey] = [];
      }
      fareRulesByPassenger[passengerKey].push(rule);
    } else {
      console.log(`⚠️ No passenger match found for ObjectKey: "${objectKey}"`);
    }
  });

  // Map to passenger types
  console.log('🔍 Final fareRulesByPassenger mapping:', fareRulesByPassenger);

  const result: PassengerFareRules[] = [];
  passengers.forEach((passenger: any, passengerIndex: number) => {
    const passengerKey = passenger.ObjectKey;
    const passengerType = passenger.PTC?.value || 'ADT';
    const rules = fareRulesByPassenger[passengerKey] || [];

    console.log(`🔍 Processing passenger ${passengerIndex}:`, {
      passengerKey,
      passengerType,
      rulesCount: rules.length
    });

    if (rules.length > 0) {
      result.push({
        passengerType,
        rules
      });
    }
  });

  console.log('🔍 Final fare rules result:', result.length, 'passenger groups');
  return result;
}

// Helper function to extract fare rules from processed flight price data
function extractFareRulesFromProcessedData(flightPriceData: any): PassengerFareRules[] {
  console.log('🎯 extractFareRulesFromProcessedData - Input data:', {
    hasPassengers: !!flightPriceData.passengers,
    passengerCount: flightPriceData.passengers?.length || 0,
    firstPassengerHasFareRules: !!flightPriceData.passengers?.[0]?.fare_rules
  });

  const result: PassengerFareRules[] = [];

  if (!flightPriceData.passengers || !Array.isArray(flightPriceData.passengers)) {
    console.log('🎯 No passengers array found in processed data');
    return result;
  }

  flightPriceData.passengers.forEach((passenger: any, index: number) => {
    console.log(`🎯 Processing passenger ${index}:`, {
      type: passenger.type,
      hasFareRules: !!passenger.fare_rules,
      fareRulesKeys: passenger.fare_rules ? Object.keys(passenger.fare_rules) : []
    });

    if (!passenger.fare_rules) return;

    const rules: FareRule[] = [];
    const fareRulesData = passenger.fare_rules;

    // Process different rule types
    Object.keys(fareRulesData).forEach(ruleType => {
      const ruleCategory = fareRulesData[ruleType];

      Object.keys(ruleCategory).forEach(timing => {
        const ruleDetails = ruleCategory[timing];

        const rule: FareRule = {
          type: ruleType.includes('Cancel') ? 'Cancel' : 'Change',
          application: timing,
          timing: timing,
          minAmount: ruleDetails.min_amount || 0,
          maxAmount: ruleDetails.max_amount || 0,
          currency: ruleDetails.currency || 'USD',
          description: ruleDetails.interpretation || '',
          allowed: ruleDetails.min_amount === 0 && ruleDetails.max_amount === 0
        };

        rules.push(rule);
      });
    });

    console.log(`🎯 Extracted ${rules.length} rules for passenger ${index}`);

    if (rules.length > 0) {
      result.push({
        passengerType: passenger.type || 'ADT',
        rules
      });
    }
  });

  console.log('🎯 extractFareRulesFromProcessedData - Final result:', result.length, 'passenger groups');
  return result;
}

// Helper function to get application description
function getApplicationDescription(code: string): string {
  const descriptions: Record<string, string> = {
    '1': 'After Departure - No Show',
    '2': 'Before Departure',
    '3': 'After Departure',
    '4': 'Before Departure - No Show'
  };
  return descriptions[code] || 'Standard';
}

// Helper function to get timing description
function getTimingDescription(code: string): string {
  const timings: Record<string, string> = {
    '1': 'After departure with no-show penalty',
    '2': 'Before departure standard timing',
    '3': 'After departure standard timing',
    '4': 'Before departure with no-show penalty'
  };
  return timings[code] || 'Standard timing';
}

/**
 * Transform data from the frontend API response structure (already processed)
 */
function transformFromFrontendAPIResponse(data: any): ItineraryData {
  console.log('🔄 Transforming from frontend API response structure');

  // Extract booking information from transformed structure
  const bookingInfo: BookingInfo = {
    orderId: data.order_id || data.orderItemId || 'N/A',
    bookingReference: data.bookingReference || 'N/A',
    alternativeOrderId: data.order_id || data.orderItemId || 'N/A',
    status: data.status || 'CONFIRMED',
    issueDate: data.createdAt || new Date().toISOString(),
    issueDateFormatted: formatDate(data.createdAt || new Date().toISOString()),
    agencyName: 'Rea Travels Agency',
    discountApplied: undefined
  };

  // Extract passenger information from transformed structure
  const passengers: PassengerInfo[] = [];
  if (data.passengerDetails && Array.isArray(data.passengerDetails)) {
    data.passengerDetails.forEach((passenger: any, index: number) => {
      passengers.push({
        objectKey: `PAX${index + 1}`,
        fullName: `${passenger.firstName || ''} ${passenger.lastName || ''}`.trim(),
        title: passenger.title || 'MR',
        firstName: passenger.firstName || '',
        lastName: passenger.lastName || '',
        passengerType: (passenger.type || 'ADT') as 'ADT' | 'CHD' | 'INF',
        passengerTypeLabel: passenger.type === 'CHD' ? 'Child' : passenger.type === 'INF' ? 'Infant' : 'Adult',
        birthDate: passenger.dateOfBirth || '',
        age: 0,
        documentType: 'PT',
        documentNumber: passenger.documentNumber || 'N/A',
        documentExpiry: '',
        countryOfIssuance: '',
        ticketNumber: passenger.ticketNumber || `TKT${String(index + 1).padStart(3, '0')}`
      });
    });
  }

  // Extract flight segments from transformed structure
  const outboundFlight: FlightSegment[] = [];
  const returnFlight: FlightSegment[] = [];

  if (data.flightDetails) {
    // Handle outbound flight
    if (data.flightDetails.outbound) {
      const outbound = data.flightDetails.outbound;
      outboundFlight.push({
        segmentKey: 'SEG1',
        flightNumber: outbound.airline?.flightNumber || 'N/A',
        airline: outbound.airline?.name || getAirlineName(outbound.airline?.code || ''),
        airlineCode: outbound.airline?.code || '',
        airlineLogo: outbound.airline?.logo || `/airlines/${outbound.airline?.code || 'default'}.svg`,
        aircraft: 'Unknown',
        aircraftCode: '',
        departure: {
          airport: outbound.departure?.code || '',
          airportName: outbound.departure?.airport || '',
          date: formatDateOnly(outbound.departure?.fullDate || ''),
          time: outbound.departure?.time || '',
          terminal: outbound.departure?.terminal || '',
          formattedDateTime: `${formatDateOnly(outbound.departure?.fullDate || '')} ${outbound.departure?.time || ''}`
        },
        arrival: {
          airport: outbound.arrival?.code || '',
          airportName: outbound.arrival?.airport || '',
          date: formatDateOnly(outbound.arrival?.fullDate || ''),
          time: outbound.arrival?.time || '',
          terminal: outbound.arrival?.terminal || '',
          formattedDateTime: `${formatDateOnly(outbound.arrival?.fullDate || '')} ${outbound.arrival?.time || ''}`
        },
        duration: 'N/A',
        durationFormatted: 'N/A',
        classOfService: 'Economy',
        cabinClass: 'Economy',
        fareBasisCode: 'N/A'
      });
    }

    // Handle return flight
    if (data.flightDetails.return) {
      const returnSeg = data.flightDetails.return;
      returnFlight.push({
        segmentKey: 'SEG2',
        flightNumber: returnSeg.airline?.flightNumber || 'N/A',
        airline: returnSeg.airline?.name || getAirlineName(returnSeg.airline?.code || ''),
        airlineCode: returnSeg.airline?.code || '',
        airlineLogo: returnSeg.airline?.logo || `/airlines/${returnSeg.airline?.code || 'default'}.svg`,
        aircraft: 'Unknown',
        aircraftCode: '',
        departure: {
          airport: returnSeg.departure?.code || '',
          airportName: returnSeg.departure?.airport || '',
          date: formatDateOnly(returnSeg.departure?.fullDate || ''),
          time: returnSeg.departure?.time || '',
          terminal: returnSeg.departure?.terminal || '',
          formattedDateTime: `${formatDateOnly(returnSeg.departure?.fullDate || '')} ${returnSeg.departure?.time || ''}`
        },
        arrival: {
          airport: returnSeg.arrival?.code || '',
          airportName: returnSeg.arrival?.airport || '',
          date: formatDateOnly(returnSeg.arrival?.fullDate || ''),
          time: returnSeg.arrival?.time || '',
          terminal: returnSeg.arrival?.terminal || '',
          formattedDateTime: `${formatDateOnly(returnSeg.arrival?.fullDate || '')} ${returnSeg.arrival?.time || ''}`
        },
        duration: 'N/A',
        durationFormatted: 'N/A',
        classOfService: 'Economy',
        cabinClass: 'Economy',
        fareBasisCode: 'N/A'
      });
    }
  }

  // Extract pricing information from transformed structure
  const pricing: PricingInfo = {
    totalAmount: data.paymentInfo?.amount?.amount || 0,
    currency: data.paymentInfo?.amount?.currency || 'USD',
    formattedTotal: formatCurrency(data.paymentInfo?.amount?.amount || 0, data.paymentInfo?.amount?.currency || 'USD'),
    paymentMethod: data.paymentInfo?.method || 'CA',
    paymentMethodLabel: PAYMENT_METHODS[data.paymentInfo?.method || 'CA'] || 'Cash'
  };

  // Contact information (basic fallback)
  const contactInfo = {
    email: 'customer@reatravels.com',
    phone: '+254 729 582 121'
  };

  // Extract baggage allowance from transformed data - use actual API values
  const baggageAllowance: BaggageDetails = {
    checkedBags: data.baggageAllowance?.checkedBags || null,
    carryOnBags: data.baggageAllowance?.carryOnBags || null,
    checkedBagAllowance: data.baggageAllowance?.checkedBagAllowance,
    carryOnAllowance: data.baggageAllowance?.carryOnAllowance
  };

  return {
    bookingInfo,
    passengers,
    outboundFlight,
    returnFlight: returnFlight.length > 0 ? returnFlight : null,
    pricing,
    contactInfo,
    baggageAllowance,
    fareRules: []
  };
}

/**
 * Fallback transformation using originalFlightOffer when OrderCreate response is unavailable
 */
function transformFromOriginalFlightOffer(originalFlightOffer: any, basicBookingData?: any): ItineraryData {

  const flight = originalFlightOffer.flight_segments?.[0] || {};
  const pricing = originalFlightOffer.total_price || {};
  const passenger = originalFlightOffer.passengers?.[0] || {};

  // Extract booking info
  const bookingInfo: BookingInfo = {
    orderId: originalFlightOffer.order_id || originalFlightOffer.offer_id || 'N/A',
    bookingReference: basicBookingData?.bookingReference || 'N/A',
    alternativeOrderId: originalFlightOffer.original_offer_id || 'N/A',
    status: 'CONFIRMED',
    issueDate: basicBookingData?.createdAt || new Date().toISOString(),
    issueDateFormatted: formatDate(basicBookingData?.createdAt || new Date().toISOString()),
    agencyName: 'Rea Travels Agency',
    discountApplied: undefined
  };

  // Extract passenger info
  const passengers: PassengerInfo[] = [];
  if (basicBookingData?.passengerDetails?.names) {
    const names = basicBookingData.passengerDetails.names.split(', ');
    const documents = basicBookingData.documentNumbers || [];

    names.forEach((name: string, index: number) => {
      const passengerType = (passenger.type || 'ADT') as 'ADT' | 'CHD' | 'INF';
      passengers.push({
        objectKey: `PAX${index + 1}`,
        fullName: name.trim(),
        title: '',
        firstName: name.split(' ')[0] || '',
        lastName: name.split(' ').slice(1).join(' ') || '',
        passengerType: passengerType,
        passengerTypeLabel: passengerType === 'ADT' ? 'Adult' : passengerType === 'CHD' ? 'Child' : passengerType === 'INF' ? 'Infant' : passengerType,
        birthDate: '',
        age: 0,
        documentType: 'PT',
        documentNumber: documents[index] || '',
        documentExpiry: '',
        countryOfIssuance: '',
        ticketNumber: `TKT-${basicBookingData?.bookingReference || 'UNKNOWN'}-${index + 1}`
      });
    });
  }

  // Extract flight info
  const outboundFlight: FlightSegment[] = [{
    segmentKey: 'SEG1',
    flightNumber: flight.flight_number || 'Unknown',
    airline: flight.airline_name || 'Unknown Airline',
    airlineCode: flight.airline_code || 'Unknown',
    airlineLogo: `/airlines/${flight.airline_code || 'default'}.svg`,
    aircraft: 'TBD',
    aircraftCode: '',
    departure: {
      airport: flight.departure_airport || 'Unknown',
      airportName: flight.departure_airport || 'Unknown',
      time: flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
      date: flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleDateString() : 'Unknown',
      terminal: 'TBD',
      formattedDateTime: flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleString() : 'Unknown'
    },
    arrival: {
      airport: flight.arrival_airport || 'Unknown',
      airportName: flight.arrival_airport || 'Unknown',
      time: flight.arrival_datetime ? new Date(flight.arrival_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
      date: flight.arrival_datetime ? new Date(flight.arrival_datetime).toLocaleDateString() : 'Unknown',
      terminal: 'TBD',
      formattedDateTime: flight.arrival_datetime ? new Date(flight.arrival_datetime).toLocaleString() : 'Unknown'
    },
    duration: flight.duration || 'Unknown',
    durationFormatted: flight.duration || 'Unknown',
    classOfService: originalFlightOffer.fare_family || 'Economy',
    cabinClass: originalFlightOffer.fare_family || 'Economy',
    fareBasisCode: 'N/A'
  }];

  // Extract pricing
  const pricingInfo: PricingInfo = {
    totalAmount: pricing.amount || 0,
    formattedTotal: pricing.amount ? `${pricing.amount} ${pricing.currency || 'USD'}` : '0 USD',
    currency: pricing.currency || 'USD',
    paymentMethod: 'CA',
    paymentMethodLabel: 'Credit Card'
  };

  // Extract contact info
  const contactInfo = {
    email: basicBookingData?.contactInfo?.email || '',
    phone: basicBookingData?.contactInfo?.phone || ''
  };

  // Extract baggage allowance from originalFlightOffer if available - use actual API values
  const baggageAllowance: BaggageDetails = {
    checkedBags: originalFlightOffer?.baggage_allowance?.checked_bags || null,
    carryOnBags: originalFlightOffer?.baggage_allowance?.carry_on_bags || null,
    checkedBagAllowance: originalFlightOffer?.baggage_allowance?.checked_bag_details ? {
      pieces: originalFlightOffer.baggage_allowance.checked_bag_details.pieces,
      weight: originalFlightOffer.baggage_allowance.checked_bag_details.weight,
      description: originalFlightOffer.baggage_allowance.checked_bag_details.description
    } : undefined,
    carryOnAllowance: originalFlightOffer?.baggage_allowance?.carry_on_details ? {
      pieces: originalFlightOffer.baggage_allowance.carry_on_details.pieces,
      weight: originalFlightOffer.baggage_allowance.carry_on_details.weight,
      description: originalFlightOffer.baggage_allowance.carry_on_details.description
    } : undefined
  };

  return {
    bookingInfo,
    passengers,
    outboundFlight,
    returnFlight: null,
    pricing: pricingInfo,
    contactInfo,
    baggageAllowance,
    fareRules: []
  };
}

/**
 * Main transformation function to extract itinerary data from OrderCreate response
 */
export function transformOrderCreateToItinerary(orderCreateResponse: any, originalFlightOffer?: any, basicBookingData?: any): ItineraryData {
  // Validate input - if no OrderCreate response, try originalFlightOffer fallback
  if (!orderCreateResponse) {
    if (originalFlightOffer) {
      console.log('⚠️ No OrderCreate response, using originalFlightOffer fallback');
      return transformFromOriginalFlightOffer(originalFlightOffer, basicBookingData);
    }
    throw new Error('OrderCreate response is null or undefined and no originalFlightOffer fallback available');
  }

  console.log('🔍 Starting itinerary transformation...');
  console.log('📋 Input data structure:', {
    hasResponse: !!orderCreateResponse.Response,
    hasOrder: !!orderCreateResponse.Response?.Order,
    hasBookingReference: !!orderCreateResponse.bookingReference,
    hasTransformedData: !!orderCreateResponse.data,
    topLevelKeys: Object.keys(orderCreateResponse)
  });

  // Check if this is already transformed data from the frontend API response
  if (orderCreateResponse.status === 'success' && orderCreateResponse.data) {
    console.log('✅ Detected transformed frontend API response structure');
    return transformFromFrontendAPIResponse(orderCreateResponse.data);
  }

  // Handle different response structures - check multiple paths for NDC data
  let response;

  // Priority 1: Check raw_order_create_response.Response (most common for newer bookings)
  if (orderCreateResponse.raw_order_create_response?.Response) {
    response = orderCreateResponse.raw_order_create_response.Response;
    console.log('✅ Using NDC data from raw_order_create_response.Response');
  }
  // Priority 2: Check direct Response (legacy structure)
  else if (orderCreateResponse.Response) {
    response = orderCreateResponse.Response;
    console.log('✅ Using NDC data from direct Response');
  }
  // Priority 3: Check nested data.Response
  else if (orderCreateResponse.data?.Response) {
    response = orderCreateResponse.data.Response;
    console.log('✅ Using NDC data from data.Response');
  }
  // Priority 4: Check if response is at root level (direct NDC structure)
  else if (orderCreateResponse.Order || orderCreateResponse.Passengers || orderCreateResponse.TicketDocInfos) {
    response = orderCreateResponse;
    console.log('✅ Using NDC data from root level');
  }
  // Priority 5: Check raw_order_create_response.data.Response
  else if (orderCreateResponse.raw_order_create_response?.data?.Response) {
    response = orderCreateResponse.raw_order_create_response.data.Response;
    console.log('✅ Using NDC data from raw_order_create_response.data.Response');
  }
  else {
    console.error('Invalid OrderCreate response structure:', {
      topLevelKeys: Object.keys(orderCreateResponse),
      hasRawOrderCreate: !!orderCreateResponse.raw_order_create_response,
      rawOrderCreateKeys: orderCreateResponse.raw_order_create_response ? Object.keys(orderCreateResponse.raw_order_create_response) : []
    });
    throw new Error('Invalid OrderCreate response structure - missing required NDC fields');
  }

  if (!response) {
    throw new Error('Unable to extract response data from OrderCreate response');
  }

  // Extract booking information
  const order = response.Order?.[0];
  const bookingInfo: BookingInfo = {
    orderId: order?.OrderID?.value || 'N/A',
    bookingReference: order?.BookingReferences?.BookingReference?.[0]?.ID || 'N/A',
    alternativeOrderId: order?.BookingReferences?.BookingReference?.[0]?.OtherID?.value || 'N/A',
    status: order?.Status?.StatusCode?.Code || 'UNKNOWN',
    issueDate: response.TicketDocInfos?.TicketDocInfo?.[0]?.TicketDocument?.[0]?.DateOfIssue || new Date().toISOString(),
    issueDateFormatted: formatDate(response.TicketDocInfos?.TicketDocInfo?.[0]?.TicketDocument?.[0]?.DateOfIssue || new Date().toISOString()),
    agencyName: 'Rea Travels Agency', // Default agency name
    discountApplied: undefined
  };

  // Extract discount information if available
  const firstOrderItem = order?.OrderItems?.OrderItem?.[0];
  const discount = firstOrderItem?.FlightItem?.Price?.Discount?.[0];
  if (discount) {
    bookingInfo.discountApplied = {
      name: discount.discountName || 'Discount',
      percentage: discount.DiscountPercent || 0,
      amount: discount.DiscountAmount?.value || 0
    };
    // Update agency name from discount owner if available
    if (discount.discountOwner) {
      bookingInfo.agencyName = discount.discountOwner;
    }
  }

  // Extract pricing information
  const totalPrice = order?.TotalOrderPrice?.SimpleCurrencyPrice;
  const payment = response.Payments?.Payment?.[0];
  const pricing: PricingInfo = {
    totalAmount: totalPrice?.value || 0,
    currency: totalPrice?.Code || 'USD',
    formattedTotal: formatCurrency(totalPrice?.value || 0, totalPrice?.Code || 'USD'),
    paymentMethod: payment?.Type?.Code || 'CA',
    paymentMethodLabel: PAYMENT_METHODS[payment?.Type?.Code || 'CA'] || 'Cash'
  };

  // Extract passenger information with ticket numbers using ObjectKey-based mapping
  const passengers: PassengerInfo[] = [];
  const passengersData = response.Passengers?.Passenger || [];
  const ticketDocInfos = response.TicketDocInfos?.TicketDocInfo || [];

  // Create a mapping of ObjectKey to ticket information for efficient lookup
  const ticketMapping: Record<string, { ticketNumber: string; dateOfIssue: string; issuingAirline: string }> = {};
  ticketDocInfos.forEach((ticketDoc: any) => {
    const passengerRefs = ticketDoc.PassengerReference || [];
    const ticketDocuments = ticketDoc.TicketDocument || [];

    // Handle both single passenger reference and multiple passenger references
    passengerRefs.forEach((passengerRef: string) => {
      if (ticketDocuments.length > 0) {
        ticketMapping[passengerRef] = {
          ticketNumber: ticketDocuments[0].TicketDocNbr || 'N/A',
          dateOfIssue: ticketDocuments[0].DateOfIssue || '',
          issuingAirline: ticketDoc.IssuingAirlineInfo?.AirlineName || ''
        };
      }
    });
  });

  passengersData.forEach((passenger: any, index: number) => {
    const name = passenger.Name || {};
    const contact = passenger.Contacts?.Contact?.[0];
    const document = passenger.PassengerIDInfo?.PassengerDocument?.[0];

    // Find corresponding ticket number using ObjectKey mapping
    const passengerObjectKey = passenger.ObjectKey || `PAX${index + 1}`;
    const ticketInfo = ticketMapping[passengerObjectKey] || {};
    const ticketNumber = ticketInfo.ticketNumber || 'N/A';

    const passengerInfo: PassengerInfo = {
      objectKey: passenger.ObjectKey || `PAX${index + 1}`,
      fullName: `${name.Title || ''} ${name.Given?.[0]?.value || ''} ${name.Surname?.value || ''}`.trim(),
      title: name.Title || '',
      firstName: name.Given?.[0]?.value || '',
      lastName: name.Surname?.value || '',
      passengerType: passenger.PTC?.value || 'ADT',
      passengerTypeLabel: PASSENGER_TYPE_LABELS[passenger.PTC?.value || 'ADT'] || 'Adult',
      birthDate: passenger.Age?.BirthDate?.value || '',
      age: calculateAge(passenger.Age?.BirthDate?.value || ''),
      documentType: document?.Type || 'PT',
      documentNumber: document?.ID || 'N/A',
      documentExpiry: document?.DateOfExpiration || '',
      countryOfIssuance: document?.CountryOfIssuance || '',
      countryOfResidence: document?.CountryOfResidence,
      ticketNumber: ticketNumber,
      email: contact?.EmailContact?.Address?.value,
      phone: contact?.PhoneContact?.Number?.[0] ? 
        `+${contact.PhoneContact.Number[0].CountryCode}${contact.PhoneContact.Number[0].value}` : undefined
    };

    passengers.push(passengerInfo);
  });

  // Extract contact information from primary passenger
  const primaryPassenger = passengers.find(p => p.email) || passengers[0];
  const contactInfo = {
    email: primaryPassenger?.email || 'N/A',
    phone: primaryPassenger?.phone || 'N/A'
  };

  // Extract flight segments
  const originDestinations = firstOrderItem?.FlightItem?.OriginDestination || [];
  const outboundFlight: FlightSegment[] = [];
  const returnFlight: FlightSegment[] = [];

  originDestinations.forEach((od: any, odIndex: number) => {
    const flights = od.Flight || [];
    
    flights.forEach((flight: any) => {
      const segment: FlightSegment = {
        segmentKey: flight.SegmentKey || `SEG${odIndex + 1}`,
        flightNumber: `${flight.MarketingCarrier?.AirlineID?.value || ''} ${flight.MarketingCarrier?.FlightNumber?.value || ''}`.trim(),
        airline: (() => {
          const carrierName = flight.MarketingCarrier?.Name;
          const carrierCode = flight.MarketingCarrier?.AirlineID?.value;
          console.log(`🔍 Flight segment airline data: Name="${carrierName}", Code="${carrierCode}"`);

          // Prioritize API-provided name, use fallback mapping only if API name is missing
          if (carrierName && carrierName.trim() && carrierName !== 'None') {
            console.log(`🔍 Using API-provided airline name: "${carrierName}"`);
            return carrierName;
          } else {
            console.log(`🔍 API name missing/invalid, using fallback mapping for code: "${carrierCode}"`);
            return getAirlineName(carrierCode || '');
          }
        })(),
        airlineCode: flight.MarketingCarrier?.AirlineID?.value || '',
        airlineLogo: `/airlines/${flight.MarketingCarrier?.AirlineID?.value || 'default'}.svg`,
        aircraft: flight.Equipment?.Name || 'Unknown',
        aircraftCode: flight.Equipment?.AircraftCode?.value || '',
        departure: {
          airport: flight.Departure?.AirportCode?.value || '',
          airportName: getAirportName(flight.Departure?.AirportCode?.value || ''),
          date: formatDateOnly(flight.Departure?.Date || ''),
          time: flight.Departure?.Time || formatTimeOnly(flight.Departure?.Date || ''),
          terminal: flight.Departure?.Terminal?.Name || '',
          formattedDateTime: formatDateTimeFromISO(flight.Departure?.Date || '')
        },
        arrival: {
          airport: flight.Arrival?.AirportCode?.value || '',
          airportName: getAirportName(flight.Arrival?.AirportCode?.value || ''),
          date: formatDateOnly(flight.Arrival?.Date || ''),
          time: flight.Arrival?.Time || formatTimeOnly(flight.Arrival?.Date || ''),
          terminal: flight.Arrival?.Terminal?.Name || '',
          formattedDateTime: formatDateTimeFromISO(flight.Arrival?.Date || '')
        },
        duration: flight.Details?.FlightDuration?.Value || '',
        durationFormatted: formatDuration(flight.Details?.FlightDuration?.Value || ''),
        classOfService: flight.ClassOfService?.MarketingName?.value || 'Economy',
        cabinClass: flight.ClassOfService?.CabinDesignator || 'Y',
        fareBasisCode: flight.MarketingCarrier?.ResBookDesigCode || ''
      };

      // Determine if this is outbound or return based on segment key or index
      if (odIndex === 0) {
        outboundFlight.push(segment);
      } else {
        returnFlight.push(segment);
      }
    });
  });

  // Extract detailed baggage allowance
  const baggageAllowance = extractBaggageDetails(response);

  // Extract fare rules - try multiple data sources
  let fareRules: PassengerFareRules[] = [];

  // First try to get fare rules from processed flight price data (session storage format)
  if (originalFlightOffer?.passengers?.[0]?.fare_rules) {
    console.log('🎯 Found processed fare rules in originalFlightOffer');
    fareRules = extractFareRulesFromProcessedData(originalFlightOffer);
    console.log('🎯 Extracted fare rules from processed data:', fareRules.length, 'passenger groups');
  }

  // Second try to get fare rules from the original flight price response
  if (fareRules.length === 0 && originalFlightOffer?.raw_flight_price_response) {
    console.log('🎯 Attempting to extract fare rules from FlightPrice response');
    fareRules = extractFareRules(originalFlightOffer.raw_flight_price_response);
    console.log('🎯 Extracted fare rules from FlightPrice:', fareRules.length, 'passenger groups');
  }

  // If no fare rules found, try from OrderCreate response
  if (fareRules.length === 0) {
    console.log('🎯 No fare rules in FlightPrice response, trying OrderCreate response');
    fareRules = extractFareRules(response);
    console.log('🎯 Extracted fare rules from OrderCreate:', fareRules.length, 'passenger groups');
  }

  return {
    bookingInfo,
    passengers,
    outboundFlight,
    returnFlight: returnFlight.length > 0 ? returnFlight : null,
    pricing,
    contactInfo,
    baggageAllowance,
    fareRules
  };
}
