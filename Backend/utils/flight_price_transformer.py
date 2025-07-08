### Refactored Data Transformer - FINAL CONSOLIDATED VERSION (with Time & Logo Fixes)
# This file merges logic from all previous transformers and is the single source of truth.

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

# --- Airline Data & Helpers ---
AIRLINE_NAMES = {
    "EK": "Emirates", "KQ": "Kenya Airways", "AF": "Air France", "KL": "KLM Royal Dutch Airlines",
    "QR": "Qatar Airways", "SQ": "Singapore Airlines", "BA": "British Airways", "LH": "Lufthansa"
}

def get_airline_name(code: str) -> str:
    return AIRLINE_NAMES.get(code, f"Unknown Airline ({code})")

def get_airline_logo_url(airline_code: str) -> Optional[str]:
    if not airline_code: return None
    code = airline_code.strip().upper()
    available_logos = {"AA", "AC", "AF", "AI", "AS", "AV", "B6", "BA", "CM", "CX", "DL", "EK", "EY", "F9", "FR", "GA", "IB", "JL", "JQ", "KL", "KQ", "LA", "LH", "LX", "MH", "NK", "NZ", "OZ", "PR", "QF", "QR", "SK", "SQ", "SV", "TK", "TP", "UA", "UX", "VA", "VN", "VS", "WN", "WY"}
    return f"/airlines/{code}.svg" if code in available_logos else None

def parse_iso_duration(duration_str: str) -> str:
    # --- FIX 1: Re-integrated robust duration parsing ---
    """Parses an ISO 8601 duration string (e.g., PT8H40M) into a human-readable format."""
    if not duration_str or not duration_str.startswith('PT'):
        return "N/A"
    
    try:
        match = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_str)
        if not match:
            return duration_str
            
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
            
        return " ".join(parts) if parts else "0m"
    except Exception:
        return duration_str # Fallback to original string on error
# --- End of Helpers ---

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Dataclasses ---
@dataclass
class FlightSegment:
    departure_airport: str; arrival_airport: str; departure_datetime: str; arrival_datetime: str
    airline_code: str; airline_name: str; airline_logo_url: Optional[str]; flight_number: str; duration: str

@dataclass
class PenaltyInterpretation:
    action_type: str; timing_code: int; timing_description: str; penalty_applicable: str
    refund_applicable: str; cancel_allowed: str; change_allowed: str; interpretation: str
    raw_penalty_data: Dict[str, Any]

