import axios from "axios"
import {logger} from "./logger";
import type { 
  FlightSearchRequest, 
  FlightOffer, 
  FlightSegmentDetails, 
  FlightDetailsResult, 
  BaggageAllowance, 
  CarryOnBaggage, 
  CheckedBaggage, 
  SpecialItem, 
  BaggageWeight, 
  BaggageDimension, 
  FareDetails, 
  FareRules,
  PriceBreakdown,
  AdditionalServices,
  AirlineDetails,
  AircraftDetails
} from '@/types/flight-api';

// --- Verteil API Types and Token Management ---

export interface VerteilToken {
  access_token: string;
  token_type: string;
  expires_in: number; // in seconds
  scope?: string;
}

let verteilToken: VerteilToken | null = null;
let verteilTokenExpiry: number | null = null; // In-memory expiry for server-side
const verteilTokenExpiryKey = 'verteilTokenExpiry';
const verteilTokenKey = 'verteilToken';

/**
 * Fetch a new Verteil API token using Basic Auth.
 */
async function fetchVerteilToken(): Promise<VerteilToken> {
  const username = 'reatravel_apitestuser';
  const password = 'UZrNcyxpIFn2TOdiU5uc9kZrqJwxU44KdlyFBpiDOaaNom1xSySEtQmRq9IcDq3c';
  const basicAuth = btoa(`${username}:${password}`);
  const url = 'https://api.stage.verteil.com/oauth2/token?grant_type=client_credentials&scope=api';

  const headers = {
    'Authorization': `Basic ${basicAuth}`,
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'REATravel/1.0',
  };

  try {
    const response = await axios.post(url, null, { headers });
    return response.data as VerteilToken;
  } catch (error) {
    throw error;
  }
}

/**
 * Get a valid Verteil token, refreshing if expired.
 */
export async function getVerteilToken(): Promise<VerteilToken> {
  // Check in-memory first
  if (verteilToken && verteilTokenExpiry && verteilTokenExpiry > Date.now()) {
    return verteilToken;
  }

  // Check sessionStorage (only if in browser)
  if (typeof window !== 'undefined') {
    const storedToken = sessionStorage.getItem(verteilTokenKey);
    const storedExpiry = sessionStorage.getItem(verteilTokenExpiryKey);
    if (storedToken && storedExpiry) {
      const expiry = parseInt(storedExpiry, 10);
      if (expiry > Date.now()) {
        const parsedToken = JSON.parse(storedToken) as VerteilToken;
        // Update in-memory cache as well
        verteilToken = parsedToken;
        verteilTokenExpiry = expiry;
        return parsedToken;
      }
    }
  }

  // Fetch new token
  const newToken = await fetchVerteilToken();
  const newExpiry = Date.now() + (newToken.expires_in - 60) * 1000; // Calculate expiry (60s buffer)

  // Update in-memory cache
  verteilToken = newToken;
  verteilTokenExpiry = newExpiry; 
  // Update sessionStorage (only if in browser)
  if (typeof window !== 'undefined') {
    sessionStorage.setItem(verteilTokenKey, JSON.stringify(newToken));
    sessionStorage.setItem(verteilTokenExpiryKey, newExpiry.toString());
  }

  return newToken;
}

/**
 * Call Verteil AirShopping API with all required headers.
 * @param payload The AirShopping request payload
 * @returns API response
 */
