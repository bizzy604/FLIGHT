# --- START OF FILE build_airshopping_rq.py (Extended for One-Way & Multi-City) ---
import json
from datetime import datetime, date # Not strictly used now, but good for future date validation
from typing import List, Dict, Any, Optional, Literal

# Define TripType literal for better type hinting
TripType = Literal["ONE_WAY", "ROUND_TRIP", "MULTI_CITY"]

def build_airshopping_request(
    trip_type: TripType,
    od_segments: List[Dict[str, str]],
    num_adults: int,
    num_children: int = 0,
    num_infants: int = 0,
    cabin_preference_code: str = "Y",  # Y=Economy, C=Business, F=First, W=PremiumEconomy
    fare_type_code: str = "PUBL",
    sort_order: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Builds an AirShoppingRQ JSON payload for Verteil API.

    Args:
        trip_type: Type of trip ("ONE_WAY", "ROUND_TRIP", "MULTI_CITY")
        od_segments: List of origin-destination segments with "Origin", "Destination", "DepartureDate"
        num_adults: Number of adult passengers
        num_children: Number of child passengers (default: 0)
        num_infants: Number of infant passengers (default: 0)
        cabin_preference_code: Cabin class code (Y=Economy, C=Business, F=First, W=PremiumEconomy)
        fare_type_code: Fare type code (default: "PUBL" for published fares)
        sort_order: Optional list of sort criteria

    Returns:
        Dictionary containing the AirShopping request payload
    """
    # Input validation
    if num_adults <= 0:
        raise ValueError("Number of adults must be at least 1")
    if num_infants > num_adults:
        raise ValueError("Number of infants cannot exceed number of adults")
    if not od_segments:
        raise ValueError("At least one origin-destination segment is required")
    if trip_type == "ONE_WAY" and len(od_segments) != 1:
        raise ValueError("ONE_WAY trip requires exactly one segment")
    if trip_type == "ROUND_TRIP" and len(od_segments) != 2:
        raise ValueError("ROUND_TRIP requires exactly two segments (outbound and return)")
    if trip_type == "MULTI_CITY" and len(od_segments) < 2:
        raise ValueError("MULTI_CITY requires at least two segments")

    # Prepare origin-destination segments
    origin_destinations = []
    od_references = []
    
    for i, segment in enumerate(od_segments, 1):
        od_key = f"OD{i}"
        od_references.append(od_key)
        origin_destinations.append({
            "OriginDestinationKey": od_key,
            "Departure": {
                "AirportCode": {"value": segment["Origin"]},
                "Date": segment["DepartureDate"]
            },
            "Arrival": {
                "AirportCode": {"value": segment["Destination"]}
            }
        })

    # Prepare travelers
    travelers = []
    for _ in range(num_adults):
        travelers.append({
            "AnonymousTraveler": [{"PTC": {"value": "ADT"}}]
        })
    for _ in range(num_children):
        travelers.append({
            "AnonymousTraveler": [{"PTC": {"value": "CHD"}}]
        })
    for _ in range(num_infants):
        travelers.append({
            "AnonymousTraveler": [{"PTC": {"value": "INF"}}]
        })

    # Prepare cabin preferences
    cabin_preferences = {
        "CabinType": [
            {
                "Code": cabin_preference_code,
                "OriginDestinationReferences": [od_ref]
            } for od_ref in od_references
        ]
    }

    # Prepare fare preferences
    fare_preferences = {
        "Types": {
            "Type": [{"Code": fare_type_code}]
        }
    }

    # Prepare preferences
    preferences = {
        "CabinPreferences": cabin_preferences,
        "FarePreferences": fare_preferences,
        "PricingMethodPreference": {
            "BestPricingOption": "Y"
        }
    }

    # Prepare response parameters
    if sort_order is None:
        sort_order = [
            {"Order": "ASCENDING", "Parameter": "PRICE"},
            {"Order": "ASCENDING", "Parameter": "STOP"},
            {"Order": "ASCENDING", "Parameter": "DEPARTURE_TIME"}
        ]

    response_parameters = {
        "SortOrder": sort_order,
        "ShopResultPreference": "FULL"
    }

    # Assemble the final request
    airshopping_request = {
        "Preference": preferences,
        "ResponseParameters": response_parameters,
        "Travelers": {"Traveler": travelers},
        "CoreQuery": {
            "OriginDestinations": {
                "OriginDestination": origin_destinations
            }
        }
    }

    return airshopping_request

def main():
    """Main function to generate and save AirShoppingRQ for different trip types."""
    
    output_dir = "generated_rqs"
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Example common passenger details
    adults = 2
    children = 1
    infants = 1
    cabin = "C"

    # --- Example 1: One-Way ---
    try:
        one_way_segments = [
            {"Origin": "NBO", "Destination": "CDG", "DepartureDate": "2025-06-10"}
        ]
        one_way_rq = build_airshopping_request(
            trip_type="ONE_WAY",
            od_segments=one_way_segments,
            num_adults=adults, num_children=children, num_infants=infants,
            cabin_preference_code=cabin
        )
        with open(os.path.join(output_dir, "AirShoppingRQ_OneWay.json"), "w", encoding="utf-8") as f:
            json.dump(one_way_rq, f, indent=2, ensure_ascii=False)
        print("AirShoppingRQ for One-Way generated.")
    except ValueError as ve:
        print(f"Error (One-Way): {ve}")

    # --- Example 2: Round-Trip ---
    # (Matches your original sample more closely in terms of structure)
    try:
        round_trip_segments = [
            {"Origin": "NBO", "Destination": "CDG", "DepartureDate": "2025-06-06"}, # Outbound
            {"Origin": "CDG", "Destination": "NBO", "DepartureDate": "2025-06-12"}  # Return segment with its own date
        ] # Note: For roundtrip, the second segment's Origin/Destination are derived from the first
          # only the DepartureDate is critical from the second segment here.

        request_payload_rt = build_airshopping_request(
            trip_type="ROUND_TRIP",
            od_segments=round_trip_segments, # Provide both segments with dates
            num_adults=adults, num_children=children, num_infants=infants,
            cabin_preference_code=cabin
        )
        with open(os.path.join(output_dir, "AirShoppingRQ_RoundTrip.json"), "w", encoding="utf-8") as f:
            json.dump(request_payload_rt, f, indent=2, ensure_ascii=False)
        print("AirShoppingRQ for Round-Trip generated.")
    except ValueError as ve:
        print(f"Error (Round-Trip): {ve}")


    # --- Example 3: Multi-City ---
    try:
        multi_city_segments = [
            {"Origin": "NBO", "Destination": "CDG", "DepartureDate": "2025-06-06"},
            {"Origin": "CDG", "Destination": "NBO", "DepartureDate": "2025-06-12"},
            {"Origin": "NBO", "Destination": "CDG", "DepartureDate": "2025-06-18"}
        ]
        multi_city_rq = build_airshopping_request(
            trip_type="MULTI_CITY",
            od_segments=multi_city_segments,
            num_adults=adults, num_children=children, num_infants=infants,
            cabin_preference_code=cabin
        )
        with open(os.path.join(output_dir, "AirShoppingRQ_MultiCity.json"), "w", encoding="utf-8") as f:
            json.dump(multi_city_rq, f, indent=2, ensure_ascii=False)
        print("AirShoppingRQ for Multi-City generated.")
    except ValueError as ve:
        print(f"Error (Multi-City): {ve}")
    
    except Exception as e:
        print(f"An unexpected error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
# --- END OF FILE build_airshopping_rq.py (Extended for One-Way & Multi-City) ---