# --- Core Interpreter and Transformation Logic ---
class VDCPenaltyInterpreter:
    TIMING_CODES = {1: "After Departure NO Show", 2: "Prior to Departure", 3: "After Departure", 4: "Before Departure No Show"}
    CANCEL_MATRIX = {
        (True, True): ("Yes", "Yes", "Yes", "Refunable with penalty (partially refundable)"),
        (False, True): ("No", "Yes", "Yes", "Fully refundable (without penalty)"),
        (False, False): ("No", "No", "No", "Non-refundable"),
        (None, True): ("Unknown", "Yes", "Yes", "Refundable but penalty is unknown"),
        (None, False): ("No", "No", "No", "Non refundable"),
        (False, None): ("No", "Unknown", "Unknown", "Refundability Unknown"),
        (True, None): ("Yes", "Unknown", "Yes", "Cancel allowed with fee, refundability unknown"),
        (None, None): ("Unknown", "Unknown", "Unknown", "Cancellation details unknown")
    }
    CHANGE_MATRIX = {
        (True, True): ("Yes", "Yes", "Change allowed with penalty + difference in fare"),
        (False, True): ("No", "Yes", "Free change + difference in fare"),
        (False, False): ("No", "No", "Change not allowed"),
        (None, True): ("Unknown", "Yes", "Change allowed, Penalty details unknown"),
        (None, False): ("No", "No", "Change not allowed"),
        (False, None): ("No", "Unknown", "Change allowed unknown"),
        (True, None): ("Yes", "Yes", "Change allowed with fee"),
        (None, None): ("Unknown", "Unknown", "Change allowed unknown")
    }

    @classmethod
    def _safe_bool_convert(cls, value: Any) -> Optional[bool]:
        if value is None or value == "Missing": return None
        if isinstance(value, bool): return value
        if isinstance(value, int):
            if value == 1: return True
            if value == 0: return False
        if isinstance(value, str):
            val_lower = value.lower()
            if val_lower in ['true', '1', 'yes', 'allowed']: return True
            if val_lower in ['false', '0', 'no', 'not allowed', 'nav']: return False
        return None

    @classmethod
    def interpret_penalty(cls, penalty_data: Dict[str, Any]) -> PenaltyInterpretation:
        details = penalty_data.get('Details', {}).get('Detail', [{}])
        first_detail = details[0]
        try: timing_code = int(first_detail.get('Application', {}).get('Code', 2))
        except (ValueError, TypeError): timing_code = 2
        timing_description = cls.TIMING_CODES.get(timing_code, "Unknown Timing")
        action_type = first_detail.get('Type', 'Cancel').title().replace('_', '-')
        base_action_type = action_type.split('-')[0].lower()
        is_no_show = 'noshow' in action_type.lower()
        def get_indicator(data, *keys):
            for k in keys:
                if k in data: return data[k]
            return None
        cancel_fee = cls._safe_bool_convert(get_indicator(penalty_data, 'CancelFeeInd', 'CancelFeeIndicator'))
        refundable = cls._safe_bool_convert(get_indicator(penalty_data, 'RefundableInd', 'RefundableIndicator'))
        change_fee = cls._safe_bool_convert(get_indicator(penalty_data, 'ChangeFeeInd', 'ChangeFeeIndicator'))
        change_allowed = cls._safe_bool_convert(get_indicator(penalty_data, 'ChangeAllowedInd', 'ChangeAllowedIndicator'))
        penalty_applicable, refund_applicable, cancel_allowed_res, change_allowed_res, interpretation = "Unknown", "Unknown", "Unknown", "Unknown", f"Unknown action: {action_type}"
        if base_action_type == 'cancel':
            penalty_applicable, refund_applicable, cancel_allowed_res, interpretation = cls.CANCEL_MATRIX.get((cancel_fee, refundable), ("Unknown", "Unknown", "Unknown", "Cancellation details unknown"))
            change_allowed_res = "N/A"
        elif base_action_type == 'change':
            penalty_applicable, change_allowed_res, interpretation = cls.CHANGE_MATRIX.get((change_fee, change_allowed), ("Unknown", "Unknown", "Change allowed unknown"))
            refund_applicable, cancel_allowed_res = "N/A", "N/A"
        # Only override for scenarios where flight has actually departed (codes 1, 3)
        # Code 4 (Before Departure No Show) should use matrix logic with penalties
        if timing_code in [1, 3]:
            if base_action_type == 'cancel':
                refund_applicable, cancel_allowed_res = "No", "No"
                interpretation = f"Non-refundable ({timing_description.lower()})"
            elif base_action_type == 'change':
                change_allowed_res = "No"
                interpretation = f"Change not allowed ({timing_description.lower()})"
        if is_no_show and not interpretation.endswith("[No-show]"): interpretation += " [No-show]"
        return PenaltyInterpretation(action_type, timing_code, timing_description, penalty_applicable, refund_applicable, cancel_allowed_res, change_allowed_res, interpretation, penalty_data)


def _format_allowance_description(allowance: Dict[str, Any]) -> str:
    if not allowance: return "N/A"
    parts = []
    piece_allowance_list = allowance.get('PieceAllowance', [])
    if isinstance(piece_allowance_list, dict): piece_allowance_list = [piece_allowance_list]
    if piece_allowance_list and (total_quantity := piece_allowance_list[0].get('TotalQuantity')) is not None:
        if total_quantity == 0: return "No baggage"
        parts.append(f"{total_quantity} piece{'s' if total_quantity > 1 else ''}")
    weight_allowance_list = allowance.get('WeightAllowance', {}).get('MaximumWeight', [])
    if isinstance(weight_allowance_list, dict): weight_allowance_list = [weight_allowance_list]
    if weight_allowance_list and (weight := weight_allowance_list[0].get('Value')) is not None:
        uom = weight_allowance_list[0].get('UOM', 'kg').capitalize()
        parts.append(f"up to {weight} {uom}")
    if not parts and (desc := allowance.get('AllowanceDescription', {}).get('Descriptions', {}).get('Description', [])):
        return desc[0].get('Text', {}).get('value', "Details available")
    return ", ".join(parts) if parts else "Details available"

