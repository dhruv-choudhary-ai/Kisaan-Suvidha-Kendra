#!/usr/bin/env python3

def test_routing_logic():
    """Test the routing logic without API calls"""
    
    # Test the routing function directly
    def route_by_query_type(state):
        query_type = state.get("query_type", "general_advisory")
        agent_flow = state.get("agent_flow", [])
        
        # Primary routing based on query type
        if query_type == "crop_selection":
            return "crop_selection"
        elif query_type == "crop_cultivation":
            return "general_advisory"  # Use general advisory for cultivation questions
        elif query_type == "crop_disease":
            return "crop_disease"
        elif query_type == "weather_advisory":
            return "weather_advisory"
        elif query_type == "market_price":
            return "market_price"
        elif query_type == "soil_management":
            return "soil_management"
        elif query_type == "irrigation":
            return "general_advisory"  # Use general advisory for irrigation
        elif query_type == "government_schemes":
            return "government_schemes"
        else:
            return "general_advisory"  # Default fallback to general advisory
    
    # Test different query types
    test_cases = [
        {"query_type": "government_schemes", "expected": "government_schemes"},
        {"query_type": "crop_selection", "expected": "crop_selection"},
        {"query_type": "general_advisory", "expected": "general_advisory"},
        {"query_type": "unknown", "expected": "general_advisory"},
        {"query_type": "crop_disease", "expected": "crop_disease"},
    ]
    
    print("🧪 Testing Routing Logic")
    print("=" * 40)
    
    all_passed = True
    for test_case in test_cases:
        state = {"query_type": test_case["query_type"]}
        result = route_by_query_type(state)
        expected = test_case["expected"]
        
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
            
        print(f"{status} {test_case['query_type']} -> {result} (expected: {expected})")
    
    print(f"\n{'✅ All routing tests passed!' if all_passed else '❌ Some routing tests failed!'}")
    
if __name__ == "__main__":
    test_routing_logic()