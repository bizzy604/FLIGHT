/**
 * Test script to validate baggage and fare rules integration in itinerary system
 * This test uses the OrdercreateRS.json file to verify data extraction and mapping
 */

const fs = require('fs');
const path = require('path');

// Import the transformer function (we'll need to adjust the import for Node.js)
// For now, we'll copy the relevant functions here for testing

// Test data loading
function loadTestData() {
  try {
    const testDataPath = path.join(__dirname, '..', 'OrdercreateRS.json');
    const rawData = fs.readFileSync(testDataPath, 'utf8');
    return JSON.parse(rawData);
  } catch (error) {
    console.error('Error loading test data:', error);
    return null;
  }
}

// Simplified baggage extraction function for testing
function extractBaggageDetails(orderCreateResponse) {
  const response = orderCreateResponse.Response || orderCreateResponse;
  const dataLists = response.DataLists;
  
  // Extract checked bag allowance
  const checkedBagAllowance = dataLists?.CheckedBagAllowanceList?.CheckedBagAllowance || [];
  const carryOnAllowance = dataLists?.CarryOnAllowanceList?.CarryOnAllowance || [];
  
  // Get basic baggage info from ticket documents
  const baggageInfo = response.TicketDocInfos?.TicketDocInfo?.[0]?.TicketDocument?.[0]?.CouponInfo?.[0]?.AddlBaggageInfo;
  
  let checkedBagDetails = null;
  let carryOnDetails = null;
  
  // Process checked bag allowance
  if (checkedBagAllowance.length > 0) {
    const checkedBag = checkedBagAllowance[0];
    if (checkedBag.PieceAllowance) {
      checkedBagDetails = {
        pieces: checkedBag.PieceAllowance[0]?.TotalQuantity || 0,
        description: 'Checked Bag Allowance'
      };
    } else if (checkedBag.WeightAllowance) {
      checkedBagDetails = {
        weight: {
          value: checkedBag.WeightAllowance.MaximumWeight[0]?.Value || 0,
          unit: checkedBag.WeightAllowance.MaximumWeight[0]?.UOM || 'Kilogram'
        },
        description: 'Checked Bag Weight Allowance'
      };
    }
  }
  
  // Process carry-on allowance
  if (carryOnAllowance.length > 0) {
    const carryOn = carryOnAllowance[0];
    if (carryOn.PieceAllowance) {
      carryOnDetails = {
        pieces: carryOn.PieceAllowance[0]?.TotalQuantity || 0,
        description: 'Carry-On Bag Allowance'
      };
    }
  }
  
  return {
    checkedBags: baggageInfo?.AllowableBag?.[0]?.Number || checkedBagDetails?.pieces || 1,
    carryOnBags: carryOnDetails?.pieces || 1,
    checkedBagAllowance: checkedBagDetails,
    carryOnAllowance: carryOnDetails
  };
}

// Simplified fare rules extraction function for testing
function extractFareRules(orderCreateResponse) {
  const response = orderCreateResponse.Response || orderCreateResponse;
  const penalties = response.DataLists?.PenaltyList?.Penalty || [];
  const passengers = response.Passengers?.Passenger || [];
  
  const fareRulesByPassenger = {};
  
  // Process penalties
  penalties.forEach((penalty) => {
    const details = penalty.Details?.Detail?.[0];
    if (!details) return;
    
    const rule = {
      type: details.Type,
      application: getApplicationDescription(details.Application?.Code),
      timing: getTimingDescription(details.Application?.Code),
      minAmount: details.Amounts?.Amount?.[0]?.CurrencyAmountValue?.value || 0,
      maxAmount: details.Amounts?.Amount?.[1]?.CurrencyAmountValue?.value || 0,
      currency: details.Amounts?.Amount?.[0]?.CurrencyAmountValue?.Code || 'USD',
      description: details.Amounts?.Amount?.[0]?.ApplicableFeeRemarks?.Remark?.[0]?.value || '',
      allowed: penalty.CancelFeeInd !== false || penalty.ChangeFeeInd !== false || penalty.RefundableInd !== false || penalty.ChangeAllowedInd !== false
    };
    
    // Extract passenger reference from penalty ObjectKey
    const objectKey = penalty.ObjectKey || '';
    const passengerMatch = objectKey.match(/PAX(\d+)/);
    if (passengerMatch) {
      const passengerKey = `PAX${passengerMatch[1]}`;
      if (!fareRulesByPassenger[passengerKey]) {
        fareRulesByPassenger[passengerKey] = [];
      }
      fareRulesByPassenger[passengerKey].push(rule);
    }
  });
  
  // Map to passenger types
  const result = [];
  passengers.forEach((passenger) => {
    const passengerKey = passenger.ObjectKey;
    const passengerType = passenger.PTC?.value || 'ADT';
    const rules = fareRulesByPassenger[passengerKey] || [];
    
    if (rules.length > 0) {
      result.push({
        passengerType,
        rules
      });
    }
  });
  
  return result;
}

// Helper functions
function getApplicationDescription(code) {
  const descriptions = {
    '1': 'After Departure - No Show',
    '2': 'Before Departure',
    '3': 'After Departure',
    '4': 'Before Departure - No Show'
  };
  return descriptions[code] || 'Standard';
}

