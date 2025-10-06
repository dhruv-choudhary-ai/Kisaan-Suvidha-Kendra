#!/usr/bin/env python3

from langgraph_kisaan_agents import build_kisaan_graph

def test_market_price():
    """Test market price queries"""
    graph = build_kisaan_graph()
    
    test_cases = [
        {
            'query': 'गेहू का दाम क्या है अभी?',
            'language': 'hindi',
            'location': {'city': 'Delhi', 'state': 'Delhi'}
        },
        {
            'query': 'What is the current price of wheat?',
            'language': 'english',
            'location': {'city': 'Punjab', 'state': 'Punjab'}
        },
        {
            'query': 'market price',
            'language': 'english',
            'location': {'city': 'Mumbai', 'state': 'Maharashtra'}
        }
    ]
    
    print("💰 Testing Market Price Agent")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Query: {test_case['query']}")
        print(f"   Language: {test_case['language']}")
        print(f"   Location: {test_case['location']}")
        
        try:
            result = graph.invoke(test_case)
            
            query_type = result.get('query_type', 'unknown')
            final_response = result.get('final_response', 'No response')
            
            print(f"   Query Type: {query_type}")
            print(f"\n   Response:")
            print("-" * 60)
            print(final_response)
            print("-" * 60)
            
            # Check if response is empty
            if not final_response or final_response == 'No response':
                print("   ❌ EMPTY RESPONSE!")
            elif len(final_response) < 20:
                print("   ⚠️  Response too short")
            else:
                print(f"   ✅ Response generated ({len(final_response)} chars)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)

if __name__ == "__main__":
    test_market_price()
