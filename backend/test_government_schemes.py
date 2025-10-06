#!/usr/bin/env python3

from langgraph_kisaan_agents import build_kisaan_graph

def test_government_schemes():
    """Test the updated government schemes agent"""
    graph = build_kisaan_graph()
    
    test_cases = [
        {
            'query': 'Tell me about PM-Kisan scheme',
            'language': 'english',
            'location': {'city': 'Delhi', 'state': 'Delhi'}
        },
        {
            'query': 'मुझे फसल बीमा के बारे में बताइए',
            'language': 'hindi',
            'location': {'city': 'Mumbai', 'state': 'Maharashtra'}
        },
        {
            'query': 'What government schemes are available for farmers?',
            'language': 'english',
            'location': {'city': 'Bangalore', 'state': 'Karnataka'}
        },
         {
            'query': 'credit scheme for farmers?',
            'language': 'english',
            'location': {'city': 'Bangalore', 'state': 'Karnataka'}
        }
    ]
    
    print("🏛️ Testing Government Schemes Agent")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['query']}'")
        print(f"   Location: {test_case['location']}")
        
        try:
            result = graph.invoke(test_case)
            
            query_type = result.get('query_type', 'unknown')
            response = result.get('final_response', 'No response')
            
            print(f"   Query Type: {query_type}")
            print(f"   Response Length: {len(response)} characters")
            print(f"   Response Preview: {response}...")
            
            # Check if response contains scheme information
            scheme_keywords = ['PM-Kisan', 'फसल बीमा', 'Kisan Credit', 'scheme', 'योजना', 'subsidy', 'सब्सिडी']
            has_scheme_info = any(keyword.lower() in response.lower() for keyword in scheme_keywords)
            
            if has_scheme_info:
                print("   ✅ Contains scheme information")
            else:
                print("   ⚠️  May not contain specific scheme information")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_government_schemes()