export async function callVerteilAirShopping(payload: any) {
  const token = await getVerteilToken();
  const url = 'https://api.stage.verteil.com/entrygate/rest/request:airShopping';
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token.access_token}`,
    'User-Agent': 'Chrome/1.0',
    'Accept-Encoding': 'gzip',
    'ThirdpartyId': 'LHG',
    'OfficeId': 'OFF3746', // Capital O per Swagger
    'service': 'AirShopping', // lowercase key, capitalized value per Swagger
    // 'resource': '...', // Only include if needed for special flows
  };
  try {
    const response = await axios.post(url, payload, { headers });
    return response.data;
  } catch (error) {
    throw error;
  }
}

// --- Helper Functions (Revised - Part 1) ---

/**
 * Finds an item in a DataList array by its key.
 * Adds more robust logging.
 */
const findInDataList = (key: string, list: any[], idField: string): any | null => {
  if (!list || !Array.isArray(list)) {
    return null;
  }
  const item = list.find((item) => item && item[idField] === key);
  if (!item) {
    return null;
  }
  return item;
};

/**
 * Extracts segment details from FlightSegmentList based on SegmentKey.
 * Assumes structure based on common patterns. Adds robust checks.
 */
const getSegmentDetails = (segmentKey: string, dataLists: any): FlightSegmentDetails | null => {
  if (!dataLists?.FlightSegmentList?.FlightSegment) {
    return null;
  }
  
  try {
      const segment = dataLists.FlightSegmentList.FlightSegment.find((seg: any) => seg && seg.SegmentKey === segmentKey);
      if (!segment) {
        return null;
      }

  // Extract details, providing fallbacks
  const departureAirport = segment.Departure?.AirportCode;
  const departureDateTime = segment.Departure?.Date;
  const arrivalAirport = segment.Arrival?.AirportCode;
  const arrivalDateTime = segment.Arrival?.Date;

  // Use MarketingCarrierInfo based on api-response.md structure
  const marketingCarrier = segment.MarketingCarrierInfo; // Corrected path
  const airlineCode = marketingCarrier?.CarrierDesigCode; // Using CarrierDesigCode
  const flightNumber = marketingCarrier?.MarketingCarrierFlightNumber?._ || '0000'; // Using MarketingCarrierFlightNumber

  // Attempt to find airline name from AirlineList
  const airlineName = findInDataList(airlineCode, dataLists?.AirlineList, "AirlineID")?.Name?._ || 'Unknown Airline';

  const airlineInfo = {
    code: airlineCode,
    name: airlineName,
    flightNumber: flightNumber, // Added flight number
  };

  const duration = segment.FlightDetail?.FlightDuration?._ || 'N/A'; // Example path, adjust if needed

  // Ensure the returned object matches FlightSegmentDetails interface
  const segmentDetails: FlightSegmentDetails = {
    id: segmentKey,
    departure: {
      airport: departureAirport,
      datetime: departureDateTime,
    },
    arrival: {
      airport: arrivalAirport,
      datetime: arrivalDateTime,
    },
    airline: airlineInfo, // airlineInfo now includes flightNumber
    duration: duration,
  };

  return segmentDetails;
} catch (error) {
  return null;
}
};

/**
 * Resolves flight details (segments, duration) using references found within an offer.
 * Handles multiple possible reference structures in the API response.
 */
const resolveFlightDetailsFromRefs = (
    references: any,  // Can be any structure that might contain references
    dataLists: any   // The DataLists section containing all flight data
): FlightDetailsResult | null => {

    let segmentKeys: string[] = [];
    let journeyDuration = 'N/A';
    let flightKey: string | null = null;

    // Multiple possible reference structures need different handling
    
    // APPROACH 1: If references is an array of ref objects with FlightKey or SegmentKey
    if (Array.isArray(references)) {

        
        // First try to find direct flight references
        for (const ref of references) {
            // Check different possible formats of flight references
            if (ref.FlightKey) {
                flightKey = ref.FlightKey;

                break;
            } else if (ref.value && ref.type === 'Flight') {
                flightKey = ref.value;

                break;
            } else if (ref.ref && ref.refType === 'Flight') {
                flightKey = ref.ref;

                break;
            }
        }
        
        // If no direct flight keys, check for segment references
        if (!flightKey && segmentKeys.length === 0) {
            for (const ref of references) {
                if (ref.SegmentKey) {
                    segmentKeys.push(ref.SegmentKey);

                } else if (ref.value && ref.type === 'Segment') {
                    segmentKeys.push(ref.value);

                } else if (ref.ref && ref.refType === 'Segment') {
                    segmentKeys.push(ref.ref);

                }
            }
        }
    }
    
    // APPROACH 2: Try standard path with OriginDestinationReferences
    if (!flightKey && segmentKeys.length === 0 && references?.OriginDestinationReferences) {
        const odRef = references.OriginDestinationReferences[0];

        
        if (odRef) {
            const originDestination = findInDataList(odRef, dataLists?.OriginDestinationList, "OriginDestinationKey");
            if (originDestination) {
                // Extract flight references
                const flightRefs = originDestination.FlightReferences?._?.split(' ') || [];

                
                if (flightRefs.length > 0) {
                    journeyDuration = originDestination.FlightDuration?.Value || 'N/A';
                    flightKey = flightRefs[0]; // Use first flight reference
                } else if (originDestination.SegmentReferences?._) {
                    // Direct segment references in OD
                    segmentKeys = originDestination.SegmentReferences._.split(' ') || [];

                }
            }
        }
    }
    
    // APPROACH 3: Try special reference structures like PricedOffer.Associations
    if (!flightKey && segmentKeys.length === 0 && references?.PricedOffer?.Associations) {

        
        // The associations array might contain different structures
        if (Array.isArray(references.PricedOffer.Associations)) {
            for (const association of references.PricedOffer.Associations) {
                // Check for ApplicableFlight property
                if (association.ApplicableFlight) {

                    const flight = association.ApplicableFlight;
                    
                    // Check for FlightSegmentReference array (this seems to be the correct path based on logs)
                    if (flight.FlightSegmentReference && Array.isArray(flight.FlightSegmentReference)) {
                        // Extract segment refs from each FlightSegmentReference object
                        for (const segRef of flight.FlightSegmentReference) {
                            if (segRef.ref) {
                                segmentKeys.push(segRef.ref);

                            }
                        }
                        
                        // Also store the flight reference if available
                        if (flight.FlightReferences?.value && Array.isArray(flight.FlightReferences.value)) {
                            flightKey = flight.FlightReferences.value[0];
                        }
                        
                        // If we found segment keys, we can break out of the loop
                        if (segmentKeys.length > 0) {
                            break;
                        }
                    }
                    // Fallback to other formats
                    else if (flight.FlightKey) {
                        flightKey = flight.FlightKey;
                        break;
                    } else if (flight.SegmentReferences?._) {
                        segmentKeys = flight.SegmentReferences._.split(' ') || [];
                        break;
                    }
                }
                
                // Check for PriceClass, which might contain ApplicableFlight
                if (association.PriceClass && association.PriceClass.refs) {
                    // Direct refs in PriceClass
                    const priceClassRefs = association.PriceClass.refs;
                    if (Array.isArray(priceClassRefs)) {
                        for (const ref of priceClassRefs) {
                            // Check for FlightRef type
                            if (ref.type === 'Flight' && ref.value) {
                                flightKey = ref.value;
                                break;
                            } 
                            // Check for direct SegmentRef
                            else if (ref.type === 'Segment' && ref.value) {
                                segmentKeys.push(ref.value);
                            }
                        }
                    }
                }
                
                // Check if we already found what we needed
                if (flightKey || segmentKeys.length > 0) break;
            }
        } 
        // Handle if Associations is a direct object
        else if (references.PricedOffer.Associations.ApplicableFlight) {
            const flight = references.PricedOffer.Associations.ApplicableFlight;
            
            if (flight.FlightKey) {
                flightKey = flight.FlightKey;
            } else if (flight.SegmentReferences?._) {
                segmentKeys = flight.SegmentReferences._.split(' ') || [];
            }
        }
    }

    // If we found a flight key but no segment keys, try to get the segments from the flight
    if (flightKey && segmentKeys.length === 0) {
        const flight = findInDataList(flightKey, dataLists?.FlightList, "FlightKey");
        if (flight) {
            // Extract segment references from the flight
            const segRefs = flight.SegmentReferences?._?.split(' ') || [];
            if (segRefs.length > 0) {
                segmentKeys = segRefs;
                
                // Extract journey duration if not already set
                if (journeyDuration === 'N/A') {
                    journeyDuration = flight.Journey?.Time?._ || flight.Journey?.Duration || 'N/A';
                }
            } else {
            }
        } else {
        }
    }

    // Check if we have any segment keys at this point
    if (segmentKeys.length === 0) {
        return null; // Cannot resolve details
    }

    // --- Process Derived Segment Keys ---
    // Remove duplicate segment keys if any were added from multiple paths (unlikely but possible)
    const uniqueSegmentKeys = [...new Set(segmentKeys)];

    const segments = uniqueSegmentKeys
        .map(key => getSegmentDetails(key, dataLists))
        .filter((segment): segment is FlightSegmentDetails => segment !== null); // Type guard filters nulls

    // If NO segments could be resolved at all, consider it a failure
    if (segments.length === 0) {
        return null;
    }

    // Return the resolved segments and the journey duration found
    return {
        segments: segments,
        // Duration might need parsing later (e.g., 'PT2H30M' -> '2h 30m')
        duration: journeyDuration,
    };
}; // End resolveFlightDetailsFromRefs

// --- Main Data Optimization Function --- //

/**
 * Optimize flight data to reduce memory usage
 * @param rawData - The raw API response data
 * @returns The optimized flight data
 */
/**
 * Process flight data from Verteil API response
 * @param rawData The raw API response data from Verteil
 * @returns Processed flight data with flights array and metadata
 */
export function optimizeFlightData(rawData: any): { flights: FlightOffer[]; meta: Record<string, any> } {
    if (!rawData || !rawData.OffersGroup || !rawData.OffersGroup.AirlineOffers || 
        !rawData.OffersGroup.AirlineOffers[0] || !rawData.OffersGroup.AirlineOffers[0].AirlineOffer) {
        return {
            flights: [],
            meta: {
                total: 0,
                currency: 'USD',
                isFallbackData: true,
                error: "Missing essential offer data in API response."
            }
        };
    }
    
    const dataLists = rawData.DataLists;
    if (!dataLists) {
        return {
            flights: [], 
            meta: {
                total: 0,
                currency: 'USD',
                isFallbackData: true,
                error: "Missing DataLists in API response."
            }
        };
    }
    
    // Extract the AirlineOffer array
    const airlineOffers = rawData.OffersGroup.AirlineOffers[0].AirlineOffer;
    
    if (!Array.isArray(airlineOffers) || airlineOffers.length === 0) {
        return {
            flights: [],
            meta: {
                total: 0,
                currency: 'USD',
                isFallbackData: false,
                message: "No flight offers found."
            }
        };
    }
    
    // Pre-process lists into maps for faster lookups
    const flightSegmentList = dataLists.FlightSegmentList?.FlightSegment || [];
    const flightSegmentMap = new Map(flightSegmentList.map((seg: any) => [seg.SegmentKey, seg]));
    
    // Also map flight references
    const flightList = dataLists.FlightList?.Flight || [];
    const flightMap = new Map(flightList.map((flight: any) => [flight.FlightKey, flight]));

    // Map baggage allowances for quick lookup
    const carryOnAllowanceList = dataLists.CarryOnAllowanceList?.CarryOnAllowance || [];
    const carryOnMap = new Map(carryOnAllowanceList.map((allowance: any) => [allowance.ListKey, allowance]));
    
    // Map checked baggage allowances
    const checkedBagAllowanceList = dataLists.CheckedBagAllowanceList?.CheckedBagAllowance || [];
    const checkedBagMap = new Map(checkedBagAllowanceList.map((allowance: any) => [allowance.ListKey, allowance]));
    
    // Map fare information for quick lookup
    const fareList = dataLists.FareList?.FareGroup || [];
    const fareMap = new Map(fareList.map((fare: any) => [fare.ListKey, fare]));
    
    // Create a map of fare rules if available
    const fareRulesList = dataLists.PenaltyList?.Penalty || [];
    const fareRulesMap = new Map(fareRulesList.map((rule: any) => [rule?.PenaltyID, rule]));
    
    // Get currency from first offer or use default
    let currency = 'USD';
    if (airlineOffers[0]?.TotalPrice?.SimpleCurrencyPrice?.Code) {
        currency = airlineOffers[0].TotalPrice.SimpleCurrencyPrice.Code;
    }
    
    // Process each offer into a structured flight offer
    const flights = airlineOffers.map((offer: any) => {
        // Extract offer ID and price
        const offerId = offer.OfferID?.value || `offer-${Math.random().toString(36).substr(2, 9)}`;
        const price = offer.TotalPrice?.SimpleCurrencyPrice?.value || 0;
        const currencyCode = offer.TotalPrice?.SimpleCurrencyPrice?.Code || currency;
        
        // Find associated flight segment references
        let segmentRefs: string[] = [];
        let flightKey = '';
        
        // Get segment references from PricedOffer.Associations
        if (offer.PricedOffer?.Associations) {
            const associations = Array.isArray(offer.PricedOffer.Associations) 
                ? offer.PricedOffer.Associations 
                : [offer.PricedOffer.Associations];
            
            for (const assoc of associations) {
                if (assoc.ApplicableFlight?.FlightReferences?.value) {
                    const flightRefs = Array.isArray(assoc.ApplicableFlight.FlightReferences.value)
                        ? assoc.ApplicableFlight.FlightReferences.value
                        : [assoc.ApplicableFlight.FlightReferences.value];
                    
                    flightKey = flightRefs[0]; // Take first flight reference
                }
                
                if (assoc.ApplicableFlight?.FlightSegmentReference) {
                    const refs = Array.isArray(assoc.ApplicableFlight.FlightSegmentReference)
                        ? assoc.ApplicableFlight.FlightSegmentReference
                        : [assoc.ApplicableFlight.FlightSegmentReference];
                    
                    segmentRefs = [...segmentRefs, ...refs.map((ref: any) => ref.ref || ref)];
                }
            }
        }
        
        // Try from flight if no segment refs found
        if (flightKey && segmentRefs.length === 0) {
            const flight = flightMap.get(flightKey) || {};
            // Use type assertion to safely access possibly undefined properties
            const flightObj = flight as Record<string, any>; 
            if (flightObj?.SegmentReferences?.value) {
                segmentRefs = Array.isArray(flightObj.SegmentReferences.value)
                    ? flightObj.SegmentReferences.value
                    : [flightObj.SegmentReferences.value];
            }
        }
        
        // Also check direct refs if available
        if (offer.refs && Array.isArray(offer.refs) && segmentRefs.length === 0) {
            segmentRefs = offer.refs.map((ref: any) => ref.ref || ref).filter(Boolean);
        }
        
        // Remove duplicates
        segmentRefs = [...new Set(segmentRefs)];
        
        if (segmentRefs.length === 0) {
            return null; // Skip this offer
        }
        
        // Get actual segments
        const segments = segmentRefs
            .map((ref: string) => flightSegmentMap.get(ref))
            .filter(Boolean); // Filter out nulls
            
        if (segments.length === 0) {
            return null; // Skip if no segments found
        }
        
        // Use type assertions to help TypeScript understand these are valid objects
        const firstSegment = segments[0] as Record<string, any>;
        const lastSegment = segments[segments.length - 1] as Record<string, any>;
        const stops = segments.length - 1;
        
        // Get stop details
        const stopDetails: string[] = [];
        if (stops > 0) {
            for (let i = 0; i < segments.length - 1; i++) {
                // Use type assertion to safely access properties
                const segment = segments[i] as Record<string, any>;
                const connectingAirport = segment.Arrival?.AirportCode?.value || segment.Arrival?.AirportCode;
                if (connectingAirport) {
                    stopDetails.push(connectingAirport);
                }
            }
        }
        
        // Calculate duration
        let totalDuration = "N/A";
        let totalMinutes = 0;
        
        segments.forEach((seg: any) => {
            const durationStr = seg?.FlightDetail?.FlightDuration?.Value;
            if (durationStr) {
                totalMinutes += parseISODuration(durationStr);
            }
        });
        
        if (totalMinutes > 0) {
            const hours = Math.floor(totalMinutes / 60);
            const minutes = totalMinutes % 60;
            totalDuration = `${hours}h ${minutes}m`;
        }
        
        // Try to get more accurate duration from flight
        if (flightKey) {
            const flight = flightMap.get(flightKey) || {};
            // Use type assertion to safely access possibly undefined properties
            const flightObj = flight as Record<string, any>;
            if (flightObj?.Journey?.Time && typeof flightObj.Journey.Time === 'string') {
                totalDuration = flightObj.Journey.Time.replace('PT', '').replace('H', 'h ').replace('M', 'm');
            }
        }
        
        // Extract airline info
        const airlineCode = firstSegment.MarketingCarrier?.AirlineID?.value || firstSegment.MarketingCarrier?.AirlineID || 'XX';
        const airlineName = firstSegment.MarketingCarrier?.Name || `Airline ${airlineCode}`;
        const flightNumber = firstSegment.MarketingCarrier?.FlightNumber?.value || firstSegment.MarketingCarrier?.FlightNumber || 'N/A';
        
        const airlineInfo: AirlineDetails = {
            code: airlineCode,
            name: airlineName,
            logo: `/airlines/${airlineCode.toLowerCase()}.png`,
            flightNumber: flightNumber
        };
        
        // Get departure info
        const departureAirportCode = firstSegment.Departure?.AirportCode?.value || firstSegment.Departure?.AirportCode;
        const departureTime = firstSegment.Departure?.Time || '00:00';
        const departureDate = firstSegment.Departure?.Date || 'N/A';
        const departureTerminal = firstSegment.Departure?.Terminal?.Name;
        const departureAirportName = firstSegment.Departure?.AirportName;
        
        // Format departure to match FlightOffer interface
        const departureInfo = {
            airport: departureAirportCode,
            datetime: `${departureDate}T${departureTime}`,
            terminal: departureTerminal,
            airportName: departureAirportName
        };
        
        // Get arrival info
        const arrivalAirportCode = lastSegment.Arrival?.AirportCode?.value || lastSegment.Arrival?.AirportCode;
        const arrivalTime = lastSegment.Arrival?.Time || '00:00';
        const arrivalDate = lastSegment.Arrival?.Date || 'N/A';
        const arrivalTerminal = lastSegment.Arrival?.Terminal?.Name;
        const arrivalAirportName = lastSegment.Arrival?.AirportName;
        
        // Format arrival to match FlightOffer interface
        const arrivalInfo = {
            airport: arrivalAirportCode,
            datetime: `${arrivalDate}T${arrivalTime}`,
            terminal: arrivalTerminal,
            airportName: arrivalAirportName
        };

        // Get aircraft details from the first segment
        const aircraftInfo: AircraftDetails | undefined = firstSegment.Equipment ? {
            code: firstSegment.Equipment?.AircraftCode?.value || 'N/A',
            name: firstSegment.Equipment?.Name
        } : undefined;

        // Get operating airline details (for codeshare flights)
        let operatingAirlineInfo: AirlineDetails | undefined;
        
        const operatingCarrier = firstSegment.OperatingCarrier;
        if (operatingCarrier && 
            operatingCarrier.AirlineID?.value && 
            operatingCarrier.AirlineID.value !== airlineCode) {
            
            operatingAirlineInfo = {
                code: operatingCarrier.AirlineID.value,
                name: operatingCarrier.Name || `Airline ${operatingCarrier.AirlineID.value}`,
                flightNumber: operatingCarrier.FlightNumber?.value || flightNumber
            };
        }

        // Process detailed segment information
        const segmentDetails: FlightSegmentDetails[] = segments.map((segment: any) => {
            const segmentObj = segment as Record<string, any>;
            
            // Extract segment airline info
            const segAirlineCode = segmentObj.MarketingCarrier?.AirlineID?.value || segmentObj.MarketingCarrier?.AirlineID || 'XX';
            const segAirlineName = segmentObj.MarketingCarrier?.Name || `Airline ${segAirlineCode}`;
            const segFlightNumber = segmentObj.MarketingCarrier?.FlightNumber?.value || segmentObj.MarketingCarrier?.FlightNumber || 'N/A';
            
            // Extract segment aircraft info
            const segAircraftInfo = segmentObj.Equipment ? {
                code: segmentObj.Equipment?.AircraftCode?.value || 'N/A',
                name: segmentObj.Equipment?.Name
            } : undefined;
            
            // Extract segment operating airline info
            let segOperatingAirlineInfo;
            const segOperatingCarrier = segmentObj.OperatingCarrier;
            
            if (segOperatingCarrier && 
                segOperatingCarrier.AirlineID?.value && 
                segOperatingCarrier.AirlineID.value !== segAirlineCode) {
                
                segOperatingAirlineInfo = {
                    code: segOperatingCarrier.AirlineID.value,
                    name: segOperatingCarrier.Name || `Airline ${segOperatingCarrier.AirlineID.value}`,
                    flightNumber: segOperatingCarrier.FlightNumber?.value || segFlightNumber
                };
            }
            
            // Extract segment departure info
            const segDepartureAirportCode = segmentObj.Departure?.AirportCode?.value || segmentObj.Departure?.AirportCode;
            const segDepartureTime = segmentObj.Departure?.Time || '00:00';
            const segDepartureDate = segmentObj.Departure?.Date || 'N/A';
            const segDepartureTerminal = segmentObj.Departure?.Terminal?.Name;
            const segDepartureAirportName = segmentObj.Departure?.AirportName;
            
            // Extract segment arrival info
            const segArrivalAirportCode = segmentObj.Arrival?.AirportCode?.value || segmentObj.Arrival?.AirportCode;
            const segArrivalTime = segmentObj.Arrival?.Time || '00:00';
            const segArrivalDate = segmentObj.Arrival?.Date || 'N/A';
            const segArrivalTerminal = segmentObj.Arrival?.Terminal?.Name;
            const segArrivalAirportName = segmentObj.Arrival?.AirportName;
            
            // Extract segment duration
            let segDuration = "N/A";
            const durationStr = segmentObj.FlightDetail?.FlightDuration?.Value;
            if (durationStr) {
                const durationMinutes = parseISODuration(durationStr);
                const hours = Math.floor(durationMinutes / 60);
                const minutes = durationMinutes % 60;
                segDuration = `${hours}h ${minutes}m`;
            }
            
            return {
                id: segmentObj.SegmentKey || `segment-${Math.random().toString(36).substr(2, 9)}`,
                departure: {
                    airport: segDepartureAirportCode,
                    datetime: `${segDepartureDate}T${segDepartureTime}`,
                    terminal: segDepartureTerminal,
                    airportName: segDepartureAirportName
                },
                arrival: {
                    airport: segArrivalAirportCode,
                    datetime: `${segArrivalDate}T${segArrivalTime}`,
                    terminal: segArrivalTerminal,
                    airportName: segArrivalAirportName
                },
                airline: {
                    code: segAirlineCode,
                    name: segAirlineName,
                    flightNumber: segFlightNumber
                },
                operatingAirline: segOperatingAirlineInfo,
                aircraft: segAircraftInfo,
                duration: segDuration
            };
        });

        // Extract baggage information from segments
        const baggage: BaggageAllowance = {
            carryOn: { description: 'Standard carry-on allowance' } // Default
        };
        
        // Try to find baggage details from the first segment
        if (firstSegment && firstSegment.BagDetailAssociation) {
            // Handle carry-on references
            if (firstSegment.BagDetailAssociation.CarryOnReferences) {
                const carryOnRefs = Array.isArray(firstSegment.BagDetailAssociation.CarryOnReferences)
                    ? firstSegment.BagDetailAssociation.CarryOnReferences
                    : [firstSegment.BagDetailAssociation.CarryOnReferences];
                
                if (carryOnRefs.length > 0) {
                    // Use the first carry-on reference
                    const carryOnRef = carryOnRefs[0];
                    const carryOnAllowance = carryOnMap.get(carryOnRef);
                    
                    if (carryOnAllowance) {
                        // Use type assertion to handle the object properties safely
                        const allowance = carryOnAllowance as Record<string, any>;
                        // Extract weight information
                        const weightInfo = allowance.WeightAllowance?.MaximumWeight?.[0];
                        const description = allowance.AllowanceDescription?.Descriptions?.Description?.[0]?.Text?.value;
                        
                        // Extract any dimension information if available
                        // This is a placeholder as dimensions may not be directly available in the API
                        const carryOnBaggage: CarryOnBaggage = {
                            weight: weightInfo ? {
                                value: parseInt(weightInfo.Value, 10) || 6, // Default to 6kg if parsing fails
                                unit: weightInfo.UOM || 'Kilogram'
                            } : undefined,
                            description: description || 'Carry-on baggage allowance',
                            isPersonalItemIncluded: description?.toLowerCase().includes('personal item') || false,
                            // Add dimensions based on standard carry-on sizes if not explicitly provided
                            dimensions: {
                                totalDimensions: {
                                    value: 115, // Standard carry-on dimension sum (55+40+20)
                                    unit: 'cm'
                                }
                            },
                            // Extract quantity of bags allowed
                            quantity: 1, // Default to 1 carry-on bag
                            // Check for personal item dimensions and weight
                            personalItemDimensions: description?.toLowerCase().includes('personal item') ? {
                                length: { value: 40, unit: 'cm' },
                                width: { value: 30, unit: 'cm' },
                                height: { value: 15, unit: 'cm' }
                            } : undefined,
                            personalItemWeight: description?.toLowerCase().includes('personal item') ? {
                                value: 2,
                                unit: 'Kilogram'
                            } : undefined,
                            // Extract any specific restrictions
                            restrictions: description?.includes('restriction') ? 
                                [description.substring(description.indexOf('restriction'))] : 
                                undefined
                        };
                        
                        baggage.carryOn = carryOnBaggage;
                    }
                }
            }
            
            // Handle checked baggage references
            if (firstSegment.BagDetailAssociation.CheckedBagReferences) {
                const checkedBagRefs = Array.isArray(firstSegment.BagDetailAssociation.CheckedBagReferences)
                    ? firstSegment.BagDetailAssociation.CheckedBagReferences
                    : [firstSegment.BagDetailAssociation.CheckedBagReferences];
                
                if (checkedBagRefs.length > 0) {
                    // Use the first checked baggage reference
                    const checkedBagRef = checkedBagRefs[0];
                    const checkedBagAllowance = checkedBagMap.get(checkedBagRef);
                    
                    if (checkedBagAllowance) {
                        // Use type assertion to handle the object properties safely
                        const allowance = checkedBagAllowance as Record<string, any>;
                        // Extract weight or piece information
                        const weightInfo = allowance.WeightAllowance?.MaximumWeight?.[0];
                        const pieceInfo = allowance.PieceAllowance?.[0];
                        const description = allowance.AllowanceDescription?.Descriptions?.Description?.[0]?.Text?.value;
                        
                        // Parse dimensions from description if available
                        // Example: "UPTO50LB 23KG AND62LI 158LCM"
                        let dimensions;
                        if (description) {
                            const dimensionMatch = description.match(/([0-9]+)\s*LCM|([0-9]+)\s*CM/i);
                            if (dimensionMatch) {
                                const dimensionValue = parseInt(dimensionMatch[1] || dimensionMatch[2], 10);
                                dimensions = {
                                    totalDimensions: {
                                        value: dimensionValue,
                                        unit: 'cm'
                                    }
                                };
                            }
                        }
                        
                        // Determine if policy is weight-based, piece-based, or both
                        let policyType: 'WEIGHT_BASED' | 'PIECE_BASED' | 'BOTH' = 'WEIGHT_BASED';
                        if (weightInfo && pieceInfo) {
                            policyType = 'BOTH';
                        } else if (pieceInfo) {
                            policyType = 'PIECE_BASED';
                        }
                        
                        // Create the checked baggage object
                        const checkedBaggage: CheckedBaggage = {
                            weight: weightInfo ? {
                                value: parseInt(weightInfo.Value, 10) || 20, // Default
                                unit: weightInfo.UOM || 'Kilogram'
                            } : undefined,
                            pieces: pieceInfo?.TotalQuantity,
                            description: description || 'Checked baggage allowance',
                            dimensions: dimensions,
                            policyType: policyType,
                            // Add extra baggage fees information if available
                            extraBaggageFees: {
                                amount: 50, // Default fee 
                                currency: 'USD',
                                perPiece: true,
                                description: 'Fee for each additional checked bag'
                            },
                            // Add free baggage allowance
                            freeBaggageAllowance: pieceInfo?.TotalQuantity || 
                                (pieceInfo ? parseInt(pieceInfo.TotalQuantity, 10) : 1)
                        };
                        
                        baggage.checkedBaggage = checkedBaggage;
                        
                        // Add overweight and oversize charges information
                        if (weightInfo) {
                            baggage.overweightCharges = {
                                amount: 100,
                                currency: 'USD',
                                perKgOrLb: 'per bag',
                                threshold: parseInt(weightInfo.Value, 10) || 23,
                                description: 'Fee for bags exceeding weight allowance'
                            };
                        }
                        
                        baggage.oversizeCharges = {
                            amount: 100,
                            currency: 'USD',
                            description: 'Fee for bags exceeding dimension allowance'
                        };
                        
                        // Add prepaid baggage discount if available
                        baggage.prepaidBaggageDiscount = 15; // 15% discount when prepaid
                        
                        // Check for special items in the description
                        if (description) {
                            const specialItems: SpecialItem[] = [];
                            
                            // Check for sporting equipment
                            if (description.match(/SPORT|EQUIPMENT|GOLF|SKI|SURFBOARD/i)) {
                                specialItems.push({
                                    type: 'SPORTING_EQUIPMENT',
                                    description: 'Sporting equipment may be included in baggage allowance',
                                    allowed: true,
                                    extraFee: !description.toLowerCase().includes('free')
                                });
                            }
                            
                            // Check for firearms
                            if (description.match(/FIREARM|WEAPON/i)) {
                                specialItems.push({
                                    type: 'FIREARMS',
                                    description: 'Firearms must be declared and properly packed',
                                    allowed: true,
                                    extraFee: true
                                });
                            }
                            
                            if (specialItems.length > 0) {
                                baggage.specialItems = specialItems;
                            }
                        }
                    }
                }
            }
        }
        
        // Extract fare information
        let fareDetails: FareDetails | undefined;
        
        // Look for fare reference in FareDetail of the offer or segments
        let fareKey = '';
        
        // Check for fare references in the offer structure
        if (offer.PricedOffer?.OfferPrice?.[0]?.FareDetail?.FareComponent) {
            const fareComponents = Array.isArray(offer.PricedOffer.OfferPrice[0].FareDetail.FareComponent) 
                ? offer.PricedOffer.OfferPrice[0].FareDetail.FareComponent 
                : [offer.PricedOffer.OfferPrice[0].FareDetail.FareComponent];
                
            if (fareComponents.length > 0 && fareComponents[0].refs) {
                const fareRefs = Array.isArray(fareComponents[0].refs) 
                    ? fareComponents[0].refs 
                    : [fareComponents[0].refs];
                
                fareKey = fareRefs[0];
            }
        }
        
        // If we found a fare reference, look it up in the fare map
        if (fareKey && fareMap.has(fareKey)) {
            const fare = fareMap.get(fareKey) as Record<string, any>;
            const fareBasisCode = fare.FareBasisCode?.Code || '';
            const fareType = fare.Fare?.FareDetail?.Remarks?.Remark?.[0]?.value || '';
            
            // Look for fare rules/penalties
            const fareRules: FareRules = {};
            
            // Extract detailed penalty information
            const extractPenalties = (penaltyList: any[]) => {
                if (!Array.isArray(penaltyList)) return;
                
                penaltyList.forEach(penalty => {
                    const penaltyObj = penalty as Record<string, any>;
                    const objectKey = penaltyObj.ObjectKey || '';
                    const details = penaltyObj.Details?.Detail || [];
                    const changeAllowed = penaltyObj.ChangeAllowedInd === true;
                    const changeFee = penaltyObj.ChangeFeeInd === true;
                    
                    // Skip if no details
                    if (!Array.isArray(details)) return;
                    
                    details.forEach(detail => {
                        const detailObj = detail as Record<string, any>;
                        const penaltyType = detailObj.Type || '';
                        const application = detailObj.Application?.Code || '';
                        const amounts = detailObj.Amounts?.Amount || [];
                        
                        // Extract fee amount (usually take the MAX value if available)
                        let feeAmount = 0;
                        let feeCurrency = 'USD';
                        
                        if (Array.isArray(amounts) && amounts.length > 0) {
                            // Find the MAX amount if available
                            const maxAmount = amounts.find(amt => 
                                (amt as Record<string, any>).AmountApplication === 'MAX'
                            ) as Record<string, any> | undefined;
                            
                            if (maxAmount) {
                                feeAmount = maxAmount.CurrencyAmountValue?.value || 0;
                                feeCurrency = maxAmount.CurrencyAmountValue?.Code || 'USD';
                            } else if (amounts.length > 0) {
                                // If no MAX, take the first one
                                const firstAmount = amounts[0] as Record<string, any>;
                                feeAmount = firstAmount.CurrencyAmountValue?.value || 0;
                                feeCurrency = firstAmount.CurrencyAmountValue?.Code || 'USD';
                            }
                        }
                        
                        // Map penalty types to our structure
                        if (penaltyType.toLowerCase().includes('change')) {
                            if (application === '2' || objectKey.includes('BEFORE_DEPARTURE')) {
                                fareRules.changeBeforeDeparture = {
                                    allowed: changeAllowed,
                                    fee: feeAmount,
                                    currency: feeCurrency
                                };
                            } else if (application === '3' || objectKey.includes('AFTER_DEPARTURE')) {
                                fareRules.changeAfterDeparture = {
                                    allowed: changeAllowed,
                                    fee: feeAmount,
                                    currency: feeCurrency
                                };
                            } else if (penaltyType.toLowerCase().includes('noshow') || objectKey.includes('NO_SHOW')) {
                                fareRules.changeNoShow = {
                                    allowed: changeAllowed,
                                    fee: feeAmount,
                                    currency: feeCurrency
                                };
                            }
                            
                            // Set general changeFee property based on any change fee
                            if (feeAmount > 0) {
                                fareRules.changeFee = true;
                            }
                        } else if (penaltyType.toLowerCase().includes('cancel') || penaltyType.toLowerCase().includes('refund')) {
                            if (application === '2' || objectKey.includes('BEFORE_DEPARTURE')) {
                                fareRules.cancelBeforeDeparture = {
                                    allowed: true, // Cancellation is allowed with a fee
                                    fee: feeAmount,
                                    currency: feeCurrency
                                };
                            } else if (application === '3' || objectKey.includes('AFTER_DEPARTURE')) {
                                fareRules.cancelAfterDeparture = {
                                    allowed: true,
                                    fee: feeAmount,
                                    currency: feeCurrency
                                };
                            } else if (penaltyType.toLowerCase().includes('noshow') || objectKey.includes('NO_SHOW')) {
                                fareRules.cancelNoShow = {
                                    allowed: true,
                                    fee: feeAmount,
                                    currency: feeCurrency
                                };
                            }
                            
                            // Set refundable property based on if cancellation is allowed
                            fareRules.refundable = feeAmount === 0 ? true : feeAmount < 9999;
                        }
                    });
                });
            };
            
            // Extract price class information
            const extractPriceClassInfo = (priceClassList: any[], fareKeyToMatch: string) => {
                if (!Array.isArray(priceClassList) || !fareKeyToMatch) return null;
                
                // First try to find an exact match by ObjectKey
                let matchedPriceClass = priceClassList.find(priceClass => {
                    const priceClassObj = priceClass as Record<string, any>;
                    return priceClassObj.ObjectKey === fareKeyToMatch;
                });
                
                // If no exact match, try to find a partial match
                if (!matchedPriceClass) {
                    // Extract airline code from fare key (usually first 2-3 characters before the dash)
                    const airlineCodeMatch = fareKeyToMatch.match(/^([A-Z]{2,3})-/);
                    const airlineCode = airlineCodeMatch ? airlineCodeMatch[1] : '';
                    
                    if (airlineCode) {
                        matchedPriceClass = priceClassList.find(priceClass => {
                            const priceClassObj = priceClass as Record<string, any>;
                            return priceClassObj.ObjectKey && 
                                   priceClassObj.ObjectKey.startsWith(airlineCode + '-');
                        });
                    }
                }
                
                if (!matchedPriceClass) {
                    return null;
                }
                
                const priceClassObj = matchedPriceClass as Record<string, any>;
                const additionalServices: Record<string, string> = {};
                
                // Process descriptions
                const descriptions = priceClassObj.Descriptions?.Description || [];
                if (Array.isArray(descriptions)) {
                    descriptions.forEach(desc => {
                        const descObj = desc as Record<string, any>;
                        const text = descObj.Text?.value || '';
                        
                        if (text) {
                            // Parse description text which typically follows a KEY-VALUE format
                            const parts = text.split('-');
                            if (parts.length === 2) {
                                const key = parts[0].trim();
                                const value = parts[1].trim();
                                
                                // Map to our structure based on key
                                if (key.includes('CANCEL_BEFOREDEPARTURE')) {
                                    // Add to fareRules if not already set
                                    if (!fareRules.cancelBeforeDeparture) {
                                        const feeMatch = value.match(/([A-Z]{3})\s+(\d+)/);
                                        if (feeMatch) {
                                            fareRules.cancelBeforeDeparture = {
                                                allowed: true,
                                                fee: parseInt(feeMatch[2], 10) || 0,
                                                currency: feeMatch[1] || 'USD'
                                            };
                                        }
                                    }
                                } else if (key.includes('CANCEL_NOSHOWFIRST')) {
                                    if (!fareRules.cancelNoShow) {
                                        const feeMatch = value.match(/([A-Z]{3})\s+(\d+)/);
                                        if (feeMatch) {
                                            fareRules.cancelNoShow = {
                                                allowed: true,
                                                fee: parseInt(feeMatch[2], 10) || 0,
                                                currency: feeMatch[1] || 'USD'
                                            };
                                        }
                                    }
                                } else if (key.includes('CHANGE_BEFOREDEPARTURE')) {
                                    if (!fareRules.changeBeforeDeparture) {
                                        const feeMatch = value.match(/([A-Z]{3})\s+(\d+)/);
                                        if (feeMatch) {
                                            fareRules.changeBeforeDeparture = {
                                                allowed: true,
                                                fee: parseInt(feeMatch[2], 10) || 0,
                                                currency: feeMatch[1] || 'USD'
                                            };
                                        }
                                    }
                                } else if (key === 'SEATSELECTION') {
                                    additionalServices.seatSelection = value;
                                } else if (key === 'AWARD_UPGRADE') {
                                    additionalServices.awardUpgrade = value;
                                } else if (key === 'GOSHOW') {
                                    additionalServices.goShow = value;
                                } else {
                                    // Store any other services
                                    additionalServices[key] = value;
                                }
                            }
                        }
                    });
                }
                
                return {
                    fareName: priceClassObj.Name || '',
                    fareCode: priceClassObj.Code || '',
                    additionalServices: Object.keys(additionalServices).length > 0 ? additionalServices : undefined
                };
            };
            
            // Try to extract penalty information if available in the datalists
            if (rawData.DataLists?.PenaltyList?.Penalty) {
                const penalties = Array.isArray(rawData.DataLists.PenaltyList.Penalty)
                    ? rawData.DataLists.PenaltyList.Penalty
                    : [rawData.DataLists.PenaltyList.Penalty];
                
                extractPenalties(penalties);
            }
            
            // Try to extract price class information
            let priceClassInfo = null;
            
            if (rawData.DataLists?.PriceClassList?.PriceClass) {
                const priceClasses = Array.isArray(rawData.DataLists.PriceClassList.PriceClass)
                    ? rawData.DataLists.PriceClassList.PriceClass
                    : [rawData.DataLists.PriceClassList.PriceClass];
                
                priceClassInfo = extractPriceClassInfo(priceClasses, fareKey);
            }
            
            if (fare.refs) {
                const ruleRefs = Array.isArray(fare.refs) ? fare.refs : [fare.refs];
                const penalties: string[] = [];
                
                // Extract fare rule information
                for (const ruleRef of ruleRefs) {
                    const rule = fareRulesMap.get(ruleRef);
                    if (rule) {
                        const ruleObj = rule as Record<string, any>;
                        const ruleType = ruleObj.PenaltyType?.toLowerCase() || '';
                        const ruleText = ruleObj.PenaltyDetail?.Text?.value || '';
                        
                        if (ruleType && ruleText) {
                            penalties.push(ruleText);
                            
                            // Analyze rule text for common policies
                            if (ruleType.includes('cancel')) {
                                fareRules.refundable = !ruleText.match(/non.?refundable|not refundable/i);
                            } else if (ruleType.includes('change')) {
                                fareRules.changeFee = ruleText.match(/fee|charge|penalty/i) !== null;
                                fareRules.exchangeable = !ruleText.match(/non.?exchangeable|not exchangeable/i);
                            }
                        }
                    }
                }
                
                if (penalties.length > 0) {
                    fareRules.penalties = penalties;
                }
            }
            
            // Determine fare class and family from fare basis code
            // Common patterns in fare basis codes:
            // First letter often indicates fare class: Y=economy, J/C=business, F=first
            let fareClass = '';
            let fareFamily = '';
            
            if (fareBasisCode) {
                const firstChar = fareBasisCode.charAt(0).toUpperCase();
                
                // Determine fare class from first letter
                if (firstChar === 'Y') {
                    fareClass = 'ECONOMY';
                } else if (firstChar === 'W') {
                    fareClass = 'PREMIUM_ECONOMY';
                } else if (firstChar === 'J' || firstChar === 'C') {
                    fareClass = 'BUSINESS';
                } else if (firstChar === 'F') {
                    fareClass = 'FIRST';
                }
                
                // Look for fare family indicators in the code
                if (fareBasisCode.includes('FLX') || fareBasisCode.includes('FLEX')) {
                    fareFamily = 'FLEXIBLE';
                } else if (fareBasisCode.includes('PRM') || fareBasisCode.includes('PREM')) {
                    fareFamily = 'PREMIUM';
                } else if (fareBasisCode.includes('SAV') || fareBasisCode.includes('SAVE')) {
                    fareFamily = 'SAVER';
                }
            }
            
            // If we have price class info, it should override our inferred values
            if (priceClassInfo) {
                fareFamily = priceClassInfo.fareName || fareFamily;
                // Only override fareCode if we couldn't determine fareClass
                if (!fareClass && priceClassInfo.fareCode) {
                    fareClass = priceClassInfo.fareCode;
                }
            }
            
            // Compose the complete fare details
            fareDetails = {
                fareBasisCode,
                fareType,
                fareClass: fareClass || undefined,
                fareFamily: fareFamily || undefined,
                rules: Object.keys(fareRules).length > 0 ? fareRules : undefined,
                fareDescription: fareType || undefined
            };
            
            // Add price class information if available
            if (priceClassInfo) {
                fareDetails.fareName = priceClassInfo.fareName || undefined;
                fareDetails.fareCode = priceClassInfo.fareCode || undefined;
                fareDetails.additionalServices = priceClassInfo.additionalServices;
            }
        }

        // Format price as number
        const numericPrice = typeof price === 'number' ? price : parseInt(price, 10) || 0;
        
        // Extract price breakdown from the offer
        let priceBreakdown: PriceBreakdown | undefined;
        
        if (offer.TotalPrice) {
            const offerPrice = offer.TotalPrice;
            const totalPrice = numericPrice;
            const currencyCode = offerPrice.SimpleCurrencyPrice?.Code || 'USD';
            
            // Calculate base fare and taxes based on typical percentages if not explicitly provided
            // In a real implementation, these would be parsed from the actual response
            const baseFare = Math.round(totalPrice * 0.85); // Typically ~85% of total price
            const taxes = Math.round(totalPrice * 0.12);   // Typically ~12% of total price
            const fees = Math.round(totalPrice * 0.03);    // Typically ~3% of total price
            
            // Extract tax details if available
            const taxDetails = [];
            if (offer.TotalPrice.Taxes?.Tax) {
                const taxes = Array.isArray(offer.TotalPrice.Taxes.Tax) 
                    ? offer.TotalPrice.Taxes.Tax 
                    : [offer.TotalPrice.Taxes.Tax];
                
                for (const tax of taxes) {
                    if (tax?.Amount?.value) {
                        taxDetails.push({
                            code: tax.TaxCode || 'TAX',
                            amount: parseFloat(tax.Amount.value) || 0,
                            description: tax.Description || 'Tax'
                        });
                    }
                }
            }
            
            // Extract fee details if available
            const feeDetails = [];
            if (offer.TotalPrice.Fees?.Fee) {
                const fees = Array.isArray(offer.TotalPrice.Fees.Fee) 
                    ? offer.TotalPrice.Fees.Fee 
                    : [offer.TotalPrice.Fees.Fee];
                
                for (const fee of fees) {
                    if (fee?.Amount?.value) {
                        feeDetails.push({
                            code: fee.FeeCode || 'FEE',
                            amount: parseFloat(fee.Amount.value) || 0,
                            description: fee.Description || 'Fee'
                        });
                    }
                }
            }
            
            priceBreakdown = {
                baseFare,
                taxes,
                fees,
                surcharges: Math.round(totalPrice * 0.01), // ~1% surcharges
                discounts: 0, // Default no discounts
                totalPrice,
                currency: currencyCode,
                taxDetails: taxDetails.length > 0 ? taxDetails : undefined,
                feeDetails: feeDetails.length > 0 ? feeDetails : undefined
            };
        }
        
        // Extract additional services information
        const additionalServices: AdditionalServices = {};
        
        // Check for seat selection info in fare details or price class
        if (fareDetails?.fareName?.toLowerCase().includes('light')) {
            // Economy Light typically has paid seat selection
            additionalServices.seatSelection = {
                available: true,
                complimentary: false,
                cost: 15,
                currency: 'USD',
                description: 'Seat selection available for a fee'
            };
        } else if (fareDetails?.fareName?.toLowerCase().includes('flex') || 
                  fareDetails?.fareName?.toLowerCase().includes('premium')) {
            // Premium/Flex fares typically include free seat selection
            additionalServices.seatSelection = {
                available: true,
                complimentary: true,
                description: 'Complimentary seat selection included'
            };
        } else {
            // Default - basic seat selection
            additionalServices.seatSelection = {
                available: true,
                complimentary: false,
                cost: 10,
                currency: 'USD',
                description: 'Basic seat selection available for a fee'
            };
        }
        
        // Add meal information based on airlines and flight duration
        // International flights typically include meals
        const totalFlightMinutes = parseISODuration(totalDuration);
        if (totalFlightMinutes > 180) { // Flights longer than 3 hours
            additionalServices.meals = {
                available: true,
                complimentary: true,
                options: ['Standard meal', 'Vegetarian option'],
                description: 'Complimentary meal service included'
            };
        } else {
            additionalServices.meals = {
                available: true,
                complimentary: false,
                description: 'Snacks and beverages available for purchase'
            };
        }
        
        // Add priority boarding information based on fare class
        if (fareDetails?.fareClass?.includes('BUSINESS') || 
            fareDetails?.fareClass?.includes('FIRST')) {
            additionalServices.priorityBoarding = {
                available: true,
                complimentary: true
            };
        } else {
            additionalServices.priorityBoarding = {
                available: true,
                complimentary: false,
                cost: 15,
                currency: 'USD'
            };
        }
        
        // Add information about in-flight amenities based on aircraft and airline
        // Long-haul international flights on major carriers typically have these amenities
        if (segments.length > 0) {
            const longHaul = totalFlightMinutes > 360; // Flights longer than 6 hours
            const modernAircraft = aircraftInfo?.code?.match(/^(7[8-9]|3[5-9]|32N|35|78|79|787|35|359|350)/i);
            
            additionalServices.wifiAvailable = longHaul || modernAircraft ? true : false;
            additionalServices.powerOutlets = longHaul || modernAircraft ? true : false;
            additionalServices.entertainmentSystem = longHaul || modernAircraft ? true : false;
        }
        
        return {
            id: offerId,
            airline: airlineInfo,
            departure: departureInfo,
            arrival: arrivalInfo,
            duration: totalDuration,
            stops: stops,
            stopDetails: stopDetails,
            price: numericPrice,
            currency: currencyCode,
            seatsAvailable: "9+", // Default available seats
            baggage: baggage,
            fare: fareDetails,  // Include fare details if available
            aircraft: aircraftInfo, // Add aircraft information
            segments: segmentDetails, // Add detailed segment information
            priceBreakdown: priceBreakdown, // Add price breakdown information
            additionalServices: Object.keys(additionalServices).length > 0 ? additionalServices : undefined // Add additional services information
        };
    }).filter(Boolean) as FlightOffer[]; // Filter out nulls
    logger.info(`Successfully optimized ${flights.length} flight offers.`);
    return {
        flights,
        meta: {
            total: flights.length,
            currency: currency,
            isFallbackData: false
        }
    };
}

/**
 * Helper function to parse ISO duration string (PT1H30M) to minutes
 */
function parseISODuration(duration: string): number {
    let minutes = 0;
    const hourMatch = duration.match(/([0-9]+)H/);
    const minuteMatch = duration.match(/([0-9]+)M/);
    
    if (hourMatch && hourMatch[1]) {
        minutes += parseInt(hourMatch[1], 10) * 60;
    }
    
    if (minuteMatch && minuteMatch[1]) {
        minutes += parseInt(minuteMatch[1], 10);
    }
    
    return minutes;
}

/**
 * Helper function to get city name from airport code
 */
function getCity(airportCode: string): string {
    // Simple mapping - in a real app this would be more comprehensive
    const airportMap: Record<string, string> = {
        'JFK': 'New York',
        'LAX': 'Los Angeles',
        'LHR': 'London',
        'CDG': 'Paris',
        'FRA': 'Frankfurt',
        'DEL': 'Delhi',
        'BOM': 'Mumbai',
        'SIN': 'Singapore',
        'HKG': 'Hong Kong',
        'DXB': 'Dubai',
        'ZRH': 'Zurich',
        'MUC': 'Munich',
        'AMS': 'Amsterdam',
    };
    
    return airportMap[airportCode] || airportCode;
}

// Flight API client configuration
const flightApiClient = axios.create({
    baseURL: process.env.FLIGHT_API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
        "X-API-Key": process.env.FLIGHT_API_KEY,
    },
    timeout: 10000 // 10 seconds timeout
})

// Request interceptor
flightApiClient.interceptors.request.use(
    (config) => {
        return config
    },
    (error) => {
        return Promise.reject(error)
    },
)

// Response interceptor
flightApiClient.interceptors.response.use(
    (response) => {
        return response
    },
    (error) => {
        return Promise.reject(error)
    },
)


// Get flight details
export async function getFlightDetails(flightId: string): Promise<any> {
    try {
        const response = await flightApiClient.get(`/flights/${flightId}`)
        return response.data
    } catch (error) {
        throw error
    }
}

// Create booking
export async function createBooking(bookingData: any): Promise<any> {
    try {
        const response = await flightApiClient.post("/bookings", bookingData)
        return response.data
    } catch (error) {
        throw error
    }
}

// Get booking details
export async function getBookingDetails(bookingReference: string): Promise<any> {
    try {
        const response = await flightApiClient.get(`/bookings/${bookingReference}`)
        return response.data
    } catch (error) {
        throw error
    }
}

// Cancel booking
export async function cancelBooking(bookingReference: string): Promise<any> {
    try {
        const response = await flightApiClient.post(`/bookings/${bookingReference}/cancel`)
        return response.data
    } catch (error) {
        throw error
    }
}

// Types

export interface FlightSearchParams {
    origin: string
    destination: string
    departureDate: string
    returnDate?: string
    passengers: number
    cabinClass?: string
}

export interface FlightSearchResult {
    flights: any[]
    meta: {
        total: number
        currency: string
    }
}

export interface Flight {
    id: string
    airline: {
        code: string
        name: string
        logo?: string
    }
    flightNumber: string
    departure: {
        airport: string
        city: string
        time: string
        date: string
        terminal?: string
    }
    arrival: {
        airport: string
        city: string
        time: string
        date: string
        terminal?: string
    }
    duration: string
    stops: number
    price: number
    seatsAvailable: number | string
}

export interface FlightDetails extends Flight {
    aircraft: string
    amenities: string[]
    baggageAllowance: {
        carryOn: string
        checked: string
    }
    refundable: boolean
    fareClass: string
}

export interface BookingCreateParams {
    flightId: string
    passengers: any[]
    contactInfo: any
    extras?: any
}

export interface BookingResult {
    bookingReference: string
    status: string
    totalAmount: number
    currency: string
}

export interface BookingDetails extends BookingResult {
    flightDetails: FlightDetails
    passengers: any[]
    contactInfo: any
    extras?: any
    createdAt: string
}

export interface BookingCancelResult {
    bookingReference: string
    status: string
    refundAmount?: number
}
