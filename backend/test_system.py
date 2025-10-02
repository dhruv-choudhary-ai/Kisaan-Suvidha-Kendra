"""
Test script to verify Kisaan Voice Assistant is working correctly
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_start_session():
    """Test starting a new voice session"""
    print("\n=== Testing Start Session ===")
    try:
        response = requests.post(f"{BASE_URL}/voice/start-session")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Session ID: {data.get('session_id')}")
        print(f"Language: {data.get('language')}")
        print(f"Has audio: {'audio_base64' in data}")
        return data.get('session_id')
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_language_selection(session_id):
    """Test language selection"""
    print("\n=== Testing Language Selection ===")
    try:
        response = requests.post(
            f"{BASE_URL}/voice/select-language",
            json={"session_id": session_id, "language": "hindi"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response text: {data.get('text_response')[:100]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_farmer_registration():
    """Test farmer registration"""
    print("\n=== Testing Farmer Registration ===")
    try:
        farmer_data = {
            "name": "Test Kisaan",
            "phone_number": "9999999999",
            "village": "Test Village",
            "district": "Indore",
            "state": "Madhya Pradesh",
            "land_size_acres": 5.0,
            "soil_type": "Black Soil",
            "irrigation_type": "Canal",
            "primary_crops": ["Wheat", "Soybean"]
        }
        response = requests.post(
            f"{BASE_URL}/farmer/register",
            json=farmer_data
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Message: {data.get('message')}")
        print(f"Farmer ID: {data.get('farmer_id')}")
        return data.get('farmer_id')
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_database_connection():
    """Test database connectivity"""
    print("\n=== Testing Database Connection ===")
    try:
        from db import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM farmers")
        count = cur.fetchone()[0]
        print(f"Total farmers in database: {count}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database Error: {str(e)}")
        return False

def test_voice_service():
    """Test voice service components"""
    print("\n=== Testing Voice Service ===")
    try:
        from voice_service import voice_service
        
        # Test greeting message
        greeting = voice_service.get_greeting_message("hindi")
        print(f"Hindi greeting (first 100 chars): {greeting[:100]}...")
        
        # Test language detection
        detected = voice_service.detect_language_from_speech("हिंदी में बोलें")
        print(f"Detected language: {detected}")
        
        return True
    except Exception as e:
        print(f"Voice Service Error: {str(e)}")
        return False

def test_agriculture_apis():
    """Test agriculture API services"""
    print("\n=== Testing Agriculture APIs ===")
    try:
        import asyncio
        from agriculture_apis import agriculture_api_service
        
        # Test weather API (might fail without API key)
        print("Testing weather API...")
        weather = asyncio.run(agriculture_api_service.get_current_weather(city="Indore"))
        if weather:
            print(f"Weather data received: {weather.get('location')}, {weather.get('temperature')}°C")
        else:
            print("Weather API returned no data (check API key)")
        
        return True
    except Exception as e:
        print(f"Agriculture API Error: {str(e)}")
        return False

def test_langgraph_agents():
    """Test LangGraph agent system"""
    print("\n=== Testing LangGraph Agents ===")
    try:
        from langgraph_kisaan_agents import build_kisaan_graph
        
        graph = build_kisaan_graph()
        print("LangGraph compiled successfully")
        
        # Test with sample state
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
        
        print("Running agent workflow...")
        result = graph.invoke(test_state)
        print(f"Query type identified: {result.get('query_type')}")
        print(f"Final response (first 150 chars): {result.get('final_response', '')[:150]}...")
        
        return True
    except Exception as e:
        print(f"LangGraph Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("KISAAN VOICE ASSISTANT - SYSTEM TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = test_health()
    
    # Test 2: Database
    results['database'] = test_database_connection()
    
    # Test 3: Voice Service
    results['voice_service'] = test_voice_service()
    
    # Test 4: Agriculture APIs
    results['agriculture_apis'] = test_agriculture_apis()
    
    # Test 5: LangGraph Agents
    results['langgraph'] = test_langgraph_agents()
    
    # Test 6: Start Session
    session_id = test_start_session()
    results['start_session'] = session_id is not None
    
    # Test 7: Language Selection
    if session_id:
        results['language_selection'] = test_language_selection(session_id)
    else:
        results['language_selection'] = False
    
    # Test 8: Farmer Registration
    farmer_id = test_farmer_registration()
    results['farmer_registration'] = farmer_id is not None
    
    # Print Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print("\n" + "=" * 60)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! System is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())