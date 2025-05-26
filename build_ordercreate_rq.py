import json
from typing import Dict, Any, List
from datetime import datetime

def generate_order_create_rq(flight_price_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate OrderCreateRQ from FlightPriceResponse with dynamic extraction of values.
    
    Args:
        flight_price_response: The FlightPriceResponse JSON as a Python dictionary
        
    Returns:
        dict: The generated OrderCreateRQ as a Python dictionary
    """
    # Extract key information from FlightPriceResponse
    shopping_response_id = flight_price_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
    
    # Get the first priced offer
    priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    if not priced_offers:
        raise ValueError("No PricedFlightOffer found in the response")
    
    offer = priced_offers[0]
    offer_id = offer.get('OfferID', {})
    
    # Initialize the OrderCreateRQ structure
    order_create_rq = {
        "Query": {
            "OrderItems": {
                "ShoppingResponse": {
                    "Owner": offer_id.get('Owner'),
                    "ResponseID": {
                        "value": shopping_response_id
                    },
                    "Offers": {
                        "Offer": []
                    }
                },
                "OfferItem": []
            },
            "DataLists": {
                "FareList": {
                    "FareGroup": []
                }
            },
            "Passengers": {
                "Passenger": []
            },
            "Payments": {
                "Payment": []
            },
            "Metadata": {
                "Other": {
                    "OtherMetadata": []
                }
            }
        }
    }
    
    # Process offers and build the structure
    process_offer(flight_price_response, offer, order_create_rq)
    process_data_lists(flight_price_response, order_create_rq)
    process_passengers(flight_price_response, order_create_rq)
    process_payments(flight_price_response, order_create_rq)
    process_metadata(flight_price_response, order_create_rq)
    
    return order_create_rq

def process_offer(flight_price_response: Dict[str, Any], offer: Dict[str, Any], order_create_rq: Dict[str, Any]) -> None:
    """Process the offer and add to OrderCreateRQ."""
    # Get offer details
    offer_id = offer.get('OfferID', {})
    offer_id_value = offer_id.get('value')
    
    # Create offer item references
    offer_prices = offer.get('OfferPrice', [])
    if not isinstance(offer_prices, list):
        offer_prices = [offer_prices]
    
    offer_item_refs = []
    for i, price in enumerate(offer_prices, 1):
        item_id = f"{offer_id_value}-{i}"
        offer_item_refs.append({
            "OfferItemID": {
                "Owner": offer_id.get('Owner'),
                "value": item_id
            }
        })
    
    # Add offer to main structure
    order_create_rq['Query']['OrderItems']['ShoppingResponse']['Offers']['Offer'].append({
        "OfferID": {
            "ObjectKey": offer_id_value,
            "value": offer_id_value,
            "Owner": offer_id.get('Owner'),
            "Channel": offer_id.get('Channel')
        },
        "OfferItems": {
            "OfferItem": offer_item_refs
        }
    })
    
    # Process each offer price to create offer items
    for i, price in enumerate(offer_prices, 1):
        process_offer_item(flight_price_response, offer, price, i, order_create_rq)

def process_offer_item(flight_price_response: Dict[str, Any], offer: Dict[str, Any], price: Dict[str, Any], index: int, order_create_rq: Dict[str, Any]) -> None:
    """Process each offer price and create detailed flight items."""
    offer_id = offer.get('OfferID', {})
    offer_id_value = offer_id.get('value')
    item_id = f"{offer_id_value}-{index}"
    
    # Get price details
    requested_date = price.get('RequestedDate', {})
    price_detail = requested_date.get('PriceDetail', {})
    
    # Get base amount and taxes
    base_amount = price_detail.get('BaseAmount', {})
    taxes = price_detail.get('Taxes', {}).get('Total', {})
    
    # Get traveler references
    associations = requested_date.get('Associations', [])
    if not isinstance(associations, list):
        associations = [associations]
    
    traveler_refs = set()  # Use a set to ensure uniqueness
    for assoc in associations:
        assoc_traveler = assoc.get('AssociatedTraveler', {})
        refs = assoc_traveler.get('TravelerReferences', [])
        if isinstance(refs, str):
            traveler_refs.add(refs)
        else:
            for ref in refs:
                traveler_refs.add(ref)
    
    traveler_refs = list(traveler_refs)  # Convert back to list
    
    # Create flight item structure
    offer_item = {
        "OfferItemID": {
            "Owner": offer_id.get('Owner'),
            "value": item_id
        },
        "OfferItemType": {
            "DetailedFlightItem": [
                {
                    "Price": {
                        "BaseAmount": {
                            "value": base_amount.get('value'),
                            "Code": base_amount.get('Code')
                        },
                        "Taxes": {
                            "Total": {
                                "value": taxes.get('value'),
                                "Code": taxes.get('Code')
                            }
                        }
                    },
                    "OriginDestination": [],
                    "refs": traveler_refs
                }
            ]
        }
    }
    
    # Process origin-destination for the first passenger (with OD keys and segment keys)
    # For other passengers, we don't need OD keys
    is_first_passenger = index == 1  # First offer price is for the first passenger
    
    # Process each association (each OD)
    for od_idx, assoc in enumerate(associations, 1):
        applicable_flight = assoc.get('ApplicableFlight', {})
        flight_segment_refs = applicable_flight.get('FlightSegmentReference', [])
        if not isinstance(flight_segment_refs, list):
            flight_segment_refs = [flight_segment_refs]
        
        # For first passenger, add OD keys and segment keys
        if is_first_passenger:
            od = {
                "OriginDestinationKey": f"OD{od_idx}",
                "Flight": []
            }
            
            # Process each flight segment in this OD
            process_flight_segments(flight_price_response, flight_segment_refs, od['Flight'], True)
            
            # Add OD to offer item
            offer_item['OfferItemType']['DetailedFlightItem'][0]['OriginDestination'].append(od)
        else:
            # For other passengers, just add flights without OD keys
            od = {
                "Flight": []
            }
            
            # Process each flight segment in this OD
            process_flight_segments(flight_price_response, flight_segment_refs, od['Flight'], False)
            
            # Add OD to offer item
            offer_item['OfferItemType']['DetailedFlightItem'][0]['OriginDestination'].append(od)
    
    # Add offer item to OrderCreateRQ
    order_create_rq['Query']['OrderItems']['OfferItem'].append(offer_item)

def process_flight_segments(flight_price_response: Dict[str, Any], flight_segment_refs: List[Dict[str, Any]], flight_list: List, include_segment_keys: bool) -> None:
    """Process flight segments and add to flight list."""
    # Get flight segments from DataLists
    data_lists = flight_price_response.get('DataLists', {})
    flight_segment_list = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
    if not isinstance(flight_segment_list, list):
        flight_segment_list = [flight_segment_list]
    
    # Create a mapping of segment keys to flight segments for quick lookup
    segment_map = {segment.get('SegmentKey'): segment for segment in flight_segment_list}
    
    # Process each flight segment reference
    for segment_ref in flight_segment_refs:
        # Get segment reference and class of service details
        ref = segment_ref.get('ref')
        class_of_service = segment_ref.get('ClassOfService', {})
        class_code = class_of_service.get('Code', {}).get('value')
        class_refs = class_of_service.get('refs', [])
        if isinstance(class_refs, str):
            class_refs = [class_refs]
        
        # Get the segment details from the mapping
        segment = segment_map.get(ref, {})
        if not segment:
            continue
        
        # Create flight structure
        flight = {
            "Departure": {
                "AirportCode": {
                    "value": segment.get('Departure', {}).get('AirportCode', {}).get('value')
                },
                "Date": segment.get('Departure', {}).get('Date'),
                "Time": segment.get('Departure', {}).get('Time'),
                "AirportName": segment.get('Departure', {}).get('AirportName')
            },
            "Arrival": {
                "AirportCode": {
                    "value": segment.get('Arrival', {}).get('AirportCode', {}).get('value')
                },
                "Date": segment.get('Arrival', {}).get('Date'),
                "Time": segment.get('Arrival', {}).get('Time'),
                "AirportName": segment.get('Arrival', {}).get('AirportName')
            },
            "ClassOfService": {
                "Code": {
                    "value": class_code
                },
                "refs": class_refs
            },
            "MarketingCarrier": {
                "AirlineID": {
                    "value": segment.get('MarketingCarrier', {}).get('AirlineID', {}).get('value')
                },
                "Name": segment.get('MarketingCarrier', {}).get('Name'),
                "FlightNumber": {
                    "value": segment.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value')
                }
            },
            "Equipment": {
                "Name": segment.get('Equipment', {}).get('Name'),
                "AircraftCode": {
                    "value": segment.get('Equipment', {}).get('AircraftCode', {}).get('value')
                }
            },
            "FlightDetail": {
                "FlightDuration": segment.get('FlightDetail', {}).get('FlightDuration', {})
            }
        }
        
        # Add SegmentKey for first passenger only
        if include_segment_keys:
            flight['SegmentKey'] = ref
        
        # Add terminal information if available
        if 'Terminal' in segment.get('Departure', {}):
            flight['Departure']['Terminal'] = segment['Departure']['Terminal']
        if 'Terminal' in segment.get('Arrival', {}):
            flight['Arrival']['Terminal'] = segment['Arrival']['Terminal']
        
        # Add flight to list
        flight_list.append(flight)

def process_data_lists(flight_price_response: Dict[str, Any], order_create_rq: Dict[str, Any]) -> None:
    """Process fare data lists."""
    # Get fare list from FlightPriceResponse
    data_lists = flight_price_response.get('DataLists', {})
    fare_list = data_lists.get('FareList', {}).get('FareGroup', [])
    if not isinstance(fare_list, list):
        fare_list = [fare_list]
    
    # Add fare groups to OrderCreateRQ
    for fare_group in fare_list:
        order_create_rq['Query']['DataLists']['FareList']['FareGroup'].append({
            "ListKey": fare_group.get('ListKey'),
            "Fare": {
                "FareCode": {
                    "Code": fare_group.get('Fare', {}).get('FareCode', {}).get('Code')
                },
                "FareDetail": {
                    "Remarks": {
                        "Remark": [
                            {
                                "value": "PUBL"
                            }
                        ]
                    }
                }
            },
            "FareBasisCode": {
                "Code": fare_group.get('FareBasisCode', {}).get('Code')
            },
            "refs": fare_group.get('refs', [])
        })
    
def process_passengers(flight_price_response: Dict[str, Any], order_create_rq: Dict[str, Any]) -> None:
    """Process passenger information."""
    # Get travelers from AnonymousTravelerList or IdentifiedTravelerList
    data_lists = flight_price_response.get('DataLists', {})
    traveler_list = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
    if not traveler_list:
        traveler_list = data_lists.get('IdentifiedTravelerList', {}).get('IdentifiedTraveler', [])
    
    if not isinstance(traveler_list, list):
        traveler_list = [traveler_list]
    
    # Add standard passenger information
    passengers = [
        {
            "Contacts": {
                "Contact": [
                    {
                        "PhoneContact": {
                            "Number": [
                                {
                                    "CountryCode": "254",
                                    "value": "0700000000"
                                }
                            ],
                            "Application": "Home"
                        },
                        "EmailContact": {
                            "Address": {
                                "value": "kevinamoni20@gmail.com"
                            }
                        },
                        "AddressContact": {
                            "Street": [
                                "Nairobi, Kenya 30500"
                            ],
                            "PostalCode": "301",
                            "CityName": "Nairobi",
                            "CountryCode": {
                                "value": "254"
                            }
                        }
                    }
                ]
            },
            "ObjectKey": "T1",
            "Gender": {
                "value": "Male"
            },
            "PTC": {
                "value": "ADT"
            },
            "Name": {
                "Given": [
                    {
                        "value": "Amoni"
                    }
                ],
                "Title": "Mr",
                "Surname": {
                    "value": "Kevin"
                }
            }
        },
        {
            "ObjectKey": "T2",
            "Gender": {
                "value": "Female"
            },
            "PTC": {
                "value": "ADT"
            },
            "Name": {
                "Given": [
                    {
                        "value": "Egole"
                    }
                ],
                "Title": "Mr",
                "Surname": {
                    "value": "David"
                }
            }
        },
        {
            "ObjectKey": "T3",
            "Gender": {
                "value": "Male"
            },
            "PTC": {
                "value": "CHD"
            },
            "Name": {
                "Given": [
                    {
                        "value": "Egole"
                    }
                ],
                "Title": "Mstr",
                "Surname": {
                    "value": "David"
                }
            }
        },
        {
            "ObjectKey": "T1.1",
            "Gender": {
                "value": "Male"
            },
            "PTC": {
                "value": "INF"
            },
            "PassengerAssociation": "T1",
            "Age": {
                "BirthDate": {
                    "value": "2024-05-25"
                }
            },
            "Name": {
                "Given": [
                    {
                        "value": "Egole"
                    }
                ],
                "Title": "Miss",
                "Surname": {
                    "value": "Bizzy"
                }
            }
        }
    ]
    
    # Add passengers to OrderCreateRQ
    order_create_rq['Query']['Passengers']['Passenger'] = passengers

def process_payments(flight_price_response: Dict[str, Any], order_create_rq: Dict[str, Any]) -> None:
    """Process payment information."""
    # Calculate total amount from all offer prices
    total_amount = 0
    currency_code = "INR"  # Default currency code
    
    offer_prices = []
    for offer in flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []):
        prices = offer.get('OfferPrice', [])
        if not isinstance(prices, list):
            prices = [prices]
        offer_prices.extend(prices)
    
    for price in offer_prices:
        requested_date = price.get('RequestedDate', {})
        price_detail = requested_date.get('PriceDetail', {})
        
        # Get total amount from TotalAmount.SimpleCurrencyPrice as requested
        total_price_detail = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
        if not total_price_detail:
            # Fallback to calculating from base + tax if TotalAmount not available
            base_amount = price_detail.get('BaseAmount', {})
            taxes = price_detail.get('Taxes', {}).get('Total', {})
            
            price_value = base_amount.get('value', 0)
            tax_value = taxes.get('value', 0)
            
            if isinstance(price_value, str):
                price_value = float(price_value)
            if isinstance(tax_value, str):
                tax_value = float(tax_value)
                
            price_amount = price_value + tax_value
            
            # Get currency from base amount
            if not currency_code and base_amount.get('Code'):
                currency_code = base_amount.get('Code')
        else:
            # Get amount directly from TotalAmount
            price_amount = total_price_detail.get('value', 0)
            if isinstance(price_amount, str):
                price_amount = float(price_amount)
                
            # Get currency from TotalAmount
            if not currency_code and total_price_detail.get('Code'):
                currency_code = total_price_detail.get('Code')
        
        # Get associated passenger count to multiply the amount
        passenger_count = 1  # Default to 1 if we can't determine count
        associations = requested_date.get('Associations', [])
        if not isinstance(associations, list):
            associations = [associations]
            
        # Count unique passengers for this price
        passenger_refs = set()
        for assoc in associations:
            assoc_traveler = assoc.get('AssociatedTraveler', {})
            refs = assoc_traveler.get('TravelerReferences', [])
            if isinstance(refs, str):
                passenger_refs.add(refs)
            else:
                for ref in refs:
                    passenger_refs.add(ref)
                    
        if passenger_refs:
            passenger_count = len(passenger_refs)
        
        # Add to total after multiplying by passenger count
        total_amount += price_amount * passenger_count
    
    # Add payment to OrderCreateRQ
    order_create_rq['Query']['Payments']['Payment'] = [
        {
            "Amount": {
                "Code": currency_code,
                "value": round(total_amount, 2)  # Round to 2 decimal places
            },
            "Method": {
                "Cash": {
                    "CashInd": True
                }
            }
        }
    ]

def process_metadata(flight_price_response: Dict[str, Any], order_create_rq: Dict[str, Any]) -> None:
    """Process metadata information."""
    # Get metadata from FlightPriceResponse
    metadata = flight_price_response.get('Metadata', {})
    
    # Extract price metadata if available
    price_metadata = []
    other_metadata = metadata.get('Other', {}).get('OtherMetadata', [])
    if not isinstance(other_metadata, list):
        other_metadata = [other_metadata]
    
    for item in other_metadata:
        if 'PriceMetadatas' in item:
            price_metadatas = item.get('PriceMetadatas', {}).get('PriceMetadata', [])
            if not isinstance(price_metadatas, list):
                price_metadatas = [price_metadatas]
            price_metadata.extend(price_metadatas)
    
    # Add metadata to OrderCreateRQ if available
    if price_metadata:
        order_create_rq['Query']['Metadata']['Other']['OtherMetadata'].append({
            "PriceMetadatas": {
                "PriceMetadata": price_metadata
            }
        })
    else:
        # Use sample metadata from template
        order_create_rq['Query']['Metadata']['Other']['OtherMetadata'] = [
            {
                "PriceMetadatas": {
                    "PriceMetadata": [
                        {
                            "MetadataKey": "Pfrk2ny2axc1vwpgr",
                            "AugmentationPoint": {
                                "AugPoint": [
                                    {
                                        "any": {
                                            "VdcAugPoint": [
                                                {
                                                    "Value": "NO80Q~MVB8OLO~MqA9UX~MqM9@NK~MpC8CVA~MEA9QBK5G@~MSN9NT@K~M@K9+0~MBS9GMP~MMS8H~MEP9/~MKF8A~`D*skUlegwksiYq*flxKey"
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        ]
    
    return order_create_rq



def save_order_create_rq(order_create_rq: Dict[str, Any], output_file: str = None) -> None:
    """
    Save OrderCreateRQ to a JSON file.
    
    Args:
        order_create_rq: The OrderCreateRQ dictionary
        output_file: Output file path (default: OrderCreateRQ_<timestamp>.json)
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"OrderCreateRQ_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(order_create_rq, f, indent=2)
    
    print(f"OrderCreateRQ saved to {output_file}")

def main():
    """Main function to run the script."""
    # Set file paths
    input_file = 'FlightPriceResponse.json'
    output_file = 'OrderCreateRQ.json'
    
    try:
        # Load the FlightPriceResponse
        with open(input_file, 'r') as f:
            flight_price_response = json.load(f)
        
        # Generate OrderCreateRQ
        order_create_rq = generate_order_create_rq(flight_price_response)
        
        # Save to file
        save_order_create_rq(order_create_rq, output_file)
        
        print("OrderCreateRQ generation completed successfully!")
        
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: {input_file} is not a valid JSON file.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()


