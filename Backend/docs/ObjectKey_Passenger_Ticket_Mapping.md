# ObjectKey-Based Passenger-Ticket Mapping

## Overview

This document explains the improved ObjectKey-based approach for mapping passengers to their corresponding ticket numbers in the official itinerary generation system.

## Problem with Previous Approach

The previous implementation used **index-based mapping**, which assumed that:
- `passengers_data[0]` corresponds to `ticket_doc_infos[0]`
- `passengers_data[1]` corresponds to `ticket_doc_infos[1]`
- And so on...

### Issues with Index-Based Mapping:
1. **Fragile**: Relies on array ordering which may not be guaranteed
2. **No explicit linking**: No clear relationship between passenger and ticket
3. **Error-prone**: Array length mismatches could cause incorrect mappings

## New ObjectKey-Based Approach

The improved implementation uses **explicit ObjectKey references** to create reliable passenger-ticket mappings.

### Data Structure Analysis

From the OrderCreateRs.json test data, we can see the structure:

#### Passengers Section:
```json
{
  "Passengers": {
    "Passenger": [
      {
        "ObjectKey": "PAX1",
        "Name": { "Title": "MR", "Given": [{"value": "AMONI"}], "Surname": {"value": "KEVIN"} },
        "PTC": {"value": "ADT"}
      },
      {
        "ObjectKey": "PAX2", 
        "Name": { "Title": "MRS", "Given": [{"value": "REBECCA"}], "Surname": {"value": "MIANO"} },
        "PTC": {"value": "ADT"}
      }
      // ... more passengers
    ]
  }
}
```

#### Ticket Documents Section:
```json
{
  "TicketDocInfos": {
    "TicketDocInfo": [
      {
        "TicketDocument": [{"TicketDocNbr": "0572332934667"}],
        "PassengerReference": ["PAX4"],
        "IssuingAirlineInfo": {"AirlineName": "AF"}
      },
      {
        "TicketDocument": [{"TicketDocNbr": "0572332934664"}],
        "PassengerReference": ["PAX3"],
        "IssuingAirlineInfo": {"AirlineName": "AF"}
      }
      // ... more tickets
    ]
  }
}
```

### Mapping Algorithm

1. **Create Ticket Mapping Dictionary**: Build a lookup table from PassengerReference to ticket information
2. **Iterate Through Passengers**: For each passenger, use their ObjectKey to find the corresponding ticket
3. **Extract Ticket Information**: Retrieve ticket number, issue date, and airline information

### Implementation

#### Backend Implementation (Python)
```python
# Create a mapping of ObjectKey to ticket information
ticket_mapping = {}
for ticket_doc in ticket_doc_infos:
    passenger_refs = ticket_doc.get('PassengerReference', [])
    ticket_documents = ticket_doc.get('TicketDocument', [])
    
    for passenger_ref in passenger_refs:
        if ticket_documents:
            ticket_mapping[passenger_ref] = {
                'ticketNumber': ticket_documents[0].get('TicketDocNbr', 'N/A'),
                'dateOfIssue': ticket_documents[0].get('DateOfIssue', ''),
                'issuingAirline': ticket_doc.get('IssuingAirlineInfo', {}).get('AirlineName', '')
            }

# Map passengers to tickets using ObjectKey
for passenger in passengers_data:
    passenger_object_key = passenger.get('ObjectKey', f'PAX{index + 1}')
    ticket_info = ticket_mapping.get(passenger_object_key, {})
    ticket_number = ticket_info.get('ticketNumber', 'N/A')
```

#### Frontend Implementation (TypeScript)
```typescript
// Create a mapping of ObjectKey to ticket information
const ticketMapping: Record<string, { ticketNumber: string; dateOfIssue: string; issuingAirline: string }> = {};
ticketDocInfos.forEach((ticketDoc: any) => {
  const passengerRefs = ticketDoc.PassengerReference || [];
  const ticketDocuments = ticketDoc.TicketDocument || [];
  
  passengerRefs.forEach((passengerRef: string) => {
    if (ticketDocuments.length > 0) {
      ticketMapping[passengerRef] = {
        ticketNumber: ticketDocuments[0].TicketDocNbr || 'N/A',
        dateOfIssue: ticketDocuments[0].DateOfIssue || '',
        issuingAirline: ticketDoc.IssuingAirlineInfo?.AirlineName || ''
      };
    }
  });
});

// Map passengers to tickets using ObjectKey
const passengerObjectKey = passenger.ObjectKey || `PAX${index + 1}`;
const ticketInfo = ticketMapping[passengerObjectKey] || {};
const ticketNumber = ticketInfo.ticketNumber || 'N/A';
```

## Test Results

Using the OrderCreateRs.json test data with 4 passengers:

| ObjectKey | Passenger Name | Ticket Number | Mapping Result |
|-----------|----------------|---------------|----------------|
| PAX1 | MR AMONI KEVIN | 0572332934665 | ✅ CORRECT |
| PAX2 | MRS REBECCA MIANO | 0572332934666 | ✅ CORRECT |
| PAX3 | MSTR EGOLE DAVID | 0572332934664 | ✅ CORRECT |
| PAX4 | MSTR EGOLE BIZZY | 0572332934667 | ✅ CORRECT |

## Benefits of ObjectKey-Based Mapping

1. **Reliable**: Uses explicit references instead of array positioning
2. **Robust**: Handles cases where arrays might be in different orders
3. **Explicit**: Clear relationship between passenger and ticket
4. **Maintainable**: Easier to debug and understand
5. **Future-proof**: Works with various API response structures

## Files Modified

- `Backend/routes/itinerary_routes.py` - Updated extract_itinerary_data function
- `Frontend/utils/itinerary-data-transformer.ts` - Updated transformOrderCreateToItinerary function

## Testing

Two test scripts were created to validate the implementation:
- `Backend/test_objectkey_mapping.py` - Tests backend implementation
- `Backend/test_frontend_transformer.py` - Tests frontend logic

Both tests pass with 100% accuracy using the OrderCreateRs.json test data.
