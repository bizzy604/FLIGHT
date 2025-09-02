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

        # Extract ALL cabin configurations (multi-cabin support)
        cabin_sections = _extract_all_cabin_sections(api_response)
        
        # Extract complete seat list (ALL seats)
        seats = _extract_complete_seat_map(api_response)
        
        # Create frontend-compatible structure with multiple cabins
        frontend_data = {
            "flights": [{
                "cabin": cabin_sections
            }],
            "dataLists": {
                "seatList": {
                    "seats": seats
                }
            },
            "raw_response": api_response  # Include raw response for OrderCreate builder
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

def _detect_cabin_separation_type(cabin, cabin_index, all_cabins):
    """
    🧠 INTELLIGENT CABIN SEPARATION DETECTION
    Analyzes cabin characteristics to determine logical separation type
    """
    try:
        current_rows = cabin.get('SeatDisplay', {}).get('Rows', {})
        current_first = int(current_rows.get('First', 1))
        current_last = int(current_rows.get('Last', 30))
        current_columns = cabin.get('SeatDisplay', {}).get('Columns', [])
        current_col_count = len(current_columns)
        is_upper_deck = current_rows.get('UpperDeckInd', False)
        cabin_code = cabin.get('Code', 'Y')
        
        # First cabin is always continuous (aircraft nose)
        if cabin_index == 0:
            if is_upper_deck:
                return "upper_deck_start"
            return "aircraft_nose"
        
        # Get previous cabin for comparison
        prev_cabin = all_cabins[cabin_index - 1] if cabin_index > 0 else None
        prev_rows = prev_cabin.get('SeatDisplay', {}).get('Rows', {}) if prev_cabin else {}
        prev_last = int(prev_rows.get('Last', 0)) if prev_cabin else 0
        prev_col_count = len(prev_cabin.get('SeatDisplay', {}).get('Columns', [])) if prev_cabin else 0
        prev_upper_deck = prev_rows.get('UpperDeckInd', False) if prev_cabin else False
        prev_cabin_code = prev_cabin.get('Code', 'Y') if prev_cabin else 'Y'
        
        # Calculate row gap between cabin sections
        row_gap = current_first - prev_last - 1
        
        # 🔼 UPPER DECK DETECTION
        if is_upper_deck and not prev_upper_deck:
            return "upper_deck_start"
        elif not is_upper_deck and prev_upper_deck:
            return "upper_deck_end"
        elif is_upper_deck and prev_upper_deck:
            return "upper_deck_continue"
        
        # 🏢 CLASS SEPARATION (Business, Premium Economy, Economy)
        if cabin_code != prev_cabin_code:
            class_map = {
                'F': 'First Class',
                'J': 'Business Class', 
                'W': 'Premium Economy',
                'Y': 'Economy Class'
            }
            prev_class = class_map.get(prev_cabin_code, 'Unknown')
            current_class = class_map.get(cabin_code, 'Unknown')
            return f"class_change_{prev_cabin_code}_to_{cabin_code}"
        
        # 🚪 LARGE ROW GAP (Usually indicates major aircraft section change)
        if row_gap >= 10:
            return "major_separation"  # Likely wing-to-tail or major structural break
        elif row_gap >= 5:
            return "significant_gap"  # Likely galley, lavatory, or exit area
        elif row_gap >= 2:
            return "minor_gap"  # Small galley or service area
        
        # 📐 COLUMN CONFIGURATION CHANGE (Different aircraft width)
        if current_col_count != prev_col_count:
            if current_col_count > prev_col_count:
                return "wider_section"  # Aircraft gets wider (rare)
            else:
                return "narrower_section"  # Aircraft gets narrower (common near tail)
        
        # 🎯 EXIT ROW DETECTION (Check for emergency exit markers)
        cabin_layout = cabin.get('CabinLayout', {})
        has_exit_indicators = any([
            'emergency' in str(cabin_layout).lower(),
            'exit' in str(cabin_layout).lower(),
            current_first in [30, 40, 50, 63, 75],  # Common exit row numbers
        ])
        
        if has_exit_indicators:
            return "exit_row_section"
        
        # 🌐 ROW NUMBER ANALYSIS (Detect logical sections by row numbering patterns)
        if current_first <= 10:
            return "front_section"  # Nose/Premium area
        elif current_first <= 30:
            return "forward_section"  # Forward cabin
        elif current_first <= 50:
            return "mid_section"  # Mid cabin
        elif current_first <= 70:
            return "rear_section"  # Rear cabin
        else:
            return "tail_section"  # Tail area
            
    except Exception as e:
        logger.warning(f"Error in cabin separation detection: {e}")
        return "unknown"

def _extract_all_cabin_sections(api_response):
    """Extract ALL cabin sections with their individual configurations and intelligent separation detection"""
    try:
        cabin_sections = []
        
        # Process all cabin sections from API response
        flights = api_response.get('Flights', [])
        if flights and len(flights) > 0:
            cabins = flights[0].get('Cabin', [])
            
            for i, cabin in enumerate(cabins):
                seat_display = cabin.get('SeatDisplay', {})
                if seat_display:
                    columns = seat_display.get('Columns', [])
                    rows = seat_display.get('Rows', {})
                    cabin_layout = cabin.get('CabinLayout', {})
                    
                    # 🧠 INTELLIGENT SEPARATION DETECTION
                    separation_type = _detect_cabin_separation_type(cabin, i, cabins)
                    
                    cabin_section = {
                        "seatDisplay": {
                            "columns": [{"value": col.get('value', ''), "position": col.get('Position', '')} for col in columns],
                            "rows": {
                                "first": int(rows.get('First', 1)),
                                "last": int(rows.get('Last', 30)),
                                "upperDeckInd": rows.get('UpperDeckInd', False)
                            },
                            "component": seat_display.get('Component', [])
                        },
                        "code": cabin.get('Code', 'Y'),  # Cabin class code
                        "cabinLayout": cabin_layout,  # Exit rows, wing positions, etc.
                        "separationType": separation_type  # Intelligent separation detection
                    }
                    
                    cabin_sections.append(cabin_section)
                    logger.info(f"✅ Processed cabin section {i+1}: Rows {cabin_section['seatDisplay']['rows']['first']}-{cabin_section['seatDisplay']['rows']['last']}, {len(cabin_section['seatDisplay']['columns'])} columns, separation: {separation_type}")
        
        if not cabin_sections:
            # Fallback: create single default cabin
            logger.warn("⚠️ No cabin sections found, creating default cabin")
            cabin_sections = [{
                "seatDisplay": {
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
                },
                "code": "Y",
                "cabinLayout": {}
            }]
        
        logger.info(f"🛫 Total cabin sections extracted: {len(cabin_sections)}")
        return cabin_sections
        
    except Exception as e:
        logger.error(f"❌ Error extracting cabin sections: {str(e)}")
        # Return single fallback cabin
        return [{
            "seatDisplay": {
                "columns": [{"value": "A", "position": "W"}, {"value": "F", "position": "W"}],
                "rows": {"first": 1, "last": 30, "upperDeckInd": False},
                "component": []
            },
            "code": "Y",
            "cabinLayout": {}
        }]

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
        
        # Debug logging to understand the actual API response structure
        logger.info(f"DEBUG: DataLists keys: {list(data_lists.keys())}")
        if 'SeatList' in data_lists:
            logger.info(f"DEBUG: SeatList keys: {list(data_lists['SeatList'].keys())}")
            logger.info(f"DEBUG: Found {len(seat_data)} seats in Seats array")
            if seat_data and len(seat_data) > 0:
                first_seat = seat_data[0]
                logger.info(f"DEBUG: First seat keys: {list(first_seat.keys()) if isinstance(first_seat, dict) else 'Not a dict'}")
                if isinstance(first_seat, dict) and 'Location' in first_seat:
                    location = first_seat['Location']
                    logger.info(f"DEBUG: First seat location keys: {list(location.keys())}")
                    if 'Row' in location:
                        row_data = location['Row']
                        logger.info(f"DEBUG: Row data structure: {row_data}")
                        if isinstance(row_data, dict) and 'Number' in row_data:
                            number_data = row_data['Number']
                            logger.info(f"DEBUG: Number data structure: {number_data}")
                            if isinstance(number_data, dict) and 'value' in number_data:
                                logger.info(f"DEBUG: Row value: {number_data['value']}")
        
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
                
                # Extract price from refs (seat services) - API doesn't provide refs, so we create them
                # The seat availability API doesn't include pricing references, so we need to create them
                # based on the seat position and the flight price response structure
                
                # Create a pricing reference based on seat position and offer structure
                # This is a workaround since the API doesn't provide the actual refs
                # We need to create a reference that the OrderCreate builder can use
                # to map seat positions to pricing ObjectKeys
                
                # Create a unique reference for this seat that can be used for pricing lookup
                # The format should match what the OrderCreate builder expects
                seat_ref = f"SEAT-{row_value}{column}"
                
                # Try to find a matching service for this seat
                matching_service_ref = None
                if services_data:
                    for service in services_data:
                        # Check if service has associations that match this seat
                        associations = service.get('Associations', [])
                        for assoc in associations:
                            if isinstance(assoc, dict):
                                # Look for seat-related associations
                                if 'Seat' in assoc or 'Location' in str(assoc):
                                    matching_service_ref = service.get('ObjectKey')
                                    break
                        if matching_service_ref:
                            break
                
                # Use the matching service ref if found, otherwise use the seat ref
                if matching_service_ref:
                    refs = [matching_service_ref]
                else:
                    # Create a reference that includes both seat position and potential pricing info
                    # This will help the OrderCreate builder identify this as a seat selection
                    refs = [f"SEAT-POSITION-{row_value}{column}"]
                
                price_value = 0.0
                currency_code = 'INR'
                
                # Try to find pricing from services if available
                if services_data:
                    # Look for a service that matches this seat
                    for service in services_data:
                        service_refs = service.get('refs', [])
                        if seat_ref in service_refs or any(seat_ref in str(ref) for ref in service_refs):
                            price_info = service.get('Price', [{}])[0] if service.get('Price') else {}
                            if price_info:
                                total = price_info.get('Total', {})
                                price_value = float(total.get('value', 0))
                                currency_code = total.get('Code', 'INR')
                                break
                
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
                    
                    # 🚀 CRITICAL FIX: Add pricing refs for OrderCreate mapping
                    # Frontend needs these to map seat positions to pricing ObjectKeys
                    if refs:
                        seat_obj["refs"] = refs  # Use 'refs' to match what OrderCreate builder expects
                    
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