"""
Quick test script to verify voice assistant end-to-end flow
Run backend first: uvicorn main:app --reload
Then run this script
"""
import requests
import json
import base64

BASE_URL = "http://localhost:8000"

def test_complete_flow():
    print("="*60)
    print("TESTING COMPLETE VOICE ASSISTANT FLOW")
    print("="*60)
    
    # Step 1: Start session
    print("\n[1/5] Starting session...")
    response = requests.post(f"{BASE_URL}/voice/start-session")
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    data = response.json()
    session_id = data.get('session_id')
    print(f"✅ Session started: {session_id}")
    print(f"   Greeting: {data.get('text')[:50]}...")
    print(f"   Audio size: {len(data.get('audio', ''))} chars")
    
    # Step 2: Select language
    print("\n[2/5] Selecting Hindi language...")
    response = requests.post(
        f"{BASE_URL}/voice/select-language",
        json={"session_id": session_id, "language": "hindi"}
    )
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✅ Language selected")
    print(f"   Response: {data.get('text')}")
    print(f"   Audio size: {len(data.get('audio', ''))} chars")
    
    # Step 3: Test LangGraph with text query (simulated)
    print("\n[3/5] Testing LangGraph agents...")
    from langgraph_kisaan_agents import build_kisaan_graph
    
    graph = build_kisaan_graph()
    test_state = {
        "user_query": "मेरी गेहूं की फसल में पीले धब्बे हैं",
        "language": "hindi",
        "location": {"city": "Indore", "state": "Madhya Pradesh"},
        "query_type": "",
        "parsed_entities": {},
        "crop_info": [],
        "weather_data": {},
        "market_data": [],
        "government_schemes": [],
        "pest_disease_info": {},
        "recommendations": [],
        "final_response": ""
    }
    
    result = graph.invoke(test_state)
    print(f"✅ LangGraph workflow completed")
    print(f"   Query type: {result.get('query_type')}")
    print(f"   Response: {result.get('final_response')[:100]}...")
    
    # Step 4: Test voice service
    print("\n[4/5] Testing voice service...")
    from voice_service import voice_service
    
    test_text = "यह एक परीक्षण संदेश है।"
    audio_b64 = voice_service.text_to_speech(test_text, "hindi")
    print(f"✅ TTS generated: {len(audio_b64)} chars")
    
    # Step 5: Test database
    print("\n[5/5] Testing database...")
    from db import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM farmers")
    if hasattr(cur.fetchone(), '__getitem__'):
        count = cur.fetchone()[0]
    else:
        result = cur.fetchone()
        count = result[0] if result else 0
    cur.close()
    conn.close()
    print(f"✅ Database connected: {count} farmers registered")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n🎉 System is ready for use!")
    print("\nNext steps:")
    print("1. Start backend: uvicorn main:app --reload")
    print("2. Start frontend: cd frontend && pnpm dev")
    print("3. Open browser: http://localhost:3000")
    
    return True

def test_api_endpoints():
    """Test all API endpoints"""
    print("\n" + "="*60)
    print("TESTING API ENDPOINTS")
    print("="*60)
    
    endpoints = [
        ("GET", "/health", None),
        ("POST", "/voice/start-session", None),
    ]
    
    for method, endpoint, data in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data)
            
            status_icon = "✅" if response.status_code == 200 else "❌"
            print(f"{status_icon} {method} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {method} {endpoint}: ERROR - {str(e)}")

if __name__ == "__main__":
    import asyncio
    
    # Test API endpoints first
    try:
        test_api_endpoints()
    except Exception as e:
        print(f"❌ API tests failed: {e}")
    
    # Test complete flow
    try:
        asyncio.run(test_complete_flow())
    except Exception as e:
        print(f"❌ Flow test failed: {e}")
        import traceback
        traceback.print_exc()
