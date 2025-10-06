#!/usr/bin/env python3

from langgraph_kisaan_agents import build_kisaan_graph
import json

def debug_classification():
    """Debug the classification issue"""
    graph = build_kisaan_graph()
    
    test_queries = [
        "Tell me about PM-Kisan scheme",
        "मुझे फसल बीमा के बारे में बताइए", 
        "What government schemes are available for farmers?",
        "credit scheme for farmers?",
        "PM-Kisan Samman Nidhi information",
        "Kisan Credit Card details"
    ]
    
    print("🔍 Debugging Query Classification")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nTesting: '{query}'")
        
        test_state = {
            'user_query': query,
            'language': 'english',
            'location': {'city': 'Delhi', 'state': 'Delhi'}
        }
        
        # Only run query understanding to see classification
        from langgraph_kisaan_agents import query_understanding_agent
        result = query_understanding_agent(test_state)
        
        print(f"  Classified as: {result.get('query_type', 'unknown')}")
        print(f"  Entities: {result.get('parsed_entities', {})}")

if __name__ == "__main__":
    debug_classification()