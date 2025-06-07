# Advanced Penalty Structure Enhancement Implementation Plan

## Background and Motivation

Based on comprehensive penalty documentation provided, the current basic penalty implementation needs significant enhancement to support complex penalty calculations, MIN/MAX penalty ranges, OD-level aggregation, and different trip types. The current implementation only handles basic penalty mapping without the sophisticated logic required for production-ready penalty calculations.

### Current Implementation Status
- ✅ Basic penalty extraction from API responses
- ✅ Simple penalty type mapping (Change, Cancel)
- ✅ Basic application mapping (Prior to Departure, After Departure, No Show)
- ✅ Structured FareRules format for frontend compatibility

### Advanced Requirements Identified
- **Application Code Mapping**: Correct interpretation of API Application.Code values (1-4)
- **MIN/MAX Penalty Calculations**: Calculate penalty ranges across segments
- **OD-Level Aggregation**: Show penalties at Origin-Destination level vs segment level
- **Trip Type Support**: One-way, Round-trip, Multi-city penalty logic
- **Passenger Category Support**: ADT, Young Adult, CHD, INFT specific penalties
- **UI Representation**: Agency UI penalty display at OD/Itinerary level

## API Structure Documentation

### Penalty Data Location
**Path**: `JSON.DataLists.PenaltyList.Penalty[0].Details.Detail[0].Application.Code`

### Application Code Definitions (CRITICAL)
- **Code "1"**: After Departure NO Show
- **Code "2"**: Prior to Departure
- **Code "3"**: After Departure  
- **Code "4"**: Before Departure No Show

### Complete Penalty Structure Example
```json
{
  "ObjectKey": "KQ-PEN3",
  "Details": {
    "Detail": [
      {
        "Type": "Cancel",
        "Application": {
          "Code": "2"
        },
        "Amounts": {
          "Amount": [
            {
              "CurrencyAmountValue": {
                "value": 0,
                "Code": "INR"
              },
              "AmountApplication": "MIN",
              "ApplicableFeeRemarks": {
                "Remark": [
                  {
                    "value": "Cancel permitted"
                  }
                ]
              }
            },
            {
              "CurrencyAmountValue": {
                "value": 0,
                "Code": "INR"
              },
              "AmountApplication": "MAX",
              "ApplicableFeeRemarks": {
                "Remark": [
                  {
                    "value": "Cancel permitted"
                  }
                ]
              }
            }
          ]
        }
      }
    ]
  },
  "CancelFeeInd": false,
  "RefundableInd": true
}
```

### Key API Fields
- **ObjectKey**: Penalty reference identifier
- **Type**: Penalty type ("Cancel", "Change", etc.)
- **Application.Code**: Timing code ("1", "2", "3", "4")
- **AmountApplication**: "MIN" or "MAX" for penalty ranges
- **CurrencyAmountValue**: Penalty amount and currency
- **CancelFeeInd**: Boolean indicating if cancellation fee applies
- **RefundableInd**: Boolean indicating if ticket is refundable

## Key Challenges and Analysis

### 1. Application Code Mapping (CRITICAL)
- **API Structure**: `JSON.DataLists.PenaltyList.Penalty[0].Details.Detail[0].Application.Code`
- **Code Definitions**:
  - **Code "1"**: After Departure NO Show
  - **Code "2"**: Prior to Departure  
  - **Code "3"**: After Departure
  - **Code "4"**: Before Departure No Show
- **Current Gap**: Basic implementation doesn't properly map these specific application codes
- **Solution Required**: Update penalty extraction to correctly interpret Application.Code values

### 2. MIN/MAX Penalty Calculation Logic
- **Challenge**: API consumers must consider maximum value as max penalty and lowest value as minimum penalty across all segments
- **API Structure**: `Amounts.Amount[].AmountApplication` ("MIN" or "MAX")
- **Current Gap**: No aggregation logic for penalty ranges
- **Solution Required**: Implement penalty range calculation across segments for each penalty type

