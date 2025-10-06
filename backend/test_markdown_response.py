#!/usr/bin/env python3

from langgraph_kisaan_agents import build_kisaan_graph

def test_markdown_formatting():
    """Test if responses come with proper markdown formatting"""
    graph = build_kisaan_graph()
    
    test_cases = [
        {
            'query': 'Tell me about PM-Kisan scheme',
            'language': 'english',
            'location': {'city': 'Delhi', 'state': 'Delhi'}
        },
        {
            'query': 'सरकारी योजनाओं के बारे में बताइए',
            'language': 'hindi',
            'location': {'city': 'Indore', 'state': 'Madhya Pradesh'}
        },
        {
            'query': 'Should I grow wheat this season?',
            'language': 'english',
            'location': {'city': 'Punjab', 'state': 'Punjab'}
        }
    ]
    
    print("🧪 Testing Markdown Formatting in Responses")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Query: {test_case['query']}")
        print(f"   Language: {test_case['language']}")
        
        try:
            result = graph.invoke(test_case)
            response = result.get('final_response', 'No response')
            
            print(f"   Query Type: {result.get('query_type', 'unknown')}")
            print(f"\n   Response:")
            print("-" * 60)
            print(response)
            print("-" * 60)
            
            # Check for markdown elements
            has_bold = '**' in response
            has_bullets = '•' in response or '*' in response or '-' in response
            has_headers = '#' in response
            
            print(f"\n   Markdown Elements Detected:")
            print(f"   - Bold text (**): {'✅' if has_bold else '❌'}")
            print(f"   - Bullet points: {'✅' if has_bullets else '❌'}")
            print(f"   - Headers (#): {'✅' if has_headers else '❌'}")
            print("=" * 60)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_markdown_formatting()
