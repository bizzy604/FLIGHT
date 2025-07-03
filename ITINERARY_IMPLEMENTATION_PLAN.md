# Official Flight Itinerary Implementation Plan
## Rea Travels Agency - Professional Flight Itinerary System

### **Data Extraction from OrderCreate Response**

Based on analysis of `OrdercreateRS.json`, the following data points will be extracted and included in the official itinerary:

#### **1. Booking Information**
- **Order ID**: `Response.Order[0].OrderID.value` → "OPOXT8"
- **Booking Reference**: `Response.Order[0].BookingReferences.BookingReference[0].ID` → "1749041"
- **Alternative Order ID**: `Response.Order[0].BookingReferences.BookingReference[0].OtherID.value` → "KQ_OPOXT8"
- **Status**: `Response.Order[0].Status.StatusCode.Code` → "OPENED"
- **Issue Date**: `Response.TicketDocInfos.TicketDocInfo[0].TicketDocument[0].DateOfIssue` → "2025-06-03T00:00:00.000"

#### **2. Passenger Information**
For each passenger in `Response.Passengers.Passenger[]`:
- **Full Name**: `Name.Title` + `Name.Given[0].value` + `Name.Surname.value`
  - Example: "MR AMONI KEVIN", "MRS REBECCA MIANO", "MSTR EGOLE BIZZY", "MSTR EGOLE DAVID"
- **Passenger Type**: `PTC.value` → "ADT" (Adult), "CHD" (Child), "INF" (Infant)
- **Birth Date**: `Age.BirthDate.value`
- **Document Type**: `PassengerIDInfo.PassengerDocument[0].Type` → "PT" (Passport)
- **Document Number**: `PassengerIDInfo.PassengerDocument[0].ID`
- **Document Expiry**: `PassengerIDInfo.PassengerDocument[0].DateOfExpiration`
- **Country of Issuance**: `PassengerIDInfo.PassengerDocument[0].CountryOfIssuance`
- **Ticket Number**: From `Response.TicketDocInfos.TicketDocInfo[].TicketDocument[0].TicketDocNbr`
  - PAX2: "7062306748902"
  - PAX4: "7062306748903" 
  - PAX5: "7062306748904"
  - PAX3: "7062306748905"

#### **3. Contact Information**
From primary passenger's contact details:
- **Email**: `Contacts.Contact[0].EmailContact.Address.value` → "KEVINAMONI20@EXAMPLE.COM"
- **Phone**: `Contacts.Contact[0].PhoneContact.Number[0].CountryCode` + `Number[0].value` → "+254700000000"

#### **4. Flight Details**
For each flight segment in `Response.Order[0].OrderItems.OrderItem[0].FlightItem.OriginDestination[]`:

**Outbound Flight (SEG1)**:
- **Flight Number**: `Flight[0].MarketingCarrier.AirlineID.value` + `FlightNumber.value` → "KQ 112"
- **Airline**: `Flight[0].MarketingCarrier.Name` → "Kenya Airways"
- **Aircraft**: `Flight[0].Equipment.Name` → "788" (Boeing 787-8)
- **Departure**: 
  - Airport: `Flight[0].Departure.AirportCode.value` → "NBO"
  - Date: `Flight[0].Departure.Date` → "2025-06-06T23:50:00.000"
  - Time: `Flight[0].Departure.Time` → "23:50:00"
  - Terminal: `Flight[0].Departure.Terminal.Name` → "1A"
- **Arrival**:
  - Airport: `Flight[0].Arrival.AirportCode.value` → "CDG"
  - Date: `Flight[0].Arrival.Date` → "2025-06-07T07:30:00.000"
  - Time: `Flight[0].Arrival.Time` → "07:30:00"
  - Terminal: `Flight[0].Arrival.Terminal.Name` → "2E"
- **Duration**: `Flight[0].Details.FlightDuration.Value` → "PT8H40M"
- **Class**: `Flight[0].ClassOfService.MarketingName.value` → "BUSINESS"

**Return Flight (SEG2)**:
- **Flight Number**: "KQ 113"
- **Departure**: CDG Terminal 2E at 10:55:00 on 2025-06-12
- **Arrival**: NBO Terminal 1A at 20:20:00 on 2025-06-12
- **Duration**: "PT8H25M"
- **Class**: "BUSINESS"

#### **5. Pricing Information**
- **Total Amount**: `Response.Order[0].TotalOrderPrice.SimpleCurrencyPrice.value` → "534993"
- **Currency**: `Response.Order[0].TotalOrderPrice.SimpleCurrencyPrice.Code` → "INR"
- **Payment Method**: `Response.Payments.Payment[0].Type.Code` → "CA" (Cash)

#### **6. Agency Information**
- **Agency Name**: From discount owner → "Magellan Travel Services (P) Ltd."
- **Discount Applied**: "ReaDiscount" (5% discount)

#### **7. Baggage Allowance**
From ticket coupon information:
- **Checked Baggage**: `TicketDocument[0].CouponInfo[].AddlBaggageInfo.AllowableBag[0].Number` → 2 pieces per segment

### **Implementation Phases**

#### **Phase 1: Data Transformation Service (45 minutes)**
Create `utils/itinerary-data-transformer.ts` to:
- Extract all data points from OrderCreate response
- Handle multiple passengers with different types
- Format dates, times, and currencies
- Map airport codes to full names
- Calculate total journey time

#### **Phase 2: Itinerary Components (60 minutes)**
Create modular React components:
- `components/itinerary/OfficialItinerary.tsx` - Main container
- `components/itinerary/ItineraryHeader.tsx` - Agency branding & booking info
- `components/itinerary/PassengerSection.tsx` - Passenger details with ticket numbers
- `components/itinerary/FlightSection.tsx` - Flight details for outbound/return
- `components/itinerary/ImportantInfo.tsx` - Check-in, baggage, terms

#### **Phase 3: PDF Generation (45 minutes)**
- Backend endpoint `/api/itinerary/generate-pdf`
- Use Puppeteer for high-quality PDF generation
- A4 page format with proper margins
- Professional styling for business use

#### **Phase 4: Frontend Integration (30 minutes)**
- Replace boarding pass download with official itinerary
- Update payment confirmation page
- Maintain existing share/email functionality
- Add loading states and error handling

#### **Phase 5: Testing & Refinement (30 minutes)**
- Test with provided OrderCreate response
- Verify all data extraction
- Test PDF generation quality
- Ensure responsive design

### **Key Features**
- ✅ Professional business-grade design
- ✅ Complete passenger information with ticket numbers
- ✅ Detailed flight information for round-trip
- ✅ Agency branding with Rea Travels logo
- ✅ Total pricing (no breakdown as requested)
- ✅ High-quality PDF download
- ✅ Responsive design for all devices
- ✅ Error handling and data validation

### **Technical Stack**
- **Frontend**: React/TypeScript components
- **PDF Generation**: Puppeteer (already installed)
- **Styling**: Tailwind CSS for professional appearance
- **Data Source**: OrderCreate response from session/database

### **Implementation Status**
- [x] Phase 1: Data Transformation Service - IN PROGRESS
- [ ] Phase 2: Itinerary Components
- [ ] Phase 3: PDF Generation
- [ ] Phase 4: Frontend Integration
- [ ] Phase 5: Testing & Refinement
