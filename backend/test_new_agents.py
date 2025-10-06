#!/usr/bin/env python3

from langgraph_kisaan_agents import build_kisaan_graph
from models import SessionData
import json

# List of 30 diverse farmer queries to test app robustness
test_queries = [
    # Crop selection
    "shall I do rice cultivation this season?",
    "which crop is best for monsoon in Maharashtra?",
    "should I grow wheat or barley this year?",
    # Soil and fertilizers
    "how to improve my soil health?",
    "what fertilizer should I use for tomatoes?",
    "how to increase organic matter in soil?",
    # Weather queries
    "will it rain tomorrow?",
    "is frost expected next week?",
    "how hot will it be this month in Punjab?",
    # Pest and disease management
    "my wheat crop has rust disease, what should I do?",
    "how to prevent pest attacks in cotton?",
    "what are natural ways to control aphids?",
    # Government schemes
    "which government schemes are available for small farmers?",
    "how to apply for crop insurance?",
    "are there subsidies for drip irrigation?",
    # Market and pricing
    "current market price of sugarcane in Uttar Pradesh?",
    "where can I sell my mangoes at a good rate?",
    "how to predict crop price trends?",
    # Irrigation and water management
    "best irrigation method for paddy fields?",
    "how to conserve water in agriculture?",
    "when should I water my vegetable garden?",
    # Animal husbandry
    "how to increase milk production in cows?",
    "what is the best feed for goats?",
    "how to prevent poultry diseases?",
    # Technology and modern methods
    "are there drones for crop monitoring?",
    "how to use soil sensors for irrigation?",
    "what are good mobile apps for farmers?",
    # Miscellaneous
    "tips for sustainable farming?",
    "how to rotate crops effectively?",
    "how to start organic farming?",
    "how to get soil tested nearby?",
    "advice for starting a small farm in Delhi?"
]

def test_new_agents():
    try:
        graph = build_kisaan_graph()
        
        for i, query in enumerate(test_queries, start=1):
            test_state = {
                'user_query': query,
                'language': 'english',
                'location': {'city': 'TestCity'}  # generic location; can customize per query
            }
            
            print(f'Test {i}: {query}')
            result = graph.invoke(test_state)
            print(f'Query Type: {result.get("query_type", "Unknown")}')
            print(f'Response: {result.get("final_response", "No response")}')
            print('-' * 50)
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_agents()
