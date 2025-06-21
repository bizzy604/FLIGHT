# Flight API Implementation Guide

## 1. End-to-End Booking Flow Overview
```
 ┌───────────┐      1. POST /air-shopping
 │  Frontend │ ──────────────────────────────────────►
 └───────────┘                                     │
                                                   │ 2. JSON AirShoppingRQ
                                                   ▼
                                             Verteil NDC API
                                                   │ 3. JSON AirShoppingRS
 ┌───────────┐                                     │
 │  Backend  │ ◄────────────────────────────────────┘
 └───────────┘
      │
      │ 4. User selects offer
      ▼
 ┌───────────┐      5. POST /flight-price
 │  Frontend │ ──────────────────────────────────────►
 └───────────┘                                     │
                                                   ▼
                                             Verteil NDC API
                                                   ▲
 ┌───────────┐                                     │
 │  Backend  │ ◄────────────────────────────────────┘
 └───────────┘
      │
      │ 6. Collect pax / payment
      ▼
 ┌───────────┐      7. POST /order-create
 │  Frontend │ ──────────────────────────────────────►
 └───────────┘                                     │
                                                   ▼
                                             Verteil NDC API
                                                   ▲
 ┌───────────┐                                     │
 │  Backend  │ ◄────────────────────────────────────┘
 └───────────┘
```

*All subsequent endpoints depend on the data returned from their predecessors.*

---

## 2. Endpoint Specifications

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/verteil/air-shopping` | `GET` \| `POST` | Search flight offers |
| `/api/verteil/flight-price` | `POST` | Retrieve price breakdown for a selected offer |
| `/api/verteil/order-create` | `POST` | Create a booking (Order) |

### 2.1 `/air-shopping`
*Search for flight offers (one-way / round-trip / multi-city).*

#### Request
*GET* parameters (one-way & round-trip quick search):
```
origin=LHR
destination=BOM
departDate=2025-08-20
returnDate=2025-08-27      # (optional)
tripType=round-trip|one-way
adults=1
children=0
infants=0
cabinClass=Y|W|C|F
```

*POST* body (full support incl. multi-city):
```json
{
  "tripType": "MULTI_CITY",
  "odSegments": [
    { "origin": "LHR", "destination": "DXB", "departureDate": "2025-08-20" },
    { "origin": "DXB", "destination": "BOM", "departureDate": "2025-08-25" }
  ],
  "numAdults": 1,
  "numChildren": 0,
  "numInfants": 0,
  "cabinPreference": "ECONOMY",
  "directOnly": false
}
```

#### Success Response `200`
```json
{
  "status": "success",
  "data": {
    "shopping_response_id": "SR123",
    "offers": [
      {
        "id": "OFF123",
        "price": { "amount": 580.23, "currency": "USD" },
        "segments": [ ... ],
        "duration": "PT9H10M"
      }
    ]
  },
  "request_id": "2f0d..."
}
```

### 2.2 `/flight-price`
*Price an individual flight offer.*

#### Request `POST`
```json
{
  "offer_id": "OFF123",
  "shopping_response_id": "SR123",
  "air_shopping_rs": { ... },      // Raw AirShoppingRS payload
  "currency": "USD"
}
```

#### Success Response `200`
```json
{
  "status": "success",
  "data": {
    "priced_offer": {
      "total_amount": 612.45,
      "currency": "USD",
      "breakdown": [
        { "passenger_type": "ADT", "base": 500, "taxes": 112.45 }
      ]
    },
    "offer_items": [ ... ]
  },
  "request_id": "7ab3..."
}
```

### 2.3 `/order-create`
*Convert a priced offer into a confirmed booking.*

#### Request `POST`
```json
{
  "flight_offer": { ... },           // The priced offer object
  "passengers": [
    {
      "type": "ADT",
      "title": "MR",
      "firstName": "JOHN",
      "lastName": "DOE",
      "dateOfBirth": "1985-01-15",
      "gender": "M",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "nationality": "US",
      "documentType": "PASSPORT",
      "documentNumber": "AB123456",
      "documentExpiryDate": "2030-01-01",
      "documentIssuingCountry": "US"
    }
  ],
  "payment": {
    "type": "CREDIT_CARD",
    "cardNumber": "4111111111111111",
    "cardHolderName": "JOHN DOE",
    "expiryMonth": "12",
    "expiryYear": "2030",
    "cvv": "123"
  },
  "contact_info": {
    "email": "john.doe@example.com",
    "phone": "+1234567890"
  }
}
```

#### Success Response `200`
```json
{
  "status": "success",
  "data": {
    "booking_reference": "PNR8XY",
    "order_id": "ORD456",
    "ticket_numbers": ["0987654321012"]
  },
  "request_id": "e3de..."
}
```

---

## 3. Dependencies Between Endpoints
| Producer | Consumer | Required Fields Passed Forward |
|----------|----------|--------------------------------|
| Air-Shopping | Flight-Price | `shopping_response_id`, full `AirShoppingRS`, selected `offer_id` |
| Flight-Price | Order-Create | Priced `flight_offer` (with OfferItems & metadata) |

If any earlier step fails, subsequent calls **must not** be attempted.

---

## 4. Headers Configuration
Every call from backend ➜ Verteil NDC requires:
| Header | Source |
|--------|--------|
| `service` | Fixed string provided by Verteil |
| `thirdpartyId` | Selected airline IATA code |
| `officeId` | IATA office identifier |
| `Authorization` | `Bearer <access-token>` (fetched via OAuth2 token endpoint) |

Internally, these values are loaded from `Backend/config.py` and injected by the service layer before hitting Verteil.

---

## 5. Error Handling Patterns
Standardised JSON:
```json
{
  "status": "error",
  "message": "Human-readable message",
  "request_id": "uuid-v4",
  "details": { ... }          // optional structured info
}
```
Status codes:
* `400` – validation / missing fields
* `401` – authentication failure (token expired)
* `429` – rate limit (decorators enforce per-minute caps)
* `500` – unexpected or upstream errors

All endpoints wrap internal exceptions in `FlightServiceError` to guarantee consistent formatting.

---

## 6. Architecture Overview
```
Frontend (Next.js 15)
  ├─ utils/api-client.ts        <-- Axios wrapper
  └─ pages & components         <-- Search form, results, booking UI

