import json
import os

try:
    with open(os.path.join('tests', 'airshoping_response.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('JSON loaded successfully')
    print('Type:', type(data))
    print('Top-level keys:', list(data.keys())[:10])
    
    # Check if it has Response key
    if 'Response' in data:
        print('Has Response key')
        response_keys = list(data['Response'].keys())[:10]
        print('Response keys:', response_keys)
        
        if 'DataLists' in data['Response']:
            print('Has DataLists')
            datalists_keys = list(data['Response']['DataLists'].keys())[:10]
            print('DataLists keys:', datalists_keys)
            
            if 'PricedOfferList' in data['Response']['DataLists']:
                print('Has PricedOfferList')
                priced_offer_list = data['Response']['DataLists']['PricedOfferList']
                print('PricedOfferList type:', type(priced_offer_list))
                
                if 'PricedOffer' in priced_offer_list:
                    print('Has PricedOffer')
                    priced_offers = priced_offer_list['PricedOffer']
                    print('PricedOffer type:', type(priced_offers))
                    print('Number of offers:', len(priced_offers) if isinstance(priced_offers, list) else 'Not a list')
                    
                    if isinstance(priced_offers, list) and len(priced_offers) > 0:
                        first_offer = priced_offers[0]
                        print('First offer keys:', list(first_offer.keys())[:10])
                        
                        if 'OfferID' in first_offer:
                            print('First offer has OfferID:', first_offer['OfferID'])
    else:
        print('No Response key found')
        
except Exception as e:
    print('Error:', str(e))
    print('Error type:', type(e).__name__)