def extract_baggage_from_association(assoc: Dict[str, Any], refs: Dict[str, Any]) -> Dict[str, str]:
    price_class_ref = assoc.get('PriceClass', {}).get('PriceClassReference')
    if price_class_ref and (price_class_data := refs.get('price_classes', {}).get(price_class_ref)):
        descs = price_class_data.get('Descriptions', {}).get('Description', [])
        carry_text = next((d.get('Text', {}).get('value', '').replace('BAGGAGEALLOWANCE_CARRYON-', '') for d in descs if 'CARRYON' in d.get('Text', {}).get('value', '')), None)
        checked_text = next((d.get('Text', {}).get('value', '').replace('BAGGAGEALLOWANCE_CHECKED-', '') for d in descs if 'CHECKED' in d.get('Text', {}).get('value', '')), None)
        if carry_text or checked_text:
            return {'carryOn': carry_text or "N/A", 'checked': checked_text or "N/A"}
    carry_on_desc, checked_desc = "N/A", "N/A"
    for seg_ref in assoc.get('ApplicableFlight', {}).get('FlightSegmentReference', []):
        bag_detail = seg_ref.get('BagDetailAssociation', {})
        if not bag_detail: continue
        if carry_on_desc == "N/A":
            inline_carry = bag_detail.get('CarryOnAllowance', [])
            if inline_carry: carry_on_desc = _format_allowance_description(inline_carry[0] if isinstance(inline_carry, list) else inline_carry)
            elif (carry_refs := bag_detail.get('CarryOnReferences', [])) and (allowance_obj := refs['carryon'].get(carry_refs[0])):
                carry_on_desc = _format_allowance_description(allowance_obj)
        if checked_desc == "N/A":
            inline_checked = bag_detail.get('CheckedBagAllowance', [])
            if inline_checked: checked_desc = _format_allowance_description(inline_checked[0] if isinstance(inline_checked, list) else inline_checked)
            elif (checked_refs := bag_detail.get('CheckedBagReferences', [])) and (allowance_obj := refs['checked'].get(checked_refs[0])):
                checked_desc = _format_allowance_description(allowance_obj)
        if carry_on_desc != "N/A" and checked_desc != "N/A": break
    return {'carryOn': carry_on_desc, 'checked': checked_desc}

def extract_reference_data(response: Dict[str, Any]) -> Dict[str, Any]:
    lists = response.get('DataLists', {})
    if not lists: return {}
    return {
        'flights': {f.get('FlightKey'): f for f in lists.get('FlightList', {}).get('Flight', []) if f.get('FlightKey')},
        'segments': {s.get('SegmentKey'): s for s in lists.get('FlightSegmentList', {}).get('FlightSegment', []) if s.get('SegmentKey')},
        'penalties': {p.get('ObjectKey'): p for p in lists.get('PenaltyList', {}).get('Penalty', []) if p.get('ObjectKey')},
        'carryon': {c.get('ListKey'): c for c in lists.get('CarryOnAllowanceList', {}).get('CarryOnAllowance', []) if c.get('ListKey')},
        'checked': {c.get('ListKey'): c for c in lists.get('CheckedBagAllowanceList', {}).get('CheckedBagAllowance', []) if c.get('ListKey')},
        'price_classes': {pc.get('ObjectKey'): pc for pc in lists.get('PriceClassList', {}).get('PriceClass', []) if pc.get('ObjectKey')},
        'origin_destinations': lists.get('OriginDestinationList', {}).get('OriginDestination', [])
    }