function getTimingDescription(code) {
  const timings = {
    '1': 'After departure with no-show penalty',
    '2': 'Before departure standard timing',
    '3': 'After departure standard timing',
    '4': 'Before departure with no-show penalty'
  };
  return timings[code] || 'Standard timing';
}

// Test functions
function testBaggageExtraction(testData) {
  console.log('\n=== TESTING BAGGAGE EXTRACTION ===');
  
  const baggageDetails = extractBaggageDetails(testData);
  
  console.log('Extracted Baggage Details:');
  console.log(JSON.stringify(baggageDetails, null, 2));
  
  // Validation checks
  const checks = [
    { name: 'Has checked bags count', pass: typeof baggageDetails.checkedBags === 'number' },
    { name: 'Has carry-on bags count', pass: typeof baggageDetails.carryOnBags === 'number' },
    { name: 'Has checked bag allowance details', pass: baggageDetails.checkedBagAllowance !== null },
    { name: 'Has carry-on allowance details', pass: baggageDetails.carryOnAllowance !== null }
  ];
  
  console.log('\nBaggage Extraction Validation:');
  checks.forEach(check => {
    console.log(`  ${check.pass ? '✅' : '❌'} ${check.name}`);
  });
  
  return checks.every(check => check.pass);
}

function testFareRulesExtraction(testData) {
  console.log('\n=== TESTING FARE RULES EXTRACTION ===');
  
  const fareRules = extractFareRules(testData);
  
  console.log(`Extracted Fare Rules for ${fareRules.length} passenger types:`);
  fareRules.forEach((passengerRules, index) => {
    console.log(`\n${index + 1}. Passenger Type: ${passengerRules.passengerType}`);
    console.log(`   Rules Count: ${passengerRules.rules.length}`);
    
    passengerRules.rules.slice(0, 3).forEach((rule, ruleIndex) => {
      console.log(`   Rule ${ruleIndex + 1}: ${rule.type} - ${rule.application}`);
      console.log(`     Min: ${rule.minAmount} ${rule.currency}, Max: ${rule.maxAmount} ${rule.currency}`);
      console.log(`     Allowed: ${rule.allowed}`);
    });
    
    if (passengerRules.rules.length > 3) {
      console.log(`   ... and ${passengerRules.rules.length - 3} more rules`);
    }
  });
  
  // Validation checks
  const checks = [
    { name: 'Has fare rules data', pass: fareRules.length > 0 },
    { name: 'All passenger types have rules', pass: fareRules.every(pr => pr.rules.length > 0) },
    { name: 'Rules have required fields', pass: fareRules.every(pr => 
      pr.rules.every(rule => 
        rule.type && rule.application && typeof rule.minAmount === 'number'
      )
    )}
  ];
  
  console.log('\nFare Rules Extraction Validation:');
  checks.forEach(check => {
    console.log(`  ${check.pass ? '✅' : '❌'} ${check.name}`);
  });
  
  return checks.every(check => check.pass);
}

function testDataStructureMapping(testData) {
  console.log('\n=== TESTING DATA STRUCTURE MAPPING ===');

  const response = testData.Response || testData;

  // Test key data structure paths
  const structureChecks = [
    {
      name: 'DataLists.CheckedBagAllowanceList exists',
      pass: !!response.DataLists?.CheckedBagAllowanceList
    },
    {
      name: 'DataLists.CarryOnAllowanceList exists',
      pass: !!response.DataLists?.CarryOnAllowanceList
    },
    {
      name: 'DataLists.PenaltyList exists',
      pass: !!response.DataLists?.PenaltyList
    },
    {
      name: 'Passengers data exists',
      pass: !!response.Passengers?.Passenger
    },
    {
      name: 'TicketDocInfos exists',
      pass: !!response.TicketDocInfos
    }
  ];
  
  console.log('Data Structure Validation:');
  structureChecks.forEach(check => {
    console.log(`  ${check.pass ? '✅' : '❌'} ${check.name}`);
  });
  
  return structureChecks.every(check => check.pass);
}

// Main test execution
function runTests() {
  console.log('🧪 BAGGAGE AND FARE RULES INTEGRATION TEST');
  console.log('==========================================');
  
  const testData = loadTestData();
  if (!testData) {
    console.error('❌ Failed to load test data');
    return;
  }
  
  console.log('✅ Test data loaded successfully');
  console.log(`📊 Data contains ${Object.keys(testData).length} top-level keys`);
  
  const results = {
    dataStructure: testDataStructureMapping(testData),
    baggageExtraction: testBaggageExtraction(testData),
    fareRulesExtraction: testFareRulesExtraction(testData)
  };
  
  console.log('\n=== FINAL TEST RESULTS ===');
  Object.entries(results).forEach(([testName, passed]) => {
    console.log(`${passed ? '✅' : '❌'} ${testName}: ${passed ? 'PASSED' : 'FAILED'}`);
  });
  
  const allPassed = Object.values(results).every(result => result);
  console.log(`\n🎯 Overall Result: ${allPassed ? 'ALL TESTS PASSED' : 'SOME TESTS FAILED'}`);
  
  return allPassed;
}

// Run the tests
if (require.main === module) {
  runTests();
}

module.exports = {
  runTests,
  extractBaggageDetails,
  extractFareRules,
  loadTestData
};
