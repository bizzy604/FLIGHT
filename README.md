# Flight Booking Portal

A modern flight booking portal that integrates with Verteil NDC API for flight search, pricing, and booking.

## Features

- Flight search with flexible date selection
- Real-time pricing and availability
- Passenger details collection
- Secure payment processing
- Booking confirmation

## Tech Stack

### Frontend
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- React Hook Form
- Zod for validation

### Backend
- Python Flask
- Verteil NDC API Integration
- SQLAlchemy (for future database integration)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- npm or yarn

### Installation

1. Clone the repository
2. Set up the backend:
   ```bash
   cd my_flight_portal_backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd ../my_flight_portal_frontend
   npm install
   ```

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```
FLASK_APP=app.py
FLASK_ENV=development
VERTEIL_API_KEY=your_verteil_api_key
VERTEIL_API_SECRET=your_verteil_api_secret
VERTEIL_API_BASE_URL=your_verteil_api_base_url
```

### Running the Application

1. Start the backend:
   ```bash
   cd my_flight_portal_backend
   flask run
   ```

2. Start the frontend:
   ```bash
   cd my_flight_portal_frontend
   npm run dev
   ```

## Project Structure

```
FLIGHT/
├── my_flight_portal_backend/    # Flask backend
│   ├── app.py                   # Main application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── routes/                  # API routes
│   ├── services/               # Business logic
│   ├── scripts/                # Scripts for building NDC requests
│   └── instance/               # Instance-specific configuration
└── my_flight_portal_frontend/   # Next.js frontend
    ├── app/                    # App Router directory
    ├── public/                 # Static files
    └── package.json            # Frontend dependencies
```

## Development

### Backend

1. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   flask run
   ```

### Frontend

1. Install dependencies:
   ```bash
   cd my_flight_portal_frontend
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

## Testing

To run tests:

```bash
# Backend tests
pytest

# Frontend tests
npm test
```

## Backend API Documentation

### Base URL
All API endpoints are prefixed with `/api`.

### Authentication
All requests require API key authentication. Include the following headers in your requests:

```
X-API-Key: your_verteil_api_key
X-API-Secret: your_verteil_api_secret
```

### Endpoints

#### 1. Search Flights

**Endpoint:** `POST /api/flights/search`

**Request Body:**
```json
{
  "origin": "JFK",
  "destination": "LAX",
  "departure_date": "2025-06-15",
  "return_date": "2025-06-22",
  "adults": 1,
  "children": 0,
  "infants": 0,
  "cabin_class": "ECONOMY",
  "currency": "USD",
  "non_stop": false
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "OffersGroup": {
      "AirlineOffers": [
        {
          "AirlineOffer": [
            {
              "OfferID": "OFFER123",
              "Price": {
                "TotalAmount": 299.99,
                "Currency": "USD"
              },
              "FlightSegments": [
                {
                  "Origin": "JFK",
                  "Destination": "LAX",
                  "DepartureTime": "2025-06-15T08:00:00",
                  "ArrivalTime": "2025-06-15T11:00:00"
                }
              ]
            }
          ]
        }
      ]
    }
  },
  "meta": {
    "count": 1,
    "currency": "USD"
  }
}
```

#### 2. Get Flight Price

**Endpoint:** `POST /api/flights/price`

**Request Body:**
```json
{
  "airshopping_response": { ... },
  "offer_index": 0,
  "currency": "USD"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "PriceResponse": {
      "TotalPrice": {
        "TotalAmount": 299.99,
        "Currency": "USD"
      },
      "PricingInfo": { ... }
    }
  },
  "meta": {
    "currency": "USD",
    "offer_index": 0
  }
}
```

#### 3. Create Booking

**Endpoint:** `POST /api/bookings`

**Request Body:**
```json
{
  "flight_offer": { ... },
  "passengers": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "type": "ADT",
      "birth_date": "1990-01-01",
      "gender": "M",
      "passport_number": "AB123456",
      "passport_expiry": "2030-01-01",
      "passport_country": "US"
    }
  ],
  "payment": {
    "type": "CARD",
    "card_number": "4111111111111111",
    "expiry_month": "12",
    "expiry_year": "2025",
    "cvv": "123",
    "card_holder_name": "John Doe"
  },
  "contact_info": {
    "email": "john.doe@example.com",
    "phone": "+1234567890"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "booking_reference": "BOOKING123",
    "status": "CONFIRMED",
    "etickets": [
      {
        "ticket_number": "1234567890",
        "passenger_name": "John Doe",
        "status": "ISSUED"
      }
    ],
    "amount_paid": 299.99,
    "currency": "USD"
  },
  "meta": {
    "timestamp": "2025-05-27T04:32:53.123456",
    "reference": "BOOKING123"
  }
}
```

#### 4. Get Booking Details

**Endpoint:** `GET /api/bookings/:booking_reference`

**Response:**
```json
{
  "status": "success",
  "data": {
    "booking_reference": "BOOKING123",
    "status": "CONFIRMED",
    "passengers": [
      {
        "first_name": "John",
        "last_name": "Doe",
        "type": "ADT",
        "passenger_id": "PAX1"
      }
    ],
    "flights": [
      {
        "flight_number": "AA123",
        "origin": "JFK",
        "destination": "LAX",
        "departure_time": "2025-06-15T08:00:00",
        "arrival_time": "2025-06-15T11:00:00",
        "cabin_class": "ECONOMY",
        "booking_class": "Y"
      }
    ],
    "price": {
      "total_amount": 299.99,
      "currency": "USD"
    },
    "contact_info": {
      "email": "john.doe@example.com",
      "phone": "+1234567890"
    }
  },
  "meta": {
    "timestamp": "2025-05-27T04:32:53.123456",
    "reference": "BOOKING123"
  }
}
```

### Error Handling

All error responses follow this format:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field_name": "Additional error details"
    }
  },
  "meta": {
    "timestamp": "2025-05-27T04:32:53.123456"
  }
}
```

#### Common Error Codes

- `400`: Bad Request - Invalid request parameters
- `401`: Unauthorized - Invalid or missing authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `422`: Unprocessable Entity - Validation error
- `500`: Internal Server Error - Unexpected server error

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
