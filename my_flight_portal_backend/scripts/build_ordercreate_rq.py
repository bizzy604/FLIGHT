# --- START OF FILE build_ordercreate_rq.py ---
import json
from typing import Dict, Any, List, Optional, Union

def generate_order_create_rq(flight_price_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an OrderCreate request from a FlightPrice response.
    
    Args:
        flight_price_response (dict): The FlightPrice response
        
    Returns:
        dict: OrderCreate request payload
    """
    if not isinstance(flight_price_response, dict):
        raise ValueError("Invalid flight_price_response format")
    
    # Extract necessary data from FlightPrice response
    flight_price_result = flight_price_response.get("FlightPriceRS", {})
    data_lists = flight_price_result.get("DataLists", {})
    
    # Get the PricedOffer from the response
    priced_offer = flight_price_result.get("PricedOffer")
    if not priced_offer:
        raise ValueError("No PricedOffer found in FlightPrice response")
    
    # Get the OfferID
    offer_id = priced_offer.get("OfferID")
    if not offer_id:
        raise ValueError("No OfferID found in PricedOffer")
    
    # Get the OfferItems
    offer_items = priced_offer.get("OfferItem", [])
    if not isinstance(offer_items, list):
        offer_items = [offer_items] if offer_items else []
    
    # Get the Price
    price = priced_offer.get("Price", {})
    total_amount = price.get("TotalAmount", {})
    
    # Build the OrderCreate request
    order_create_rq = {
        "OrderCreateRQ": {
            "Query": {
                "ShoppingResponseIDs": {
                    "ResponseID": flight_price_response.get("ResponseID", {})
                },
                "Offer": {
                    "OfferID": offer_id,
                    "OfferItem": []
                },
                "DataLists": {}
            }
        }
    }
    
    # Add OfferItems
    for item in offer_items:
        offer_item = {
            "OfferItemID": item.get("OfferItemID"),
            "PTC_Quantity": item.get("PTC_Quantity", {})
        }
        
        # Add Service if present
        service = item.get("Service")
        if service:
            offer_item["Service"] = service
        
        order_create_rq["OrderCreateRQ"]["Query"]["Offer"]["OfferItem"].append(offer_item)
    
    # Add DataLists if present
    if data_lists:
        order_create_rq["OrderCreateRQ"]["Query"]["DataLists"] = data_lists
    
    # Add Payment information (to be filled by the caller)
    order_create_rq["OrderCreateRQ"]["Query"]["Payments"] = {
        "Payment": {
            "Type": "CARD",  # Default, can be overridden
            "Amount": total_amount,
            "Method": {
                "PaymentCard": {
                    # To be filled by the caller
                }
            }
        }
    }
    
    return order_create_rq


def main():
    """Main function to test the OrderCreate request builder."""
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python build_ordercreate_rq.py <flight_price_response.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            flight_price_response = json.load(f)
        
        order_create_rq = generate_order_create_rq(flight_price_response)
        
        # Create output directory if it doesn't exist
        output_dir = "generated_rqs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}_OrderCreateRQ.json")
        
        # Save the request
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(order_create_rq, f, indent=2, ensure_ascii=False)
        
        print(f"OrderCreate request saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
# --- END OF FILE build_ordercreate_rq.py ---
