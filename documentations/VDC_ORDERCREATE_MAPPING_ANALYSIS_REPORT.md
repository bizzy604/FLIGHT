# VDC OrderCreate Payload Mapping Analysis Report

## Executive Summary

This comprehensive report analyzes the precise mapping patterns used to construct VDC OrderCreate payloads from FlightPrice, SeatAvailability, and ServiceList responses. The analysis is based on the official VDC API documentation and real sample payloads to ensure accuracy and eliminate guesswork.

## Data Flow Overview

The OrderCreate payload construction follows a three-source mapping pattern:

1. **FlightPriceRS** → Core flight offer and pricing data
2. **SeatAvailabilityRS** → Seat selection and pricing data  
3. **ServiceListRS** → Ancillary services and pricing data

All three sources contribute to the final OrderCreateRQ payload with specific mapping rules for each data element.

## Detailed Mapping Analysis

### 1. FlightPriceRS to OrderCreateRQ Mapping

#### Core Offer Mapping
| **Source Path (FlightPriceRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `PricedFlightOffers/PricedFlightOffer/OfferID/value` | `Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/value` | Direct |
| `PricedFlightOffers/PricedFlightOffer/OfferID/Owner` | `Query/OrderItems/ShoppingResponse/Owner` | Direct |
| `PricedFlightOffers/PricedFlightOffer/OfferID/Owner` | `Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/Owner` | Direct |
| `ShoppingResponseID/ResponseID/value` | `Query/OrderItems/ShoppingResponse/ResponseID/value` | Direct |

#### Pricing Data Mapping
| **Source Path (FlightPriceRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/BaseAmount` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/BaseAmount` | Direct |
| `PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/Taxes` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/Taxes` | Direct |
| `PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID` | `Query/OrderItems/OfferItem/OfferItemID/value` | Direct |

#### Flight Segment Mapping
| **Source Path (FlightPriceRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `DataLists/FlightSegmentList/FlightSegment/SegmentKey` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/SegmentKey` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Departure/AirportCode/value` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/Departure/Date` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Departure/Date` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/Departure/Time` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Departure/Time` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Arrival/AirportCode/value` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/Date` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Arrival/Date` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/Time` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Arrival/Time` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/AirlineID/value` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/MarketingCarrier/AirlineID/value` | Direct |
| `DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/FlightNumber/value` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/MarketingCarrier/FlightNumber/value` | Direct |

#### Traveler Data Mapping
| **Source Path (FlightPriceRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey` | `Query/Passengers/Passenger/ObjectKey` | Direct |
| `DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value` | `Query/Passengers/Passenger/PTC/value` | Direct |
| `PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedTraveler/TravelerReferences` | `Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/refs` | Direct |

#### Fare Data Mapping
| **Source Path (FlightPriceRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `DataLists/FareList/FareGroup/ListKey` | `Query/DataLists/FareList/FareGroup/ListKey` | Direct |
| `DataLists/FareList/FareGroup/Fare/FareCode/Code` | `Query/DataLists/FareList/FareGroup/Fare/FareCode/Code` | Direct |
| `DataLists/FareList/FareGroup/FareBasisCode/Code` | `Query/DataLists/FareList/FareGroup/FareBasisCode/Code` | Direct |

### 2. SeatAvailabilityRS to OrderCreateRQ Mapping

#### Seat Service Mapping
| **Source Path (SeatAvailabilityRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|---------------------------------------|--------------------------------------|------------------|
| `Services/Service/ObjectKey` | `Query/OrderItems/OfferItem/OfferItemID/value` | Direct |
| `Services/Service/Price/Total` | `Query/OrderItems/OfferItem/OfferItemType/SeatItem/Price/Total` | Direct |
| `Services/Service/Associations/Flight/.../SegmentReferences/value` | `Query/OrderItems/OfferItem/OfferItemType/SeatItem/SeatAssociation/SegmentReferences/value` | Direct |
| `Services/Service/Associations/Traveler/TravelerReferences` | `Query/OrderItems/OfferItem/OfferItemType/SeatItem/SeatAssociation/TravelerReference` | Direct |

#### Seat Location Mapping
| **Source Path (SeatAvailabilityRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|---------------------------------------|--------------------------------------|------------------|
| `DataLists/SeatList/Seats/Location/Column` | `Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Column` | Direct |
| `DataLists/SeatList/Seats/Location/Row/Number/value` | `Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Row/Number/value` | Direct |
| `DataLists/SeatList/Seats/Location/Characteristics/Characteristic` | `Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Characteristics/Characteristic` | Direct |

#### Reference Mapping
| **Source Path (SeatAvailabilityRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|---------------------------------------|--------------------------------------|------------------|
| `ShoppingResponseID/ResponseID/value` | `Query/OrderItems/OfferItem/OfferItemID/refs` | Array Addition |
| `Services/Service/ObjectKey` | `Query/OrderItems/OfferItem/OfferItemID/refs` | Array Addition |

### 3. ServiceListRS to OrderCreateRQ Mapping

#### Service Identification Mapping
| **Source Path (ServiceListRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `Services/Service/ServiceID/ObjectKey` | `Query/OrderItems/OfferItem/OfferItemID/value` | Direct |
| `Services/Service/ServiceID/Owner` | `Query/OrderItems/OfferItem/OfferItemID/Owner` | Direct |
| `Services/Service/ServiceID/value` | `Query/OrderItems/OfferItem/OfferItemType/OtherItem/refs` | Array Addition |

#### Service Pricing Mapping
| **Source Path (ServiceListRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `Services/Service/Price/Total` | `Query/OrderItems/OfferItem/OfferItemType/OtherItem/Price/SimpleCurrencyPrice` | Direct |
| `Services/Service/Price/Total/Code` | `Query/OrderItems/OfferItem/OfferItemType/OtherItem/Price/SimpleCurrencyPrice/Code` | Direct |

#### Service Association Mapping
| **Source Path (ServiceListRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `Services/Service/Associations/Traveler/TravelerReferences` | `Query/OrderItems/OfferItem/OfferItemType/OtherItem/refs` | Array Addition |
| `Services/Service/Associations/Flight/.../SegmentReferences/value` | `Query/OrderItems/OfferItem/OfferItemType/OtherItem/refs` | Array Addition |

#### Reference Chain Mapping
| **Source Path (ServiceListRS)** | **Destination Path (OrderCreateRQ)** | **Mapping Type** |
|----------------------------------|--------------------------------------|------------------|
| `ShoppingResponseID/ResponseID/value` | `Query/OrderItems/OfferItem/OfferItemID/refs` | Array Addition |
| `Services/Service/ObjectKey` | `Query/OrderItems/OfferItem/OfferItemID/refs` | Array Addition |

## Critical Mapping Patterns

### 1. Reference Chain Construction

The most critical pattern is the **reference chain construction** for OfferItemID refs:

```
OrderCreateRQ.OfferItem.OfferItemID.refs = [
    FlightPriceRS.PricedFlightOffers.PricedFlightOffer.OfferID.value,
    FlightPriceRS.ShoppingResponseID.ResponseID.value
]
```

### 2. Service Item Reference Construction

For service items, the reference chain includes:
```
OrderCreateRQ.OfferItem.OfferItemType.OtherItem.refs = [
    TravelerReference,
    SegmentReference, 
    ServiceID
]
```

### 3. Seat Item Reference Construction

For seat items, the reference chain includes:
```
OrderCreateRQ.OfferItem.OfferItemType.SeatItem.SeatAssociation = [
    {
        SegmentReferences: [SegmentKey],
        TravelerReference: TravelerKey
    }
]
```

## Data Structure Transformations

### 1. Price Structure Transformation

**FlightPriceRS Price Structure:**
```json
{
  "PriceDetail": {
    "BaseAmount": { "value": 64000, "Code": "INR" },
    "Taxes": { "Total": { "value": 16000, "Code": "INR" } }
  }
}
```

**OrderCreateRQ Price Structure:**
```json
{
  "Price": {
    "BaseAmount": { "value": 64000, "Code": "INR" },
    "Taxes": { "Total": { "value": 16000, "Code": "INR" } }
  }
}
```

### 2. Service Price Transformation

**ServiceListRS Price Structure:**
```json
{
  "Price": [
    {
      "Total": { "value": 20837, "Code": "INR" }
    }
  ]
}
```

**OrderCreateRQ Service Price Structure:**
```json
{
  "Price": {
    "SimpleCurrencyPrice": { "value": 20837, "Code": "INR" }
  }
}
```

### 3. Seat Price Transformation

**SeatAvailabilityRS Price Structure:**
```json
{
  "Price": [
    {
      "Total": { "value": 11920, "Code": "INR" }
    }
  ]
}
```

**OrderCreateRQ Seat Price Structure:**
```json
{
  "Price": {
    "Total": { "value": 11920, "Code": "INR" }
  }
}
```

## Validation Rules

### 1. Mandatory Field Validation

**FlightPriceRS Mandatory Fields:**
- `PricedFlightOffers.PricedFlightOffer.OfferID.value`
- `PricedFlightOffers.PricedFlightOffer.OfferID.Owner`
- `ShoppingResponseID.ResponseID.value`
- `DataLists.FlightSegmentList.FlightSegment.SegmentKey`

**SeatAvailabilityRS Mandatory Fields:**
- `Services.Service.ObjectKey`
- `Services.Service.Price.Total`
- `Services.Service.Associations.Traveler.TravelerReferences`

**ServiceListRS Mandatory Fields:**
- `Services.Service.ServiceID.value`
- `Services.Service.ServiceID.Owner`
- `Services.Service.Price.Total`

### 2. Reference Integrity Validation

All reference chains must maintain integrity:
- Traveler references must exist in all associated items
- Segment references must match across all items
- Service references must be consistent

### 3. Price Consistency Validation

- All prices must have consistent currency codes
- Price totals must match between source and destination
- PricedInd flags must be properly set

## Implementation Guidelines

### 1. Mapping Order

1. **Primary Flight Item**: Map from FlightPriceRS first
2. **Seat Items**: Map from SeatAvailabilityRS
3. **Service Items**: Map from ServiceListRS
4. **DataLists**: Consolidate from all sources
5. **References**: Build reference chains last

### 2. Error Handling

- Validate all mandatory fields before mapping
- Check reference integrity after mapping
- Verify price consistency across all items
- Handle missing optional fields gracefully

### 3. Performance Considerations

- Cache frequently accessed data structures
- Use efficient JSON parsing libraries
- Minimize deep object traversal
- Implement proper error logging

## Conclusion

The VDC OrderCreate payload construction follows precise mapping patterns with no room for guesswork. Each data element has a specific source path and destination path with defined transformation rules. The critical success factors are:

1. **Precise Path Mapping**: Every field has an exact source-to-destination path
2. **Reference Chain Integrity**: All references must be properly linked
3. **Price Structure Consistency**: Price data must maintain structural integrity
4. **Validation Completeness**: All mandatory fields must be present and valid

This analysis provides the foundation for implementing accurate OrderCreate payload generation with zero tolerance for mapping errors.
