import json
import re
from typing import Dict, Any, Optional
from utils.airline_data import get_airline_name, AIRLINE_NAMES

class FlightPriceTransformer:
    def __init__(self, ndc_json: dict):
        self.data = ndc_json
        self.traveler_map = {
            t['ObjectKey']: t['PTC']['value']
            for t in self.data['DataLists']['AnonymousTravelerList']['AnonymousTraveler']
        }
        self.segment_map = {
            seg['SegmentKey']: seg
            for seg in self.data['DataLists']['FlightSegmentList']['FlightSegment']
        }
        self.flight_map = {
            flt['FlightKey']: flt['SegmentReferences']['value']
            for flt in self.data['DataLists']['FlightList']['Flight']
        }
        self.origin_dest_map = {
            od['OriginDestinationKey']: od
            for od in self.data['DataLists']['OriginDestinationList']['OriginDestination']
        }

        self.price_class_map = {}
        if 'PriceClassList' in self.data['DataLists']:
            self.price_class_map = {
                pc['ObjectKey']: pc for pc in self.data['DataLists']['PriceClassList']['PriceClass']
            }
        elif 'ServiceList' in self.data['DataLists']:
            self.price_class_map = {
                pc['ObjectKey']: pc for pc in self.data['DataLists']['ServiceList']['Service']
            }

        self.penalty_map = {
            p['ObjectKey']: p for p in self.data['DataLists'].get('PenaltyList', {}).get('Penalty', [])
        }
        self.carryon_map = {
            c['ListKey']: c for c in self.data['DataLists'].get('CarryOnAllowanceList', {}).get('CarryOnAllowance', [])
        }
        self.checked_map = {
            c['ListKey']: c for c in self.data['DataLists'].get('CheckedBagAllowanceList', {}).get('CheckedBagAllowance', [])
        }

    def parse_duration(self, pt_str: str) -> str:
        """Parse ISO 8601 duration format (e.g., PT2H30M) to human-readable format.
        
        Args:
            pt_str: ISO 8601 duration string
            
        Returns:
            str: Formatted duration (e.g., "2h 30m") or original string if invalid
        """
        if not pt_str:
            return ""
            
        try:
            # Handle PT#H#M format
            if 'H' in pt_str and 'M' in pt_str:
                hours = pt_str.split('H')[0].replace('PT', '')
                minutes = pt_str.split('H')[1].replace('M', '')
                return f"{int(hours)}h {int(minutes)}m"
            # Handle PT#H format
            elif 'H' in pt_str:
                hours = pt_str.replace('PT', '').replace('H', '')
                return f"{int(hours)}h"
            # Handle PT#M format
            elif 'M' in pt_str:
                minutes = pt_str.replace('PT', '').replace('M', '')
                return f"{int(minutes)}m"
            return pt_str
        except (ValueError, AttributeError, IndexError):
            return pt_str

    def get_baggage(self, assoc):
        price_class_ref = assoc.get('PriceClass', {}).get('PriceClassReference')
        if price_class_ref and price_class_ref in self.price_class_map:
            descs = self.price_class_map[price_class_ref].get('Descriptions', {}).get('Description', [])
            carry = next((d['Text']['value'] for d in descs if 'CARRYON' in d['Text']['value']), None)
            check = next((d['Text']['value'] for d in descs if 'CHECKED' in d['Text']['value']), None)
            if carry or check:
                return {"carry_on_allowance": carry, "checked_allowance": check}

        carry_descs, checked_descs = [], []
        for segment in assoc.get('ApplicableFlight', {}).get('FlightSegmentReference', []):
            bag_detail = segment.get('BagDetailAssociation', {})
            for carry_key in bag_detail.get('CarryOnReferences', []):
                carry_data = self.carryon_map.get(carry_key, {})
                for d in carry_data.get('AllowanceDescription', {}).get('Descriptions', {}).get('Description', []):
                    carry_descs.append(d['Text']['value'])
            for check_key in bag_detail.get('CheckedBagReferences', []):
                checked_data = self.checked_map.get(check_key, {})
                for d in checked_data.get('AllowanceDescription', {}).get('Descriptions', {}).get('Description', []):
                    checked_descs.append(d['Text']['value'])

        return {
            "carry_on_allowance": carry_descs[0] if carry_descs else None,
            "checked_allowance": checked_descs[0] if checked_descs else None
        }

    def extract_penalties(self, refs):
        cancel_vals, change_vals = [], []
        for ref in refs:
            entry = self.penalty_map.get(ref, {})
            for d in entry.get('Details', {}).get('Detail', []):
                for amt in d['Amounts']['Amount']:
                    val = amt['CurrencyAmountValue']['value']
                    if 'Cancel' in d['Type']:
                        cancel_vals.append(val)
                    if 'Change' in d['Type']:
                        change_vals.append(val)
        return {
            "cancel_fee_min": min(cancel_vals) if cancel_vals else 0,
            "cancel_fee_max": max(cancel_vals) if cancel_vals else 0,
            "change_fee_min": min(change_vals) if change_vals else 0,
            "change_fee_max": max(change_vals) if change_vals else 0
        }

    def transform(self):
        """
        Transform the flight pricing data into a structured format.
        
        Returns:
            list: List of transformed flight offers
        """
        results = []
        
        try:
            for offer in self.data.get('PricedFlightOffers', {}).get('PricedFlightOffer', []):
                time_limits = offer.get('TimeLimits', {})
                offer_expiry = time_limits.get('OfferExpiration', {}).get('DateTime')
                payment_expiry = time_limits.get('PaymentTimeLimit', {}).get('DateTime') or \
                                time_limits.get('Payment', {}).get('DateTime')

                for price_block in offer.get('OfferPrice', []):
                    try:
                        rd = price_block.get('RequestedDate', {})
                        pd = rd.get('PriceDetail', {})
                        
                        # Safely extract currency and total price
                        currency = pd.get('TotalAmount', {}).get('SimpleCurrencyPrice', {}).get('Code', 'USD')
                        total_per_ptc = float(pd.get('TotalAmount', {}).get('SimpleCurrencyPrice', {}).get('value', 0))

                        # Safely extract segments
                        segments = []
                        if rd.get('Associations') and len(rd['Associations']) > 0:
                            for key in rd['Associations'][0].get('ApplicableFlight', {}).get('OriginDestinationReferences', []):
                                if key in self.origin_dest_map:
                                    for flight_ref in self.origin_dest_map[key].get('FlightReferences', {}).get('value', []):
                                        for seg_key in self.flight_map.get(flight_ref, []):
                                            if seg_key in self.segment_map:
                                                segments.append(self.segment_map[seg_key])

                        segment_list = []
                        for seg in segments:
                            if not isinstance(seg, dict):
                                continue
                                
                            # Safely extract marketing carrier info
                            marketing_carrier = seg.get('MarketingCarrier', {}) or {}
                            
                            # Get airline ID with fallback
                            airline_id = 'UNKNOWN'
                            if isinstance(marketing_carrier, dict):
                                airline_id_obj = marketing_carrier.get('AirlineID', {}) or {}
                                if isinstance(airline_id_obj, dict):
                                    airline_id = str(airline_id_obj.get('value', 'UNKNOWN')).strip().upper()
                            
                            # Get flight number with fallback
                            flight_number = '0000'
                            if isinstance(marketing_carrier, dict):
                                flight_number_obj = marketing_carrier.get('FlightNumber', {}) or {}
                                if isinstance(flight_number_obj, dict):
                                    flight_number = str(flight_number_obj.get('value', '0000')).strip()
                            
                            # Get airline name using the shared mapping
                            airline_name = get_airline_name(airline_id)
                            
                            # Safely extract airport and timing info with fallbacks
                            departure = seg.get('Departure', {}) or {}
                            arrival = seg.get('Arrival', {}) or {}
                            flight_detail = seg.get('FlightDetail', {}) or {}
                            
                            # Build the segment with safe dictionary access
                            segment = {
                                "airline_name": airline_name,
                                "airline_code": airline_id,  # Keep the code for reference
                                "flight_number": f"{airline_id}{flight_number}",
                                "origin": departure.get('AirportCode', {}).get('value', ''),
                                "destination": arrival.get('AirportCode', {}).get('value', ''),
                                "departure_date": departure.get('Date', '').split('T')[0] if departure.get('Date') else '',
                                "departure_time": departure.get('Time', ''),
                                "arrival_date": arrival.get('Date', '').split('T')[0] if arrival.get('Date') else '',
                                "arrival_time": arrival.get('Time', ''),
                            }
                            
                            # Add flight duration if available
                            if flight_detail and isinstance(flight_detail.get('FlightDuration', {}), dict):
                                duration_value = flight_detail['FlightDuration'].get('Value')
                                if duration_value:
                                    segment["flight_duration"] = self.parse_duration(duration_value)
                            
                            segment_list.append(segment)

                        # Try to get fare basis from FareComponent, fallback to empty string if not available
                        fare_basis = ''
                        try:
                            fare_basis = price_block.get('FareDetail', {}).get('FareComponent', [{}])[0].get('FareBasisCode', {}).get('Code', '')
                        except (KeyError, IndexError, AttributeError):
                            pass
                            
                        # Extract penalty references safely
                        penalty_refs = []
                        try:
                            for fc in price_block.get('FareDetail', {}).get('FareComponent', []):
                                penalty_refs.extend(fc.get('FareRules', {}).get('Penalty', {}).get('refs', []))
                        except (KeyError, AttributeError):
                            pass
                            
                        penalties = self.extract_penalties(penalty_refs)
                        seen_ptc = set()

                        for assoc in rd.get('Associations', []):
                            try:
                                traveler_refs = assoc.get('AssociatedTraveler', {}).get('TravelerReferences', [])
                                if not traveler_refs or traveler_refs[0] not in self.traveler_map:
                                    continue
                                    
                                ptc = self.traveler_map[traveler_refs[0]]
                                count = len(traveler_refs)
                                ptc_key = (ptc, count)

                                if ptc_key in seen_ptc:
                                    continue
                                seen_ptc.add(ptc_key)

                                baggage = self.get_baggage(assoc)
                                base = float(pd.get('BaseAmount', {}).get('value', 0))
                                taxes = float(pd.get('Taxes', {}).get('Total', {}).get('value', 0))
                                discount = sum(float(d.get('DiscountAmount', {}).get('value', 0)) 
                                             for d in pd.get('Discount', []))

                                record = {
                                    "segments": segment_list,
                                    "fare_basis": fare_basis,
                                    "passenger_type": ptc,
                                    "traveler_count": count,
                                    "baggage_allowance": baggage,
                                    "pricing": {
                                        "base_fare_per_traveler": base,
                                        "taxes_per_traveler": taxes,
                                        "discount_per_traveler": discount,
                                        "total_price_per_traveler": total_per_ptc,
                                        "currency": currency,
                                        "traveler_count": count,
                                        "total_base_fare": base * count,
                                        "total_taxes": taxes * count,
                                        "total_discount": discount * count,
                                        "total_price": total_per_ptc * count
                                    },
                                    "penalties": penalties,
                                    "total_amount_per_ptc": {
                                        "passenger_type": ptc,
                                        "traveler_count": count,
                                        "price_per_ptc": total_per_ptc,
                                        "currency": currency,
                                        "total_amount": total_per_ptc * count
                                    }
                                }
                                
                                if offer_expiry:
                                    record["offer_expiration_utc"] = offer_expiry
                                if payment_expiry:
                                    record["payment_expiration_utc"] = payment_expiry

                                results.append(record)
                                
                            except Exception as e:
                                import logging
                                logging.error(f"Error processing traveler association: {str(e)}")
                                continue
                                
                    except Exception as e:
                        import logging
                        logging.error(f"Error processing price block: {str(e)}")
                        continue
                        
        except Exception as e:
            import logging
            logging.error(f"Error in transform: {str(e)}")
            raise
            
        return results
