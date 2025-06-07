// Types for Flight API request structure

export interface Preference {
  CabinPreferences: {
    CabinType: Array<{
      PrefLevel: {
        PrefLevelCode: string;
      };
      OriginDestinationReferences: string[];
      Code: string;
    }>;
  };
  FarePreferences: {
    Types: {
      Type: Array<{
        Code: string;
      }>;
    };
  };
  PricingMethodPreference: {
    BestPricingOption: string;
  };
}

export interface ResponseParameters {
  ResultsLimit: {
    value: number;
  };
  SortOrder: Array<{
    Order: 'ASCENDING' | 'DESCENDING';
    Parameter: string;
  }>;
  ShopResultPreference: string;
}

export interface Traveler {
  AnonymousTraveler: Array<{
    PTC: {
      value: string;
    };
    Age: {
      Value: {
        value: number;
      };
      BirthDate: {
        value: string;
      };
    };
  }>;
}

export interface Travelers {
  Traveler: Traveler[];
}

export interface CoreQuery {
  OriginDestinations: {
    OriginDestination: Array<{
      Departure: {
        AirportCode: {
          value: string;
        };
        Date: string;
      };
      Arrival: {
        AirportCode: {
          value: string;
        };
      };
      OriginDestinationKey: string;
    }>;
  };
}

export interface FlightSearchRequest {
  Preference: Preference;
  ResponseParameters: ResponseParameters;
  Travelers: Travelers;
  CoreQuery: CoreQuery;
}

// Add response types as needed based on actual API response structure.

// --- Response Processing and Optimized Output Types ---

export interface AirportDetails {
  code: string;       // Airport code (e.g., 'BOM', 'DXB')
  name?: string;      // Full airport name (e.g., 'Dubai International')
  terminal?: string;  // Terminal information
  city?: string;      // City where the airport is located
}

export interface AircraftDetails {
  code: string;       // Aircraft code (e.g., '77W', '789')
  name?: string;      // Full aircraft name (e.g., 'Boeing 777-300ER')
}

export interface AirlineDetails {
  code: string;       // Airline code (e.g., 'EK', 'QR')
  name: string;       // Full airline name (e.g., 'Emirates')
  logo?: string;      // Path to airline logo
  flightNumber: string; // Flight number
}

export interface FlightSegmentDetails {
  id: string;
  departure: { 
    airport: string; 
    datetime: string; 
    terminal?: string;
    airportName?: string;
  };
  arrival: { 
    airport: string; 
    datetime: string; 
    terminal?: string;
    airportName?: string; 
  };
  airline: AirlineDetails;
  operatingAirline?: AirlineDetails; // For codeshare flights
  aircraft?: AircraftDetails;        // Aircraft information
  duration: string;
}

export interface FlightDetailsResult {
  segments: FlightSegmentDetails[];
  duration: string;
}

// Represents the final, simplified flight offer structure returned by optimizeFlightData
export interface BaggageDimension {
  value?: number;
  unit?: string; // cm, inches, etc.
}

export interface BaggageWeight {
  value: number;
  unit: string; // kg, lb, etc.
}

export interface SpecialItem {
  type: string; // e.g., 'SPORTING_EQUIPMENT', 'MUSICAL_INSTRUMENT', etc.
  description: string;
  allowed: boolean;
  extraFee?: boolean;
}

export interface CarryOnBaggage {
  weight?: BaggageWeight;
  dimensions?: {
    length?: BaggageDimension;
    width?: BaggageDimension;
    height?: BaggageDimension;
    totalDimensions?: BaggageDimension; // Sum of length + width + height
  };
  description?: string;
  isPersonalItemIncluded?: boolean;
  quantity?: number;         // Number of carry-on bags allowed
  personalItemDimensions?: { // For personal item (e.g., purse, laptop bag)
    length?: BaggageDimension;
    width?: BaggageDimension;
    height?: BaggageDimension;
  };
  personalItemWeight?: BaggageWeight;
  restrictions?: string[];
  personalItem?: {
    description?: string;
    dimensions?: any;
    weight?: BaggageWeight;
  };
}

export interface CheckedBaggage {
  weight?: BaggageWeight;
  pieces?: number;
  dimensions?: {
    length?: BaggageDimension;
    width?: BaggageDimension;
    height?: BaggageDimension;
    totalDimensions?: BaggageDimension; // Sum of length + width + height
  };
  description?: string;
  policyType: 'WEIGHT_BASED' | 'PIECE_BASED' | 'BOTH';
  extraBaggageFees?: {      // Fees for additional baggage
    amount: number;
    currency: string;
    perPiece?: boolean;     // Whether fee is per piece or per kg/lb
    description?: string;
  };
  freeBaggageAllowance?: number; // Number of pieces allowed for free
  overweightCharge?: {
    amount: number;
    currency: string;
    perKgOrLb?: string;
    threshold?: number;
    description?: string;
  };
  oversizeCharge?: {
    amount: number;
    currency: string;
    description?: string;
  };
  additionalBaggagePrices?: Array<{
    amount: number;
    currency: string;
    weight?: BaggageWeight;
  }>;
  prepaidDiscount?: {
    percentage: number;
    description?: string;
  };
  specialItems?: Array<{
    type: string;
    description: string;
    allowed: boolean;
    extraFee?: boolean;
  }>;
}

