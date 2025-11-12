"""
Comprehensive Test Suite for All Kisaan Agents
Tests all 16 agents including new fertilizer, pesticide, irrigation, and support agents
"""

import asyncio
import sys
from langgraph_kisaan_agents import build_kisaan_graph

# Test queries for each agent type
TEST_QUERIES = {
    "fertilizer_recommendation": [
        "मेरी गेहूं की फसल में कौन सा उर्वरक डालना चाहिए?",
        "Which fertilizer is best for tomato plants?",
        "धान में पीले पत्ते हो रहे हैं, कौन सा उर्वरक दूं?",
    ],
    
    "pesticide_recommendation": [
        "टमाटर में कीड़े लग गए हैं, कौन सी दवा डालूं?",
        "Which pesticide for cotton bollworm?",
        "गेहूं में रस्ट लग गया है, उपचार बताएं",
    ],
    
    "application_guide": [
        "यूरिया कितनी मात्रा में डालना है?",
        "How to apply pesticide spray?",
        "उर्वरक डालने की विधि बताइए",
    ],
    
    "fertilizer_schedule": [
        "धान की पूरी उर्वरक अनुसूची बताइए",
        "Complete fertilizer schedule for wheat crop",
        "गेहूं में कब-कब खाद डालनी है?",
    ],
    
    "irrigation_management": [
        "टमाटर को पानी कब देना चाहिए?",
        "Drip irrigation benefits for cotton",
        "सिंचाई कितने दिन में करनी चाहिए?",
    ],
    
    "soil_health": [
        "मिट्टी की जांच कहां करवाएं?",
        "How to improve soil pH?",
        "मिट्टी में नाइट्रोजन की कमी है, क्या करूं?",
    ],
    
    "crop_calendar": [
        "गेहूं की बुवाई से कटाई तक की पूरी जानकारी",
        "Complete calendar for rice cultivation",
        "टमाटर की फसल का समय-सारणी",
    ],
    
    "cost_calculation": [
        "गेहूं की खेती में कितना खर्च आता है?",
        "Total cost of growing cotton per acre",
        "धान की खेती में लाभ कितना होगा?",
    ],
    
    "emergency_response": [
        "खेत में अचानक बहुत सारे कीड़े आ गए हैं, क्या करूं?",
        "Crop failure due to heavy rain, urgent help needed",
        "फसल में रोग फैल रहा है, तुरंत उपाय बताएं",
    ],
    
    "expert_connection": [
        "मुझे कृषि विशेषज्ञ से बात करनी है",
        "Contact agricultural officer",
        "KVK का नंबर चाहिए",
    ],
    
    # Existing agents
    "crop_selection": [
        "इस मौसम में कौन सी फसल लगाएं?",
        "Best crop for rabi season",
    ],
    
    "crop_disease": [
        "पत्तियों में धब्बे हैं",
        "Leaf disease identification",
    ],
    
    "weather_advisory": [
        "आज मौसम कैसा रहेगा?",
        "Weather forecast for farming",
    ],
    
    "market_price": [
        "गेहूं का भाव क्या है?",
        "Current price of rice",
    ],
    
    "government_schemes": [
        "PM-Kisan योजना के बारे में बताएं",
        "Government schemes for farmers",
    ],
    
    "general_advisory": [
        "खेती कैसे करें?",
        "General farming advice",
    ],
}


