#!/usr/bin/env python3

from langgraph_kisaan_agents import build_kisaan_graph
import json

def comprehensive_test():
    """Test all the enhanced query categories"""
    graph = build_kisaan_graph()
    
    test_cases = [
        {
            'query': 'Should I grow wheat or rice this season?',
            'expected_type': 'crop_selection',
            'language': 'english'
        },
        {
            'query': 'How to cultivate tomatoes properly?',
            'expected_type': 'crop_cultivation',
            'language': 'english'
        },
        {
            'query': 'My plants have yellow spots on leaves',
            'expected_type': 'crop_disease',
            'language': 'english'
        },
        {
            'query': 'What is the weather forecast for farming?',
            'expected_type': 'weather_advisory',
            'language': 'english'
        },
        {
            'query': 'What fertilizer should I use for better soil?',
            'expected_type': 'soil_management',
            'language': 'english'
        },
        {
            'query': 'When should I water my crops?',
            'expected_type': 'irrigation',
            'language': 'english'
        },
        {
            'query': 'Tell me about PM-Kisan scheme',
            'expected_type': 'government_schemes',
            'language': 'english'
        },
        {
            'query': 'How to become a successful farmer?',
            'expected_type': 'general_advisory',
            'language': 'english'
        }
    ]
    
    print("🧪 Comprehensive Agent Testing")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['query']}'")
        print(f"   Expected: {test_case['expected_type']}")
        
        try:
            test_state = {
                'user_query': test_case['query'],
                'language': test_case['language'],
                'location': {'city': 'Delhi'}
            }
            
            result = graph.invoke(test_state)
            actual_type = result.get('query_type', 'unknown')
            
            print(f"   Actual: {actual_type}")
            
            # Check if classification is correct
            if actual_type == test_case['expected_type']:
                print("   ✅ PASS")
                success_count += 1
            else:
                print("   ❌ FAIL")
            
            # Show response sample (first 80 chars)
            response = result.get('final_response', 'No response')
            print(f"   Response: {response[:80]}...")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("-" * 40)
    
    print(f"\n📊 TEST RESULTS:")
    print(f"   Passed: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("   🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print("   ⚠️  Some tests failed. Check the classifications above.")

if __name__ == "__main__":
    comprehensive_test()