def build_flight_segment(segment_data: Dict[str, Any]) -> FlightSegment:
    dep = segment_data.get('Departure', {})
    arr = segment_data.get('Arrival', {})

    # Extract airline code - prioritize OperatingCarrier for consistency with air shopping
    operating_carrier = segment_data.get('OperatingCarrier', {})
    marketing_carrier = segment_data.get('MarketingCarrier', {})

    # Use operating carrier first, fallback to marketing carrier
    if operating_carrier and operating_carrier.get('AirlineID'):
        airline_id = operating_carrier.get('AirlineID', {})
        airline_code = airline_id.get('value') if isinstance(airline_id, dict) else airline_id
    else:
        airline_id = marketing_carrier.get('AirlineID', {})
        airline_code = airline_id.get('value') if isinstance(airline_id, dict) else airline_id

    # Default if no airline found
    if not airline_code:
        airline_code = '??'

    # Flight number comes from marketing carrier
    flight_num = marketing_carrier.get('FlightNumber', {}).get('value', '000')
    raw_duration = segment_data.get('FlightDetail', {}).get('FlightDuration', {}).get('Value', 'N/A')
    
    return FlightSegment(
        departure_airport=dep.get('AirportCode', {}).get('value', ''),
        arrival_airport=arr.get('AirportCode', {}).get('value', ''),
        departure_datetime=dep.get('Date', ''),
        arrival_datetime=arr.get('Date', ''),
        airline_code=airline_code,
        airline_name=get_airline_name(airline_code),
        airline_logo_url=get_airline_logo_url(airline_code),
        flight_number=f"{airline_code}{flight_num}",
        duration=parse_iso_duration(raw_duration)  # ## FIX 1 ##: Call parser here
    )

def collect_all_offers(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    all_offers = []
    if priced_flight_offers := response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []):
        all_offers.extend(priced_flight_offers)
    if airline_offers_root := response.get('AirlineOffers', {}):
        airline_offer_list = airline_offers_root.get('AirlineOffer', [])
        if isinstance(airline_offer_list, dict): airline_offer_list = [airline_offer_list]
        for branded_offer_group in airline_offer_list:
            if priced_offers := branded_offer_group.get('PricedOffer', []):
                all_offers.extend(priced_offers)
    return all_offers

def _get_od_mapping(refs: Dict[str, Any]) -> Dict[str, str]:
    od_map = {}
    for od in refs.get('origin_destinations', []):
        od_string = f"{od.get('DepartureCode', {}).get('value')}-{od.get('ArrivalCode', {}).get('value')}"
        flight_refs = od.get('FlightReferences', {}).get('value', [])
        if isinstance(flight_refs, dict): flight_refs = [flight_refs]
        for flight_key_obj in flight_refs:
            flight_key = flight_key_obj if isinstance(flight_key_obj, str) else flight_key_obj.get('value')
            if flight_data := refs.get('flights', {}).get(flight_key):
                seg_refs = flight_data.get('SegmentReferences', {}).get('value', [])
                if isinstance(seg_refs, dict): seg_refs = [seg_refs]
                for seg_key_obj in seg_refs:
                    seg_key = seg_key_obj if isinstance(seg_key_obj, str) else seg_key_obj.get('ref')
                    if seg_key: od_map[seg_key] = od_string
    return od_map

def _extract_min_max_amount(penalty_detail: Dict[str, Any]) -> tuple:
    min_amount, max_amount, currency = None, None, None
    for amount in penalty_detail.get('Amounts', {}).get('Amount', []):
        app = amount.get('AmountApplication')
        value = amount.get('CurrencyAmountValue', {}).get('value')
        if currency is None: currency = amount.get('CurrencyAmountValue', {}).get('Code')
        if app == 'MIN': min_amount = value
        elif app == 'MAX': max_amount = value
    if min_amount is None and max_amount is not None: min_amount = max_amount
    if max_amount is None and min_amount is not None: max_amount = min_amount
    return min_amount, max_amount, currency