### 3. OD-Level vs Segment-Level Penalty Aggregation
- **Challenge**: Different penalty structures for Origin-Destination vs individual segments
- **Current Gap**: Only segment-level penalty extraction
- **Solution Required**: Aggregate segment penalties to OD level with proper MIN/MAX calculations

### 4. Trip Type Specific Logic
- **Challenge**: Different penalty calculation rules for one-way, round-trip, and multi-city trips
- **Current Gap**: No trip type awareness in penalty calculations
- **Solution Required**: Implement trip type detection and specific penalty aggregation logic

### 5. Passenger Category Support
- **Challenge**: Different penalties for ADT, Young Adult, CHD, INFT
- **Current Gap**: No passenger category consideration
- **Solution Required**: Extract and apply passenger-specific penalty rules

### 6. Frontend Display Requirements
- **Challenge**: UI needs to show penalty ranges (MIN-MAX) appropriately
- **Current Gap**: Frontend only shows single penalty values
- **Solution Required**: Update frontend components to display penalty ranges

## High-level Task Breakdown

### Phase 1: Backend Penalty Enhancement

#### Task 1.1: Create Feature Branch
- **Success Criteria**: Feature branch `feature/advanced-penalty-structure` created from main
- **Commands**: 
  ```bash
  git checkout main
  git pull origin main
  git checkout -b feature/advanced-penalty-structure
  ```

#### Task 1.2: Fix Application Code Mapping (CRITICAL)
- **Success Criteria**: 
  - Correct interpretation of Application.Code values ("1", "2", "3", "4")
  - Proper mapping to penalty timing categories
  - Updated penalty extraction to use Application.Code instead of string matching
  - Unit tests pass for all application code scenarios
- **Files to Modify**: 
  - `Backend/utils/data_transformer.py`
- **Implementation Details**:
  - Update `_extract_penalty_info()` to read `Application.Code` from API structure
  - Map codes correctly: 1=After Departure NO Show, 2=Prior to Departure, 3=After Departure, 4=Before Departure No Show
  - Remove existing string-based application detection logic
  - Add comprehensive logging for penalty code mapping

#### Task 1.3: Enhance Penalty Extraction with MIN/MAX Logic
- **Success Criteria**: 
  - `_extract_penalty_info()` function enhanced to calculate MIN/MAX penalty ranges
  - Support for segment-level penalty aggregation using `AmountApplication` field
  - Proper handling of missing penalty data (assume max value)
  - Unit tests pass for penalty range calculations
- **Files to Modify**: 
  - `Backend/utils/data_transformer.py`
- **Implementation Details**:
  - Parse `Amounts.Amount[]` array for MIN/MAX values
  - Use `AmountApplication` field to identify MIN vs MAX amounts
  - Add penalty range calculation logic
  - Implement segment-level penalty aggregation
  - Handle edge cases for missing penalty data

#### Task 1.4: Implement OD-Level Penalty Aggregation
- **Success Criteria**: 
  - Penalties aggregated at Origin-Destination level
  - Proper MIN/MAX calculation across all segments in an OD
  - Support for one-way, round-trip, and multi-city trip types
  - Unit tests pass for OD-level aggregation
- **Files to Modify**: 
  - `Backend/utils/data_transformer.py`
- **Implementation Details**:
  - Add trip type detection logic
  - Implement OD-level penalty aggregation
  - Calculate MIN/MAX across segments within each OD

#### Task 1.5: Add Passenger Category Support
- **Success Criteria**: 
  - Extract passenger category-specific penalties (ADT, Young Adult, CHD, INFT)
  - Apply appropriate penalty rules based on passenger category
  - Maintain backward compatibility with existing penalty structure
  - Unit tests pass for passenger category handling
- **Files to Modify**: 
  - `Backend/utils/data_transformer.py`
- **Implementation Details**:
  - Add passenger category detection
  - Implement category-specific penalty extraction
  - Update penalty transformation logic

#### Task 1.6: Update FareRules Structure for Penalty Ranges
- **Success Criteria**: 
  - FareRules structure updated to include penalty ranges (min/max)
  - Backward compatibility maintained
  - Frontend receives penalty range data
  - Unit tests pass for updated structure
