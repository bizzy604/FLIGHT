"""Tests for data transformation utilities."""

import pytest
import json
from unittest.mock import patch
from Backend.utils.data_transformer import (
    transform_verteil_to_frontend,
    _extract_reference_data,
    _transform_single_offer,
    _transform_segment,
    _calculate_duration,
    _build_price_breakdown,
    _get_airline_name
)

# Sample Verteil API response structure for testing
SAMPLE_VERTEIL_RESPONSE = {
    "Document": {
        "ReferenceVersion": "18.1"
    },
    "OffersGroup": {
        "AirlineOffers": [
            {
                "TotalOfferQuantity": 1,
                "Owner": {
                    "value": "KQ"
                },
                "AirlineOffer": [
                    {
                        "PricedOffer": {
                            "OfferPrice": {
                                "Associations": [
                                    {
                                        "AssociatedTraveler": {
                                            "TravelerReferences": ["KQ-PAX11"]
                                        },
                                        "ApplicableFlight": {
                                            "FlightSegmentReference": [
                                                {"ref": "KQ-SEG1"}
                                            ],
                                            "OriginDestinationReferences": ["KQ-NBOCDG"],
                                            "FlightReferences": {
                                                "value": ["KQ-FLT1"]
                                            }
                                        }
                                    }
                                ],
                                "PriceDetail": {
                                    "TotalAmount": {
                                        "SimpleCurrencyPrice": {
                                            "value": 16409,
                                            "Code": "INR"
                                        }
                                    },
                                    "BaseAmount": {
                                        "value": 13675,
                                        "Code": "INR"
                                    },
                                    "Taxes": {
                                        "Total": {
                                            "value": 2734,
                                            "Code": "INR"
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        ]
    },
    "FlightSegmentList": {
        "FlightSegment": {
            "SegmentKey": "KQ-SEG1",
            "Departure": {
                "AirportCode": "NBO",
                "Date": "2024-01-15",
                "Time": "10:30",
                "Terminal": "1A"
            },
            "Arrival": {
                "AirportCode": "CDG",
                "Date": "2024-01-15",
                "Time": "18:45",
                "Terminal": "2E"
            },
            "MarketingCarrier": {
                "FlightNumber": "565"
            },
            "Equipment": {
                "AircraftCode": "B787"
            }
        }
    },
    "OriginDestinationList": {
        "OriginDestination": {
            "Departure": {
                "AirportCode": "NBO",
                "AirportName": "Jomo Kenyatta International Airport",
                "Terminal": "1A"
            },
            "Arrival": {
                "AirportCode": "CDG",
                "AirportName": "Charles de Gaulle Airport",
                "Terminal": "2E"
            }
        }
    },
    "FlightList": {
        "Flight": {
            "FlightKey": "KQ-FLT1",
            "Journey": {
                "Time": "8h 15m"
            }
        }
    }
}

class TestDataTransformer:
    """Test cases for data transformation functions."""
    
    def test_transform_verteil_to_frontend_success(self):
        """Test successful transformation of Verteil response to frontend format."""
        result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        flight_offer = result[0]
        
        # Check required fields
        assert 'id' in flight_offer
        assert 'airline' in flight_offer
        assert 'departure' in flight_offer
        assert 'arrival' in flight_offer
        assert 'duration' in flight_offer
        assert 'stops' in flight_offer
        assert 'price' in flight_offer
        assert 'currency' in flight_offer
        
        # Check airline details
        airline = flight_offer['airline']
        assert airline['code'] == 'KQ'
        assert airline['name'] == 'Kenya Airways'
        
        # Check price details
        assert flight_offer['price'] == 16409
        assert flight_offer['currency'] == 'INR'
        
        # Check departure/arrival
        assert flight_offer['departure']['airport'] == 'NBO'
        assert flight_offer['arrival']['airport'] == 'CDG'
        
    def test_transform_verteil_to_frontend_empty_response(self):
        """Test transformation with empty response."""
        result = transform_verteil_to_frontend({})
        assert result == []
        
    def test_transform_verteil_to_frontend_invalid_response(self):
        """Test transformation with invalid response structure."""
        invalid_response = {"invalid": "data"}
        result = transform_verteil_to_frontend(invalid_response)
        assert result == []
        
    def test_extract_reference_data(self):
        """Test extraction of reference data from Verteil response."""
        reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)
        
        assert 'flights' in reference_data
        assert 'segments' in reference_data
        assert 'airports' in reference_data
        assert 'aircraft' in reference_data
        
        # Check segments
        assert 'KQ-SEG1' in reference_data['segments']
        segment = reference_data['segments']['KQ-SEG1']
        assert segment['SegmentKey'] == 'KQ-SEG1'
        
        # Check airports
        assert 'NBO' in reference_data['airports']
        assert 'CDG' in reference_data['airports']
        
        nbo_airport = reference_data['airports']['NBO']
        assert nbo_airport['code'] == 'NBO'
        assert nbo_airport['name'] == 'Jomo Kenyatta International Airport'
        
    def test_transform_segment(self):
        """Test transformation of a single flight segment."""
        segment_data = SAMPLE_VERTEIL_RESPONSE['FlightSegmentList']['FlightSegment']
        reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)
        
        result = _transform_segment(segment_data, reference_data)
        
        assert 'departure' in result
        assert 'arrival' in result
        assert 'flightNumber' in result
        assert 'aircraft' in result
        
        # Check departure details
        departure = result['departure']
        assert departure['airport'] == 'NBO'
        assert departure['datetime'] == '2024-01-15T10:30'
        assert departure['terminal'] == '1A'
        assert departure['airportName'] == 'Jomo Kenyatta International Airport'
        
        # Check arrival details
        arrival = result['arrival']
        assert arrival['airport'] == 'CDG'
        assert arrival['datetime'] == '2024-01-15T18:45'
        assert arrival['terminal'] == '2E'
        assert arrival['airportName'] == 'Charles de Gaulle Airport'
        
        # Check flight number
        assert result['flightNumber'] == '565'
        
        # Check aircraft
        assert result['aircraft']['code'] == 'B787'
        
    def test_calculate_duration(self):
        """Test duration calculation between segments."""
        first_segment = {
            'departure': {'datetime': '2024-01-15T10:30'},
            'arrival': {'datetime': '2024-01-15T12:30'}
        }
        last_segment = {
            'departure': {'datetime': '2024-01-15T14:00'},
            'arrival': {'datetime': '2024-01-15T18:45'}
        }
        
        duration = _calculate_duration(first_segment, last_segment)
        assert duration == '8h 15m'
        
    def test_calculate_duration_invalid_format(self):
        """Test duration calculation with invalid datetime format."""
        first_segment = {
            'departure': {'datetime': 'invalid-datetime'},
            'arrival': {'datetime': 'invalid-datetime'}
        }
        last_segment = {
            'departure': {'datetime': 'invalid-datetime'},
            'arrival': {'datetime': 'invalid-datetime'}
        }
        
        duration = _calculate_duration(first_segment, last_segment)
        assert duration == 'N/A'
        
    def test_build_price_breakdown(self):
        """Test building price breakdown from Verteil price detail."""
        price_detail = {
            "TotalAmount": {
                "SimpleCurrencyPrice": {
                    "value": 16409,
                    "Code": "INR"
                }
            },
            "BaseAmount": {
                "value": 13675,
                "Code": "INR"
            },
            "Taxes": {
                "Total": {
                    "value": 2734,
                    "Code": "INR"
                }
            }
        }
        
        result = _build_price_breakdown(price_detail)
        
        assert result['baseFare'] == 13675
        assert result['taxes'] == 2734
        assert result['fees'] == 0
        assert result['totalPrice'] == 16409
        assert result['currency'] == 'INR'
        
    def test_build_price_breakdown_missing_data(self):
        """Test building price breakdown with missing data."""
        price_detail = {}
        
        result = _build_price_breakdown(price_detail)
        
        assert result['baseFare'] == 0
        assert result['taxes'] == 0
        assert result['fees'] == 0
        assert result['totalPrice'] == 0
        assert result['currency'] == 'USD'
        
    def test_get_airline_name(self):
        """Test airline name lookup."""
        assert _get_airline_name('KQ') == 'Kenya Airways'
        assert _get_airline_name('AA') == 'American Airlines'
        assert _get_airline_name('UNKNOWN') == 'Airline UNKNOWN'
        
    def test_transform_single_offer_success(self):
        """Test transformation of a single priced offer."""
        priced_offer = SAMPLE_VERTEIL_RESPONSE['OffersGroup']['AirlineOffers'][0]['AirlineOffer'][0]['PricedOffer']
        reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)
        
        result = _transform_single_offer(priced_offer, 'KQ', reference_data)
        
        assert result is not None
        assert result['airline']['code'] == 'KQ'
        assert result['price'] == 16409
        assert result['currency'] == 'INR'
        assert result['stops'] == 0  # Direct flight
        assert len(result['segments']) == 1
        
    def test_transform_single_offer_no_price(self):
        """Test transformation of offer without price information."""
        priced_offer = {"OfferPrice": []}
        reference_data = {}
        
        result = _transform_single_offer(priced_offer, 'KQ', reference_data)
        
        assert result is None
        
    def test_transform_single_offer_invalid_data(self):
        """Test transformation with invalid offer data."""
        priced_offer = {"invalid": "data"}
        reference_data = {}
        
        result = _transform_single_offer(priced_offer, 'KQ', reference_data)
        
        assert result is None

if __name__ == '__main__':
    pytest.main([__file__])