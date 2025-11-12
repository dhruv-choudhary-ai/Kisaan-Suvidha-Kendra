"""
Test image integration with fertilizer and pesticide agents
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from langgraph_kisaan_agents import kisaan_graph

async def test_fertilizer_with_images():
    """Test fertilizer agent to verify image retrieval"""
    print("\n🧪 Testing Fertilizer Recommendation with Images\n")
    
    test_query = "मेरी गेहूं की फसल में कौन सा उर्वरक डालना चाहिए?"
    
    initial_state = {
        "user_query": test_query,
        "language": "hindi",
        "location": {"city": "Delhi", "state": "Delhi"},
        "query_type": "",
        "parsed_entities": {},
        "crop_info": [],
        "weather_data": {},
        "market_data": [],
        "government_schemes": [],
        "pest_disease_info": {},
        "fertilizer_info": {},
        "pesticide_info": {},
        "application_guide_info": {},
        "irrigation_info": {},
        "soil_health_info": {},
        "crop_calendar_info": {},
        "cost_info": {},
        "emergency_info": {},
        "expert_contact_info": {},
        "recommendations": [],
        "final_response": "",
        "requires_camera": False,
        "seasonal_info": {},
        "agent_flow": [],
        # Image fields
        "requires_images": False,
        "image_queries": [],
        "image_urls": [],
        "image_context": "",
        "layout_type": "chat-only"
    }
    
    print(f"Query: {test_query}\n")
    print("=" * 80)
    
    try:
        final_state = kisaan_graph.invoke(initial_state)
        
        print("\n✅ Test completed successfully!\n")
        print("=" * 80)
        
        # Check image integration
        print("\n📊 Image Integration Results:")
        print(f"  • Requires Images: {final_state.get('requires_images', False)}")
        print(f"  • Image Context: {final_state.get('image_context', 'N/A')}")
        print(f"  • Layout Type: {final_state.get('layout_type', 'chat-only')}")
        print(f"  • Number of Image Queries: {len(final_state.get('image_queries', []))}")
        
        if final_state.get('image_queries'):
            print(f"\n🔍 Image Queries Generated:")
            for i, query in enumerate(final_state.get('image_queries', []), 1):
                print(f"  {i}. {query}")
        
        if final_state.get('image_urls'):
            print(f"\n🖼️ Images Retrieved ({len(final_state.get('image_urls', []))}):")
            for i, img in enumerate(final_state.get('image_urls', []), 1):
                print(f"  {i}. {img.get('title', 'No title')}")
                print(f"     URL: {img.get('url', 'N/A')[:80]}...")
        else:
            print(f"\n⚠️ No images retrieved (this may be due to rate limits)")
        
        print(f"\n💬 Response:")
        print(final_state.get('final_response', 'No response'))
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_pesticide_with_images():
    """Test pesticide agent to verify image retrieval"""
    print("\n\n🧪 Testing Pesticide Recommendation with Images\n")
    
    test_query = "टमाटर में कीड़े लग गए हैं कौन सी दवा छिड़कें?"
    
    initial_state = {
        "user_query": test_query,
        "language": "hindi",
        "location": {"city": "Mumbai", "state": "Maharashtra"},
        "query_type": "",
        "parsed_entities": {},
        "crop_info": [],
        "weather_data": {},
        "market_data": [],
        "government_schemes": [],
        "pest_disease_info": {},
        "fertilizer_info": {},
        "pesticide_info": {},
        "application_guide_info": {},
        "irrigation_info": {},
        "soil_health_info": {},
        "crop_calendar_info": {},
        "cost_info": {},
        "emergency_info": {},
        "expert_contact_info": {},
        "recommendations": [],
        "final_response": "",
        "requires_camera": False,
        "seasonal_info": {},
        "agent_flow": [],
        # Image fields
        "requires_images": False,
        "image_queries": [],
        "image_urls": [],
        "image_context": "",
        "layout_type": "chat-only"
    }
    
    print(f"Query: {test_query}\n")
    print("=" * 80)
    
    try:
        final_state = kisaan_graph.invoke(initial_state)
        
        print("\n✅ Test completed successfully!\n")
        print("=" * 80)
        
        # Check image integration
        print("\n📊 Image Integration Results:")
        print(f"  • Requires Images: {final_state.get('requires_images', False)}")
        print(f"  • Image Context: {final_state.get('image_context', 'N/A')}")
        print(f"  • Layout Type: {final_state.get('layout_type', 'chat-only')}")
        print(f"  • Number of Image Queries: {len(final_state.get('image_queries', []))}")
        
        if final_state.get('image_queries'):
            print(f"\n🔍 Image Queries Generated:")
            for i, query in enumerate(final_state.get('image_queries', []), 1):
                print(f"  {i}. {query}")
        
        if final_state.get('image_urls'):
            print(f"\n🖼️ Images Retrieved ({len(final_state.get('image_urls', []))}):")
            for i, img in enumerate(final_state.get('image_urls', []), 1):
                print(f"  {i}. {img.get('title', 'No title')}")
                print(f"     URL: {img.get('url', 'N/A')[:80]}...")
        else:
            print(f"\n⚠️ No images retrieved (this may be due to rate limits)")
        
        print(f"\n💬 Response:")
        print(final_state.get('final_response', 'No response'))
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 80)
    print("  IMAGE INTEGRATION TEST SUITE  ")
    print("=" * 80)
    
    asyncio.run(test_fertilizer_with_images())
    asyncio.run(test_pesticide_with_images())
    
    print("\n" + "=" * 80)
    print("  ALL TESTS COMPLETED  ")
    print("=" * 80)
