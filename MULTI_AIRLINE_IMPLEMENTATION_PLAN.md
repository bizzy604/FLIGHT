# Multi-Airline Support Implementation Plan

## Overview
This document outlines the comprehensive implementation strategy for adding multi-airline support to the FLIGHT application while preserving existing single-airline functionality. The implementation will handle airline-prefixed references, proper ThirdParty ID extraction, and maintain the current index-based offer selection interface.

## Table of Contents
1. [Current State Analysis](#current-state-analysis)
2. [Implementation Strategy](#implementation-strategy)
3. [Phase 1: Core Infrastructure](#phase-1-core-infrastructure)
4. [Phase 2: Air Shopping Enhancement](#phase-2-air-shopping-enhancement)
5. [Phase 3: Flight Pricing Enhancement](#phase-3-flight-pricing-enhancement)
6. [Phase 4: Order Creation Enhancement](#phase-4-order-creation-enhancement)
7. [Phase 5: Testing & Validation](#phase-5-testing--validation)
8. [Rollback Strategy](#rollback-strategy)
9. [Performance Considerations](#performance-considerations)

---

## Current State Analysis

### Working Single-Airline Flow
```
Air Shopping (no ThirdpartyId) → Single Airline Response → 
Transform with simple refs → Index-based selection → 
Flight Price (airline-specific ThirdpartyId) → Order Creation
```

### Multi-Airline Challenge
```
Air Shopping (no ThirdpartyId) → Multi-Airline Response → 
Transform with airline-prefixed refs → Index-based selection → 
Extract correct airline → Flight Price (correct ThirdpartyId) → Order Creation
```

### Key Differences Identified
| Aspect | Single-Airline | Multi-Airline |
|--------|----------------|---------------|
| Reference Keys | `"SEG1"`, `"PAX1"` | `"KL-SEG1"`, `"LHG-PAX1"` |
| Offer Structure | Grouped by airline | Flat array, mixed airlines |
| ThirdParty ID | Single airline code | Airline-specific extraction |
| ShoppingResponseID | Single ID | Multiple IDs per airline |

---

## Implementation Strategy

### Core Principles
1. **Backward Compatibility**: Existing single-airline flows must continue working
2. **Minimal Frontend Changes**: Preserve index-based offer selection
3. **Airline Context Preservation**: Maintain airline information throughout the pipeline
4. **Robust Error Handling**: Graceful fallbacks for edge cases
5. **Performance Optimization**: Efficient reference resolution

### Detection Strategy
Implement automatic detection of response type to route to appropriate processing logic:

```python
def _is_multi_airline_response(response: dict) -> bool:
    """Detect multi-airline response by checking reference patterns"""
    # Check for airline-prefixed segment keys
    # Check for multiple airline owners in warnings
    # Check for multiple ShoppingResponseIDs
```

---

## Phase 1: Core Infrastructure

### 1.1 Multi-Airline Detection Module
**File**: `Backend/utils/multi_airline_detector.py`

```python
class MultiAirlineDetector:
    @staticmethod
    def is_multi_airline_response(response: dict) -> bool:
        """Detect if response contains multiple airlines"""
        
    @staticmethod
    def extract_airline_codes(response: dict) -> List[str]:
        """Extract all airline codes present in response"""
        
    @staticmethod
    def get_airline_prefixed_references(response: dict) -> Dict[str, List[str]]:
        """Group references by airline prefix"""
```

**Implementation Details**:
- Check segment keys for airline prefixes (`KL-SEG1`, `LHG-SEG2`)
- Analyze warning messages for multiple airline owners
- Examine ShoppingResponseID metadata for multiple entries
- Validate against known airline code patterns

### 1.2 Enhanced Reference Extractor
**File**: `Backend/utils/reference_extractor.py`

```python
class EnhancedReferenceExtractor:
    def __init__(self, response: dict):
        self.response = response
        self.is_multi_airline = MultiAirlineDetector.is_multi_airline_response(response)
    
    def extract_references(self) -> Dict[str, Any]:
        """Extract references with airline context awareness"""
        if self.is_multi_airline:
            return self._extract_multi_airline_refs()
        else:
            return self._extract_single_airline_refs()
    
    def _extract_multi_airline_refs(self) -> Dict[str, Any]:
        """Extract airline-prefixed references"""
        # Group segments by airline: {"KL": {...}, "LHG": {...}}
        # Maintain global lookup: {"KL-SEG1": segment_data}
        
    def _extract_single_airline_refs(self) -> Dict[str, Any]:
        """Use existing simple reference extraction"""
```

### 1.3 Airline Code Mapping Service
**File**: `Backend/services/airline_mapping_service.py`

```python
class AirlineMappingService:
    # Airline code to ThirdParty ID mappings
    AIRLINE_TO_THIRD_PARTY_ID = {
        'KL': 'KL',
        'AF': 'AF',
        'LHG': 'LHG',
        'QR': 'QR',
        'EK': 'EK',
        'KQ': 'KQ',
        'ET': 'ET',
        '6E': '6E',
        'EY': 'EY',
        'TK': 'TK',
        'SQ': 'SQ',
        'GF': 'GF'
    }
    
    @classmethod
    def get_third_party_id(cls, airline_code: str) -> str:
        """Map airline code to ThirdParty ID"""
        
    @classmethod
    def validate_airline_code(cls, airline_code: str) -> bool:
        """Validate if airline code is supported"""
```

---

## Phase 2: Air Shopping Enhancement

### 2.1 Enhanced Air Shopping Transformer
**File**: `Backend/utils/air_shopping_transformer.py`

#### Current Method Enhancement:
```python
def transform_air_shopping_for_results(response: dict) -> dict:
    """Enhanced transformer with multi-airline support"""

    # Step 1: Detect response type
    is_multi_airline = MultiAirlineDetector.is_multi_airline_response(response)

    # Step 2: Extract references with appropriate strategy
    ref_extractor = EnhancedReferenceExtractor(response)
    refs = ref_extractor.extract_references()

    # Step 3: Process offers with airline context
    if is_multi_airline:
        return _transform_multi_airline_offers(response, refs)
    else:
        return _transform_single_airline_offers(response, refs)
```

#### New Multi-Airline Processing:
```python
def _transform_multi_airline_offers(response: dict, refs: dict) -> dict:
    """Transform multi-airline offers preserving airline context"""
    offers = []

    # Extract all offers from flat structure
    offers_group = response.get('OffersGroup', {})
    airline_offers_list = offers_group.get('AirlineOffers', [])

    for airline_offer_group in airline_offers_list:
        for offer in airline_offer_group.get('AirlineOffer', []):
            priced_offer = offer.get('PricedOffer')
            if priced_offer:
                # Extract airline context
                airline_code = offer.get('OfferID', {}).get('Owner', 'UNKNOWN')

                # Transform with airline-aware reference resolution
                transformed = _transform_offer_with_airline_context(
                    priced_offer, refs, offer, airline_code
                )

                if transformed:
                    # Preserve airline context for later extraction
                    transformed.update({
                        'original_offer_id': transformed.get('id'),
                        'airline_code': airline_code,
                        'third_party_id': AirlineMappingService.get_third_party_id(airline_code),
                        'id': str(len(offers)),  # Index-based ID
                        'offer_index': len(offers),
                        'is_multi_airline': True
                    })
                    offers.append(transformed)

    return {
        'offers': offers,
        'total_offers': len(offers),
        'is_multi_airline': True,
        'airlines_present': list(set(offer['airline_code'] for offer in offers)),
        'ShoppingResponseID': _extract_all_shopping_response_ids(response),
        'raw_response': response
    }
```

### 2.2 Airline-Aware Reference Resolution
```python
def _transform_offer_with_airline_context(priced_offer, refs, offer, airline_code):
    """Transform offer with airline-specific reference resolution"""

    # Get airline-specific references
    airline_refs = refs.get('by_airline', {}).get(airline_code, {})
    global_refs = refs.get('global', {})

    # Resolve segment references with airline context
    segments_data = []
    for assoc in priced_offer.get('OfferPrice', [{}])[0].get('RequestedDate', {}).get('Associations', []):
        for seg_ref in assoc.get('ApplicableFlight', {}).get('FlightSegmentReference', []):
            ref_key = seg_ref.get('ref')

            # Try airline-specific lookup first, then global
            segment_data = airline_refs.get('segments', {}).get(ref_key) or \
                          global_refs.get('segments', {}).get(ref_key)

            if segment_data:
                segments_data.append(segment_data)

    # Continue with existing transformation logic...
```

### 2.3 ShoppingResponseID Management
```python
def _extract_all_shopping_response_ids(response: dict) -> Dict[str, str]:
    """Extract all airline-specific ShoppingResponseIDs"""
    shopping_response_ids = {}

    try:
        metadata_section = response.get("Metadata", {})
        other_metadata_list = metadata_section.get("Other", {}).get("OtherMetadata", [])

        for other_metadata in other_metadata_list:
            desc_metadatas = other_metadata.get("DescriptionMetadatas", {})
            desc_metadata_list = desc_metadatas.get("DescriptionMetadata", [])

            for desc_metadata in desc_metadata_list:
                if desc_metadata.get("MetadataKey") == "SHOPPING_RESPONSE_IDS":
                    aug_points = desc_metadata.get("AugmentationPoint", {}).get("AugPoint", [])

                    for aug_point in aug_points:
                        owner = aug_point.get("Owner")
                        key = aug_point.get("Key")
                        if owner and key:
                            shopping_response_ids[owner] = key

    except Exception as e:
        logger.error(f"Error extracting ShoppingResponseIDs: {e}")

    return shopping_response_ids
```

---

## Phase 3: Flight Pricing Enhancement

### 3.1 Enhanced Flight Pricing Service
**File**: `Backend/services/flight/pricing.py`

#### Enhanced Airline Code Extraction:
```python
def _extract_airline_code_from_offer(self, airshopping_response: dict, offer_id: str) -> str:
    """Enhanced airline code extraction with multi-airline support"""

    # Detect response type
    is_multi_airline = MultiAirlineDetector.is_multi_airline_response(airshopping_response)

    if is_multi_airline:
        return self._extract_airline_from_multi_airline_offer(airshopping_response, offer_id)
    else:
        return self._extract_airline_from_single_airline_offer(airshopping_response, offer_id)

def _extract_airline_from_multi_airline_offer(self, airshopping_response: dict, offer_id: str) -> str:
    """Extract airline code from multi-airline response using offer index"""
    try:
        # Convert offer_id (index) to integer
        offer_index = int(offer_id)

        # Recreate the flattened offers array (matching transformer logic)
        offers_group = airshopping_response.get('OffersGroup', {})
        airline_offers_list = offers_group.get('AirlineOffers', [])

        all_offers = []
        for airline_offer_group in airline_offers_list:
            for offer in airline_offer_group.get('AirlineOffer', []):
                if offer.get('PricedOffer'):
                    all_offers.append(offer)

        # Get the offer at the specified index
        if 0 <= offer_index < len(all_offers):
            selected_offer = all_offers[offer_index]
            airline_code = selected_offer.get('OfferID', {}).get('Owner')

            if airline_code:
                logger.info(f"Extracted airline code '{airline_code}' from offer index {offer_index}")
                return airline_code
            else:
                logger.warning(f"No Owner found in OfferID for offer index {offer_index}")
                return 'UNKNOWN'
        else:
            logger.error(f"Offer index {offer_index} out of range (total offers: {len(all_offers)})")
            return 'UNKNOWN'

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid offer_id format for multi-airline: {offer_id}, error: {e}")
        return 'UNKNOWN'
    except Exception as e:
        logger.error(f"Error extracting airline code from multi-airline offer: {e}")
        return 'UNKNOWN'
```

#### Enhanced ShoppingResponseID Selection:
```python
def _get_shopping_response_id_for_airline(self, airshopping_response: dict, airline_code: str) -> str:
    """Get the correct ShoppingResponseID for the specific airline"""

    # For multi-airline responses, extract airline-specific ID
    if MultiAirlineDetector.is_multi_airline_response(airshopping_response):
        shopping_ids = _extract_all_shopping_response_ids(airshopping_response)
        airline_specific_id = shopping_ids.get(airline_code)

        if airline_specific_id:
            logger.info(f"Using airline-specific ShoppingResponseID for {airline_code}: {airline_specific_id}")
            return airline_specific_id
        else:
            logger.warning(f"No ShoppingResponseID found for airline {airline_code}, using first available")
            return list(shopping_ids.values())[0] if shopping_ids else ''
    else:
        # For single-airline responses, use existing logic
        return airshopping_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
```

### 3.2 Enhanced Flight Price Request Building
**File**: `Backend/scripts/build_flightprice_rq.py`

```python
def build_flight_price_request(
    air_shopping_response: dict,
    offer_id: str,
    shopping_response_id: str = '',
    currency: str = 'USD'
) -> dict:
    """Enhanced flight price request builder with multi-airline support"""

    # Detect response type and extract airline context
    is_multi_airline = MultiAirlineDetector.is_multi_airline_response(air_shopping_response)

    if is_multi_airline:
        # Extract airline code from offer index
        airline_code = _extract_airline_code_from_multi_airline_context(air_shopping_response, offer_id)

        # Get airline-specific ShoppingResponseID
        if not shopping_response_id:
            shopping_response_id = _get_shopping_response_id_for_airline(air_shopping_response, airline_code)

        # Build request with airline-specific context
        return _build_multi_airline_flight_price_request(
            air_shopping_response, offer_id, airline_code, shopping_response_id, currency
        )
    else:
        # Use existing single-airline logic
        return _build_single_airline_flight_price_request(
            air_shopping_response, offer_id, shopping_response_id, currency
        )
```

---

## Phase 4: Order Creation Enhancement

### 4.1 Enhanced Order Creation Service
**File**: `Backend/services/flight/booking.py`

#### Enhanced Airline Code Extraction for Booking:
```python
def _extract_airline_code_from_enhanced_payload(self, payload: dict, flight_price_response: dict) -> str:
    """Enhanced airline code extraction for order creation"""

    try:
        # First try to extract from the payload's ShoppingResponse Owner
        shopping_response = payload.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {})
        owner = shopping_response.get('Owner')
        if owner:
            logger.info(f"Found airline code '{owner}' in OrderCreate payload ShoppingResponse.Owner")
            return owner

        # For multi-airline responses, extract from flight price response structure
        if self._is_multi_airline_flight_price_response(flight_price_response):
            return self._extract_airline_from_multi_airline_price_response(flight_price_response)

        # Fallback to original extraction method
        return self._extract_airline_code_from_price_response(flight_price_response)

    except Exception as e:
        logger.error(f"Error extracting airline code from enhanced payload: {str(e)}", exc_info=True)
        return 'UNKNOWN'
```

### 4.2 Enhanced Order Creation Request Building
**File**: `Backend/scripts/build_ordercreate_rq.py`

```python
def build_ordercreate_rq(
    flight_price_response: Dict[str, Any],
    passenger_details: List[Dict[str, Any]],
    payment_details: Dict[str, Any],
    contact_info: Dict[str, str]
) -> Dict[str, Any]:
    """Enhanced OrderCreate request builder with multi-airline support"""

    # Detect if this is a multi-airline flight price response
    is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)

    if is_multi_airline:
        # Extract airline context from flight price response
        airline_code = _extract_airline_from_multi_airline_price_response(flight_price_response)

        # Build order create request with airline-specific context
        return _build_multi_airline_order_create_request(
            flight_price_response, passenger_details, payment_details, contact_info, airline_code
        )
    else:
        # Use existing single-airline logic
        return _build_single_airline_order_create_request(
            flight_price_response, passenger_details, payment_details, contact_info
        )
```

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests
**File**: `Backend/tests/test_multi_airline_support.py`

```python
class TestMultiAirlineSupport(unittest.TestCase):

    def setUp(self):
        # Load test data
        with open('postman/airshopingresponse.json', 'r') as f:
            self.multi_airline_response = json.load(f)

        with open('tests/single_airline_response.json', 'r') as f:
            self.single_airline_response = json.load(f)

    def test_multi_airline_detection(self):
        """Test detection of multi-airline responses"""

    def test_airline_code_extraction(self):
        """Test airline code extraction from offers"""

    def test_reference_resolution(self):
        """Test airline-prefixed reference resolution"""

    def test_shopping_response_id_extraction(self):
        """Test extraction of airline-specific ShoppingResponseIDs"""

    def test_backward_compatibility(self):
        """Test that single-airline responses still work"""
```

### 5.2 Integration Tests
**File**: `Backend/tests/test_multi_airline_integration.py`

```python
class TestMultiAirlineIntegration(unittest.TestCase):

    def test_complete_flow_kl_airline(self):
        """Test complete flow: Air Shopping → Flight Price → Order Create for KL"""

    def test_complete_flow_qr_airline(self):
        """Test complete flow for Qatar Airways"""

    def test_complete_flow_af_airline(self):
        """Test complete flow for Air France"""

    def test_mixed_airline_selection(self):
        """Test selecting different airlines in same session"""
```

### 5.3 Performance Tests
```python
def test_transformation_performance(self):
    """Ensure multi-airline transformation doesn't significantly impact performance"""

def test_memory_usage(self):
    """Monitor memory usage with large multi-airline responses"""
```

---

## Rollback Strategy

### Immediate Rollback Options
1. **Feature Flag**: Implement feature flag to disable multi-airline processing
2. **Fallback Logic**: Automatic fallback to single-airline processing on errors
3. **Configuration Switch**: Environment variable to control multi-airline behavior

### Rollback Implementation
```python
# Environment variable control
ENABLE_MULTI_AIRLINE = os.getenv('ENABLE_MULTI_AIRLINE', 'true').lower() == 'true'

def transform_air_shopping_for_results(response: dict) -> dict:
    if not ENABLE_MULTI_AIRLINE:
        return _legacy_transform_air_shopping_for_results(response)

    # New multi-airline logic with fallback
    try:
        return _enhanced_transform_air_shopping_for_results(response)
    except Exception as e:
        logger.error(f"Multi-airline transformation failed, falling back: {e}")
        return _legacy_transform_air_shopping_for_results(response)
```

---

## Performance Considerations

### Optimization Strategies
1. **Lazy Loading**: Load airline-specific references only when needed
2. **Caching**: Cache airline mappings and reference lookups
3. **Batch Processing**: Process multiple offers efficiently
4. **Memory Management**: Optimize large response handling

### Monitoring Points
1. **Transformation Time**: Monitor air shopping transformation performance
2. **Memory Usage**: Track memory consumption with large responses
3. **API Response Times**: Monitor flight price/order create response times
4. **Error Rates**: Track multi-airline specific errors

### Performance Targets
- Air shopping transformation: < 2 seconds for responses with 100+ offers
- Memory usage: < 50MB increase for large multi-airline responses
- API response times: No more than 10% increase over single-airline

---

## Implementation Timeline

### Week 1-2: Core Infrastructure
- Implement multi-airline detection
- Create enhanced reference extractor
- Set up airline mapping service
- Unit tests for core components

### Week 3-4: Air Shopping Enhancement
- Enhance air shopping transformer
- Implement airline-aware reference resolution
- Add ShoppingResponseID management
- Integration tests for air shopping

### Week 5-6: Flight Pricing Enhancement
- Enhance flight pricing service
- Update flight price request building
- Add airline-specific header management
- Integration tests for flight pricing

### Week 7-8: Order Creation Enhancement
- Enhance order creation service
- Update order create request building
- End-to-end integration tests
- Performance optimization

### Week 9-10: Testing & Deployment
- Comprehensive testing with real data
- Performance testing and optimization
- Documentation and deployment
- Monitoring and rollback preparation

---

## Success Criteria

### Functional Requirements
- ✅ Multi-airline air shopping responses processed correctly
- ✅ Correct airline-specific ThirdParty ID extraction and usage
- ✅ Proper reference resolution for airline-prefixed keys
- ✅ Backward compatibility with single-airline responses
- ✅ Index-based offer selection preserved

### Performance Requirements
- ✅ Transformation time < 2 seconds for 100+ offers
- ✅ Memory usage increase < 50MB
- ✅ API response time increase < 10%

### Quality Requirements
- ✅ 95%+ test coverage for new components
- ✅ Zero regression in existing functionality
- ✅ Comprehensive error handling and logging
- ✅ Clear rollback strategy implemented

---

## Key Implementation Notes

### ThirdParty ID Strategy
The most critical aspect of multi-airline support is proper ThirdParty ID extraction and usage:

1. **Air Shopping**: No ThirdpartyId header → Returns all airlines
2. **Offer Selection**: Extract airline code from selected offer index
3. **Flight Price**: Use airline-specific ThirdpartyId header
4. **Order Creation**: Maintain airline context throughout

### Reference Resolution Strategy
Multi-airline responses require enhanced reference resolution:

1. **Detection**: Identify airline-prefixed references (`KL-SEG1`, `LHG-PAX1`)
2. **Grouping**: Organize references by airline for efficient lookup
3. **Resolution**: Use airline-aware lookup with global fallback
4. **Validation**: Ensure all references resolve correctly

### Backward Compatibility Strategy
Maintain existing functionality while adding new capabilities:

1. **Detection**: Automatically identify response type
2. **Routing**: Use appropriate processing logic based on detection
3. **Fallback**: Graceful degradation on errors
4. **Testing**: Comprehensive validation of existing flows

This implementation plan provides a systematic approach to adding multi-airline support while maintaining system stability and performance. Each phase builds upon the previous one, ensuring a robust and maintainable solution.
```
