# Deep Analysis: Air Shopping to Flight Price Transformation Process

## Overview
This document provides a comprehensive analysis of how the air shopping response is transformed to build the flight price payload and process the flight price response in the FLIGHT application.

## Process Flow

### 1. Frontend Flight Selection
- **Location**: `Frontend/utils/api-client.ts`
- **Function**: `getFlightPrice()`
- **Input**: 
  - `flightIndex`: Index of selected flight from frontend display
  - `shoppingResponseId`: ID from original air shopping response
  - `airShoppingResponse`: Complete air shopping response data

```typescript
// Frontend sends index-based request
const response = await apiClient.post('/api/verteil/flight-price', {
    offer_id: flightIndex.toString(), // Send index as string to backend
    shopping_response_id: shoppingResponseId,
    air_shopping_response: airShoppingResponse
});
```

### 2. Frontend API Route (Next.js)
- **Location**: `Frontend/app/api/verteil/flight-price/route.ts`
- **Purpose**: Proxy layer that forwards requests to backend
- **Processing**:
  - Logs request details for debugging
  - Forwards request to backend Flask/Quart API
  - Adds raw response data for cache bypass
  - Returns transformed response to frontend

### 3. Backend API Route
- **Location**: `Backend/routes/verteil_flights.py`
- **Endpoint**: `/api/verteil/flight-price`
- **Function**: `flight_price()`
- **Processing**:
  - Validates request data
  - Extracts offer_id, shopping_response_id, and air_shopping_response
  - Calls `process_flight_price()` function
  - Returns JSON response

### 4. Flight Pricing Service
- **Location**: `Backend/services/flight/pricing.py`
- **Class**: `FlightPricingService`
- **Main Function**: `get_flight_price()`

#### Key Processing Steps:

##### A. Offer Selection Strategy
The system supports two approaches for offer selection:

**Index-Based Approach (Current)**:
```python
# Check if offer_id is numeric (index)
is_index_based = offer_id.isdigit()
if is_index_based:
    selected_offer_index = int(offer_id)
```

**Legacy OfferID Approach**:
```python
# Map frontend offer IDs to backend indices
original_offer_mapping = {}
# Build mapping from original offer IDs to indices
# Use suffix matching for compatibility
```

##### B. Payload Building
- **Function**: `_build_pricing_payload()`
- **Builder**: `build_flight_price_request()` from `Backend/scripts/build_flightprice_rq.py`

### 5. Flight Price Request Builder
- **Location**: `Backend/scripts/build_flightprice_rq.py`
- **Function**: `build_flight_price_request()`

#### Input Processing:
1. **Air Shopping Response Structure**:
   ```json
   {
     "OffersGroup": {
       "AirlineOffers": [
         {
           "Owner": {"value": "KQ"},
           "AirlineOffer": [
             {
               "OfferID": {"value": "...", "Owner": "KQ"},
               "OfferItem": [...],
               "TimeLimits": {...}
             }
           ]
         }
       ]
     },
     "DataLists": {
       "AnonymousTravelerList": {...},
       "FlightSegmentList": {...},
       "OriginDestinationList": {...}
     }
   }
   ```

2. **Offer Selection**:
   ```python
   # Navigate to selected offer by index
   offers_group = airshopping_response.get("OffersGroup", {})
   airline_offers_list = offers_group.get("AirlineOffers", [])
   selected_airline_offers_node = airline_offers_list[0]  # First airline
   actual_airline_offers = selected_airline_offers_node.get("AirlineOffer", [])
   selected_offer = actual_airline_offers[selected_offer_index]
   ```

3. **Payload Construction**:
   ```python
   flight_price_request = {
       "DataLists": {
           "FareGroup": fare_list_for_rq,
           "AnonymousTravelerList": data_lists.get("AnonymousTravelerList", {})
       },
       "Query": {
           "OriginDestination": origin_destinations_for_rq,
           "Offers": {
               "Offer": [query_offer]
           }
       },
       "ShoppingResponseID": shopping_response_id_node,
       "Travelers": {"Traveler": travelers_for_rq},
       "Metadata": {...}
   }
   ```

### 6. API Request to Verteil NDC
- **Endpoint**: `/entrygate/rest/request:flightPrice`
- **Method**: POST
- **Headers**: Include authentication and airline-specific headers
- **Payload**: Constructed FlightPrice request

### 7. Response Processing
- **Location**: `Backend/services/flight/pricing.py`
- **Function**: `_process_pricing_response()`
- **Transformer**: `transform_for_frontend()` from `Backend/utils/flight_price_transformer.py`

