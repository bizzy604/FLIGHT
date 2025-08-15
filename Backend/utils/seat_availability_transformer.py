"""
Seat Availability Transformer - Complete Seat Map
Transforms raw NDC SeatAvailability API responses to complete frontend seat map.

Key Features:
- Shows ALL seats (complete aircraft layout) regardless of pricing
- Includes free seats, chargeable seats, and unavailable seats
- Frontend-exact structure: flights[].cabin[].seatDisplay + dataLists.seatList.seats[]
- Optional pricing information (only when available)
- Comprehensive IATA characteristic codes (100+ seat codes supported)
- Real API compatible (handles DataLists.SeatList.Seats structure)

Purpose: Users should see the complete seat map to make informed choices,
even if they cannot afford premium seats.
"""
import logging

logger = logging.getLogger(__name__)

def transform_seat_availability_lean_frontend(api_response):
    """
    Transform seat availability API response to complete frontend seat map.
    Shows ALL seats regardless of pricing - includes free, chargeable, and unavailable seats.
    
    Frontend expects:
    {
      flights: [{ cabin: [{ seatDisplay: {...} }] }],
      dataLists: { seatList: { seats: [...] } }
    }
    
    Every seat will be included to provide complete aircraft layout visibility.
    """
    try:
        if not api_response:
            return {
                "status": "error",
                "message": "Invalid API response"
            }

        # Extract seat display configuration (minimal)
        seat_display = _extract_seat_display(api_response)
        
        # Extract complete seat list (ALL seats)
        seats = _extract_complete_seat_map(api_response)
        
        # Create frontend-compatible structure
        frontend_data = {
            "flights": [{
                "cabin": [{
                    "seatDisplay": seat_display
                }]
            }],
            "dataLists": {
                "seatList": {
                    "seats": seats
                }
            }
        }
        
        logger.info(f"✅ Lean frontend transformation complete: {len(seats)} seats")
        
        return {
            "status": "success",
            "data": frontend_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error in lean frontend seat transformation: {str(e)}")
        return {
            "status": "error",
            "message": f"Transformation failed: {str(e)}"
        }

def _extract_seat_display(api_response):
    """Extract minimal seat display configuration"""
    try:
        # Try to extract from Flights structure first
        flights = api_response.get('Flights', [])
        if flights and len(flights) > 0:
            cabin = flights[0].get('Cabin', [])
            if cabin and len(cabin) > 0:
                seat_display = cabin[0].get('SeatDisplay', {})
                if seat_display:
                    columns = seat_display.get('Columns', [])
                    rows = seat_display.get('Rows', {})
                    
                    return {
                        "columns": [{"value": col.get('value', ''), "position": col.get('Position', '')} for col in columns],
                        "rows": {
                            "first": int(rows.get('First', 1)),
                            "last": int(rows.get('Last', 30)),
                            "upperDeckInd": rows.get('UpperDeckInd', False)
                        },
                        "component": []  # Not essential for frontend
                    }
        
        # Fallback: create default seat display
        return {
            "columns": [
                {"value": "A", "position": "W"},
                {"value": "B", "position": "C"}, 
                {"value": "C", "position": "A"},
                {"value": "D", "position": "A"},
                {"value": "E", "position": "C"},
                {"value": "F", "position": "W"}
            ],
            "rows": {
                "first": 16,
                "last": 30,
                "upperDeckInd": False
            },
            "component": []
        }
    except Exception as e:
        logger.warning(f"Error extracting seat display: {e}")
        return {
            "columns": [{"value": "A", "position": "W"}],
            "rows": {"first": 1, "last": 30, "upperDeckInd": False},
            "component": []
        }

def _extract_complete_seat_map(api_response):
    """Extract complete seat map - ALL seats with full characteristics and optional pricing"""
    seats = []
    
    try:
        # Extract from DataLists.SeatList.Seat
        data_lists = api_response.get('DataLists', {})
        seat_list = data_lists.get('SeatList', {})
        seat_data = seat_list.get('Seats', [])  # Real API uses 'Seats' not 'Seat'
        
        # Create a pricing lookup from Services
        services_data = api_response.get('Services', {}).get('Service', [])
        price_lookup = {}
        for service in services_data:
            object_key = service.get('ObjectKey', '')
            price_info = service.get('Price', [])
            if price_info and len(price_info) > 0:
                total_price = price_info[0].get('Total', {})
                price_lookup[object_key] = {
                    'value': float(total_price.get('value', 0)),
                    'code': total_price.get('Code', 'INR')
                }
        
        # Track unique seats (avoid duplicates)
        seen_seats = set()
        
        for seat in seat_data:
            try:
                # Extract location
                location = seat.get('Location', {})
                column = location.get('Column', '')
                row_data = location.get('Row', {})
                
                # Handle different row formats
                if isinstance(row_data, dict):
                    row_number = row_data.get('Number', {})
                    if isinstance(row_number, dict):
                        row_value = str(row_number.get('value', ''))
                    else:
                        row_value = str(row_number)
                else:
                    row_value = str(row_data)
                
                # Create seat ID and ObjectKey (real API doesn't provide ObjectKey)
                seat_id = f"{row_value}{column}"
                object_key = seat.get('ObjectKey', seat_id)  # Use seat_id if ObjectKey missing
                
                # Skip duplicates
                if seat_id in seen_seats:
                    continue
                seen_seats.add(seat_id)
                
                # Extract price from refs (seat services)
                refs = seat.get('refs', [])
                price_value = 0.0
                currency_code = 'INR'
                
                # Look up pricing from services using refs
                for ref in refs:
                    if ref in price_lookup:
                        price_info = price_lookup[ref]
                        price_value = price_info['value']
                        currency_code = price_info['code']
                        break  # Use first price found
                
                # Extract ALL characteristics (comprehensive IATA codes)
                characteristics_data = location.get('Characteristics', {})
                characteristic_list = characteristics_data.get('Characteristic', [])
                
                all_characteristics = []
                availability = 'available'  # default
                
                # Comprehensive IATA seat characteristic codes (from documentation)
                valid_codes = {
                    '1', '2', '3', '4', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', 
                    '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', 
                    '29', '30', 'A', 'AA', 'AB', 'AC', 'AG', 'AJ', 'AL', 'AM', 'AR', 'AS', 'AT', 
                    'AU', 'AV', 'AW', 'B', 'BA', 'BK', 'BC', 'BE', 'BR', 'BS', 'C', 'CC', 'CH', 
                    'CL', 'CS', 'D', 'DE', 'E', 'EA', 'EC', 'EK', 'ES', 'EX', 'F', 'FC', 'FS', 
                    'G', 'GF', 'GN', 'GR', 'H', 'I', 'IA', 'IE', 'IF', 'IK', 'IR', 'J', 'JS', 
                    'K', 'KA', 'KN', 'L', 'LA', 'LB', 'LE', 'LF', 'LG', 'LH', 'LL', 'LR', 'LS', 
                    'LT', 'M', 'MA', 'ML', 'MS', 'MX', 'N', 'O', 'OW', 'P', 'PC', 'PE', 'Q', 
                    'RS', 'S', 'SC', 'SO', 'ST', 'T', 'TA', 'U', 'UP', 'US', 'V', 'W', 'WA', 
                    'X', 'Z', '1A', '1B', '1C', '1D', '1E', '1M', '1W', '3A', '3B', '6A', '6B', 
                    '7A', '7B', '33', '34', '35', '36', '37', '38', '39', '40', '61', '62', '63', 
                    '64', '65', '66', '70', '71', '72', '73'
                }
                
                for char in characteristic_list:
                    char_code = char.get('Code', '')
                    
                    # Include ALL valid IATA characteristic codes (not filtered)
                    if char_code in valid_codes:
                        char_obj = {"code": char_code}
                        
                        # Check availability from remarks
                        remarks = char.get('Remarks', {}).get('Remark', [])
                        for remark in remarks:
                            remark_value = remark.get('value', '')
                            if remark_value == 'N':
                                availability = 'unavailable'
                            elif remark_value == 'O':
                                availability = 'occupied'
                            
                            # Add remarks for availability tracking
                            if remark_value in ['N', 'O', 'A']:
                                char_obj["remarks"] = {"remark": [{"value": remark_value}]}
                        
                        all_characteristics.append(char_obj)
                
                # Include ALL seats - complete aircraft layout for user visibility
                # Users need to see all seats regardless of pricing capacity
                if True:  # Always include every seat
                    seat_obj = {
                        "objectKey": object_key,
                        "location": {
                            "column": column,
                            "row": {
                                "number": {
                                    "value": row_value
                                }
                            }
                        },
                        "availability": availability
                    }
                    
                    # Add price information if available (optional)
                    if price_value > 0:
                        seat_obj["price"] = {
                            "total": {
                                "value": price_value,
                                "code": currency_code
                            }
                        }
                    
                    # Add ALL characteristics if they exist
                    if all_characteristics:
                        seat_obj["location"]["characteristics"] = {
                            "characteristic": all_characteristics
                        }
                    
                    seats.append(seat_obj)
                    
            except Exception as e:
                logger.warning(f"Error processing seat {seat.get('ObjectKey', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error extracting seats: {e}")
    
    logger.info(f"Extracted {len(seats)} seats with complete aircraft layout (ALL seats included regardless of pricing)")
    return seats