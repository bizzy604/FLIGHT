"""
Flight Response Navigator Utility

This module provides utilities for navigating and extracting data from NDC flight API responses.
Consolidates common extraction patterns to reduce code duplication.
"""

import logging
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)


class FlightResponseNavigator:
    """Utility class for navigating NDC flight response structures."""
    
    @staticmethod
    def extract_id(
        response: Dict[str, Any],
        id_type: str,
        request_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Universal ID extraction from flight price response.
        Tries multiple nested structures in order of likelihood.
        
        Args:
            response: Flight price response dictionary
            id_type: Type of ID to extract ('ShoppingResponseID', 'OfferID', etc.)
            request_id: Request ID for logging
        
        Returns:
            Extracted ID or None
        """
        if not response:
            return None
        
        # Define extraction paths in order of priority
        extraction_paths = [
            # Deep nested: data.raw_response.data.raw_response
            ('data.raw_response.data.raw_response', 
             lambda r: r.get('data', {}).get('raw_response', {}).get('data', {}).get('raw_response', {}).get(id_type)),
            
            # Nested: data.raw_response
            ('data.raw_response',
             lambda r: r.get('data', {}).get('raw_response', {}).get(id_type)),
            
            # Top-level raw_response
            ('raw_response',
             lambda r: r.get('raw_response', {}).get(id_type)),
            
            # Direct field
            ('direct',
             lambda r: r.get(id_type)),
            
            # FlightPriceRS structure
            ('FlightPriceRS',
             lambda r: r.get('FlightPriceRS', {}).get(id_type)),
            
            # Response.raw_response (for cached responses)
            ('response.raw_response',
             lambda r: r.get('response', {}).get('raw_response', {}).get(id_type)),
            
            # Response.data (for cached responses)
            ('response.data',
             lambda r: r.get('response', {}).get('data', {}).get(id_type))
        ]
        
        for path_name, extract_fn in extraction_paths:
            try:
                result = extract_fn(response)
                if result:
                    # Handle nested ResponseID structure (for ShoppingResponseID)
                    if isinstance(result, dict):
                        if 'ResponseID' in result:
                            result = result['ResponseID']
                            if isinstance(result, dict) and 'value' in result:
                                result = result['value']
                        elif 'value' in result:
                            result = result['value']
                    
                    if result:
                        logger.info(f"[DEBUG] Extracted {id_type} via '{path_name}': {result} (ReqID: {request_id})")
                        return result
            except Exception as e:
                logger.debug(f"[DEBUG] Path '{path_name}' failed for {id_type}: {e}")
        
        logger.warning(f"[DEBUG] Could not extract {id_type} from response (ReqID: {request_id})")
        return None
    
    @staticmethod
    def extract_offer_id_from_priced_offers(
        response: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract OfferID from PricedFlightOffers structure.
        
        Args:
            response: Flight price response dictionary
            request_id: Request ID for logging
        
        Returns:
            OfferID or None
        """
        # Define paths to check for PricedFlightOffers
        paths = [
            # Deep nested
            lambda r: r.get('data', {}).get('raw_response', {}).get('data', {}).get('raw_response', {}),
            # Nested
            lambda r: r.get('data', {}).get('raw_response', {}),
            # Top-level raw_response
            lambda r: r.get('raw_response', {}),
            # Direct
            lambda r: r,
            # FlightPriceRS
            lambda r: r.get('FlightPriceRS', {})
        ]
        
        for i, path_fn in enumerate(paths):
            try:
                source = path_fn(response)
                priced_offers = FlightResponseNavigator.get_priced_flight_offers(source)
                
                if priced_offers:
                    offer_id_node = priced_offers[0].get('OfferID', {})
                    if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                        offer_id = offer_id_node['value']
                    else:
                        offer_id = offer_id_node
                    
                    if offer_id:
                        logger.info(f"[DEBUG] Extracted OfferID from PricedFlightOffers (path {i}): {offer_id} (ReqID: {request_id})")
                        return offer_id
            except Exception as e:
                logger.debug(f"[DEBUG] Path {i} failed for OfferID extraction: {e}")
        
        return None
    
    @staticmethod
    def get_priced_flight_offers(
        response: Dict[str, Any],
        source_path: str = "PricedFlightOffers"
    ) -> List[Dict[str, Any]]:
        """
        Safely extract PricedFlightOffer list from response.
        
        Args:
            response: Response dictionary
            source_path: Path to PricedFlightOffers (default or custom)
        
        Returns:
            List of PricedFlightOffer dictionaries (empty list if not found)
        """
        if not response:
            return []
        
        try:
            offers = response.get(source_path, {}).get('PricedFlightOffer', [])
            if not isinstance(offers, list):
                offers = [offers] if offers else []
            return offers
        except Exception as e:
            logger.warning(f"Error extracting PricedFlightOffer: {e}")
            return []
    
    @staticmethod
    def navigate_nested(
        response: Dict[str, Any],
        *paths: str
    ) -> Optional[Any]:
        """
        Navigate through nested response structures safely.
        
        Args:
            response: Response dictionary
            *paths: Variable number of path keys to navigate
        
        Returns:
            Nested value or None if path doesn't exist
        
        Example:
            navigate_nested(resp, 'data', 'raw_response', 'ShoppingResponseID')
        """
        if not response:
            return None
        
        current = response
        for path in paths:
            if isinstance(current, dict) and path in current:
                current = current[path]
            else:
                return None
        return current
    
    @staticmethod
    def extract_airline_code(
        response: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Universal airline code extraction from any response type.
        
        Args:
            response: Flight response dictionary
            request_id: Request ID for logging
        
        Returns:
            Airline code (e.g., 'KQ', 'WY') or 'UNKNOWN'
        """
        if not response:
            return 'UNKNOWN'
        
        # Strategy 1: Extract from ShoppingResponse Owner
        try:
            shopping_response = response.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {})
            owner = shopping_response.get('Owner')
            if owner:
                logger.info(f"[DEBUG] Extracted airline code from ShoppingResponse Owner: {owner}")
                return owner
        except Exception:
            pass
        
        # Strategy 2: Extract from PricedFlightOffers OfferID Owner
        try:
            priced_offers = FlightResponseNavigator.get_priced_flight_offers(response)
            if priced_offers:
                offer_id_node = priced_offers[0].get('OfferID', {})
                if isinstance(offer_id_node, dict):
                    owner = offer_id_node.get('Owner')
                    if owner:
                        logger.info(f"[DEBUG] Extracted airline code from OfferID Owner: {owner}")
                        return owner
        except Exception:
            pass
        
        # Strategy 3: Extract from ShoppingResponseID
        try:
            shopping_response_id = response.get('ShoppingResponseID', {})
            if isinstance(shopping_response_id, dict):
                response_id_value = shopping_response_id.get('ResponseID', {}).get('value', '')
                if response_id_value and '-' in response_id_value:
                    parts = response_id_value.split('-')
                    if len(parts) >= 2:
                        airline_code = parts[0]
                        logger.info(f"[DEBUG] Extracted airline code from ShoppingResponseID: {airline_code}")
                        return airline_code
        except Exception:
            pass
        
        # Strategy 4: Extract from OfferID in direct field
        try:
            offer_id = response.get('OfferID', {})
            if isinstance(offer_id, dict):
                owner = offer_id.get('Owner')
                if owner:
                    logger.info(f"[DEBUG] Extracted airline code from direct OfferID Owner: {owner}")
                    return owner
        except Exception:
            pass
        
        # Strategy 5: Extract from FlightPriceRS structure
        try:
            flight_price_rs = response.get('FlightPriceRS', {})
            priced_offer = flight_price_rs.get('PricedOffer', {})
            owner = priced_offer.get('Owner', {})
            if isinstance(owner, dict):
                airline_code = owner.get('value')
                if airline_code:
                    logger.info(f"[DEBUG] Extracted airline code from FlightPriceRS: {airline_code}")
                    return airline_code
        except Exception:
            pass
        
        logger.warning(f"[DEBUG] Could not extract airline code from response (ReqID: {request_id})")
        return 'UNKNOWN'
    
    @staticmethod
    def extract_offer_item_ids(
        response: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> List[str]:
        """
        Extract OfferItemIDs from the flight price response using multiple methods.
        
        Args:
            response: Flight price response
            request_id: Request ID for logging
        
        Returns:
            List of OfferItemIDs
        """
        offer_item_ids = []
        
        # Define paths to check
        paths = [
            ('top-level', lambda r: r),
            ('data.raw_response', lambda r: r.get('data', {}).get('raw_response', {})),
            ('raw_response', lambda r: r.get('raw_response', {})),
            ('FlightPriceRS', lambda r: r.get('FlightPriceRS', {}))
        ]
        
        for path_name, path_fn in paths:
            try:
                source = path_fn(response)
                priced_offers = FlightResponseNavigator.get_priced_flight_offers(source)
                
                if priced_offers:
                    offer_prices = priced_offers[0].get('OfferPrice', [])
                    if not isinstance(offer_prices, list):
                        offer_prices = [offer_prices] if offer_prices else []
                    
                    for offer_price in offer_prices:
                        offer_item_id = offer_price.get('OfferItemID')
                        if offer_item_id and offer_item_id not in offer_item_ids:
                            offer_item_ids.append(offer_item_id)
                    
                    if offer_item_ids:
                        logger.info(f"[DEBUG] Found OfferItemIDs at {path_name}: {offer_item_ids} (ReqID: {request_id})")
                        return offer_item_ids
            except Exception as e:
                logger.debug(f"[DEBUG] Path '{path_name}' failed for OfferItemIDs: {e}")
        
        # Fallback: Recursive search
        try:
            def recursive_search(data: Any, depth: int = 0) -> List[str]:
                """Recursively search for OfferPrice structures."""
                if depth > 10:  # Prevent infinite recursion
                    return []
                
                local_ids = []
                if isinstance(data, dict):
                    if 'OfferPrice' in data:
                        offer_prices = data['OfferPrice']
                        if not isinstance(offer_prices, list):
                            offer_prices = [offer_prices]
                        for op in offer_prices:
                            if isinstance(op, dict) and 'OfferItemID' in op:
                                local_ids.append(op['OfferItemID'])
                    
                    for value in data.values():
                        local_ids.extend(recursive_search(value, depth + 1))
                
                elif isinstance(data, list):
                    for item in data:
                        local_ids.extend(recursive_search(item, depth + 1))
                
                return local_ids
            
            offer_item_ids = list(set(recursive_search(response)))
            if offer_item_ids:
                logger.info(f"[DEBUG] Found OfferItemIDs via recursive search: {offer_item_ids} (ReqID: {request_id})")
        except Exception as e:
            logger.warning(f"[DEBUG] Recursive search for OfferItemIDs failed: {e}")
        
        logger.info(f"[DEBUG] Final extracted OfferItemIDs: {offer_item_ids} (ReqID: {request_id})")
        return offer_item_ids