#### Response Structure:
```json
{
  "FlightPriceRS": {
    "Document": {"Name": "KQ"},
    "ShoppingResponseID": {...},
    "PricedFlightOffers": {
      "PricedFlightOffer": [
        {
          "OfferID": {...},
          "OfferPrice": [...],
          "OfferItem": [...],
          "TimeLimits": {...}
        }
      ]
    },
    "DataLists": {
      "AnonymousTravelerList": {...},
      "FlightSegmentList": {...},
      "OriginDestinationList": {...},
      "FareGroup": {...}
    }
  }
}
```

### 8. Flight Price Transformer
- **Location**: `Backend/utils/flight_price_transformer.py`
- **Function**: `transform_for_frontend()`

#### Transformation Process:

##### A. Reference Data Extraction
```python
def extract_reference_data(response: dict) -> dict:
    # Extract segments, origin-destinations, fare groups
    # Build lookup maps for efficient processing
```

##### B. Offer Processing
```python
def _transform_single_offer_for_frontend(offer_data, refs, all_travelers_map, od_map):
    # Process each offer individually
    # Extract flight segments, pricing, passengers, fare rules
```

##### C. Flight Segment Transformation
```python
def _build_flight_segment(segment_data, refs) -> FlightSegment:
    # Transform raw segment data to frontend format
    # Include airline info, timing, duration
```

##### D. Passenger and Pricing Processing
```python
# Process passenger groups and pricing
passenger_groups = defaultdict(lambda: {
    'count': 0, 
    'baggage': None, 
    'fare_rules': defaultdict(lambda: defaultdict(dict))
})

# Extract total price and currency
total_price, currency = 0.0, None
for op in offer.get('OfferPrice', []):
    price_info = op.get('RequestedDate', {}).get('PriceDetail', {})
    # Process pricing details
```

### 9. Final Response Format
The transformed response follows this structure:
```json
{
  "status": "success",
  "data": {
    "offers": [
      {
        "offer_id": "frontend_offer_id",
        "fare_family": "Economy Basic",
        "flight_segments": {
          "outbound": [...],
          "return": [...]  // For round-trip
        },
        "passengers": [
          {
            "type": "ADT",
            "count": 1,
            "baggage": {...},
            "fare_rules": {...}
          }
        ],
        "total_price": {
          "amount": 450.00,
          "currency": "USD"
        },
        "time_limits": {
          "offer_expiration": "...",
          "payment_deadline": "..."
        },
        "direction": "roundtrip"
      }
    ]
  },
  "request_id": "..."
}
```

## Key Components and Their Roles

### Data Flow Summary
1. **Frontend** → Index-based selection → **Next.js API Route**
2. **Next.js API Route** → Forward request → **Backend API Route**
3. **Backend API Route** → Process request → **Flight Pricing Service**
4. **Flight Pricing Service** → Build payload → **Flight Price Request Builder**
5. **Request Builder** → Extract offer data → **Construct API payload**
6. **API Call** → Send to Verteil NDC → **Receive FlightPrice response**
7. **Response Processing** → Transform data → **Flight Price Transformer**
8. **Transformer** → Format for frontend → **Return structured response**

### Critical Transformation Points

1. **Index to Offer Mapping**: Converting frontend flight card index to actual airline offer
2. **Payload Structure**: Building NDC-compliant FlightPrice request
3. **Response Normalization**: Converting airline-specific response to standardized format
4. **Price Calculation**: Aggregating passenger-specific pricing
5. **Segment Processing**: Transforming flight segments with proper timing and airline data
6. **Fare Rules Extraction**: Processing complex fare rule structures
7. **Baggage Information**: Extracting and formatting baggage allowances

## Error Handling and Validation

### Offer Validation
- Index bounds checking
- Offer expiration validation
- Required field validation

### Response Validation
- Structure validation for required fields
- Price data validation
- Passenger data consistency checks

### Fallback Mechanisms
- Default values for missing data
- Error response formatting
- Logging for debugging

This transformation process ensures that complex airline NDC responses are properly converted into a format suitable for frontend consumption while maintaining data integrity and providing comprehensive flight pricing information.

## Detailed Code Analysis

### 1. Air Shopping Response Structure Analysis

The air shopping response contains multiple layers of nested data:

<augment_code_snippet path="Backend/scripts/build_flightprice_rq.py" mode="EXCERPT">
````python
offers_group = airshopping_response.get("OffersGroup", {})
data_lists = airshopping_response.get("DataLists", {})

# Navigate to airline offers
airline_offers_list = offers_group.get("AirlineOffers", [])
if not isinstance(airline_offers_list, list):
    airline_offers_list = [airline_offers_list]