- **Files to Modify**: 
  - `Backend/utils/data_transformer.py`
- **Implementation Details**:
  - Update `_transform_penalties_to_fare_rules()` function
  - Add penalty range fields to FareRules structure
  - Maintain existing penalty format for compatibility

### Phase 2: Frontend Penalty Display Enhancement

#### Task 2.1: Update TypeScript Interfaces
- **Success Criteria**: 
  - TypeScript interfaces updated to support penalty ranges
  - Proper typing for MIN/MAX penalty values
  - Backward compatibility maintained
  - TypeScript compilation passes
- **Files to Modify**: 
  - `Frontend/types/flight-api.ts`
- **Implementation Details**:
  - Add penalty range fields to FareRules interface
  - Update penalty-related type definitions
  - Ensure backward compatibility

#### Task 2.2: Enhance Fare Rules Component
- **Success Criteria**: 
  - Fare rules component displays penalty ranges appropriately
  - Shows MIN-MAX penalty values when available
  - Graceful fallback for single penalty values
  - UI tests pass for penalty range display
- **Files to Modify**: 
  - `Frontend/components/fare-rules.tsx`
- **Implementation Details**:
  - Update component to handle penalty ranges
  - Add UI elements for MIN-MAX display
  - Implement responsive design for penalty information

#### Task 2.3: Update Flight Card Components
- **Success Criteria**: 
  - Flight cards show penalty summary with ranges
  - Consistent penalty display across all flight components
  - Proper formatting for penalty ranges
  - UI tests pass for flight card penalty display
- **Files to Modify**: 
  - `Frontend/components/enhanced-flight-card.tsx`
  - `Frontend/components/flight-card.tsx`
- **Implementation Details**:
  - Update penalty display logic
  - Add penalty range formatting
  - Ensure consistent UI across components

### Phase 3: Testing and Validation

#### Task 3.1: Create Comprehensive Test Suite
- **Success Criteria**: 
  - Unit tests for all penalty calculation functions
  - Integration tests for penalty data flow
  - Test coverage > 90% for penalty-related code
  - All tests pass
- **Files to Create**: 
  - `Backend/tests/test_advanced_penalties.py`
  - `Frontend/tests/penalty-components.test.tsx`
- **Implementation Details**:
  - Test MIN/MAX penalty calculations
  - Test OD-level aggregation logic
  - Test trip type specific calculations
  - Test passenger category handling

#### Task 3.2: Create Test Data and Documentation
- **Success Criteria**: 
  - Test data covering all penalty scenarios including Application Code mapping
  - Documentation for penalty calculation logic
  - Examples for different trip types
  - API documentation updated
- **Files to Create**: 
  - `Backend/tests/data/penalty_test_cases.json`
  - `docs/penalty-calculation-guide.md`
- **Implementation Details**:
  - Create comprehensive test data with all Application.Code scenarios (1-4)
  - Test MIN/MAX penalty amount parsing
  - Document penalty calculation algorithms
  - Provide usage examples for each Application Code

## Application Code Test Cases (CRITICAL)

### Test Case 1: Prior to Departure (Code "2")
```json
{
  "ObjectKey": "TEST-PEN-2",
  "Details": {
    "Detail": [{
      "Type": "Cancel",
      "Application": { "Code": "2" },
      "Amounts": {
        "Amount": [
          { "CurrencyAmountValue": { "value": 100, "Code": "USD" }, "AmountApplication": "MIN" },
          { "CurrencyAmountValue": { "value": 200, "Code": "USD" }, "AmountApplication": "MAX" }
        ]
      }
    }]
  }
}
```
**Expected Result**: `cancelBeforeDeparture` with fee range 100-200 USD

### Test Case 2: After Departure (Code "3")
```json
{
  "ObjectKey": "TEST-PEN-3",
  "Details": {
    "Detail": [{
      "Type": "Change",
      "Application": { "Code": "3" },
      "Amounts": {
        "Amount": [
          { "CurrencyAmountValue": { "value": 150, "Code": "USD" }, "AmountApplication": "MIN" },
          { "CurrencyAmountValue": { "value": 300, "Code": "USD" }, "AmountApplication": "MAX" }
        ]
      }
    }]
  }
}
```
**Expected Result**: `changeAfterDeparture` with fee range 150-300 USD