Backend (Quart)
  ├─ routes/verteil_flights.py  <-- HTTP layer (3 endpoints)
  ├─ services/
  │   └─ flight/
  │       ├─ search.py          <-- AirShopping logic + cache
  │       ├─ pricing.py         <-- FlightPrice logic
  │       ├─ booking.py         <-- OrderCreate logic
  │       ├─ decorators.py      <-- async_cache, rate limiting
  │       └─ utils.py, types.py
  ├─ scripts/
  │   ├─ build_airshopping_rq.py
  │   ├─ build_flightprice_rq.py
  │   └─ build_ordercreate_rq.py
  └─ config.py                  <-- Environment & header config
```

Key points  
* **Modular service layer** keeps business logic separate from transport.  
* **Scripts** generate Verteil-compliant JSON bodies; services import and use them.  
* **Decorators** add transparent caching and throttling.

---

## 7. Request/Response Examples
(see individual sections above).  
More samples are in `Backend/tests/README.md`.

---

## 8. Testing Instructions

### Automated Integration Tests
A full async test suite is provided:

```bash
cd Backend
pip install -r requirements.txt
pytest -q test_endpoints_integration.py
```

The suite spins up an in-memory Quart app and verifies:
1. `/air-shopping` returns offers  
2. `/flight-price` prices the first offer  
3. `/order-create` completes a booking  
4. Error cases for missing parameters

### Manual cURL Smoke Test
```bash
# 1. Air shopping
curl -X POST http://localhost:5000/api/verteil/air-shopping \
     -H "Content-Type: application/json" \
     -d '{"tripType":"ONE_WAY","odSegments":[{"origin":"LHR","destination":"BOM","departureDate":"2025-08-20"}],"numAdults":1}'

# 2. Flight price (substitute IDs from step 1)
curl -X POST http://localhost:5000/api/verteil/flight-price \
     -H "Content-Type: application/json" \
     -d '{"offer_id":"OFF123","shopping_response_id":"SR123","air_shopping_rs":{...}}'

# 3. Order create (use priced offer from step 2)
curl -X POST http://localhost:5000/api/verteil/order-create \
     -H "Content-Type: application/json" \
     -d '{ "flight_offer":{...},"passengers":[...],"payment":{...},"contact_info":{...}}'
```

---

## 9. Updating / Extending
* **New headers or airlines** – add env vars in `.env` and map in `config.py`.
* **Additional endpoints** – implement in `services/flight/…` and expose via `routes/verteil_flights.py`.
* **Custom validation** – extend `validators` in each service or add Pydantic models.

---

Happy Flying 🚀