# Select airline (default: first airline)
selected_airline_offers_node = airline_offers_list[0]
actual_airline_offers = selected_airline_offers_node.get("AirlineOffer", [])
````
</augment_code_snippet>

### 2. Offer Selection Logic

The system uses index-based selection to map frontend flight cards to backend offers:

<augment_code_snippet path="Backend/services/flight/pricing.py" mode="EXCERPT">
````python
# Check if offer_id is a numeric index (new approach)
is_index_based = offer_id.isdigit()

if is_index_based:
    selected_offer_index = int(offer_id)
    # Validate index bounds
    total_offers = 0
    for airline_offers_entry in airline_offers_list:
        airline_offers = airline_offers_entry.get('AirlineOffer', [])
        total_offers += len(airline_offers)

    if selected_offer_index >= total_offers:
        raise ValueError(f"Index {selected_offer_index} out of bounds")
````
</augment_code_snippet>

### 3. Flight Price Request Construction

The request builder extracts specific data from the air shopping response:

<augment_code_snippet path="Backend/scripts/build_flightprice_rq.py" mode="EXCERPT">
````python
# Extract offer details
query_offer_id_node = selected_offer.get("OfferID", {})
query_offer = {
    "OfferID": query_offer_id_node,
    "OfferItemIDs": {"OfferItemID": []}
}

# Build complete request structure
flight_price_request = {
    "DataLists": {
        "FareGroup": fare_list_for_rq,
        "AnonymousTravelerList": data_lists.get("AnonymousTravelerList", {})
    },
    "Query": {
        "OriginDestination": origin_destinations_for_rq,
        "Offers": {"Offer": [query_offer]}
    },
    "ShoppingResponseID": shopping_response_id_node,
    "Travelers": {"Traveler": travelers_for_rq}
}
````
</augment_code_snippet>

### 4. Response Transformation Process

The flight price transformer processes the API response:

<augment_code_snippet path="Backend/utils/flight_price_transformer.py" mode="EXCERPT">
````python
def transform_for_frontend(response: dict) -> dict:
    refs = extract_reference_data(response)
    all_travelers_map = {
        anon.get('ObjectKey'): anon.get('PTC', {}).get('value', 'ADT')
        for anon in response.get('DataLists', {}).get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
    }

    od_map = _get_od_mapping(refs)
    all_offers_raw = collect_all_offers(response)

    transformed_offers = []
    for offer_data in all_offers_raw:
        transformed_offers.extend(
            _transform_single_offer_for_frontend(offer_data, refs, all_travelers_map, od_map)
        )

    return {'offers': transformed_offers}
````
</augment_code_snippet>

### 5. Flight Segment Processing

Individual flight segments are transformed with detailed information:

<augment_code_snippet path="Backend/utils/flight_price_transformer.py" mode="EXCERPT">
````python
def _build_flight_segment(segment_data, refs) -> FlightSegment:
    dep = segment_data.get('Departure', {})
    arr = segment_data.get('Arrival', {})

    return FlightSegment(
        departure_airport=dep.get('AirportCode', {}).get('value', ''),
        arrival_airport=arr.get('AirportCode', {}).get('value', ''),
        departure_datetime=dep.get('Date', ''),
        arrival_datetime=arr.get('Date', ''),
        airline_code=airline_code,
        airline_name=get_airline_name(airline_code),
        airline_logo_url=get_airline_logo_url(airline_code),
        flight_number=f"{airline_code}{flight_num}",
        duration=parse_iso_duration(raw_duration)
    )
````
</augment_code_snippet>

### 6. Pricing and Passenger Data Processing

The transformer aggregates pricing across passenger types:

<augment_code_snippet path="Backend/utils/flight_price_transformer.py" mode="EXCERPT">
````python
total_price, currency = 0.0, None
passenger_groups = defaultdict(lambda: {
    'count': 0,
    'baggage': None,
    'fare_rules': defaultdict(lambda: defaultdict(dict))
})

for op in offer.get('OfferPrice', []):
    price_info = op.get('RequestedDate', {}).get('PriceDetail', {}).get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
    per_pax_price = float(price_info.get('value', 0))
    if currency is None:
        currency = price_info.get('Code')
````
</augment_code_snippet>

## Data Structure Mappings

### Air Shopping → Flight Price Request
- **OffersGroup.AirlineOffers[i].AirlineOffer[j]** → **Query.Offers.Offer**
- **DataLists.AnonymousTravelerList** → **DataLists.AnonymousTravelerList**
- **ShoppingResponseID** → **ShoppingResponseID**
- **Selected offer metadata** → **Travelers.Traveler**

