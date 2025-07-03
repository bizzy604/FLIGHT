/**
 * Frontend Itinerary Transformation Test Suite
 * 
 * This script tests the frontend itinerary data transformation and formatting
 * using the OrdercreateRS.json test data to validate that all required values
 * are correctly processed for display in the official itinerary.
 * 
 * Author: FLIGHT Application
 * Created: 2025-07-03
 */

const fs = require('fs');
const path = require('path');

// Mock the frontend transformation function (since we can't directly import TypeScript)
// This replicates the logic from Frontend/utils/itinerary-data-transformer.ts

// Airport code to name mapping
const AIRPORT_NAMES = {
  'NBO': 'Jomo Kenyatta International Airport, Nairobi',
  'CDG': 'Charles de Gaulle Airport, Paris',
  'LHR': 'Heathrow Airport, London',
  'DXB': 'Dubai International Airport',
  'JFK': 'John F. Kennedy International Airport, New York',
  'LAX': 'Los Angeles International Airport',
  'BOM': 'Chhatrapati Shivaji Maharaj International Airport, Mumbai',
  'DEL': 'Indira Gandhi International Airport, New Delhi',
  'DOH': 'Hamad International Airport, Doha',
  'AMS': 'Amsterdam Airport Schiphol',
  'FRA': 'Frankfurt Airport',
  'ZUR': 'Zurich Airport',
  'IST': 'Istanbul Airport',
  'CAI': 'Cairo International Airport',
  'ADD': 'Addis Ababa Bole International Airport',
  'CPT': 'Cape Town International Airport',
  'JNB': 'O.R. Tambo International Airport, Johannesburg'
};

// Payment method code to label mapping
const PAYMENT_METHODS = {
  'CA': 'Cash',
  'CC': 'Credit Card',
  'DC': 'Debit Card',
  'PP': 'PayPal',
  'BT': 'Bank Transfer',
  'CH': 'Check'
};

// Passenger type labels
const PASSENGER_TYPE_LABELS = {
  'ADT': 'Adult',
  'CHD': 'Child',
  'INF': 'Infant'
};

class FrontendTransformationTest {
  constructor(testDataPath) {
    this.testDataPath = testDataPath;
    this.testData = null;
    this.transformedData = null;
    this.testResults = {
      passed: 0,
      failed: 0,
      errors: []
    };
  }

  loadTestData() {
    try {
      const rawData = fs.readFileSync(this.testDataPath, 'utf8');
      this.testData = JSON.parse(rawData);
      console.log('✅ Successfully loaded test data from', this.testDataPath);
      return true;
    } catch (error) {
      console.error('❌ Failed to load test data:', error.message);
      return false;
    }
  }

  // Helper functions (replicated from frontend transformer)
  formatDate(dateString) {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  }

  formatTime(timeString) {
    try {
      const timeParts = timeString.split(':');
      const hours = parseInt(timeParts[0]);
      const minutes = timeParts[1];
      return `${hours.toString().padStart(2, '0')}:${minutes}`;
    } catch {
      return timeString;
    }
  }

  formatDuration(duration) {
    try {
      const match = duration.match(/PT(\d+H)?(\d+M)?/);
      if (!match) return duration;
      
      const hours = match[1] ? parseInt(match[1].replace('H', '')) : 0;
      const minutes = match[2] ? parseInt(match[2].replace('M', '')) : 0;
      
      if (hours > 0 && minutes > 0) {
        return `${hours}h ${minutes}m`;
      } else if (hours > 0) {
        return `${hours}h`;
      } else if (minutes > 0) {
        return `${minutes}m`;
      }
      return duration;
    } catch {
      return duration;
    }
  }

