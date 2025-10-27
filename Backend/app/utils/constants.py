"""Application constants."""

from typing import Literal

# Trip Types
TripType = Literal["ONE_WAY", "ROUND_TRIP", "MULTI_CITY"]

# Passenger Types
PassengerType = Literal["ADT", "CHD", "INF"]

# Cabin Classes
CabinClass = Literal["Y", "C", "F", "W"]  # Economy, Business, First, Premium Economy

# Fare Types
FareType = Literal["PUBL", "PVT", "NEG", "CORP"]

# Payment Types
PaymentType = Literal["CASH", "CARD", "IATA_EASYPAY"]

# Sort Options
SortOption = Literal["PRICE", "STOP", "DEPARTURE_TIME"]

# VDC Services
VDC_SERVICES = [
    "AirShopping",
    "FlightPrice",
    "ServiceList",
    "SeatAvailability",
    "OrderCreate",
    "OrderRetrieve",
    "OrderReshop",
    "OrderChange",
    "ItinReshop",
    "OrderCancel"
]

# Supported Airlines (can be configured)
SUPPORTED_AIRLINES = [
    "AA", "AF", "BA", "DL", "EK", "KL", "LH", "QR", "UA"
]