### Flight Price Response → Frontend Format
- **PricedFlightOffers.PricedFlightOffer** → **offers[]**
- **OfferPrice** → **total_price, passengers[].pricing**
- **FlightSegmentList** → **flight_segments**
- **FareGroup** → **fare_rules**
- **TimeLimits** → **time_limits**

## Performance Considerations

### Caching Strategy
- **Service Level**: `@async_cache(timeout=300)` on pricing service
- **Rate Limiting**: `@async_rate_limited(limit=100, window=60)`
- **Frontend Caching**: Raw response stored for cache bypass

### Memory Management
- Efficient reference data extraction
- Lazy loading of transformation data
- Proper cleanup in service lifecycle

### Error Recovery
- Graceful degradation for missing data
- Comprehensive logging for debugging
- Structured error responses

## Integration Points

### Frontend Integration
- Index-based offer selection
- Consistent offer ID mapping
- Raw response preservation for booking

### Backend Integration
- Service-oriented architecture
- Async processing with proper resource management
- Configuration-driven airline support

### External API Integration
- NDC-compliant request formatting
- Airline-specific header management
- Response validation and error handling

---

# Air Shopping Response Data Structure Analysis

## Complete AirShoppingRS Structure

The air shopping response from the Verteil NDC API follows a complex nested structure that contains multiple layers of flight offers, reference data, and metadata. Here's the comprehensive breakdown:

### Root Level Structure

```json
{
  "Success": {},
  "ShoppingResponseID": {
    "ResponseID": {
      "value": "unique-shopping-response-id"
    }
  },
  "OffersGroup": {
    "AirlineOffers": [...]
  },
  "DataLists": {
    "FlightSegmentList": {...},
    "OriginDestinationList": {...},
    "AnonymousTravelerList": {...},
    "FareGroup": {...},
    "FlightList": {...}
  },
  "Metadata": {
    "Other": {
      "OtherMetadata": [...]
    }
  }
}
```

### 1. OffersGroup Structure

The main container for all flight offers, organized by airline:

<augment_code_snippet path="Backend/utils/air_shopping_transformer.py" mode="EXCERPT">
````python
# This logic handles the common structure of AirShoppingRS
offers_group = response.get('OffersGroup', {})
airline_offers_list = offers_group.get('AirlineOffers', [])
if not isinstance(airline_offers_list, list):
    airline_offers_list = [airline_offers_list] if airline_offers_list else []
````
</augment_code_snippet>

**Structure:**
```json
{
  "OffersGroup": {
    "AirlineOffers": [
      {
        "Owner": {"value": "KQ"},
        "AirlineOffer": [
          {
            "OfferID": {
              "ObjectKey": "unique-offer-key",
              "value": "offer-id-value",
              "Owner": "KQ",
              "Channel": "NDC"
            },
            "PricedOffer": {
              "OfferPrice": [...],
              "OfferItem": [...],
              "TimeLimits": {...}
            }
          }
        ]
      }
    ]
  }
}
```

### 2. DataLists Structure

Contains all reference data used by offers:

#### A. FlightSegmentList
Individual flight segments with detailed information:

<augment_code_snippet path="Backend/tests/FlightPriceRS_KQ.json" mode="EXCERPT">
````json
"FlightSegment": [
  {
    "SegmentKey": "SEG3",
    "Departure": {
      "AirportCode": {"value": "NBO"},
      "Date": "2025-06-06T23:50:00.000",
      "Time": "23:50",
      "Terminal": {"Name": "1A"}
    },
    "Arrival": {
      "AirportCode": {"value": "CDG"},
      "Date": "2025-06-07T07:30:00.000",
      "Time": "07:30",
      "Terminal": {"Name": "2E"}
    },
    "MarketingCarrier": {
      "AirlineID": {"value": "KQ"},
      "Name": "Kenya Airways",
      "FlightNumber": {"value": "112"}
    },
    "Equipment": {
      "AircraftCode": {"value": "788"}
    },
    "FlightDetail": {
      "FlightDuration": {"Value": "PT8H40M"}
    }
  }
]
````
</augment_code_snippet>

#### B. OriginDestinationList
Route definitions linking flights:

```json
{
  "OriginDestination": [
    {
      "OriginDestinationKey": "OD1",
      "FlightReferences": {
        "value": ["PJ1", "PJ2", "PJ3"]
      },
      "DepartureCode": {"value": "BLR"},
      "ArrivalCode": {"value": "LHR"}
    }
  ]
}
```

#### C. AnonymousTravelerList
Passenger type definitions:

