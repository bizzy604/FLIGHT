"""
Itinerary routes for generating official flight itineraries and PDFs
"""

import json
import logging
import tempfile
import os
from datetime import datetime
from quart import Blueprint, request, jsonify, send_file
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

itinerary_bp = Blueprint('itinerary', __name__)

def extract_itinerary_data(order_create_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format itinerary data from OrderCreate response
    """
    try:
        response = order_create_response.get('Response', order_create_response)
        
        if not response:
            raise ValueError('Invalid OrderCreate response structure')

        # Extract booking information
        order = response.get('Order', [{}])[0]
        booking_info = {
            'orderId': order.get('OrderID', {}).get('value', 'N/A'),
            'bookingReference': order.get('BookingReferences', {}).get('BookingReference', [{}])[0].get('ID', 'N/A'),
            'alternativeOrderId': order.get('BookingReferences', {}).get('BookingReference', [{}])[0].get('OtherID', {}).get('value', 'N/A'),
            'status': order.get('Status', {}).get('StatusCode', {}).get('Code', 'UNKNOWN'),
            'issueDate': response.get('TicketDocInfos', {}).get('TicketDocInfo', [{}])[0].get('TicketDocument', [{}])[0].get('DateOfIssue', datetime.now().isoformat()),
            'agencyName': 'Rea Travels Agency'
        }

        # Extract discount information if available
        first_order_item = order.get('OrderItems', {}).get('OrderItem', [{}])[0]
        discount = first_order_item.get('FlightItem', {}).get('Price', {}).get('Discount', [{}])
        if discount and len(discount) > 0:
            discount_info = discount[0]
            booking_info['discountApplied'] = {
                'name': discount_info.get('discountName', 'Discount'),
                'percentage': discount_info.get('DiscountPercent', 0),
                'amount': discount_info.get('DiscountAmount', {}).get('value', 0)
            }
            if discount_info.get('discountOwner'):
                booking_info['agencyName'] = discount_info['discountOwner']

        # Extract pricing information
        total_price = order.get('TotalOrderPrice', {}).get('SimpleCurrencyPrice', {})
        payment = response.get('Payments', {}).get('Payment', [{}])[0]
        pricing = {
            'totalAmount': total_price.get('value', 0),
            'currency': total_price.get('Code', 'USD'),
            'paymentMethod': payment.get('Type', {}).get('Code', 'CA')
        }

        # Extract passenger information with ticket numbers using ObjectKey-based mapping
        passengers = []
        passengers_data = response.get('Passengers', {}).get('Passenger', [])
        ticket_doc_infos = response.get('TicketDocInfos', {}).get('TicketDocInfo', [])

        # Create a mapping of ObjectKey to ticket information for efficient lookup
        ticket_mapping = {}
        for ticket_doc in ticket_doc_infos:
            passenger_refs = ticket_doc.get('PassengerReference', [])
            ticket_documents = ticket_doc.get('TicketDocument', [])

            # Handle both single passenger reference and multiple passenger references
            for passenger_ref in passenger_refs:
                if ticket_documents:
                    ticket_mapping[passenger_ref] = {
                        'ticketNumber': ticket_documents[0].get('TicketDocNbr', 'N/A'),
                        'dateOfIssue': ticket_documents[0].get('DateOfIssue', ''),
                        'issuingAirline': ticket_doc.get('IssuingAirlineInfo', {}).get('AirlineName', '')
                    }

        for index, passenger in enumerate(passengers_data):
            name = passenger.get('Name', {})
            contact = passenger.get('Contacts', {}).get('Contact', [{}])[0] if passenger.get('Contacts', {}).get('Contact') else {}
            document = passenger.get('PassengerIDInfo', {}).get('PassengerDocument', [{}])[0] if passenger.get('PassengerIDInfo', {}).get('PassengerDocument') else {}

            # Find corresponding ticket number using ObjectKey mapping
            passenger_object_key = passenger.get('ObjectKey', f'PAX{index + 1}')
            ticket_info = ticket_mapping.get(passenger_object_key, {})
            ticket_number = ticket_info.get('ticketNumber', 'N/A')

            passenger_info = {
                'objectKey': passenger_object_key,
                'fullName': f"{name.get('Title', '')} {name.get('Given', [{}])[0].get('value', '') if name.get('Given') else ''} {name.get('Surname', {}).get('value', '')}".strip(),
                'title': name.get('Title', ''),
                'firstName': name.get('Given', [{}])[0].get('value', '') if name.get('Given') else '',
                'lastName': name.get('Surname', {}).get('value', ''),
                'passengerType': passenger.get('PTC', {}).get('value', 'ADT'),
                'birthDate': passenger.get('Age', {}).get('BirthDate', {}).get('value', ''),
                'documentType': document.get('Type', 'PT'),
                'documentNumber': document.get('ID', 'N/A'),
                'documentExpiry': document.get('DateOfExpiration', ''),
                'countryOfIssuance': document.get('CountryOfIssuance', ''),
                'ticketNumber': ticket_number,
                'dateOfIssue': ticket_info.get('dateOfIssue', ''),
                'issuingAirline': ticket_info.get('issuingAirline', ''),
                'email': contact.get('EmailContact', {}).get('Address', {}).get('value') if contact.get('EmailContact') else None,
                'phone': f"+{contact.get('PhoneContact', {}).get('Number', [{}])[0].get('CountryCode', '')}{contact.get('PhoneContact', {}).get('Number', [{}])[0].get('value', '')}" if contact.get('PhoneContact', {}).get('Number') else None
            }
            passengers.append(passenger_info)

        # Extract contact information from primary passenger
        primary_passenger = next((p for p in passengers if p.get('email')), passengers[0] if passengers else {})
        contact_info = {
            'email': primary_passenger.get('email', 'N/A'),
            'phone': primary_passenger.get('phone', 'N/A')
        }

        # Extract flight segments
        origin_destinations = first_order_item.get('FlightItem', {}).get('OriginDestination', [])
        outbound_flight = []
        return_flight = []

        for od_index, od in enumerate(origin_destinations):
            flights = od.get('Flight', [])
            
            for flight in flights:
                segment = {
                    'segmentKey': flight.get('SegmentKey', f'SEG{od_index + 1}'),
                    'flightNumber': f"{flight.get('MarketingCarrier', {}).get('AirlineID', {}).get('value', '')} {flight.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', '')}".strip(),
                    'airline': flight.get('MarketingCarrier', {}).get('Name', 'Unknown Airline'),
                    'airlineCode': flight.get('MarketingCarrier', {}).get('AirlineID', {}).get('value', ''),
                    'aircraft': flight.get('Equipment', {}).get('Name', 'Unknown'),
                    'departure': {
                        'airport': flight.get('Departure', {}).get('AirportCode', {}).get('value', ''),
                        'date': flight.get('Departure', {}).get('Date', ''),
                        'time': flight.get('Departure', {}).get('Time', ''),
                        'terminal': flight.get('Departure', {}).get('Terminal', {}).get('Name', '')
                    },
                    'arrival': {
                        'airport': flight.get('Arrival', {}).get('AirportCode', {}).get('value', ''),
                        'date': flight.get('Arrival', {}).get('Date', ''),
                        'time': flight.get('Arrival', {}).get('Time', ''),
                        'terminal': flight.get('Arrival', {}).get('Terminal', {}).get('Name', '')
                    },
                    'duration': flight.get('Details', {}).get('FlightDuration', {}).get('Value', ''),
                    'classOfService': flight.get('ClassOfService', {}).get('MarketingName', {}).get('value', 'Economy'),
                    'cabinClass': flight.get('ClassOfService', {}).get('CabinDesignator', 'Y'),
                    'fareBasisCode': flight.get('MarketingCarrier', {}).get('ResBookDesigCode', '')
                }

                if od_index == 0:
                    outbound_flight.append(segment)
                else:
                    return_flight.append(segment)

        # Extract baggage allowance
        baggage_info = response.get('TicketDocInfos', {}).get('TicketDocInfo', [{}])[0].get('TicketDocument', [{}])[0].get('CouponInfo', [{}])
        baggage_allowance = {
            'checkedBags': baggage_info[0].get('AddlBaggageInfo', {}).get('AllowableBag', [{}])[0].get('Number', 1) if baggage_info else 1,
            'carryOnBags': 1
        }

        return {
            'bookingInfo': booking_info,
            'passengers': passengers,
            'outboundFlight': outbound_flight,
            'returnFlight': return_flight if return_flight else None,
            'pricing': pricing,
            'contactInfo': contact_info,
            'baggageAllowance': baggage_allowance
        }

    except Exception as e:
        logger.error(f"Error extracting itinerary data: {str(e)}")
        raise


@itinerary_bp.route('/api/itinerary/extract', methods=['POST'])
async def extract_itinerary():
    """
    Extract itinerary data from OrderCreate response
    """
    try:
        data = await request.get_json()
        
        if not data or 'orderCreateResponse' not in data:
            return jsonify({
                'success': False,
                'error': 'OrderCreate response is required'
            }), 400

        order_create_response = data['orderCreateResponse']
        itinerary_data = extract_itinerary_data(order_create_response)
        
        return jsonify({
            'success': True,
            'data': itinerary_data
        })

    except Exception as e:
        logger.error(f"Error in extract_itinerary: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@itinerary_bp.route('/api/itinerary/generate-pdf', methods=['POST'])
async def generate_pdf():
    """
    Generate PDF from itinerary data using Puppeteer
    Note: This endpoint requires Puppeteer to be installed and configured
    """
    try:
        data = await request.get_json()
        
        if not data or 'itineraryData' not in data:
            return jsonify({
                'success': False,
                'error': 'Itinerary data is required'
            }), 400

        itinerary_data = data['itineraryData']
        
        # For now, return the data structure that can be used by frontend
        # The actual PDF generation will be handled by the frontend using Puppeteer
        return jsonify({
            'success': True,
            'message': 'PDF generation endpoint ready',
            'data': itinerary_data
        })

    except Exception as e:
        logger.error(f"Error in generate_pdf: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@itinerary_bp.route('/api/itinerary/health', methods=['GET'])
async def health_check():
    """
    Health check endpoint for itinerary service
    """
    return jsonify({
        'success': True,
        'message': 'Itinerary service is running',
        'timestamp': datetime.now().isoformat()
    })