async def test_agent(graph, agent_type, query, location=None):
    """Test a specific agent with a query"""
    print(f"\n{'='*80}")
    print(f"🧪 Testing: {agent_type}")
    print(f"📝 Query: {query}")
    print(f"{'='*80}")
    
    # Detect language
    language = "hindi" if any(ord(char) > 127 for char in query) else "english"
    
    # Default location
    if not location:
        location = {
            "city": "Delhi",
            "state": "Delhi",
            "district": "Central Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
    
    # Initial state
    initial_state = {
        "user_query": query,
        "language": language,
        "location": location,
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
        "agent_flow": []
    }
    
    try:
        # Run the graph
        result = graph.invoke(initial_state)
        
        print(f"\n✅ Agent Triggered: {result.get('query_type', 'unknown')}")
        print(f"\n📤 Response:")
        print("-" * 80)
        print(result.get('final_response', 'No response generated'))
        print("-" * 80)
        
        return True
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_all_agents():
    """Test all agents comprehensively"""
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE AGENT TESTING - All 16 Agents")
    print("="*80)
    
    # Build the graph
    print("\n📊 Building LangGraph workflow...")
    graph = build_kisaan_graph()
    print("✅ Graph built successfully!")
    
    # Track results
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
    
    # Test each agent type
    for agent_type, queries in TEST_QUERIES.items():
        print(f"\n\n{'#'*80}")
        print(f"# 🎯 TESTING AGENT: {agent_type.upper().replace('_', ' ')}")
        print(f"{'#'*80}")
        
        for i, query in enumerate(queries, 1):
            results["total"] += 1
            print(f"\n[Test {i}/{len(queries)}]")
            
            success = await test_agent(graph, agent_type, query)
            
            if success:
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            # Small delay between tests
            await asyncio.sleep(1)
    
    # Print summary
    print("\n\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
    print("="*80)


async def test_specific_agent(agent_type):
    """Test a specific agent only"""
    if agent_type not in TEST_QUERIES:
        print(f"❌ Unknown agent type: {agent_type}")
        print(f"Available agents: {', '.join(TEST_QUERIES.keys())}")
        return
    
    print(f"\n🎯 Testing specific agent: {agent_type}")
    
    # Build graph
    graph = build_kisaan_graph()
    
    # Test queries for this agent
    queries = TEST_QUERIES[agent_type]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Test {i}/{len(queries)}]")
        await test_agent(graph, agent_type, query)
        await asyncio.sleep(1)


async def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*80)
    print("🧪 TESTING EDGE CASES")
    print("="*80)
    
    graph = build_kisaan_graph()
    
    edge_cases = [
        ("Empty query", ""),
        ("Very short query", "खाद"),
        ("Mixed language", "गेहूं fertilizer कब डालें?"),
        ("Complex query", "मेरी 5 एकड़ गेहूं की फसल में पीले पत्ते हो रहे हैं और कीड़े भी लगे हैं, मुझे उर्वरक और कीटनाशक दोनों की जानकारी चाहिए, साथ ही लागत भी बताएं"),
        ("Ambiguous query", "फसल"),
    ]
    
    for description, query in edge_cases:
        print(f"\n📝 {description}: '{query}'")
        await test_agent(graph, "edge_case", query)
        await asyncio.sleep(1)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific agent
        agent_type = sys.argv[1]
        asyncio.run(test_specific_agent(agent_type))
    elif len(sys.argv) > 2 and sys.argv[1] == "--edge":
        # Test edge cases
        asyncio.run(test_edge_cases())
    else:
        # Test all agents
        print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        🌾 KISAAN SUVIDHA KENDRA - AGENT TEST SUITE 🌾        ║
║                                                                ║
║  Testing all 16 specialized agricultural agents:              ║
║                                                                ║
║  📌 Fertilizer & Pesticide Management (4 agents)              ║
║     • Fertilizer Recommendation                                ║
║     • Pesticide Recommendation                                 ║
║     • Application Guide                                        ║
║     • Fertilizer Schedule Planner                              ║
║                                                                ║
║  📌 Resource Management (3 agents)                             ║
║     • Irrigation Management                                    ║
║     • Soil Health                                              ║
║     • Crop Calendar                                            ║
║                                                                ║
║  📌 Financial & Support (3 agents)                             ║
║     • Input Cost Calculator                                    ║
║     • Emergency Response                                       ║
║     • Local Expert Connection                                  ║
║                                                                ║
║  📌 Core Agents (6 agents)                                     ║
║     • Crop Selection                                           ║
║     • Crop Disease                                             ║
║     • Weather Advisory                                         ║
║     • Market Price                                             ║
║     • Government Schemes                                       ║
║     • General Advisory                                         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

Usage:
  python test_all_agents.py                    # Test all agents
  python test_all_agents.py fertilizer_recommendation  # Test specific agent
  python test_all_agents.py --edge             # Test edge cases

Starting comprehensive test suite...
""")
        asyncio.run(test_all_agents())