def _detect_round_trip_segments(segments: List[FlightSegment]) -> Tuple[List[FlightSegment], List[FlightSegment]]:
    """
    Detect round-trip segments by finding the turnaround point where the journey reverses direction.
    For a round trip, we need to find where the passenger reaches their final destination and starts returning.
    """
    if len(segments) < 2:
        return segments, []

    first_origin = segments[0].departure_airport
    last_destination = segments[-1].arrival_airport

    # Only proceed if this is actually a round trip (starts and ends at same place)
    if first_origin != last_destination:
        return segments, []

    # Strategy: Find the longest time gap between consecutive segments
    # This indicates the turnaround point (overnight stay or extended layover)

    max_gap_hours = 0
    split_index = None

    for i in range(len(segments) - 1):
        current_arrival_time = segments[i].arrival_datetime
        next_departure_time = segments[i + 1].departure_datetime

        try:
            from datetime import datetime
            arrival_dt = datetime.fromisoformat(current_arrival_time.replace('Z', '+00:00'))
            departure_dt = datetime.fromisoformat(next_departure_time.replace('Z', '+00:00'))
            time_gap_hours = (departure_dt - arrival_dt).total_seconds() / 3600

            # Track the longest gap
            if time_gap_hours > max_gap_hours:
                max_gap_hours = time_gap_hours
                split_index = i + 1

        except Exception as e:
            logger.warning(f"Error parsing datetime for gap calculation: {e}")
            continue

    # If we found a significant gap (more than 4 hours), split there
    if split_index is not None and max_gap_hours > 4:
        outbound = segments[:split_index]
        inbound = segments[split_index:]

        logger.info(f"Round trip detected with {max_gap_hours:.1f}h gap. Outbound: {len(outbound)} segs, Return: {len(inbound)} segs.")
        logger.info(f"Outbound route: {outbound[0].departure_airport} -> {outbound[-1].arrival_airport}")
        logger.info(f"Return route: {inbound[0].departure_airport} -> {inbound[-1].arrival_airport}")

        return outbound, inbound

    # Fallback: if no clear turnaround found, split at the midpoint
    if len(segments) >= 4:  # Only for complex itineraries
        midpoint = len(segments) // 2
        outbound = segments[:midpoint]
        inbound = segments[midpoint:]
        logger.info(f"Round trip fallback split at midpoint. Outbound: {len(outbound)} segs, Return: {len(inbound)} segs.")
        return outbound, inbound

    # If we can't detect round trip pattern, treat as one-way
    return segments, []