### Test Case 3: After Departure NO Show (Code "1")
```json
{
  "ObjectKey": "TEST-PEN-1",
  "Details": {
    "Detail": [{
      "Type": "Cancel",
      "Application": { "Code": "1" },
      "Amounts": {
        "Amount": [
          { "CurrencyAmountValue": { "value": 500, "Code": "USD" }, "AmountApplication": "MAX" }
        ]
      }
    }]
  }
}
```
**Expected Result**: `cancelNoShow` with fee 500 USD (assume as MAX when no MIN provided)

### Test Case 4: Before Departure No Show (Code "4")
```json
{
  "ObjectKey": "TEST-PEN-4",
  "Details": {
    "Detail": [{
      "Type": "Change",
      "Application": { "Code": "4" },
      "Amounts": {
        "Amount": [
          { "CurrencyAmountValue": { "value": 250, "Code": "USD" }, "AmountApplication": "MIN" },
          { "CurrencyAmountValue": { "value": 400, "Code": "USD" }, "AmountApplication": "MAX" }
        ]
      }
    }]
  }
}
```
**Expected Result**: `changeNoShow` with fee range 250-400 USD

## Branch Name
`feature/advanced-penalty-structure`

## Project Status Board

### Phase 1: Backend Penalty Enhancement
- [ ] Task 1.1: Create Feature Branch
- [ ] Task 1.2: Fix Application Code Mapping (CRITICAL)
- [ ] Task 1.3: Enhance Penalty Extraction with MIN/MAX Logic
- [ ] Task 1.4: Implement OD-Level Penalty Aggregation
- [ ] Task 1.5: Add Passenger Category Support
- [ ] Task 1.6: Update FareRules Structure for Penalty Ranges

### Phase 2: Frontend Penalty Display Enhancement
- [ ] Task 2.1: Update TypeScript Interfaces
- [ ] Task 2.2: Enhance Fare Rules Component
- [ ] Task 2.3: Update Flight Card Components

### Phase 3: Testing and Validation
- [ ] Task 3.1: Create Comprehensive Test Suite
- [ ] Task 3.2: Create Test Data and Documentation

## Current Status / Progress Tracking

**Current Phase**: Planning Phase
**Last Updated**: 2025-01-07
**Next Milestone**: Task 1.1 - Create Feature Branch

### Recent Progress
- ✅ Analyzed comprehensive penalty documentation
- ✅ Identified advanced penalty requirements
- ✅ Created detailed implementation plan
- ✅ Documented current implementation gaps

### Blockers
- None currently - ready to proceed with implementation

## Executor's Feedback or Assistance Requests

### Questions for Planner
1. Should we implement all penalty enhancements in a single feature branch or break into smaller incremental changes?
2. Are there specific UI/UX requirements for displaying penalty ranges?
3. Should we prioritize certain trip types (one-way vs round-trip vs multi-city) for initial implementation?
4. Any specific testing frameworks or validation requirements for penalty calculations?

### Technical Considerations
- Need to ensure backward compatibility with existing penalty structure
- Consider performance implications of complex penalty calculations
- Plan for error handling when penalty data is incomplete
- Consider caching strategies for penalty calculations

## Lessons Learned

### [2025-01-07] Penalty Documentation Analysis
- **Finding**: Penalty calculations are significantly more complex than initially implemented
- **Finding**: MIN/MAX penalty logic requires aggregation across multiple segments
- **Finding**: Different trip types require different penalty calculation approaches
- **Recommendation**: Implement penalty enhancements incrementally with comprehensive testing

### [2025-01-07] Current Implementation Assessment
- **Finding**: Basic penalty implementation provides good foundation for enhancement
- **Finding**: Existing penalty extraction logic can be extended rather than rewritten
- **Finding**: Frontend components already support structured penalty data
- **Recommendation**: Build upon existing implementation rather than starting from scratch