export interface BaggageAllowance {
  carryOn: CarryOnBaggage;
  checkedBaggage?: CheckedBaggage;
  specialItems?: SpecialItem[];
  additionalInfo?: string; // Any additional information about baggage policy
  prepaidBaggageDiscount?: number; // Discount percentage when prepaying for baggage
  overweightCharges?: {
    amount: number;
    currency: string;
    perKgOrLb?: string;
    threshold?: number;
    description?: string;
  };
  oversizeCharges?: {
    amount: number;
    currency: string;
    description?: string;
  };
}

export interface FareRules {
  changeFee?: boolean;
  refundable?: boolean;
  exchangeable?: boolean;
  description?: string;
  penalties?: string[];
  
  // Enhanced fare rules from PenaltyList
  changeBeforeDeparture?: {
    allowed: boolean;
    fee: number;
    currency: string;
    conditions?: string;
  };
  changeAfterDeparture?: {
    allowed: boolean;
    fee: number;
    currency: string;
    conditions?: string;
  };
  changeNoShow?: {
    allowed: boolean;
    fee: number;
    currency: string;
    conditions?: string;
  };
  cancelBeforeDeparture?: {
    allowed: boolean;
    fee: number;
    currency: string;
    conditions?: string;
    refundPercentage?: number;
  };
  cancelAfterDeparture?: {
    allowed: boolean;
    fee: number;
    currency: string;
    conditions?: string;
    refundPercentage?: number;
  };
  cancelNoShow?: {
    allowed: boolean;
    fee: number;
    currency: string;
    conditions?: string;
    refundPercentage?: number;
  };
  noShow?: {
    refundable: boolean;
    fee: number;
    currency: string;
    conditions?: string;
    refundPercentage?: number;
  };
  additionalRestrictions?: string[];
}

export interface FareDetails {
  fareBasisCode: string;           // e.g., 'TLAOPIN1', 'WDFLX1IA'
  fareType?: string;               // e.g., 'PUBL' (public fare)
  fareClass?: string;              // e.g., economy, business, first
  rules?: FareRules;               // Rules and restrictions
  fareFamily?: string;             // e.g., 'FLEX', 'STANDARD', 'BASIC'
  fareDescription?: string;        // Human-readable description
  
  // Enhanced fare details from PriceList
  fareName?: string;               // e.g., 'ECONOMY LIGHT', 'ECONOMY PROMO'
  fareCode?: string;               // e.g., 'YL'
  additionalServices?: {
    seatSelection?: string;        // e.g., 'Reserve your seat for a fee'
    awardUpgrade?: string;         // e.g., 'Not permitted', 'Permitted'
    goShow?: string;               // e.g., 'Not eligible'
    otherServices?: Record<string, string>; // Any other service information
  };
}

export interface PriceBreakdown {
  baseFare: number;
  taxes: number;
  fees: number;
  surcharges?: number;
  discounts?: number;
  totalPrice: number;
  currency: string;
  taxDetails?: {
    code: string;
    amount: number;
    description?: string;
  }[];
  feeDetails?: {
    code: string;
    amount: number;
    description?: string;
  }[];
}

export interface AdditionalServices {
  seatSelection?: {
    available: boolean;
    complimentary: boolean;
    cost?: number;
    currency?: string;
    description?: string;
    seatOptions?: Array<{
      name: string;
      cost?: number;
      currency?: string;
    }>;
  };
  meals?: {
    available: boolean;
    complimentary: boolean;
    options?: string[];
    description?: string;
    cost?: number;
    currency?: string;
    dietaryRestrictions?: string[];
  };
  priorityBoarding?: {
    available: boolean;
    complimentary: boolean;
    cost?: number;
    currency?: string;
    description?: string;
  };
  wifiAvailable?: boolean;
  powerOutlets?: boolean;
  entertainmentSystem?: boolean;
  wifiDetails?: {
    cost?: number;
    currency?: string;
    description?: string;
  };
  entertainmentDetails?: string;
  additionalAmenities?: string[];
}

export interface FlightOffer {
  id: string;
  airline: AirlineDetails;
  departure: { 
    airport: string; 
    datetime: string;
    terminal?: string;
    airportName?: string;
  };
  arrival: { 
    airport: string; 
    datetime: string;
    terminal?: string;
    airportName?: string;
  };
  duration: string;
  stops: number;
  stopDetails: string[]; // Array of airport codes for stops
  price: number;
  currency: string;
  seatsAvailable: number | string; // Can be number or 'N/A'
  baggage: BaggageAllowance; // Added baggage allowance information
  fare?: FareDetails; // Added fare details information
  aircraft?: AircraftDetails; // Added aircraft information
  segments?: FlightSegmentDetails[]; // Detailed information about each flight segment 
  priceBreakdown?: PriceBreakdown; // Added price breakdown information
  additionalServices?: AdditionalServices; // Added additional services information
}

// API Response interfaces
export interface FlightSearchResponse {
  status: string;
  data: {
    offers: FlightOffer[];
    total_offers: number;
    metadata?: any;
  };
  request_id: string;
}
