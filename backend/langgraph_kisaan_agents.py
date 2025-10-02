import os
from typing import List, TypedDict, Dict, Any
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from db import get_db_connection
import logging
import json
import asyncio

logger = logging.getLogger(__name__)
load_dotenv()

# Import after to avoid circular dependency
from agriculture_apis import agriculture_api_service

logger = logging.getLogger(__name__)
load_dotenv()

# Helper function to safely run async code from sync context
def run_async_safe(coro):
    """
    Safely run async coroutine from sync context.
    Handles both running and non-running event loops.
    """
    try:
        # Try to get the current running loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop is running, safe to use asyncio.run()
        return asyncio.run(coro)
    else:
        # Loop is already running, we need to handle this differently
        # Create a new thread to run the async code
        import concurrent.futures
        import threading
        
        result = None
        exception = None
        
        def run_in_thread():
            nonlocal result, exception
            try:
                # Create new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(coro)
                new_loop.close()
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()
        
        if exception:
            raise exception
        return result

# Shared LangGraph state definition for agriculture domain
class KisaanAgentState(TypedDict):
    user_query: str
    language: str
    location: Dict[str, Any]
    query_type: str  # crop_disease, weather, market_price, advisory, scheme, pest_control
    parsed_entities: Dict[str, Any]
    crop_info: List[Dict]
    weather_data: Dict
    market_data: List[Dict]
    government_schemes: List[Dict]
    pest_disease_info: Dict
    recommendations: List[str]
    final_response: str
    requires_camera: bool  # New field for camera trigger

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.3,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Agent 1: Query Understanding Agent
def query_understanding_agent(state: KisaanAgentState) -> KisaanAgentState:
    """
    Understand and categorize the farmer's query
    Extract key entities like crop names, symptoms, locations
    """
    logger.info("\n🔍 Query Understanding Agent running...")
    
    user_query = state.get("user_query", "")
    language = state.get("language", "hindi")
    
    prompt = f"""You are an intelligent agricultural assistant.

Analyze this farmer's query and respond ONLY with valid JSON. No extra text, no markdown, just pure JSON.

Query: {user_query}
Language: {language}

Respond in this exact JSON format:
{{
    "query_type": "crop_disease|weather|market_price|scheme|advisory|general",
    "entities": {{
        "crop": "crop name if mentioned",
        "symptom": "symptoms if mentioned",
        "location": "location if mentioned",
        "time": "time reference if mentioned"
    }},
    "urgency": "high|medium|low"
}}

Guidelines for query_type:
- crop_disease: Questions about plant diseases, pests, yellow leaves, spots, wilting, etc.
- weather: Questions about weather, rain, temperature
- market_price: Questions about crop prices, mandi rates, selling
- scheme: Questions about government schemes, subsidies, PM-Kisan
- advisory: General farming advice, when to plant, irrigation
- general: Other queries

Return ONLY the JSON object, nothing else."""
    
    messages = [
        SystemMessage(content="You are an agricultural expert. Respond only with valid JSON."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Try to extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        
        if start == -1 or end == 0:
            raise ValueError(f"No JSON found in response: {content[:100]}")
        
        json_str = content[start:end]
        parsed = json.loads(json_str)
        
        logger.info(f"✅ Query type identified: {parsed.get('query_type')}")
        
        return {
            "query_type": parsed.get("query_type", "general"),
            "parsed_entities": parsed.get("entities", {}),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Query understanding JSON parse error: {str(e)}")
        logger.error(f"Raw response: {response.content[:200]}")
        return {"query_type": "general", "parsed_entities": {}}
    except Exception as e:
        logger.error(f"Query understanding error: {str(e)}")
        logger.error(f"Raw response: {response.content[:200] if hasattr(response, 'content') else 'No response'}")
        return {"query_type": "general", "parsed_entities": {}}

# Agent 2: Crop Disease Diagnosis Agent
def crop_disease_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Diagnose crop diseases - triggers camera for visual inspection"""
    logger.info("\n🌾 Crop Disease Agent running...")
    
    if state.get("query_type") != "crop_disease":
        return {}
    
    language = state.get("language", "hindi")
    
    # Instead of text-based diagnosis, trigger camera
    camera_prompts = {
        "hindi": "क्या आप पत्ती की फोटो दिखाना चाहते हैं? यह ज्यादा सटीक निदान में मदद करेगा।",
        "english": "Would you like to show the leaf photo? This will help in more accurate diagnosis."
    }
    
    return {
        "pest_disease_info": {
            "action": "open_camera",
            "prompt": camera_prompts.get(language, camera_prompts["hindi"])
        }
    }

# Agent 3: Weather Advisory Agent
def weather_advisory_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide weather-based farming advisory"""
    logger.info("\n🌤️ Weather Advisory Agent running...")
    
    if state.get("query_type") not in ["weather", "advisory"]:
        return {}
    
    # Import here to avoid circular dependency
    from agriculture_apis import agriculture_api_service
    
    location = state.get("location", {})
    language = state.get("language", "hindi")
    
    # Fetch weather data synchronously using run_async_safe
    weather_data = {}
    try:
        if location.get("city"):
            weather_data = run_async_safe(agriculture_api_service.get_current_weather(
                city=location.get("city")
            ))
        elif location.get("latitude") and location.get("longitude"):
            weather_data = run_async_safe(agriculture_api_service.get_current_weather(
                latitude=location["latitude"],
                longitude=location["longitude"]
            ))
    except Exception as e:
        logger.error(f"Weather fetch error: {str(e)}")
        # Return generic advisory if API fails
        generic_msg = {
            "hindi": "मौसम की जानकारी अभी उपलब्ध नहीं है। कृपया बाद में पूछें।",
            "english": "Weather information is not available right now. Please try later."
        }
        return {
            "weather_data": {},
            "recommendations": [generic_msg.get(language, generic_msg["hindi"])]
        }
    
    if weather_data:
        prompt = f"""
        Based on this weather data:
        Temperature: {weather_data.get('temperature')}°C
        Humidity: {weather_data.get('humidity')}%
        Conditions: {weather_data.get('weather')}
        Wind: {weather_data.get('wind_speed')} m/s
        
        Provide farming advisory in {language}:
        1. Suitable farm activities for today
        2. Irrigation recommendations
        3. Pest risk alerts
        4. Any precautions needed
        
        Keep it simple and actionable for farmers. Maximum 100 words.
        """
        
        messages = [
            SystemMessage(content="You are an agricultural meteorologist."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = llm.invoke(messages)
            return {
                "weather_data": weather_data,
                "recommendations": [response.content]
            }
        except Exception as e:
            logger.error(f"Weather advisory error: {str(e)}")
    
    return {"weather_data": weather_data}

# Agent 4: Market Price Agent
def market_price_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Fetch and analyze market prices"""
    logger.info("\n💰 Market Price Agent running...")
    
    if state.get("query_type") != "market_price":
        return {}
    
    # Import here to avoid circular dependency
    from agriculture_apis import agriculture_api_service
    
    entities = state.get("parsed_entities", {})
    commodity = entities.get("crop", "")
    location = state.get("location", {})
    language = state.get("language", "hindi")
    
    # Fetch market data synchronously using run_async_safe
    market_data = []
    try:
        market_data = run_async_safe(agriculture_api_service.get_commodity_prices(
            commodity=commodity,
            state=location.get("state"),
            district=location.get("district")
        ))
    except Exception as e:
        logger.error(f"Market fetch error: {str(e)}")
        # Return generic message if API fails
        generic_msg = {
            "hindi": f"{commodity} का बाजार भाव अभी उपलब्ध नहीं है। कृपया अपने स्थानीय मंडी से संपर्क करें।",
            "english": f"Market price for {commodity} is not available right now. Please contact your local mandi."
        }
        return {
            "market_data": [],
            "recommendations": [generic_msg.get(language, generic_msg["hindi"])]
        }
    
    if market_data and len(market_data) > 0:
        prompt = f"""
        Market data for {commodity}:
        {market_data[:3]}  # Show top 3 results
        
        Provide in {language}:
        1. Current average price
        2. Price trend (increasing/decreasing)
        3. Best markets to sell
        4. Selling advice
        
        Keep it simple for farmers. Maximum 100 words.
        """
        
        messages = [
            SystemMessage(content="You are an agricultural market analyst."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = llm.invoke(messages)
            return {
                "market_data": market_data,
                "recommendations": [response.content]
            }
        except Exception as e:
            logger.error(f"Market analysis error: {str(e)}")
    
    return {"market_data": market_data}

# Agent 5: Government Schemes Agent
def government_schemes_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide information about government schemes"""
    logger.info("\n🏛️ Government Schemes Agent running...")
    
    if state.get("query_type") != "scheme":
        return {}
    
    language = state.get("language", "hindi")
    location = state.get("location", {})
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Import config to check DB type
        from config import Config
        
        # Fetch relevant schemes from database
        # Use different placeholders for SQLite vs PostgreSQL
        if Config.DB_TYPE == 'sqlite':
            cur.execute("""
                SELECT scheme_name, scheme_name_hindi, description, description_hindi, 
                       eligibility, how_to_apply
                FROM government_schemes
                WHERE active = 1
                AND (state IS NULL OR state = ?)
                LIMIT 5
            """, (location.get("state"),))
        else:
            cur.execute("""
                SELECT scheme_name, scheme_name_hindi, description, description_hindi, 
                       eligibility, how_to_apply
                FROM government_schemes
                WHERE active = TRUE
                AND (state IS NULL OR state = %s)
                LIMIT 5
            """, (location.get("state"),))
        
        schemes = cur.fetchall()
        cur.close()
        conn.close()
        
        if schemes:
            schemes_list = []
            for scheme in schemes:
                # Handle both dict-like (SQLite) and tuple (PostgreSQL) results
                if isinstance(scheme, dict) or hasattr(scheme, 'keys'):
                    schemes_list.append({
                        "name": scheme['scheme_name_hindi'] if language == "hindi" else scheme['scheme_name'],
                        "description": scheme['description_hindi'] if language == "hindi" else scheme['description'],
                        "eligibility": scheme['eligibility'],
                        "how_to_apply": scheme['how_to_apply']
                    })
                else:
                    schemes_list.append({
                        "name": scheme[1] if language == "hindi" else scheme[0],
                        "description": scheme[3] if language == "hindi" else scheme[2],
                        "eligibility": scheme[4],
                        "how_to_apply": scheme[5]
                    })
            
            return {"government_schemes": schemes_list}
    
    except Exception as e:
        logger.error(f"Government schemes error: {str(e)}")
        if cur:
            cur.close()
        if conn:
            conn.close()
    
    return {"government_schemes": []}

# Agent 6: Response Generation Agent
def response_generation_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Generate final consolidated response"""
    logger.info("\n📝 Response Generation Agent running...")
    
    query_type = state.get("query_type", "")
    language = state.get("language", "hindi")
    recommendations = state.get("recommendations", [])
    pest_disease_info = state.get("pest_disease_info", {})
    weather_data = state.get("weather_data", {})
    market_data = state.get("market_data", [])
    government_schemes = state.get("government_schemes", [])
    
    # Check if camera action is needed
    if pest_disease_info.get("action") == "open_camera":
        return {
            "final_response": pest_disease_info.get("prompt", ""),
            "requires_camera": True
        }
    
    # Build context for response
    context = f"Query Type: {query_type}\n"
    
    if pest_disease_info:
        context += f"\nDisease Info: {pest_disease_info.get('diagnosis', '')}\n"
    
    if weather_data:
        context += f"\nWeather: {weather_data}\n"
    
    if market_data:
        context += f"\nMarket Data Available: {len(market_data)} records\n"
    
    if government_schemes:
        context += f"\nGovernment Schemes: {len(government_schemes)} available\n"
    
    if recommendations:
        context += f"\nRecommendations: {recommendations}\n"
    
    prompt = f"""
    Consolidate all the information into a clear, concise response in {language}.
    
    Context:
    {context}
    
    Create a farmer-friendly response that:
    1. Directly answers their question
    2. Provides actionable steps
    3. Uses simple language (avoid technical jargon)
    4. Is encouraging and supportive
    5. Offers follow-up help if needed
    
    Keep the response conversational and under 150 words.
    """
    
    messages = [
        SystemMessage(content="You are a helpful agricultural assistant speaking to farmers."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        final_response = response.content
        
        logger.info(f"✅ Final response generated ({len(final_response)} chars)")
        
        return {"final_response": final_response}
    except Exception as e:
        logger.error(f"Response generation error: {str(e)}")
        
        # Fallback response
        fallback_messages = {
            "hindi": "माफ़ करें, मुझे आपके प्रश्न का उत्तर देने में समस्या हो रही है। कृपया दोबारा कोशिश करें।",
            "english": "Sorry, I'm having trouble answering your question. Please try again."
        }
        
        return {"final_response": fallback_messages.get(language, fallback_messages["hindi"])}


# Build LangGraph flow
def build_kisaan_graph():
    """Build the multi-agent workflow graph"""
    builder = StateGraph(KisaanAgentState)
    
    # Add all agents as nodes
    builder.add_node("query_understanding", query_understanding_agent)
    builder.add_node("crop_disease", crop_disease_agent)
    builder.add_node("weather_advisory", weather_advisory_agent)
    builder.add_node("market_price", market_price_agent)
    builder.add_node("government_schemes", government_schemes_agent)
    builder.add_node("response_generation", response_generation_agent)
    
    # Define workflow
    builder.set_entry_point("query_understanding")
    
    # Conditional routing based on query type
    def route_by_query_type(state):
        query_type = state.get("query_type", "general")
        
        if query_type == "crop_disease":
            return "crop_disease"
        elif query_type in ["weather", "advisory"]:
            return "weather_advisory"
        elif query_type == "market_price":
            return "market_price"
        elif query_type == "scheme":
            return "government_schemes"
        else:
            return "response_generation"
    
    builder.add_conditional_edges(
        "query_understanding",
        route_by_query_type,
        {
            "crop_disease": "crop_disease",
            "weather_advisory": "weather_advisory",
            "market_price": "market_price",
            "government_schemes": "government_schemes",
            "response_generation": "response_generation"
        }
    )
    
    # All specialized agents flow to response generation
    builder.add_edge("crop_disease", "response_generation")
    builder.add_edge("weather_advisory", "response_generation")
    builder.add_edge("market_price", "response_generation")
    builder.add_edge("government_schemes", "response_generation")
    builder.add_edge("response_generation", END)
    
    return builder.compile()