def _transform_single_offer_for_frontend(offer: Dict[str, Any], refs: Dict[str, Any], all_travelers_map: Dict[str, str], od_map: Dict[str, str]) -> List[Dict[str, Any]]:
    # --- FIX 2: Added logic to extract TimeLimits ---
    time_limits = offer.get('TimeLimits', {})
    offer_expiry = time_limits.get('OfferExpiration', {}).get('DateTime')
    payment_expiry = time_limits.get('Payment', {}).get('DateTime')

    all_segment_keys, fare_family_name = set(), "Unknown"
    for op in offer.get('OfferPrice', []):
        for assoc in op.get('RequestedDate', {}).get('Associations', []):
            for seg_ref in assoc.get('ApplicableFlight', {}).get('FlightSegmentReference', []):
                all_segment_keys.add(seg_ref.get('ref'))
            if (pc_ref := assoc.get('PriceClass', {}).get('PriceClassReference')) and (pc_data := refs.get('price_classes', {}).get(pc_ref)):
                fare_family_name = pc_data.get('Name', fare_family_name)
    
    all_segments_built = [build_flight_segment(refs['segments'][key]) for key in all_segment_keys if key in refs['segments']]
    sorted_segments = sorted(all_segments_built, key=lambda s: s.departure_datetime)
    outbound_segs, return_segs = _detect_round_trip_segments(sorted_segments)
    
    legs_to_process = []
    if outbound_segs: legs_to_process.append({'direction': 'outbound', 'segments': outbound_segs})
    if return_segs: legs_to_process.append({'direction': 'return', 'segments': return_segs})

    total_price, currency = 0.0, None
    passenger_groups = defaultdict(lambda: {'count': 0, 'baggage': None, 'fare_rules': defaultdict(lambda: defaultdict(dict))})
    for op in offer.get('OfferPrice', []):
        price_info = op.get('RequestedDate', {}).get('PriceDetail', {}).get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
        per_pax_price = float(price_info.get('value', 0))
        if currency is None: currency = price_info.get('Code')

        current_ptc, traveler_refs_in_op = None, set()
        for assoc in op.get('RequestedDate', {}).get('Associations', []):
            raw_refs = assoc.get('AssociatedTraveler', {}).get('TravelerReferences', [])
            normalized_refs = [raw_refs] if isinstance(raw_refs, str) else [r.get('ref') if isinstance(r, dict) else r for r in raw_refs]
            for ref in normalized_refs:
                if ref:
                    traveler_refs_in_op.add(ref)
                    if current_ptc is None: current_ptc = all_travelers_map.get(ref)
        if not current_ptc: continue
        num_travelers = len(traveler_refs_in_op)
        total_price += per_pax_price * num_travelers
        passenger_groups[current_ptc]['count'] += num_travelers

        if passenger_groups[current_ptc]['baggage'] is None:
            for assoc in op.get('RequestedDate', {}).get('Associations', []):
                 assoc_travelers = assoc.get('AssociatedTraveler', {}).get('TravelerReferences', [])
                 if any(all_travelers_map.get(t_ref) == current_ptc for t_ref in assoc_travelers):
                    passenger_groups[current_ptc]['baggage'] = extract_baggage_from_association(assoc, refs)
                    break

        for fc in op.get('FareDetail', {}).get('FareComponent', []):
            fc_seg_refs = fc.get('refs', [])
            if isinstance(fc_seg_refs, str): fc_seg_refs = [fc_seg_refs]
            for pen_ref in fc.get('FareRules', {}).get('Penalty', {}).get('refs', []):
                if penalty_data := refs['penalties'].get(pen_ref):
                    for detail in penalty_data.get('Details', {}).get('Detail', []):
                        interp = VDCPenaltyInterpreter.interpret_penalty(penalty_data)
                        min_amt, max_amt, pen_curr = _extract_min_max_amount(detail)
                        penalty_type = interp.action_type.replace('-', ' ').title()
                        for seg_key in fc_seg_refs:
                            od_string = od_map.get(seg_key, "ALL")
                            passenger_groups[current_ptc]['fare_rules'][penalty_type][interp.timing_description] = {
                                "od_pair": od_string, "min_amount": min_amt, "max_amount": max_amt,
                                "currency": pen_curr, "interpretation": interp.interpretation
                            }
    
    final_passengers = [{'type': ptc, 'count': data['count'], 'baggage': data['baggage'], 'fare_rules': data['fare_rules']} for ptc, data in passenger_groups.items()]
    
    # If one-way, create a single offer; if round-trip, the total price applies to the whole package
    if not return_segs:
        return [{
            'offer_id': offer.get('OfferID', {}).get('value'), 'fare_family': fare_family_name,
            'flight_segments': [s.__dict__ for s in outbound_segs],
            'passengers': final_passengers, 'total_price': {'amount': round(total_price, 2), 'currency': currency or 'USD'},
            'time_limits': {'offer_expiration': offer_expiry, 'payment_deadline': payment_expiry}, 'direction': 'oneway'
        }]
    else:
        # For round trip, the price is for the whole journey, so we create a single combined offer object
        return [{
            'offer_id': offer.get('OfferID', {}).get('value'), 'fare_family': fare_family_name,
            'flight_segments': {
                'outbound': [s.__dict__ for s in outbound_segs],
                'return': [s.__dict__ for s in return_segs]
            },
            'passengers': final_passengers, 'total_price': {'amount': round(total_price, 2), 'currency': currency or 'USD'},
            'time_limits': {'offer_expiration': offer_expiry, 'payment_deadline': payment_expiry}, 'direction': 'roundtrip'
        }]

def transform_for_frontend(response: dict) -> dict:
    refs = extract_reference_data(response)
    all_travelers_map = {
        anon.get('ObjectKey'): anon.get('PTC', {}).get('value', 'ADT')
        for anon in response.get('DataLists', {}).get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        if anon.get('ObjectKey')
    }

    # [PASSENGER DEBUG] Log passenger data summary
    logger.info(f"[PASSENGER DEBUG] Flight Price Transformer - Processing {len(all_travelers_map)} traveler types")

    od_map = _get_od_mapping(refs)
    all_offers_raw = collect_all_offers(response)

    transformed_offers = []
    for offer_data in all_offers_raw:
        try:
            transformed_offers.extend(
                _transform_single_offer_for_frontend(offer_data, refs, all_travelers_map, od_map)
            )
        except Exception as e:
            logger.error(f"Failed to transform offer {offer_data.get('OfferID', {}).get('value')}: {e}", exc_info=True)

    return {'offers': transformed_offers}


def transform_flight_price_response(response: dict) -> dict:
    """
    Legacy function name compatibility wrapper.
    This function provides backward compatibility for any code that might be calling
    the old function name 'transform_flight_price_response'.
    """
    return transform_for_frontend(response)