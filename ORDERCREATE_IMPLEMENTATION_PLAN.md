# OrderCreate Service - Comprehensive Implementation Plan

## Executive Summary

This document provides a complete blueprint for implementing the **OrderCreate service** - the final and most critical component in the REA Flight Portal's booking flow. This service creates actual flight bookings with VDC NDC API by combining data from multiple sources:

1. **FlightPrice response** (required) - Base flight offer
2. **SeatAvailability response** (optional) - Seat selections
3. **ServiceList response** (optional) - Ancillary services (meals, baggage)
4. **Passenger information** (required) - Traveler details
5. **Payment information** (required) - Payment method

### Critical Success Factors

✅ **Handle BOTH pricing scenarios**:
- `pricedInd=true`: Seats/services already include prices
- `pricedInd=false`: Extract prices from FlightPrice response

✅ **Follow clean architecture** pattern (Routes → Services → Builders → Transformers)

✅ **Proper error handling** with detailed validation

✅ **Comprehensive testing** (unit + integration with real VDC API)

> **Note on Multi-Airline**: OrderCreate does NOT need multi-airline support since we're creating a booking for a specific airline's offer (already selected in previous steps). Multi-airline handling only applies to AirShopping.

---

## Table of Contents

1. [OrderCreate Service Overview](#1-ordercreate-service-overview)
2. [PricedInd Scenarios Deep Dive](#2-pricedind-scenarios-deep-dive)
3. [Architecture Design](#3-architecture-design)
4. [Data Flow](#4-data-flow)
5. [Implementation Phases](#5-implementation-phases)
6. [Code Structure & Patterns](#6-code-structure--patterns)
7. [Testing Strategy](#7-testing-strategy)
8. [Integration Checklist](#8-integration-checklist)

---

## 1. OrderCreate Service Overview

### What is OrderCreate?

**OrderCreate** is the VDC NDC API endpoint that creates actual flight bookings. It's the culmination of the booking flow:

```
AirShopping → FlightPrice → [SeatAvailability] → [ServiceList] → **OrderCreate**
```

### VDC API Endpoint

- **URL**: `{VERTEIL_API_BASE_URL}/entrygate/rest/request:preOrderCreate`
- **Method**: POST
- **Service Header**: `OrderCreate`
- **Authentication**: Bearer token + OfficeId

### Request Structure (NDC Specification)

```json
{
  "Query": {
    "Passengers": {
      "Passenger": [...]  // Passenger details with ObjectKeys
    },
    "OrderItems": {
      "ShoppingResponse": {
        "Owner": "AF",
        "ResponseID": {"value": "shopping-response-id"},
        "Offers": {
          "Offer": [{
            "OfferID": {...},
            "OfferItems": {
              "OfferItem": [...]  // Flight OfferItemIDs
            }
          }]
        }
      },
      "OfferItem": [
        // Flight offer item (required)
        {
          "OfferItemID": {...},
          "OfferItemType": {
            "DetailedFlightItem": [...]
          }
        },
        // Seat offer items (optional)
        {
          "OfferItemID": {...},
          "OfferItemType": {
            "SeatItem": [...]
          }
        },
        // Service offer items (optional)
        {
          "OfferItemID": {...},
          "OfferItemType": {
            "ServiceItem": [...]
          }
        }
      ]
    },
    "DataLists": {
      "FareList": {...},
      "FlightSegmentList": {...},
      "FlightList": {...},
      "OriginDestinationList": {...},
      "PriceClassList": {...},
      "ServiceList": {
        "Service": [...]  // All selected services/seats
      }
    },
    "Payments": {
      "Payment": [...]  // Payment details
    }
  }
}
```

### Response Structure

```json
{
  "Response": {
    "Order": {
      "OrderID": "BOOKING123456",
      "BookingReferences": {
        "BookingReference": [
          {
            "ID": "ABC123",
            "AirlineID": "AF"
          }
        ]
      },
      "TotalOrderPrice": {...},
      "OrderItems": {...}
    }
  }
}
```

---

## 2. PricedInd Scenarios Deep Dive

### Understanding pricedInd

**pricedInd** is a boolean attribute on services (seats/ancillaries) that indicates whether pricing is included:

- **`pricedInd=true`**: Service includes price information → Use directly
- **`pricedInd=false`**: No price included → Must extract from FlightPrice response

### Why This Matters

VDC API has TWO workflows for ancillary pricing:

#### Workflow A: Shopping with Pricing (pricedInd=true)

```
1. AirShopping
2. FlightPrice (select offer)
3. SeatAvailability → Returns seats WITH prices
4. ServiceList → Returns services WITH prices
5. OrderCreate → Use prices directly from Step 3/4
```

#### Workflow B: Shopping without Pricing (pricedInd=false)

```
1. AirShopping
2. FlightPrice (select offer)
3. SeatAvailability → Returns seats WITHOUT prices
4. ServiceList → Returns services WITHOUT prices
5. **FlightPrice again** (with selected seats/services) → Get combined price
6. OrderCreate → Use prices from Step 5
```

### Detection Logic

From existing code (`build_ordercreate_enhanced_rq.py`):

```python
def detect_priced_ind_scenario(
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Returns:
    {
        "scenario": "priced_ind_true" | "priced_ind_false" | "mixed",
        "services_priced": [...],
        "services_unpriced": [...],
        "seats_priced": [...],
        "seats_unpriced": [...]
    }
    """
```

### Scenario 1: pricedInd=true (Simplest)

**When**: SeatAvailability and ServiceList responses include `Price` objects

**Example Service**:
```json
{
  "ObjectKey": "MEAL-SEG1-PAX1",
  "PricedInd": true,
  "Price": {
    "Total": {
      "value": 50.00,
      "Code": "USD"
    }
  },
  "Name": "Hot Meal"
}
```

**OrderCreate Action**: Extract price directly from service

```python
def _extract_seat_price_from_service_data(seat_service: Dict[str, Any]) -> Dict[str, Any]:
    """Extract price from SeatAvailability service (pricedInd=true case)"""
    price = seat_service.get('Service', {}).get('Price', {})
    return {
        'BaseAmount': price.get('Total', {}),
        'Taxes': {'Total': {'value': 0, 'Code': price.get('Total', {}).get('Code', 'USD')}}
    }
```

### Scenario 2: pricedInd=false (Complex)

**When**: SeatAvailability/ServiceList responses have NO `Price` objects OR `PricedInd=false`

**Example Service**:
```json
{
  "ObjectKey": "MEAL-SEG1-PAX1",
  "PricedInd": false,
  "Name": "Hot Meal"
  // ❌ NO Price attribute
}
```

**OrderCreate Action**: Extract price from **ancillary pricing FlightPrice response**

The flow becomes:
1. User selects seats/services (no prices)
2. **Call FlightPrice again** with seats/services included
3. FlightPrice returns combined pricing
4. **Extract ancillary prices** from FlightPrice's OfferPrice array
5. Map prices to OrderCreate payload

**Price Extraction** (from `build_ordercreate_rq.py`):

```python
def _extract_seat_price_from_service_data(
    seat_service: Dict[str, Any],
    pricing_response: Optional[Dict[str, Any]] = None,
    selected_seat_key: str = None
) -> Dict[str, Any]:
    """
    Extract seat price - handles BOTH scenarios
    
    Priority:
    1. If pricing_response provided → Extract from FlightPriceRS
    2. Else extract from seat_service.Price (pricedInd=true)
    """
    
    # Scenario 2: Extract from pricing response
    if pricing_response and selected_seat_key:
        offer_prices = normalize_to_list(
            pricing_response.get('PricedFlightOffers', {})
            .get('PricedFlightOffer', [{}])[0]
            .get('OfferPrice', [])
        )
        
        for offer_price in offer_prices:
            # Match ObjectKey to seat
            if offer_price.get('RequestedDate', {}).get('Associations', {}).get('ServiceDefinitionRef', {}).get('ServiceDefinitionRefID') == selected_seat_key:
                return offer_price.get('RequestedDate', {}).get('PriceDetail', {})
    
    # Scenario 1: Extract from service (pricedInd=true)
    service = seat_service.get('Service', {})
    price = service.get('Price', {})
    
    return {
        'BaseAmount': price.get('Total', {}),
        'Taxes': {'Total': {'value': 0, 'Code': price.get('Total', {}).get('Code', 'USD')}}
    }
```

### Scenario 3: Mixed (Both True and False)

**When**: Some services have prices, others don't

**Example**:
- Seat A: `pricedInd=true` → Use seat price directly
- Meal B: `pricedInd=false` → Extract from FlightPrice

**OrderCreate Action**: Handle each item individually based on its `pricedInd` status

---

### How Ancillary Pricing Payloads Are Generated (pricedInd=false)

When seats or services have `pricedInd=false`, the system must call FlightPrice API again to get pricing. This is handled by **`Backend/scripts/build_flightprice_ancillary_rq.py`**.

#### Flow for Getting Prices:

1. **Frontend detects pricedInd=false** for selected items
2. **Calls** `/api/verteil/pricing/price-ancillaries` endpoint
3. **Backend builds FlightPrice request** using one of:
   - `build_flightprice_request_for_seats()` - For seat pricing
   - `build_flightprice_request_for_services()` - For service pricing
4. **Sends to VDC** `/entrygate/rest/request:FlightPrice`
5. **Receives FlightPriceRS** with combined pricing (flight + ancillaries)
6. **Returns to frontend** as `ancillary_pricing_response`
7. **Frontend passes to OrderCreate** with this pricing data

#### Seat Pricing Payload Builder:

```python
# From Backend/scripts/build_flightprice_ancillary_rq.py

def build_flightprice_request_for_seats(
    flight_price_response: Dict[str, Any],
    seatavailability_response: Dict[str, Any],
    selected_seats: List[str],  # e.g., ["PRICE4-SEG2", "PRICE5-SEG2"]
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Build FlightPrice request ONLY for pricing selected seats.
    
    Builds FlightPriceRQ with:
    1. Base flight offer item (always included)
    2. Selected SEAT items with dynamic seat data:
       - Extracts seat Location (Row/Column) from SeatAvailabilityRS
       - Extracts SeatAssociation (segment/traveler refs)
       - Includes SelectedSeat structure with characteristics
    
    Returns: FlightPriceRQ payload to send to VDC API
    """
```

**Example Generated Payload**:
```json
{
  "Travelers": {
    "Traveler": [{"AnonymousTraveler": [{"PTC": {"value": "ADT"}}]}]
  },
  "Query": {
    "OriginDestination": [...],
    "Offers": {
      "Offer": [{
        "OfferID": {...},
        "OfferItemIDs": {
          "OfferItemID": [
            {
              "value": "flight-item-id",
              "refs": ["PAX1"]
            },
            {
              "value": "PRICE4-SEG2",  // Seat ObjectKey
              "refs": ["PAX1"],
              "SelectedSeat": [{
                "Location": {
                  "Column": "G",
                  "Row": {"Number": {"value": "47"}},
                  "Characteristics": {
                    "Characteristic": [{"Code": "O"}]  // Ordinary seat
                  }
                },
                "SeatAssociation": [{
                  "SegmentReferences": {"value": ["SEG2"]},
                  "TravelerReference": "PAX1"
                }]
              }],
              "Quantity": 1
            }
          ]
        }
      }]
    }
  },
  "ShoppingResponseID": {...}
}
```

#### Service Pricing Payload Builder:

```python
def build_flightprice_request_for_services(
    flight_price_response: Dict[str, Any],
    servicelist_response: Dict[str, Any],
    selected_services: List[str],  # e.g., ["SRV16", "SRV23"]
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Build FlightPrice request ONLY for pricing selected services.
    
    Builds FlightPriceRQ with:
    1. Base flight offer item (always included)
    2. Selected SERVICE items (meals, baggage, etc.)
    
    Returns: FlightPriceRQ payload to send to VDC API
    """
```

**Example Generated Payload**:
```json
{
  "Query": {
    "Offers": {
      "Offer": [{
        "OfferID": {...},
        "OfferItemIDs": {
          "OfferItemID": [
            {
              "value": "flight-item-id",
              "refs": ["PAX1"]
            },
            {
              "value": "1-ServiceIdAF-16",  // Service ObjectKey
              "refs": ["PAX1"],
              "Quantity": 1
            }
          ]
        }
      }]
    }
  }
}
```

#### Response from VDC:

The VDC FlightPrice API returns:
```json
{
  "PricedFlightOffers": {
    "PricedFlightOffer": [{
      "OfferPrice": [
        {
          "OfferItemID": "flight-item-id",
          "RequestedDate": {
            "PriceDetail": {
              "BaseAmount": {"value": 500, "Code": "USD"}
            }
          }
        },
        {
          "OfferItemID": "PRICE4-SEG2",  // Seat pricing
          "RequestedDate": {
            "PriceDetail": {
              "BaseAmount": {"value": 50, "Code": "USD"}
            }
          }
        }
      ]
    }]
  }
}
```

This response is what gets passed as `ancillary_pricing_response` to OrderCreate.

#### Key Files:

- **Payload Builder**: `Backend/scripts/build_flightprice_ancillary_rq.py`
  - `build_flightprice_request_for_seats()` - Seat pricing payloads
  - `build_flightprice_request_for_services()` - Service pricing payloads
  - `detect_pricing_required()` - Detects which items need pricing
  
- **API Endpoint**: `Backend/routes/ancillary_pricing_routes.py`
  - `POST /api/verteil/pricing/price-ancillaries` - Complete pricing
  - `POST /api/verteil/pricing/price-seats-only` - Seats only
  - `POST /api/verteil/pricing/price-services-only` - Services only



## 3. Architecture Design

### Clean Architecture Layers

Following the established pattern:

```
Routes (FastAPI)
    ↓
Services (Business Logic)
    ↓
Builders (Request Construction)
    ↓
Transformers (Response Processing)
```

### File Structure

```
Backend/app/
├── routes/
│   └── booking.py               # Add OrderCreate endpoint here
├── services/
│   └── order_create.py          # NEW: OrderCreate service
├── builders/
│   └── order_create.py          # NEW: OrderCreate request builder
├── transformers/
│   └── order_create.py          # NEW: OrderCreate response transformer
└── models/
    └── order_create.py          # NEW: Request/response models (optional)
```

### Component Responsibilities

#### 1. Routes (`app/routes/booking.py`)

**Responsibility**: HTTP endpoint, request validation, error handling

```python
@router.post("/create")
async def create_booking(
    flight_price_response: Dict[str, Any],
    passengers: List[Dict[str, Any]],
    payment: Dict[str, Any],
    contact_info: Dict[str, str],
    seatavailability_response: Optional[Dict[str, Any]] = None,
    servicelist_response: Optional[Dict[str, Any]] = None,
    selected_seats: Optional[List[str]] = None,
    selected_services: Optional[List[str]] = None,
    ancillary_pricing_response: Optional[Dict[str, Any]] = None,
    service: OrderCreateService = Depends(get_order_create_service)
) -> Dict[str, Any]:
    """
    Create flight booking.
    
    Handles both pricedInd=true and pricedInd=false scenarios.
    """
```

**Key Tasks**:
- Validate required fields (flight_price_response, passengers, payment)
- Detect pricing scenario (pricedInd=true/false/mixed)
- Call service layer
- Return formatted response

#### 2. Service (`app/services/order_create.py`)

**Responsibility**: Business logic, VDC API interaction, error handling

```python
class OrderCreateService:
    """Service for creating flight bookings via VDC OrderCreate API."""
    
    async def create_booking(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]] = None,
        servicelist_response: Optional[Dict[str, Any]] = None,
        selected_seats: Optional[List[str]] = None,
        selected_services: Optional[List[str]] = None,
        ancillary_pricing_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create booking with VDC OrderCreate API.
        
        Returns:
        {
            "status": "success",
            "data": {
                "order_id": "...",
                "booking_reference": "...",
                "raw_response": {...}
            }
        }
        """
```

**Key Tasks**:
- Get authentication token (TokenManager)
- Build OrderCreate request (via Builder)
- Make VDC API call with proper headers
- Transform response (via Transformer)
- Handle errors with detailed logging

#### 3. Builder (`app/builders/order_create.py`)

**Responsibility**: Construct VDC OrderCreate request payload

```python
class OrderCreateRequestBuilder:
    """Build VDC OrderCreate requests."""
    
    def build_request(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]] = None,
        servicelist_response: Optional[Dict[str, Any]] = None,
        selected_seats: Optional[List[str]] = None,
        selected_services: Optional[List[str]] = None,
        ancillary_pricing_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build complete OrderCreate request."""
```

**Key Methods**:
- `_detect_pricing_scenario()` - Determine pricedInd scenario
- `_build_passengers()` - Construct Passengers section
- `_build_order_items()` - Construct OrderItems section
  - `_build_shopping_response()` - ShoppingResponse structure
  - `_build_flight_offer_item()` - Flight DetailedFlightItem
  - `_build_seat_offer_items()` - Seat items (handle pricing)
  - `_build_service_offer_items()` - Service items (handle pricing)
- `_build_data_lists()` - Construct DataLists section
- `_build_payments()` - Construct Payments section

> **Note**: No multi-airline support needed - we're booking a specific airline's offer

#### 4. Transformer (`app/transformers/order_create.py`)

**Responsibility**: Transform VDC OrderCreate response to clean format

```python
class OrderCreateTransformer:
    """Transform VDC OrderCreate responses."""
    
    def transform(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform OrderCreate response.
        
        Returns:
        {
            "order_id": "...",
            "booking_reference": "...",
            "airline": "...",
            "total_price": {...},
            "passengers": [...],
            "flights": [...],
            "seats": [...],
            "services": [...],
            "raw_response": {...}
        }
        """
```

**Key Tasks**:
- Extract order ID and booking reference
- Extract pricing breakdown
- Map passengers to bookings
- Clean seat/service details
- Preserve raw response for debugging

---

## 4. Data Flow

### Complete Booking Flow

```
┌─────────────────┐
│  Frontend User  │
│   Selects:      │
│   - Flight      │
│   - Seats       │
│   - Services    │
│   - Passengers  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  POST /api/booking/create       │
│  (Routes Layer)                 │
│  - Validate inputs              │
│  - Detect pricedInd scenario    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  OrderCreateService             │
│  (Service Layer)                │
│  - Get auth token               │
│  - Build request via Builder    │
│  - Call VDC API                 │
│  - Transform response           │
└────────┬────────────────────────┘
         │
         ├──→ Builder.build_request()
         │    ├─→ Detect scenario
         │    ├─→ Build Passengers
         │    ├─→ Build OrderItems
         │    │   ├─→ Flight item (required)
         │    │   ├─→ Seat items (optional, handle pricing)
         │    │   └─→ Service items (optional, handle pricing)
         │    ├─→ Build DataLists
         │    └─→ Build Payments
         │
         ├──→ VDC API Call
         │    POST /request:preOrderCreate
         │    Headers: Bearer token, OfficeId, service=OrderCreate
         │
         └──→ Transformer.transform()
              └─→ Clean booking confirmation
```

### Data Sources & Mapping

#### Input Data Sources

1. **FlightPrice Response** (REQUIRED)
   - Contains: ShoppingResponseID, OfferID, OfferItemIDs, DataLists
   - Used for: Base flight offer, prices (if pricedInd=false)

2. **SeatAvailability Response** (OPTIONAL)
   - Contains: Seat maps, seat services
   - Used for: Seat selections, prices (if pricedInd=true)

3. **ServiceList Response** (OPTIONAL)
   - Contains: Ancillary services (meals, baggage, etc.)
   - Used for: Service selections, prices (if pricedInd=true)

4. **Passenger Data** (REQUIRED)
   - Frontend input
   - Used for: Passenger section, ObjectKey mapping

5. **Payment Data** (REQUIRED)
   - Frontend input
   - Used for: Payments section

6. **Ancillary Pricing Response** (CONDITIONAL)
   - FlightPrice response with seats/services included
   - Required if: pricedInd=false for any selected item
   - Used for: Extract prices for unpriced items

#### Mapping Examples

**pricedInd=true: Seat Mapping**

```
SeatAvailability Response:
{
  "Services": {
    "Service": [
      {
        "ObjectKey": "SEAT-SEG1-12A",
        "PricedInd": true,
        "Price": {
          "Total": {"value": 50, "Code": "USD"}
        },
        "Definition": {
          "Seat": {
            "Column": "A",
            "Row": "12"
          }
        }
      }
    ]
  }
}

↓ Transform to OrderCreate ↓

{
  "OfferItemID": {
    "value": "SEAT-SEG1-12A",
    "Owner": "AF"
  },
  "OfferItemType": {
    "SeatItem": [
      {
        "Price": {
          "BaseAmount": {"value": 50, "Code": "USD"}
        },
        "SeatDefinition": {
          "Column": "A",
          "Row": "12"
        },
        "refs": ["PAX1"]
      }
    ]
  }
}
```

**pricedInd=false: Extract from FlightPrice**

```
Ancillary Pricing FlightPrice Response:
{
  "PricedFlightOffers": {
    "PricedFlightOffer": [{
      "OfferPrice": [
        {
          "OfferItemID": "SEAT-SEG1-12A",
          "RequestedDate": {
            "PriceDetail": {
              "BaseAmount": {"value": 50, "Code": "USD"}
            }
          }
        }
      ]
    }]
  }
}

↓ Extract price for "SEAT-SEG1-12A" ↓

{
  "OfferItemID": {
    "value": "SEAT-SEG1-12A",
    "Owner": "AF"
  },
  "OfferItemType": {
    "SeatItem": [
      {
        "Price": {
          "BaseAmount": {"value": 50, "Code": "USD"}  // ← From FlightPrice
        },
        ...
      }
    ]
  }
}
```

---

## 5. Implementation Phases

### Phase 1: Builder Implementation (3-4 hours)

**Goal**: Create `app/builders/order_create.py` with complete request building logic

**Tasks**:

1. **Create Builder Class Structure**
   ```python
   class OrderCreateRequestBuilder:
       def __init__(self):
           self.logger = logging.getLogger(__name__)
       
       def build_request(...) -> Dict[str, Any]:
           """Main entry point"""
           pass
   ```

4. **Implement Utility Functions** (DRY principle)
   - `normalize_to_list()` - List normalization
   - `_detect_pricing_scenario()` - pricedInd detection
   - `_create_offer_item_id()` - Standard OfferItemID structure

3. **Implement Passengers Section**
   ```python
   def _build_passengers(
       self,
       passengers: List[Dict[str, Any]],
       flight_price_response: Dict[str, Any]
   ) -> List[Dict[str, Any]]:
       """
       Build Passengers section with ObjectKey mapping.
       
       Maps passenger index → AnonymousTraveler ObjectKey from FlightPrice
       """
   ```

4. **Implement OrderItems Section**
   - `_build_shopping_response()` - Extract from FlightPrice
   - `_build_flight_offer_item()` - Flight details
   - `_build_seat_offer_items()` - Handle both pricing scenarios
   - `_build_service_offer_items()` - Handle both pricing scenarios

5. **Implement DataLists Section**
   - Copy from FlightPrice response
   - Add selected services to ServiceList

6. **Implement Payments Section**
   - Map payment input to VDC format
   - Include total price calculation

**Acceptance Criteria**:
- ✅ Builder creates valid OrderCreate request structure
- ✅ Handles pricedInd=true scenario correctly
- ✅ Handles pricedInd=false scenario correctly
- ✅ Handles mixed scenario correctly
- ✅ Unit tests pass (mock data)

### Phase 2: Service Implementation (2-3 hours)

**Goal**: Create `app/services/order_create.py` with VDC API integration

**Tasks**:

1. **Create Service Class**
   ```python
   class OrderCreateService:
       def __init__(
           self,
           http_client: httpx.AsyncClient,
           config: Config,
           token_manager: TokenManager,
           builder: OrderCreateRequestBuilder,
           transformer: OrderCreateTransformer
       ):
           pass
   ```

2. **Implement create_booking() Method**
   - Validate inputs
   - Build request via Builder
   - Get auth token
   - Make VDC API call
   - Transform response
   - Error handling

3. **Add Helper Methods**
   - `_build_headers()` - VDC headers with OfficeId
   - `_validate_response()` - Check for API errors
   - `_handle_api_error()` - Format error messages

**Acceptance Criteria**:
- ✅ Service successfully calls VDC API
- ✅ Proper authentication (Bearer token + OfficeId)
- ✅ Returns transformed booking confirmation
- ✅ Handles API errors gracefully
- ✅ Unit tests pass (mocked HTTP calls)

### Phase 3: Transformer Implementation (1-2 hours)

**Goal**: Create `app/transformers/order_create.py` to clean VDC responses

**Tasks**:

1. **Create Transformer Class**
   ```python
   class OrderCreateTransformer:
       def transform(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
           pass
   ```

2. **Implement Extraction Methods**
   - `_extract_order_id()` - Order ID
   - `_extract_booking_reference()` - PNR
   - `_extract_total_price()` - Price breakdown
   - `_extract_passengers()` - Passenger bookings
   - `_extract_flights()` - Flight details
   - `_extract_seats()` - Seat assignments
   - `_extract_services()` - Service confirmations

**Acceptance Criteria**:
- ✅ Returns clean booking confirmation
- ✅ Includes all critical booking info
- ✅ Preserves raw response for debugging
- ✅ Unit tests pass

### Phase 4: Routes Implementation (1-2 hours)

**Goal**: Add OrderCreate endpoint to `app/routes/booking.py`

**Tasks**:

1. **Add Endpoint**
   ```python
   @router.post("/create")
   async def create_booking(...) -> Dict[str, Any]:
       """Create flight booking."""
   ```

2. **Implement Request Validation**
   - Check required fields
   - Validate data types
   - Check pricedInd scenario

3. **Add Error Handling**
   - HTTPException for validation errors
   - Detailed error messages

**Acceptance Criteria**:
- ✅ Endpoint accepts correct payload
- ✅ Returns booking confirmation
- ✅ Returns proper HTTP status codes
- ✅ Integrates with service layer

### Phase 5: Integration Testing (3-4 hours)

**Goal**: Create integration tests with real VDC API

**Tasks**:

1. **Create Test File**
   - `tests/integration/test_order_create.py`

2. **Implement Test Cases**
   ```python
   async def test_order_create_priced_ind_true():
       """Test booking with priced seats/services."""
   
   async def test_order_create_priced_ind_false():
       """Test booking with unpriced seats/services."""
   
   async def test_order_create_flight_only():
       """Test booking without ancillaries."""
   
   async def test_order_create_multi_passenger():
       """Test booking with multiple passengers."""
   
   async def test_order_create_error_handling():
       """Test error scenarios."""
   ```

3. **Test Complete Flow**
   - Search → Price → Seats → Services → **OrderCreate**

**Acceptance Criteria**:
- ✅ All integration tests pass with real VDC API
- ✅ Complete booking flow validated end-to-end
- ✅ Both pricing scenarios tested
- ✅ Multi-passenger bookings work

---

## 6. Code Structure & Patterns

### Builder Pattern

**Key Principle**: Build complex OrderCreate request step-by-step

```python
class OrderCreateRequestBuilder:
    """
    Build VDC OrderCreate requests following NDC specification.
    
    Patterns:
    - DRY: Reusable utility functions
    - Defensive: Validate at each step
    - Flexible: Handle all pricing scenarios
    """
    
    def build_request(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build complete OrderCreate request.
        
        Steps:
        1. Detect pricing scenario
        2. Extract base flight data
        3. Build Passengers section
        4. Build OrderItems section
        5. Build DataLists section
        6. Build Payments section
        7. Validate structure
        """
        
        # Step 1: Detect scenario
        scenario = self._detect_pricing_scenario(
            seatavailability_response=kwargs.get('seatavailability_response'),
            servicelist_response=kwargs.get('servicelist_response'),
            selected_seats=kwargs.get('selected_seats'),
            selected_services=kwargs.get('selected_services')
        )
        
        # Step 2: Extract base data
        airline_code = self._extract_airline_code(flight_price_response)
        shopping_response_id = self._extract_shopping_response_id(flight_price_response)
        selected_offer = self._extract_selected_offer(flight_price_response)
        
        # Step 3: Build request structure
        request = {
            "Query": {
                "Passengers": self._build_passengers(passengers, flight_price_response),
                "OrderItems": self._build_order_items(
                    flight_price_response=flight_price_response,
                    scenario=scenario,
                    selected_offer=selected_offer,
                    **kwargs
                ),
                "DataLists": self._build_data_lists(
                    flight_price_response=flight_price_response,
                    scenario=scenario,
                    **kwargs
                ),
                "Payments": self._build_payments(payment, flight_price_response, **kwargs)
            }
        }
        
        # Step 4: Validate
        self._validate_request(request)
        
        return request
```

### Service Pattern

**Key Principle**: Orchestrate builder, HTTP client, transformer

```python
class OrderCreateService:
    """
    Service for creating flight bookings.
    
    Responsibilities:
    - Authentication
    - Request building
    - API communication
    - Response transformation
    - Error handling
    """
    
    async def create_booking(self, **kwargs) -> Dict[str, Any]:
        """
        Create booking with VDC OrderCreate API.
        
        Flow:
        1. Validate inputs
        2. Build request
        3. Get auth token
        4. Call VDC API
        5. Transform response
        6. Handle errors
        """
        try:
            # 1. Validate
            self._validate_inputs(**kwargs)
            
            # 2. Build request
            request_payload = self.builder.build_request(**kwargs)
            
            # 3. Get token
            token = self.token_manager.get_token()
            
            # 4. Call API
            headers = self._build_headers(token)
            async with self.http_client.post(
                f"{self.config.VERTEIL_API_BASE_URL}/entrygate/rest/request:preOrderCreate",
                headers=headers,
                json=request_payload,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                raw_response = await response.json()
            
            # 5. Transform
            transformed = self.transformer.transform(raw_response)
            
            return {
                "status": "success",
                "data": transformed
            }
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"VDC API error: {e}", exc_info=True)
            raise OrderCreateError(f"Booking failed: {e.response.text}")
        except Exception as e:
            self.logger.error(f"OrderCreate failed: {e}", exc_info=True)
            raise
```

### Pricing Scenario Handling

**Critical Pattern**: Detect and handle pricedInd scenarios

```python
def _build_seat_offer_items(
    self,
    seatavailability_response: Dict[str, Any],
    selected_seats: List[str],
    scenario: Dict[str, Any],
    ancillary_pricing_response: Optional[Dict[str, Any]] = None,
    passengers: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Build seat offer items - handles BOTH pricing scenarios.
    
    Logic:
    - If pricedInd=true → Extract price from SeatAvailability
    - If pricedInd=false → Extract price from ancillary_pricing_response
    """
    
    seat_items = []
    services = normalize_to_list(
        seatavailability_response.get('Services', {}).get('Service', [])
    )
    
    for seat_key in selected_seats:
        # Find seat service
        seat_service = next(
            (s for s in services if s.get('ObjectKey') == seat_key),
            None
        )
        
        if not seat_service:
            continue
        
        # Determine price source
        if seat_key in scenario['seats_priced']:
            # pricedInd=true: Use seat service price
            price = self._extract_price_from_service(seat_service)
        else:
            # pricedInd=false: Extract from pricing response
            if not ancillary_pricing_response:
                raise ValueError(f"Seat {seat_key} requires pricing but no ancillary_pricing_response provided")
            
            price = self._extract_price_from_pricing_response(
                ancillary_pricing_response,
                seat_key
            )
        
        # Build offer item
        seat_item = {
            "OfferItemID": self._create_offer_item_id(seat_key, airline_code),
            "OfferItemType": {
                "SeatItem": [{
                    "Price": price,
                    "SeatDefinition": self._extract_seat_definition(seat_service),
                    "refs": [pax['ObjectKey'] for pax in passengers]
                }]
            }
        }
        
        seat_items.append(seat_item)
    
    return seat_items
```

### Error Handling Pattern

```python
class OrderCreateError(Exception):
    """Base exception for OrderCreate errors."""
    pass

class OrderCreateValidationError(OrderCreateError):
    """Validation error before API call."""
    pass

class OrderCreateAPIError(OrderCreateError):
    """VDC API returned an error."""
    pass

# In Service:
async def create_booking(self, **kwargs):
    try:
        # Validate inputs
        if not kwargs.get('flight_price_response'):
            raise OrderCreateValidationError("flight_price_response is required")
        
        # Build and call API
        ...
        
    except OrderCreateValidationError as e:
        # 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except OrderCreateAPIError as e:
        # 502 Bad Gateway
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        # 500 Internal Server Error
        self.logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 7. Testing Strategy

### Unit Tests

**Location**: `tests/unit/test_order_create_builder.py`, `tests/unit/test_order_create_service.py`

**Coverage**:

1. **Builder Tests**
   ```python
   def test_build_request_priced_ind_true():
       """Test request building with priced seats/services."""
   
   def test_build_request_priced_ind_false():
       """Test request building with unpriced seats/services."""
   
   def test_build_passengers_section():
       """Test Passengers section construction."""
   
   def test_build_order_items_section():
       """Test OrderItems section construction."""
   
   def test_detect_pricing_scenario():
       """Test pricedInd scenario detection."""
   
   def test_extract_price_from_service():
       """Test price extraction from service."""
   
   def test_extract_price_from_pricing_response():
       """Test price extraction from FlightPrice."""
   ```

2. **Service Tests** (with mocked HTTP)
   ```python
   @pytest.mark.asyncio
   async def test_create_booking_success(mock_http_client):
       """Test successful booking creation."""
   
   @pytest.mark.asyncio
   async def test_create_booking_api_error(mock_http_client):
       """Test API error handling."""
   
   @pytest.mark.asyncio
   async def test_create_booking_validation_error():
       """Test validation error handling."""
   ```

3. **Transformer Tests**
   ```python
   def test_transform_order_response():
       """Test response transformation."""
   
   def test_extract_booking_reference():
       """Test booking reference extraction."""
   ```

### Integration Tests

**Location**: `tests/integration/test_order_create.py`

**Setup**:
```python
import pytest
import httpx
from app.services.order_create import OrderCreateService
from app.builders.order_create import OrderCreateRequestBuilder
from app.transformers.order_create import OrderCreateTransformer
from app.utils.auth import TokenManager
from app.core.config import get_config

@pytest.fixture
async def http_client():
    """Fresh HTTP client per test."""
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture
def order_create_service(http_client):
    """OrderCreate service instance."""
    config = get_config()
    token_manager = TokenManager.get_instance()
    builder = OrderCreateRequestBuilder()
    transformer = OrderCreateTransformer()
    
    return OrderCreateService(
        http_client=http_client,
        config=config,
        token_manager=token_manager,
        builder=builder,
        transformer=transformer
    )
```

**Test Cases**:

1. **Complete Flow Tests**
   ```python
   @pytest.mark.asyncio
   async def test_complete_booking_flow_priced_ind_true(
       air_shopping_service,
       flight_price_service,
       ancillary_service,
       order_create_service
   ):
       """
       Test complete flow: Search → Price → Seats/Services → OrderCreate
       With pricedInd=true (seats/services include prices)
       """
       
       # 1. Search
       search_result = await air_shopping_service.search_flights(...)
       
       # 2. Price
       price_result = await flight_price_service.get_price(
           offer_index=0,
           airline_owner=search_result['airlines'][0]['code'],
           air_shopping_response=search_result['raw_response']
       )
       
       # 3. Get Seats (pricedInd=true)
       seats_result = await ancillary_service.get_seats(
           flight_price_response=price_result['raw_response'],
           selected_offer_index=0
       )
       
       # 4. Get Services (pricedInd=true)
       services_result = await ancillary_service.get_services(
           flight_price_response=price_result['raw_response'],
           selected_offer_index=0
       )
       
       # 5. Create Booking
       booking_result = await order_create_service.create_booking(
           flight_price_response=price_result['raw_response'],
           passengers=[{
               "given_name": "John",
               "surname": "Doe",
               "dob": "1990-01-01",
               "gender": "Male",
               "email": "john@example.com"
           }],
           payment={
               "method": "credit_card",
               "card_number": "4111111111111111",
               "expiry": "12/25",
               "cvv": "123"
           },
           seatavailability_response=seats_result['raw_response'],
           servicelist_response=services_result['raw_response'],
           selected_seats=["SEAT-SEG1-12A"],
           selected_services=["MEAL-SEG1-HOT"]
       )
       
       # Assertions
       assert booking_result['status'] == 'success'
       assert 'order_id' in booking_result['data']
       assert 'booking_reference' in booking_result['data']
   ```

2. **Scenario-Specific Tests**
   ```python
   @pytest.mark.asyncio
   async def test_booking_priced_ind_false(order_create_service, ...):
       """Test booking with pricedInd=false (requires ancillary pricing)."""
   
   @pytest.mark.asyncio
   async def test_booking_flight_only(order_create_service, ...):
       """Test booking without seats/services."""
   
   @pytest.mark.asyncio
   async def test_booking_multi_passenger(order_create_service, ...):
       """Test booking with multiple passengers."""
   ```

### Test Data

**Use Real API Responses**: Save actual VDC responses for testing

```python
# tests/fixtures/order_create_data.py

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent

def load_flight_price_response():
    with open(FIXTURES_DIR / 'flight_price_response.json') as f:
        return json.load(f)

def load_seatavailability_priced_response():
    """SeatAvailability with pricedInd=true"""
    with open(FIXTURES_DIR / 'seatavailability_priced.json') as f:
        return json.load(f)

def load_seatavailability_unpriced_response():
    """SeatAvailability with pricedInd=false"""
    with open(FIXTURES_DIR / 'seatavailability_unpriced.json') as f:
        return json.load(f)
```

---

## 8. Integration Checklist

### Pre-Implementation

- [ ] Read this complete document
- [ ] Review existing code:
  - `scripts/build_ordercreate_rq.py` - Existing builder logic
  - `app/services/ancillary.py` - Pattern reference
  - `app/builders/flight_price.py` - Builder pattern reference
- [ ] Understand VDC OrderCreate specification (`documentations/vdc-api-documentation.md`)
- [ ] Review pricedInd scenarios in depth
- [ ] Set up test environment with VDC API access

### Phase 1: Builder ✅

- [ ] Create `app/builders/order_create.py`
- [ ] Implement `OrderCreateRequestBuilder` class
- [ ] Add utility functions (normalize_to_list, etc.)
- [ ] Implement `_detect_pricing_scenario()`
- [ ] Implement `_build_passengers()`
- [ ] Implement `_build_order_items()`
  - [ ] `_build_shopping_response()`
  - [ ] `_build_flight_offer_item()`
  - [ ] `_build_seat_offer_items()` (both pricing scenarios)
  - [ ] `_build_service_offer_items()` (both pricing scenarios)
- [ ] Implement `_build_data_lists()`
- [ ] Implement `_build_payments()`
- [ ] Write unit tests
- [ ] All unit tests passing ✅

### Phase 2: Service ✅

- [ ] Create `app/services/order_create.py`
- [ ] Implement `OrderCreateService` class
- [ ] Implement `create_booking()` method
- [ ] Add `_build_headers()` helper
- [ ] Add `_validate_inputs()` helper
- [ ] Add `_validate_response()` helper
- [ ] Write unit tests with mocked HTTP
- [ ] All unit tests passing ✅

### Phase 3: Transformer ✅

- [ ] Create `app/transformers/order_create.py`
- [ ] Implement `OrderCreateTransformer` class
- [ ] Implement `transform()` method
- [ ] Add extraction helpers
- [ ] Write unit tests
- [ ] All unit tests passing ✅

### Phase 4: Routes ✅

- [ ] Update `app/routes/booking.py`
- [ ] Add `@router.post("/create")` endpoint
- [ ] Implement request validation
- [ ] Add error handling
- [ ] Update dependency injection in `app/core/dependencies.py`
- [ ] Test endpoint locally

### Phase 5: Integration Testing ✅

- [ ] Create `tests/integration/test_order_create.py`
- [ ] Set up fixtures
- [ ] Implement complete flow tests
- [ ] Test pricedInd=true scenario
- [ ] Test pricedInd=false scenario
- [ ] Test flight-only booking
- [ ] Test multi-passenger booking
- [ ] Test error handling
- [ ] All integration tests passing with real VDC API ✅

### Post-Implementation

- [ ] Update API documentation
- [ ] Add usage examples
- [ ] Update README with OrderCreate endpoint
- [ ] Code review
- [ ] Performance testing
- [ ] Production deployment checklist

---

## Summary

This implementation plan provides a **complete blueprint** for adding OrderCreate functionality to the REA Flight Portal following established clean architecture patterns.

### Key Success Factors

1. **Understand pricedInd scenarios** - This is the most complex aspect
2. **Follow existing patterns** - Use AncillaryService/FlightPriceService as reference
3. **Test thoroughly** - Both unit and integration tests with real API
4. **Handle errors gracefully** - Provide clear error messages
5. **Document as you go** - Add comments and docstrings

### Estimated Timeline

- **Phase 1** (Builder): 3-4 hours
- **Phase 2** (Service): 2-3 hours
- **Phase 3** (Transformer): 1-2 hours
- **Phase 4** (Routes): 1-2 hours
- **Phase 5** (Integration Tests): 3-4 hours
- **Total**: ~10-15 hours

### Next Steps

1. **Review and approve** this implementation plan
2. **Clarify any questions** before starting
3. **Begin Phase 1** (Builder implementation)
4. **Iterate and test** each phase before moving to next
5. **Complete integration testing** to validate end-to-end flow

---

**Document Version**: 1.0  
**Created**: 2025-01-XX  
**Status**: Ready for Implementation  
**Reviewed By**: [Pending]