<augment_code_snippet path="Backend/tests/FlightPriceRS_KQ.json" mode="EXCERPT">
````json
"AnonymousTraveler": [
  {
    "ObjectKey": "PAX1",
    "PTC": {"value": "ADT"}
  },
  {
    "ObjectKey": "PAX2",
    "PTC": {"value": "ADT"}
  },
  {
    "ObjectKey": "PAX3",
    "PTC": {"value": "CHD"}
  },
  {
    "ObjectKey": "PAX11",
    "PTC": {"value": "INF"}
  }
]
````
</augment_code_snippet>

#### D. FlightList
Groups segments into complete flights:

```json
{
  "Flight": [
    {
      "FlightKey": "PJ1",
      "SegmentReferences": {
        "value": ["SEG1", "SEG2"]
      }
    }
  ]
}
```

### 3. Offer Structure Details

Each offer contains comprehensive pricing and flight information:

#### A. OfferID Structure
```json
{
  "OfferID": {
    "ObjectKey": "1H1KQZ_BGGAU0E44J9QH7CW6U2VV4S4Q4GG",
    "value": "1H1KQZ_BGGAU0E44J9QH7CW6U2VV4S4Q4GG",
    "Owner": "KQ",
    "Channel": "NDC"
  }
}
```

#### B. OfferPrice Structure
```json
{
  "OfferPrice": [
    {
      "RequestedDate": {
        "Associations": [
          {
            "AssociatedTraveler": {
              "TravelerReferences": ["PAX1", "PAX2"]
            },
            "ApplicableFlight": {
              "FlightSegmentReference": [
                {
                  "ClassOfService": {
                    "Code": {"value": "Z"},
                    "MarketingName": {
                      "value": "BUSINESS",
                      "CabinDesignator": "C"
                    }
                  },
                  "ref": "SEG3"
                }
              ]
            }
          }
        ],
        "PriceDetail": {
          "TotalAmount": {
            "SimpleCurrencyPrice": {
              "value": 1250.00,
              "Code": "USD"
            }
          },
          "BaseAmount": {...},
          "Taxes": {...}
        }
      }
    }
  ]
}
```

#### C. TimeLimits Structure
```json
{
  "TimeLimits": {
    "OfferExpiration": {
      "DateTime": "2025-06-03T05:18:42.000"
    },
    "Payment": {
      "DateTime": "2025-06-05T04:48:00.000"
    }
  }
}
```

### 4. Metadata Structure

Contains ShoppingResponseID and other metadata:

<augment_code_snippet path="Backend/utils/air_shopping_transformer.py" mode="EXCERPT">
````python
# Extract ShoppingResponseID from metadata
sr_id_val = response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Key"]
sr_owner_val = response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Owner"]
````
</augment_code_snippet>

### 5. Data Relationships and References

The response uses a reference-based system where:

1. **Offers** reference **FlightSegments** via SegmentKey
2. **FlightSegments** are grouped into **Flights** via FlightKey
3. **Flights** are organized into **OriginDestinations** via FlightReferences
4. **Passengers** are referenced via ObjectKey in pricing associations
5. **Fare rules** are linked via FareGroup references

### 6. Transformation Process

The air shopping transformer processes this structure:

<augment_code_snippet path="Backend/utils/air_shopping_transformer.py" mode="EXCERPT">
````python
def transform_air_shopping_for_results(response: dict) -> dict:
    refs = _extract_simple_refs(response)
    offers = []

    offers_group = response.get('OffersGroup', {})
    airline_offers_list = offers_group.get('AirlineOffers', [])

    for airline_offer_group in airline_offers_list:
        for offer in airline_offer_group.get('AirlineOffer', []):
            priced_offer = offer.get('PricedOffer')
            if priced_offer:
                transformed = _transform_offer_for_results_page(priced_offer, refs, offer)
                if transformed:
                    transformed['id'] = str(len(offers))  # Use index as ID
                    offers.append(transformed)

    return {
        'offers': offers,
        'total_offers': len(offers),
        'ShoppingResponseID': response.get('ShoppingResponseID'),
        'raw_response': response
    }
````
</augment_code_snippet>

### 7. Key Differences from FlightPrice Response

**Air Shopping Response:**
- Contains `OffersGroup` with `AirlineOffers`
- Multiple offers per airline
- Basic pricing information
- Reference-based structure

**Flight Price Response:**
- Contains `PricedFlightOffers`
- Detailed pricing breakdown
- Enhanced fare rules and baggage info
- Direct offer structure

This complex nested structure allows airlines to provide comprehensive flight information while maintaining flexibility for different fare families, passenger types, and routing options.
