#!/usr/bin/env python3

from langgraph_kisaan_agents import build_kisaan_graph

def test_single_scheme_query():
    """Test a single government scheme query end-to-end"""
    graph = build_kisaan_graph()
    
    test_state = {
        'user_query': "Tell me about PM-Kisan scheme",
        'language': 'english',
        'location': {'city': 'Delhi', 'state': 'Delhi'}
    }
    
    print("🧪 Testing Single Government Scheme Query")
    print("=" * 50)
    print(f"Query: {test_state['user_query']}")
    
    try:
        result = graph.invoke(test_state)
        
        print(f"\n✅ Results:")
        print(f"Query Type: {result.get('query_type', 'unknown')}")
        print(f"Final Response: {result.get('final_response', 'No response')[:200]}...")
        
        # Check if it contains scheme information
        response = result.get('final_response', '').lower()
        has_scheme_info = any(keyword in response for keyword in [
            'pm-kisan', 'scheme', 'government', 'subsidy', 'benefit', '6000', 'rupees'
        ])
        
        if has_scheme_info:
            print("✅ Response contains scheme information")
        else:
            print("❌ Response does NOT contain scheme information")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_scheme_query()