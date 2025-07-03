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
  checkedBags: number;
  carryOnBags: number;
  checkedBagAllowance?: {
    pieces?: number;
    weight?: {
      value: number;
      unit: string;
    };
    description?: string;
  };
  carryOnAllowance?: {
    pieces?: number;
    weight?: {
      value: number;
      unit: string;
    };
    description?: string;
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
 * Combines date and time for display
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
      carryOnDetails = {
        pieces: carryOn.PieceAllowance[0]?.TotalQuantity || 0,
        description: 'Carry-On Bag Allowance'
      };
    }
  }

  return {
    checkedBags: baggageInfo?.AllowableBag?.[0]?.Number || checkedBagDetails?.pieces || 1,
    carryOnBags: carryOnDetails?.pieces || 1,
    checkedBagAllowance: checkedBagDetails,
    carryOnAllowance: carryOnDetails
  };
}

// Helper function to extract fare rules
function extractFareRules(orderCreateResponse: any): PassengerFareRules[] {
  const response = orderCreateResponse.Response || orderCreateResponse;
  const penalties = response.DataLists?.PenaltyList?.Penalty || [];
  const passengers = response.Passengers?.Passenger || [];

  const fareRulesByPassenger: Record<string, FareRule[]> = {};

  // Process penalties
  penalties.forEach((penalty: any) => {
    const details = penalty.Details?.Detail?.[0];
    if (!details) return;

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
    const passengerMatch = objectKey.match(/PAX(\d+)/);
    if (passengerMatch) {
      const passengerKey = `PAX${passengerMatch[1]}`;
      if (!fareRulesByPassenger[passengerKey]) {
        fareRulesByPassenger[passengerKey] = [];
      }
      fareRulesByPassenger[passengerKey].push(rule);
    }
  });

  // Map to passenger types
  const result: PassengerFareRules[] = [];
  passengers.forEach((passenger: any) => {
    const passengerKey = passenger.ObjectKey;
    const passengerType = passenger.PTC?.value || 'ADT';
    const rules = fareRulesByPassenger[passengerKey] || [];

    if (rules.length > 0) {
      result.push({
        passengerType,
        rules
      });
    }
  });

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
 * Main transformation function to extract itinerary data from OrderCreate response
 */
export function transformOrderCreateToItinerary(orderCreateResponse: any): ItineraryData {
  const response = orderCreateResponse.Response || orderCreateResponse;
  
  if (!response) {
    throw new Error('Invalid OrderCreate response structure');
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

  // Extract passenger information with ticket numbers
  const passengers: PassengerInfo[] = [];
  const passengersData = response.Passengers?.Passenger || [];
  const ticketDocInfos = response.TicketDocInfos?.TicketDocInfo || [];

  passengersData.forEach((passenger: any, index: number) => {
    const name = passenger.Name || {};
    const contact = passenger.Contacts?.Contact?.[0];
    const document = passenger.PassengerIDInfo?.PassengerDocument?.[0];
    
    // Find corresponding ticket number
    let ticketNumber = 'N/A';
    if (ticketDocInfos[index]?.TicketDocument?.[0]?.TicketDocNbr) {
      ticketNumber = ticketDocInfos[index].TicketDocument[0].TicketDocNbr;
    }

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
        airline: flight.MarketingCarrier?.Name || 'Unknown Airline',
        airlineCode: flight.MarketingCarrier?.AirlineID?.value || '',
        airlineLogo: `/airlines/${flight.MarketingCarrier?.AirlineID?.value || 'default'}.svg`,
        aircraft: flight.Equipment?.Name || 'Unknown',
        aircraftCode: flight.Equipment?.AircraftCode?.value || '',
        departure: {
          airport: flight.Departure?.AirportCode?.value || '',
          airportName: getAirportName(flight.Departure?.AirportCode?.value || ''),
          date: flight.Departure?.Date || '',
          time: flight.Departure?.Time || '',
          terminal: flight.Departure?.Terminal?.Name || '',
          formattedDateTime: formatDateTime(flight.Departure?.Date || '', flight.Departure?.Time || '')
        },
        arrival: {
          airport: flight.Arrival?.AirportCode?.value || '',
          airportName: getAirportName(flight.Arrival?.AirportCode?.value || ''),
          date: flight.Arrival?.Date || '',
          time: flight.Arrival?.Time || '',
          terminal: flight.Arrival?.Terminal?.Name || '',
          formattedDateTime: formatDateTime(flight.Arrival?.Date || '', flight.Arrival?.Time || '')
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

  // Extract fare rules
  const fareRules = extractFareRules(response);

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
