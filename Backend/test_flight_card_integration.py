"""
Integration test for Multi-Airline Flight Card Generator with real data

This script tests the complete integration of:
1. Enhanced Air Shopping Transformer (Phase 2.1)
2. Multi-Airline Flight Card Generator (Phase 2.2)

Using the real multi-airline test data from postman/airshopingresponse.json

Author: FLIGHT Application
Created: 2025-07-02
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from transformers.enhanced_air_shopping_transformer import transform_air_shopping_for_results_enhanced
from utils.multi_airline_flight_card_generator import generate_enhanced_flight_cards


def test_complete_integration():
    """Test complete integration with real multi-airline data."""
    print("🚀 Starting Complete Integration Test")
    print("=" * 70)
    
    # Load the multi-airline test data
    test_data_path = Path(__file__).parent.parent / "postman" / "airshopingresponse.json"
    
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            response = json.load(f)
        print(f"✅ Loaded test data from {test_data_path}")
    except FileNotFoundError:
        print(f"❌ Test data file not found: {test_data_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in test data file: {e}")
        return False
    
    print("\n📊 Phase 2.1: Enhanced Air Shopping Transformation")
    print("-" * 50)
    
    # Step 1: Transform air shopping response
    start_time = datetime.now()
    try:
        transformed_result = transform_air_shopping_for_results_enhanced(response)
        transform_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Transformation completed in {transform_time:.3f} seconds")
        print(f"   📈 Total offers: {transformed_result['metadata']['total_offers']}")
        print(f"   🏢 Airlines detected: {transformed_result['metadata']['airline_count']}")
        print(f"   🎯 Multi-airline: {transformed_result['metadata']['is_multi_airline']}")

        offers = transformed_result['offers']
        
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        return False
    
    print("\n🎨 Phase 2.2: Enhanced Flight Card Generation")
    print("-" * 50)
    
    # Step 2: Generate enhanced flight cards
    start_time = datetime.now()
    try:
        # Test with first 10 offers for performance
        test_offers = offers[:10]
        enhanced_cards = generate_enhanced_flight_cards(response, test_offers)
        card_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Flight card generation completed in {card_time:.3f} seconds")
        print(f"   🎴 Cards generated: {len(enhanced_cards)}")
        
        # Analyze the enhanced cards
        if enhanced_cards:
            print(f"\n📋 Enhanced Card Analysis:")
            
            # Check first card structure
            first_card = enhanced_cards[0]
            print(f"   🆔 First card ID: {first_card.get('id')}")
            print(f"   ✈️  Airline: {first_card.get('airline', {}).get('name')} ({first_card.get('airline', {}).get('code')})")
            print(f"   💰 Price: {first_card.get('price')} {first_card.get('currency')}")
            print(f"   🛫 Route: {first_card.get('departure', {}).get('airport')} → {first_card.get('arrival', {}).get('airport')}")
            
            # Check enhanced features
            if 'airline_context' in first_card:
                context = first_card['airline_context']
                print(f"   🔗 ThirdParty ID: {context.get('third_party_id')}")
                print(f"   🏆 Airline Priority: {context.get('airline_priority')}")
                print(f"   📊 Multi-airline: {context.get('is_multi_airline_response')}")
            
            if 'display_enhancements' in first_card:
                display = first_card['display_enhancements']
                print(f"   🎯 Recommendation Score: {display.get('recommendation_score')}")
                print(f"   📈 Price Confidence: {display.get('price_confidence')}")
                print(f"   🔧 Booking Complexity: {display.get('booking_complexity')}")
            
            if 'compatibility' in first_card:
                compatibility = first_card['compatibility']
                features = [k for k, v in compatibility.items() if v]
                print(f"   ✨ Supported Features: {', '.join(features[:3])}{'...' if len(features) > 3 else ''}")
            
            # Check multi-airline context
            if 'multi_airline_context' in first_card:
                multi_context = first_card['multi_airline_context']
                print(f"   🌐 Total Airlines: {multi_context.get('total_airlines_in_response')}")
                print(f"   🥇 Price Rank: {multi_context.get('airline_rank_by_price')}")
                advantages = multi_context.get('competitive_advantages', [])
                if advantages:
                    print(f"   🏅 Advantages: {', '.join(advantages)}")
            
            # Test different airlines
            airline_counts = {}
            for card in enhanced_cards:
                airline = card.get('airline', {}).get('code', 'Unknown')
                airline_counts[airline] = airline_counts.get(airline, 0) + 1
            
            print(f"\n📊 Airline Distribution in Test Cards:")
            for airline, count in sorted(airline_counts.items()):
                print(f"   {airline}: {count} cards")
        
    except Exception as e:
        print(f"❌ Flight card generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🔍 Integration Validation")
    print("-" * 50)
    
    # Validation checks
    validation_passed = True
    
    # Check 1: All cards have required fields
    required_fields = ['id', 'airline', 'price', 'currency', 'departure', 'arrival']
    for i, card in enumerate(enhanced_cards):
        missing_fields = [field for field in required_fields if field not in card]
        if missing_fields:
            print(f"❌ Card {i} missing fields: {missing_fields}")
            validation_passed = False
    
    if validation_passed:
        print("✅ All cards have required fields")
    
    # Check 2: Enhanced features present
    enhanced_features = ['airline_context', 'display_enhancements', 'compatibility']
    enhanced_count = 0
    for card in enhanced_cards:
        if all(feature in card for feature in enhanced_features):
            enhanced_count += 1
    
    if enhanced_count == len(enhanced_cards):
        print("✅ All cards have enhanced features")
    else:
        print(f"⚠️  Only {enhanced_count}/{len(enhanced_cards)} cards have all enhanced features")
    
    # Check 3: Multi-airline context for multi-airline response
    multi_airline_count = 0
    for card in enhanced_cards:
        if 'multi_airline_context' in card:
            multi_airline_count += 1
    
    if multi_airline_count > 0:
        print(f"✅ {multi_airline_count}/{len(enhanced_cards)} cards have multi-airline context")
    else:
        print("⚠️  No cards have multi-airline context")
    
    # Check 4: Price comparison working
    prices = [card.get('price', 0) for card in enhanced_cards]
    if prices and min(prices) != max(prices):
        print("✅ Price comparison data available")
    else:
        print("⚠️  Price comparison may not be working")
    
    print("\n" + "=" * 70)
    if validation_passed:
        print("🎉 Integration test completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Transformed {len(offers)} offers in {transform_time:.3f}s")
        print(f"   • Generated {len(enhanced_cards)} enhanced cards in {card_time:.3f}s")
        print(f"   • Total processing time: {transform_time + card_time:.3f}s")
        print(f"   • Airlines supported: {transformed_result['metadata']['airline_count']}")
        return True
    else:
        print("❌ Integration test failed validation!")
        return False


if __name__ == '__main__':
    success = test_complete_integration()
    sys.exit(0 if success else 1)