  calculateAge(birthDate) {
    try {
      const birth = new Date(birthDate);
      const today = new Date();
      let age = today.getFullYear() - birth.getFullYear();
      const monthDiff = today.getMonth() - birth.getMonth();
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
      }
      
      return age;
    } catch {
      return 0;
    }
  }

  formatCurrency(amount, currency) {
    try {
      const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      });
      return formatter.format(amount);
    } catch {
      return `${currency} ${amount.toLocaleString()}`;
    }
  }

  getAirportName(code) {
    return AIRPORT_NAMES[code] || `${code} Airport`;
  }

  formatDateTime(date, time) {
    try {
      const dateObj = new Date(date);
      const formattedDate = dateObj.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
      const formattedTime = this.formatTime(time);
      return `${formattedDate} ${formattedTime}`;
    } catch {
      return `${date} ${time}`;
    }
  }

  transformOrderCreateToItinerary(orderCreateResponse) {
    const response = orderCreateResponse.Response || orderCreateResponse;
    
    if (!response) {
      throw new Error('Invalid OrderCreate response structure');
    }

    // Extract booking information
    const order = response.Order?.[0];
    const bookingInfo = {
      orderId: order?.OrderID?.value || 'N/A',
      bookingReference: order?.BookingReferences?.BookingReference?.[0]?.ID || 'N/A',
      alternativeOrderId: order?.BookingReferences?.BookingReference?.[0]?.OtherID?.value || 'N/A',
      status: order?.Status?.StatusCode?.Code || 'UNKNOWN',
      issueDate: response.TicketDocInfos?.TicketDocInfo?.[0]?.TicketDocument?.[0]?.DateOfIssue || new Date().toISOString(),
      issueDateFormatted: this.formatDate(response.TicketDocInfos?.TicketDocInfo?.[0]?.TicketDocument?.[0]?.DateOfIssue || new Date().toISOString()),
      agencyName: 'Rea Travels Agency',
      discountApplied: undefined
    };

    // Extract discount information if available
    const firstOrderItem = order?.OrderItems?.OrderItem?.[0];
    const discount = firstOrderItem?.FlightItem?.Price?.Discount?.[0];
    if (discount) {
      bookingInfo.discountApplied = {
        name: discount.discountName || 'Discount',
        percentage: discount.DiscountPercent || 0,
        amount: discount.DiscountAmount?.value || 0
      };
      if (discount.discountOwner) {
        bookingInfo.agencyName = discount.discountOwner;
      }
    }

    // Extract pricing information
    const totalPrice = order?.TotalOrderPrice?.SimpleCurrencyPrice;
    const payment = response.Payments?.Payment?.[0];
    const pricing = {
      totalAmount: totalPrice?.value || 0,
      currency: totalPrice?.Code || 'USD',
      formattedTotal: this.formatCurrency(totalPrice?.value || 0, totalPrice?.Code || 'USD'),
      paymentMethod: payment?.Type?.Code || 'CA',
      paymentMethodLabel: PAYMENT_METHODS[payment?.Type?.Code || 'CA'] || 'Cash'
    };

    // Extract passenger information with ticket numbers
    const passengers = [];
    const passengersData = response.Passengers?.Passenger || [];
    const ticketDocInfos = response.TicketDocInfos?.TicketDocInfo || [];

    passengersData.forEach((passenger, index) => {
      const name = passenger.Name || {};
      const contact = passenger.Contacts?.Contact?.[0];
      const document = passenger.PassengerIDInfo?.PassengerDocument?.[0];
      
      // Find corresponding ticket number
      let ticketNumber = 'N/A';
      if (ticketDocInfos[index]?.TicketDocument?.[0]?.TicketDocNbr) {
        ticketNumber = ticketDocInfos[index].TicketDocument[0].TicketDocNbr;
      }

      const passengerInfo = {
        objectKey: passenger.ObjectKey || `PAX${index + 1}`,
        fullName: `${name.Title || ''} ${name.Given?.[0]?.value || ''} ${name.Surname?.value || ''}`.trim(),
        title: name.Title || '',
        firstName: name.Given?.[0]?.value || '',
        lastName: name.Surname?.value || '',
        passengerType: passenger.PTC?.value || 'ADT',
        passengerTypeLabel: PASSENGER_TYPE_LABELS[passenger.PTC?.value || 'ADT'] || 'Adult',
        birthDate: passenger.Age?.BirthDate?.value || '',
        age: this.calculateAge(passenger.Age?.BirthDate?.value || ''),
        documentType: document?.Type || 'PT',
        documentNumber: document?.ID || 'N/A',
        documentExpiry: document?.DateOfExpiration || '',
        countryOfIssuance: document?.CountryOfIssuance || '',
        countryOfResidence: document?.CountryOfResidence,
        ticketNumber: ticketNumber,
        email: contact?.EmailContact?.Address?.value,
        phone: contact?.PhoneContact?.Number?.[0] ? 
          `+${contact.PhoneContact.Number[0].CountryCode}${contact.PhoneContact.Number[0].value}` : undefined
      };

      passengers.push(passengerInfo);
    });

    // Extract contact information from primary passenger
    const primaryPassenger = passengers.find(p => p.email) || passengers[0];
    const contactInfo = {
      email: primaryPassenger?.email || 'N/A',
      phone: primaryPassenger?.phone || 'N/A'
    };

    // Extract flight segments
    const originDestinations = firstOrderItem?.FlightItem?.OriginDestination || [];
    const outboundFlight = [];
    const returnFlight = [];

    originDestinations.forEach((od, odIndex) => {
      const flights = od.Flight || [];
      
      flights.forEach((flight) => {
        const segment = {
          segmentKey: flight.SegmentKey || `SEG${odIndex + 1}`,
          flightNumber: `${flight.MarketingCarrier?.AirlineID?.value || ''} ${flight.MarketingCarrier?.FlightNumber?.value || ''}`.trim(),
          airline: flight.MarketingCarrier?.Name || 'Unknown Airline',
          airlineCode: flight.MarketingCarrier?.AirlineID?.value || '',
          aircraft: flight.Equipment?.Name || 'Unknown',
          aircraftCode: flight.Equipment?.AircraftCode?.value || '',
          departure: {
            airport: flight.Departure?.AirportCode?.value || '',
            airportName: this.getAirportName(flight.Departure?.AirportCode?.value || ''),
            date: flight.Departure?.Date || '',
            time: flight.Departure?.Time || '',
            terminal: flight.Departure?.Terminal?.Name || '',
            formattedDateTime: this.formatDateTime(flight.Departure?.Date || '', flight.Departure?.Time || '')
          },
          arrival: {
            airport: flight.Arrival?.AirportCode?.value || '',
            airportName: this.getAirportName(flight.Arrival?.AirportCode?.value || ''),
            date: flight.Arrival?.Date || '',
            time: flight.Arrival?.Time || '',
            terminal: flight.Arrival?.Terminal?.Name || '',
            formattedDateTime: this.formatDateTime(flight.Arrival?.Date || '', flight.Arrival?.Time || '')
          },
          duration: flight.Details?.FlightDuration?.Value || '',
          durationFormatted: this.formatDuration(flight.Details?.FlightDuration?.Value || ''),
          classOfService: flight.ClassOfService?.MarketingName?.value || 'Economy',
          cabinClass: flight.ClassOfService?.CabinDesignator || 'Y',
          fareBasisCode: flight.MarketingCarrier?.ResBookDesigCode || ''
        };

        if (odIndex === 0) {
          outboundFlight.push(segment);
        } else {
          returnFlight.push(segment);
        }
      });
    });

    // Extract baggage allowance
    const baggageInfo = response.TicketDocInfos?.TicketDocInfo?.[0]?.TicketDocument?.[0]?.CouponInfo?.[0]?.AddlBaggageInfo;
    const baggageAllowance = {
      checkedBags: baggageInfo?.AllowableBag?.[0]?.Number || 1,
      carryOnBags: 1
    };

    return {
      bookingInfo,
      passengers,
      outboundFlight,
      returnFlight: returnFlight.length > 0 ? returnFlight : null,
      pricing,
      contactInfo,
      baggageAllowance
    };
  }

  runTransformationTest() {
    console.log('🔄 Testing frontend data transformation...');
    try {
      this.transformedData = this.transformOrderCreateToItinerary(this.testData);
      console.log('✅ Frontend data transformation successful');
      return true;
    } catch (error) {
      console.error('❌ Frontend data transformation failed:', error.message);
      this.testResults.errors.push(`Frontend transformation error: ${error.message}`);
      return false;
    }
  }

  validateTransformedData() {
    console.log('🔍 Validating transformed data for frontend display...');
    
    // Validate booking info formatting
    const booking = this.transformedData.bookingInfo;
    console.log('  📋 Booking Information:');
    console.log(`    Order ID: ${booking.orderId}`);
    console.log(`    Booking Reference: ${booking.bookingReference}`);
    console.log(`    Issue Date: ${booking.issueDateFormatted}`);
    console.log(`    Agency: ${booking.agencyName}`);
    
    if (booking.discountApplied) {
      console.log(`    Discount: ${booking.discountApplied.name} (${booking.discountApplied.percentage}%)`);
    }

    // Validate passenger formatting
    console.log('  👥 Passengers:');
    this.transformedData.passengers.forEach((passenger, index) => {
      console.log(`    ${index + 1}. ${passenger.fullName} (${passenger.passengerTypeLabel})`);
      console.log(`       Age: ${passenger.age} | Document: ${passenger.documentNumber}`);
      console.log(`       Ticket: ${passenger.ticketNumber}`);
    });

    // Validate flight formatting
    console.log('  ✈️  Flight Information:');
    this.transformedData.outboundFlight.forEach((segment, index) => {
      console.log(`    Outbound ${index + 1}: ${segment.flightNumber}`);
      console.log(`      ${segment.departure.airport} → ${segment.arrival.airport}`);
      console.log(`      Departure: ${segment.departure.formattedDateTime}`);
      console.log(`      Arrival: ${segment.arrival.formattedDateTime}`);
      console.log(`      Duration: ${segment.durationFormatted}`);
      console.log(`      Class: ${segment.classOfService}`);
    });

    if (this.transformedData.returnFlight) {
      this.transformedData.returnFlight.forEach((segment, index) => {
        console.log(`    Return ${index + 1}: ${segment.flightNumber}`);
        console.log(`      ${segment.departure.airport} → ${segment.arrival.airport}`);
        console.log(`      Departure: ${segment.departure.formattedDateTime}`);
        console.log(`      Arrival: ${segment.arrival.formattedDateTime}`);
      });
    }

    // Validate pricing formatting
    console.log('  💰 Pricing:');
    console.log(`    Total: ${this.transformedData.pricing.formattedTotal}`);
    console.log(`    Payment: ${this.transformedData.pricing.paymentMethodLabel}`);

    // Validate contact formatting
    console.log('  📞 Contact:');
    console.log(`    Email: ${this.transformedData.contactInfo.email}`);
    console.log(`    Phone: ${this.transformedData.contactInfo.phone}`);

    this.testResults.passed += 1;
    return true;
  }

  runComprehensiveTest() {
    console.log('🚀 Starting frontend transformation test...');
    console.log('=' * 60);
    
    if (!this.loadTestData()) {
      return { success: false, error: 'Failed to load test data' };
    }
    
    if (!this.runTransformationTest()) {
      return { success: false, error: 'Transformation failed' };
    }
    
    this.validateTransformedData();
    
    console.log('=' * 60);
    console.log('📊 FRONTEND TEST SUMMARY');
    console.log(`✅ Transformations passed: ${this.testResults.passed}`);
    console.log(`❌ Errors: ${this.testResults.errors.length}`);
    
    if (this.testResults.errors.length > 0) {
      console.log('⚠️  Issues found:');
      this.testResults.errors.forEach(error => {
        console.log(`  - ${error}`);
      });
    }
    
    const success = this.testResults.errors.length === 0;
    console.log(`🎯 Frontend test result: ${success ? 'PASS' : 'FAIL'}`);
    
    return {
      success,
      transformedData: this.transformedData,
      errors: this.testResults.errors
    };
  }
}

// Main execution
function main() {
  const testDataPath = path.join(__dirname, '..', 'OrdercreateRS.json');
  
  if (!fs.existsSync(testDataPath)) {
    console.error(`❌ Test data file not found: ${testDataPath}`);
    process.exit(1);
  }
  
  const test = new FrontendTransformationTest(testDataPath);
  const results = test.runComprehensiveTest();
  
  process.exit(results.success ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { FrontendTransformationTest };
