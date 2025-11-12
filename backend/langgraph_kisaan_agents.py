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
import threading
from datetime import datetime

logger = logging.getLogger(__name__)
load_dotenv()

# Import after to avoid circular dependency
from agriculture_apis import agriculture_api_service

logger = logging.getLogger(__name__)
load_dotenv()

# Helper function to get current season
def get_current_season():
    """Get current season based on Indian agricultural calendar"""
    current_month = datetime.now().month
    
    if current_month in [6, 7, 8, 9]:  # June-September
        return "kharif"
    elif current_month in [10, 11, 12, 1, 2, 3]:  # October-March
        return "rabi"
    else:  # April-May
        return "summer"

def get_seasonal_crops(season):
    """Get crops suitable for current season"""
    seasonal_crops = {
        "kharif": ["धान (Rice)", "मक्का (Maize)", "कपास (Cotton)", "गन्ना (Sugarcane)", "ज्वार (Sorghum)", "बाजरा (Pearl Millet)"],
        "rabi": ["गेहूं (Wheat)", "जौ (Barley)", "चना (Chickpea)", "मसूर (Lentil)", "सरसों (Mustard)", "आलू (Potato)"],
        "summer": ["तरबूज (Watermelon)", "खरबूज (Muskmelon)", "भिंडी (Okra)", "लौकी (Bottle gourd)", "करेला (Bitter gourd)"]
    }
    return seasonal_crops.get(season, [])

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
    query_type: str  # crop_selection, crop_cultivation, crop_disease, weather_advisory, market_price, soil_management, irrigation, government_schemes, general_advisory, fertilizer_recommendation, pesticide_recommendation, application_guide, fertilizer_schedule, irrigation_management, soil_health, crop_calendar, cost_calculation, emergency_response, expert_connection
    parsed_entities: Dict[str, Any]
    crop_info: List[Dict]
    weather_data: Dict
    market_data: List[Dict]
    government_schemes: List[Dict]
    pest_disease_info: Dict
    fertilizer_info: Dict[str, Any]  # Fertilizer recommendations
    pesticide_info: Dict[str, Any]  # Pesticide recommendations
    application_guide_info: Dict[str, Any]  # Application instructions
    irrigation_info: Dict[str, Any]  # Irrigation recommendations
    soil_health_info: Dict[str, Any]  # Soil analysis and recommendations
    crop_calendar_info: Dict[str, Any]  # Crop lifecycle schedule
    cost_info: Dict[str, Any]  # Cost calculations and ROI
    emergency_info: Dict[str, Any]  # Emergency response actions
    expert_contact_info: Dict[str, Any]  # Expert contact details
    recommendations: List[str]
    final_response: str
    requires_camera: bool  # New field for camera trigger
    seasonal_info: Dict[str, Any]  # Current season and suitable crops
    agent_flow: List[str]  # Track which agents to use for multi-routing
    # Image integration fields
    requires_images: bool  # Whether response needs visual aids
    image_queries: List[str]  # Search queries for image retrieval
    image_urls: List[Dict[str, str]]  # Retrieved image URLs with metadata
    image_context: str  # Context for images (fertilizer_products, pesticide_products, disease_symptoms, etc.)
    layout_type: str  # UI layout type (split, full, chat-only)

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-live",
    temperature=0.3,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Agent 1: Query Understanding Agent - IMPROVED
def query_understanding_agent(state: KisaanAgentState) -> KisaanAgentState:
    """
    Understand and categorize the farmer's query
    Extract key entities like crop names, symptoms, locations
    """
    logger.info("\n🔍 Query Understanding Agent running...")
    
    user_query = state.get("user_query", "")
    language = state.get("language", "hindi")
    
    prompt = f"""You are an intelligent agricultural assistant analyzing a farmer's query.

Query: {user_query}
Language: {language}

Analyze the query and classify it into ONE primary category. Return ONLY valid JSON.

Categories and their indicators:
- crop_selection: "which crop", "what to grow", "should I plant", "best crop for"
- crop_cultivation: "how to grow", "cultivation practices", "farming methods", "planting guide"
- crop_disease: disease symptoms, pests, yellow leaves, spots, wilting, plant problems
- weather_advisory: weather, rain, temperature for farming
- market_price: crop prices, mandi rates, selling price, market value
- soil_management: soil testing, fertilizer, soil health, nutrients (general soil questions)
- irrigation: watering, drip irrigation, water management, irrigation scheduling
- government_schemes: ANY mention of schemes, subsidies, loans, PM-Kisan, insurance, credit card, government support, योजना
- fertilizer_recommendation: "which fertilizer", "fertilizer for crop", "NPK", "urea", "DAP", nutrient deficiency
- pesticide_recommendation: "which pesticide", "pest control", "insecticide", "fungicide", IPM
- application_guide: "how to apply", "dosage", "quantity", "how much fertilizer/pesticide", spray timing
- fertilizer_schedule: "fertilizer schedule", "when to apply fertilizer", stage-wise fertilization
- soil_health: soil pH, soil testing, soil improvement, soil amendments
- crop_calendar: "when to sow", "planting calendar", "harvest time", crop lifecycle
- cost_calculation: input costs, ROI, profit calculation, budget planning
- emergency_response: urgent pest outbreak, disease emergency, weather disaster, crop failure
- expert_connection: "contact expert", "agricultural officer", "KVK", need human help
- general_advisory: other farming questions

JSON format:
{{
    "query_type": "category_name",
    "entities": {{
        "crop": "crop name if mentioned or empty string",
        "symptom": "symptoms if mentioned or empty string",
        "location": "location if mentioned or empty string",
        "pest_name": "pest/disease name if mentioned or empty string",
        "growth_stage": "growth stage if mentioned or empty string"
    }},
    "confidence": "high|medium|low"
}}

Return ONLY the JSON, nothing else."""
    
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
        
        if start != -1 and end > 0:
            json_str = content[start:end]
            parsed = json.loads(json_str)
            
            query_type = parsed.get("query_type", "general_advisory")
            logger.info(f"✅ Query type identified: {query_type}")
            
            return {
                "query_type": query_type,
                "parsed_entities": parsed.get("entities", {}),
            }
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        logger.error(f"Query understanding error: {str(e)}")
        # Fallback: Simple keyword matching
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["scheme", "योजना", "subsidy", "loan", "insurance", "pm-kisan", "kisan credit"]):
            return {"query_type": "government_schemes", "parsed_entities": {}}
        elif any(word in query_lower for word in ["price", "rate", "मंडी", "mandi", "भाव"]):
            return {"query_type": "market_price", "parsed_entities": {}}
        elif any(word in query_lower for word in ["weather", "rain", "मौसम"]):
            return {"query_type": "weather_advisory", "parsed_entities": {}}
        elif any(word in query_lower for word in ["disease", "pest", "yellow", "रोग"]):
            return {"query_type": "crop_disease", "parsed_entities": {}}
        elif any(word in query_lower for word in ["which crop", "what to grow", "should i plant"]):
            return {"query_type": "crop_selection", "parsed_entities": {}}
        else:
            return {"query_type": "general_advisory", "parsed_entities": {}}

# Agent 2: Crop Disease Diagnosis Agent
def crop_disease_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Diagnose crop diseases - triggers camera for visual inspection"""
    logger.info("\n🌾 Crop Disease Agent running...")
    
    if state.get("query_type") != "crop_disease":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    symptom = entities.get("symptom", "")
    
    # Generate image queries for disease symptoms
    image_queries = []
    
    if crop and symptom:
        # Specific disease symptom images
        image_queries.append(f"{crop} {symptom} disease symptoms leaves")
        image_queries.append(f"{crop} {symptom} plant infection")
    elif crop:
        # General crop diseases
        image_queries.append(f"{crop} common diseases symptoms")
    else:
        # Generic crop disease images
        image_queries.append("crop disease symptoms identification chart")
    
    # Instead of text-based diagnosis, trigger camera
    camera_prompts = {
        "hindi": "क्या आप पत्ती की फोटो दिखाना चाहते हैं? यह ज्यादा सटीक निदान में मदद करेगा।",
        "english": "Would you like to show the leaf photo? This will help in more accurate diagnosis."
    }
    
    return {
        "pest_disease_info": {
            "action": "open_camera",
            "prompt": camera_prompts.get(language, camera_prompts["hindi"])
        },
        "requires_images": True,
        "image_queries": image_queries[:2],  # Limit to 2 queries
        "image_context": "disease_symptoms",
        "layout_type": "split"
    }

# Agent 3: Weather Advisory Agent - IMPROVED
def weather_advisory_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide weather-based farming advisory"""
    logger.info("\n🌤️ Weather Advisory Agent running...")
    
    if state.get("query_type") != "weather_advisory":
        return {}
    
    # Import here to avoid circular dependency
    from agriculture_apis import agriculture_api_service
    
    location = state.get("location", {})
    language = state.get("language", "hindi")
    user_query = state.get("user_query", "")
    
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
    
    if weather_data:
        prompt = f"""You are an agricultural meteorologist providing weather-based farming advice.

Farmer's Question: {user_query}
        
Current Weather Data:
• Temperature: {weather_data.get('temperature', 'N/A')}°C
• Humidity: {weather_data.get('humidity', 'N/A')}%
• Conditions: {weather_data.get('weather', 'N/A')}
• Wind Speed: {weather_data.get('wind_speed', 'N/A')} m/s
        
Language: {language}
        
Provide a comprehensive, accurate response that:
1. STARTS with actual temperature and humidity numbers
2. Directly answers their specific weather-related question
3. Provides actionable farming advice based on these conditions
4. Includes relevant warnings or recommendations
        
Format with clear sections and bullet points.
Respond in {language} naturally. Maximum 200 words for complete answer.
"""
        
        messages = [
            SystemMessage(content="You are an agricultural meteorologist who provides specific, data-driven farming advice based on weather conditions."),
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
    
    # Fallback if weather data unavailable
    generic_msg = {
        "hindi": "मौसम की जानकारी अभी उपलब्ध नहीं है। कृपया बाद में पूछें या अपने स्थानीय मौसम विभाग से संपर्क करें।",
        "english": "Weather information is not available right now. Please try later or contact your local weather department."
    }
    return {
        "weather_data": {},
        "recommendations": [generic_msg.get(language, generic_msg["hindi"])]
    }

# New Agent: Crop Selection Agent - IMPROVED
def crop_selection_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Help farmers choose the right crop based on season, location, and market conditions"""
    logger.info("\n🌱 Crop Selection Agent running...")
    
    if state.get("query_type") != "crop_selection":
        return {}
    
    language = state.get("language", "hindi")
    location = state.get("location", {})
    current_season = get_current_season()
    seasonal_crops = get_seasonal_crops(current_season)
    user_query = state.get("user_query", "")
    
    # Get current weather and market data for better recommendations
    weather_data = state.get("weather_data", {})
    market_data = state.get("market_data", [])
    
    prompt = f"""You are an experienced agricultural advisor helping a farmer choose the right crop.

Farmer's Question: {user_query}
    
Current Season: {current_season}
Suitable crops for this season: {', '.join(seasonal_crops)}
Location: {location.get('city', 'Not specified')}, {location.get('state', 'India')}
Language: {language}
    
Provide a comprehensive, accurate answer that includes:
1. Direct answer to their specific question
2. 2-3 specific crop recommendations with clear reasons
3. Planting timeline and harvest period
4. Expected market demand and profitability insights
5. Practical tips for success with each crop
6. Any location-specific considerations
    
Be specific with numbers, timings, and actionable steps.
Respond in {language} naturally, as a knowledgeable advisor.
Maximum 200 words for complete guidance.
"""
    
    messages = [
        SystemMessage(content="You are a knowledgeable agricultural expert providing practical, accurate advice to farmers about crop selection."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "seasonal_info": {
                "current_season": current_season,
                "suitable_crops": seasonal_crops
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Crop selection error: {str(e)}")
        return {
            "seasonal_info": {
                "current_season": current_season,
                "suitable_crops": seasonal_crops
            }
        }

# New Agent: Soil Management Agent - IMPROVED
def soil_management_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide soil health and fertilizer recommendations"""
    logger.info("\n🌾 Soil Management Agent running...")
    
    if state.get("query_type") != "soil_management":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    prompt = f"""You are a soil expert helping farmers improve their soil health and crop yields.
    
Farmer's Question: {user_query}
Crop mentioned: {crop if crop else "Not specified"}
Location: {location.get('city', 'India')}
Language: {language}
    
Provide comprehensive, accurate soil management advice:
    
1. Direct, specific answer to their exact question
2. Soil health improvement techniques relevant to their situation
3. Detailed fertilizer recommendations (with quantities and timings):
   - Organic options (compost, FYM, green manure)
   - Chemical options if crop mentioned (NPK ratios, amounts per acre)
4. Step-by-step practical implementation guide
5. Expected results and timeline
6. Cost considerations
    
Be very specific with:
- Exact quantities (kg/acre or quintals/hectare)
- Application timings (days before planting, growth stages)
- Methods (broadcasting, basal application, top dressing)
- Specific product names or formulations when relevant
    
Respond in {language} in a clear, detailed manner.
Maximum 200 words for complete guidance.
"""
    
    messages = [
        SystemMessage(content="You are a soil health expert who provides specific, accurate, actionable advice to help farmers improve their yields."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {"recommendations": [response.content]}
    except Exception as e:
        logger.error(f"Soil management error: {str(e)}")
        return {}

# New Agent: General Advisory Fallback Agent - IMPROVED
def general_advisory_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Handle any agricultural query with genuine, accurate, helpful responses"""
    logger.info("\n🤝 General Advisory Agent running...")
    
    user_query = state.get("user_query", "")
    language = state.get("language", "hindi")
    location = state.get("location", {})
    entities = state.get("parsed_entities", {})
    
    prompt = f"""You are an experienced agricultural advisor providing genuine, accurate, practical help to farmers.
    
Farmer's Question: {user_query}
Location: {location.get('city', 'India')}, {location.get('state', 'India')}
Entities identified: {entities}
Language: {language}
    
Provide a comprehensive, accurate response that:
1. Directly and specifically answers their exact question
2. Provides detailed, actionable steps they can implement immediately
3. Includes specific numbers, timings, or measurements where applicable
4. Considers their location and local conditions
5. Addresses any concerns they might have
6. Gives practical tips from field experience
    
Guidelines:
- Be highly specific and detailed with your advice
- Use exact measurements, timings, and quantities
- Provide step-by-step instructions when relevant
- Use {language} naturally and professionally
- In Hindi, use "आप" (respectful form)
- Give real, proven, implementable solutions
- If uncertain about very specific local details, provide general best practices
- Maximum 220 words for thorough answer
    
Focus on accuracy and completeness over brevity.
"""
    
    messages = [
        SystemMessage(content="You are an experienced agricultural expert who provides clear, accurate, detailed, practical advice to help farmers succeed."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {"recommendations": [response.content]}
    except Exception as e:
        logger.error(f"General advisory error: {str(e)}")
        fallback_msg = {
            "hindi": "मुझे खुशी होगी आपकी मदद करने में। कृपया अपना सवाल फिर से पूछें या अधिक विवरण दें।",
            "english": "I'd be happy to help you. Please ask your question again or provide more details."
        }
        return {"recommendations": [fallback_msg.get(language, fallback_msg["hindi"])]}

# Agent 4: Market Price Agent - IMPROVED
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
    user_query = state.get("user_query", "")
    
    # If commodity not extracted, try to identify from query
    if not commodity:
        # Simple extraction logic
        query_lower = user_query.lower()
        common_crops = ["wheat", "rice", "cotton", "soybean", "गेहूं", "धान", "कपास", "सोयाबीन"]
        for crop in common_crops:
            if crop in query_lower:
                commodity = crop
                break
    
    # If still no commodity, ask for clarification
    if not commodity:
        logger.info("No commodity specified, asking for clarification")
        
        prompt = f"""The farmer is asking about market prices but didn't specify which crop.

Farmer's Question: {user_query}
Location: {location.get('city', 'India')}
Language: {language}

Provide a helpful response that:
1. Acknowledges their question about market prices
2. Politely asks which specific crop they want to know about
3. Mentions 4-5 common crops traded in {location.get('city', 'their area')}
4. Suggests resources: e-NAM portal (enam.gov.in), local mandi

Keep it friendly and helpful.
Respond in {language}. Maximum 120 words.
"""
        
        messages = [
            SystemMessage(content="You are an agricultural market expert who helps farmers get price information."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = llm.invoke(messages)
            return {"recommendations": [response.content]}
        except Exception as e:
            logger.error(f"Market clarification error: {str(e)}")
            fallback = {
                "hindi": "कृपया बताइए आप किस फसल का भाव जानना चाहते हैं? गेहूं, धान, सोयाबीन, कपास, या कोई और फसल?",
                "english": "Please tell me which crop's price you want to know? Wheat, rice, soybean, cotton, or another crop?"
            }
            return {"recommendations": [fallback.get(language, fallback["hindi"])]}
    
    # Fetch market data synchronously
    market_data = []
    try:
        market_data = run_async_safe(agriculture_api_service.get_commodity_prices(
            commodity=commodity,
            state=location.get("state"),
            district=location.get("district")
        ))
    except Exception as e:
        logger.error(f"Market fetch error: {str(e)}")
    
    # Generate response with available data
    if market_data and len(market_data) > 0:
        prompt = f"""You are an agricultural market expert analyzing prices for a farmer.

Farmer's Question: {user_query}
        
Crop: {commodity}
Market data: {market_data[:5]}
Location: {location.get('city', 'India')}
Language: {language}

Provide comprehensive market analysis:

1. **Current Prices** - State the actual numbers from the data
2. **Price Range** - Minimum to maximum prices across mandis
3. **Best Markets** - Which mandi offers the best price
4. **Price Trends** - Are prices going up or down (if data indicates)
5. **Selling Strategy** - When and where to sell for best returns
6. **Additional Tips** - Quality factors, timing, transportation

Be specific with actual prices from the data.
Use clear formatting with sections and bullet points.
Respond in {language}. Maximum 200 words.
"""
    else:
        # API failed or no data - provide informed response
        prompt = f"""You are an agricultural market expert helping a farmer.

Farmer wants to know about {commodity} prices in {location.get('city', 'their area')}.
Language: {language}

The market data API is unavailable. Provide helpful response:

1. Acknowledge their question about {commodity} prices
2. Provide typical price range for {commodity} in current season (October 2025, Rabi season starting)
3. Suggest checking:
   - e-NAM portal (enam.gov.in) for official prices
   - Local mandi for current rates
   - Mandi helpline: 1800-270-0224
4. General advice on:
   - When to sell {commodity} for best prices
   - Quality factors that affect prices
   - Storage considerations

Be specific and helpful using your knowledge of typical prices.
Respond in {language}. Maximum 180 words.
"""
    
    messages = [
        SystemMessage(content="You are an agricultural market analyst who helps farmers get the best prices for their produce."),
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
        # Basic fallback
        if market_data:
            avg_price = sum([d.get('modal_price', 0) for d in market_data[:3]]) / len(market_data[:3])
            basic_info = {
                "hindi": f"**{commodity} का भाव** 💰\n\n• औसत मूल्य: ₹{avg_price:.2f}/क्विंटल\n• {len(market_data)} मंडियों में उपलब्ध\n\nअधिक जानकारी: enam.gov.in",
                "english": f"**{commodity} Price** 💰\n\n• Average: ₹{avg_price:.2f}/quintal\n• Available in {len(market_data)} mandis\n\nMore info: enam.gov.in"
            }
        else:
            basic_info = {
                "hindi": f"**{commodity} का भाव**\n\nकृपया देखें:\n• e-NAM: enam.gov.in\n• स्थानीय मंडी\n• हेल्पलाइन: 1800-270-0224",
                "english": f"**{commodity} Price**\n\nPlease check:\n• e-NAM: enam.gov.in\n• Local mandi\n• Helpline: 1800-270-0224"
            }
        return {
            "market_data": market_data,
            "recommendations": [basic_info.get(language, basic_info["hindi"])]
        }

# Agent 5: Government Schemes Agent - IMPROVED
def government_schemes_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide comprehensive information about government schemes"""
    logger.info("\n🏛️ Government Schemes Agent running...")
    
    if state.get("query_type") != "government_schemes":
        return {}
    
    language = state.get("language", "hindi")
    location = state.get("location", {})
    user_query = state.get("user_query", "")
    
    prompt = f"""You are a government schemes expert helping farmers access benefits and support.
    
Farmer's Question: {user_query}
Location: {location.get('city', 'India')}, {location.get('state', 'India')}
Language: {language}
    
Provide COMPREHENSIVE, SPECIFIC, ACCURATE information about relevant government schemes (2024-2025).
    
Major Schemes Available:
1. **PM-Kisan Samman Nidhi**: ₹6000/year (₹2000 × 3 installments)
2. **Pradhan Mantri Fasal Bima Yojana (PMFBY)**: 2% premium Kharif, 1.5% Rabi
3. **Kisan Credit Card (KCC)**: Up to ₹3 lakh at 4% interest
4. **PM-Kusum**: 90% subsidy on solar pumps
5. **Soil Health Card Scheme**: Free soil testing
6. **Paramparagat Krishi Vikas Yojana (PKVY)**: Organic farming support
7. **National Agriculture Market (e-NAM)**: Online trading platform
8. **Kisan Rail & Kisan Udaan**: Subsidized transport
    
For each relevant scheme mentioned in their question, provide:
    
**[Scheme Name in {language}]** 
• **लाभ/Benefits**: Exact amounts, coverage, what they get
• **पात्रता/Eligibility**: Who can apply (age, land, etc.)
• **आवेदन प्रक्रिया/How to Apply**: Step-by-step process
• **दस्तावेज/Documents**: Complete list
• **संपर्क/Contact**: Helpline, website, local office
    
Use clear sections with line breaks between different schemes.
Be extremely specific with:
- Exact amounts (₹6000, not "financial support")
- Precise eligibility criteria
- Actual application steps
- Real contact numbers and websites
    
Respond in {language} with complete, accurate details.
Maximum 250 words to provide thorough information.
"""
    
    messages = [
        SystemMessage(content="You are a government schemes expert who provides accurate, comprehensive, detailed information to help farmers access all available benefits and subsidies."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        
        return {
            "recommendations": [response.content],
            "government_schemes": [{
                "source": "llm_knowledge",
                "comprehensive_info": response.content
            }]
        }
        
    except Exception as e:
        logger.error(f"Government schemes LLM error: {str(e)}")
        
        # Comprehensive fallback information
        fallback_info = {
            "hindi": f"""📢 {location.get('city', 'भारत')} के किसानों के लिए मुख्य सरकारी योजनाएं:

**1. PM-किसान सम्मान निधि** 💰
• लाभ: ₹6000 सालाना (₹2000 × 3 किस्त)
• पात्रता: सभी भूमिधारी किसान
• दस्तावेज: आधार, बैंक खाता, भूमि रिकॉर्ड
• आवेदन: pmkisan.gov.in या CSC सेंटर
• हेल्पलाइन: 155261, 011-24300606

**2. प्रधानमंत्री फसल बीमा योजना** 🌾
• प्रीमियम: खरीफ 2%, रबी 1.5%
• लाभ: प्राकृतिक आपदा से पूर्ण सुरक्षा
• आवेदन: बैंक, CSC, या pmfby.gov.in
• समय: बुवाई से 7 दिन पहले तक

**3. किसान क्रेडिट कार्ड (KCC)** 💳
• ऋण: ₹3 लाख तक, 4% ब्याज दर
• लाभ: आसान कृषि ऋण, बीमा कवर
• आवेदन: नजदीकी बैंक शाखा
• दस्तावेज: आधार, भूमि दस्तावेज

**4. PM-कुसुम योजना** ☀️
• लाभ: 90% सब्सिडी सोलर पंप पर
• आवेदन: राज्य कृषि विभाग

📞 अधिक जानकारी:
• किसान कॉल सेंटर: 1800-180-1551
• CSC सेंटर या तहसील कार्यालय
• वेबसाइट: agricoop.gov.in""",
            
            "english": f"""📢 Major Government Schemes for Farmers in {location.get('city', 'India')}:

**1. PM-Kisan Samman Nidhi** 💰
• Benefits: ₹6000/year (₹2000 × 3 installments)
• Eligibility: All land-holding farmers
• Documents: Aadhaar, bank account, land records
• Apply: pmkisan.gov.in or CSC center
• Helpline: 155261, 011-24300606

**2. Pradhan Mantri Fasal Bima Yojana** 🌾
• Premium: Kharif 2%, Rabi 1.5%
• Benefits: Full protection from natural calamities
• Apply: Bank, CSC, or pmfby.gov.in
• Deadline: 7 days before sowing

**3. Kisan Credit Card (KCC)** 💳
• Loan: Up to ₹3 lakh at 4% interest
• Benefits: Easy agriculture loan, insurance cover
• Apply: Nearest bank branch
• Documents: Aadhaar, land documents

**4. PM-Kusum Scheme** ☀️
• Benefits: 90% subsidy on solar pumps
• Apply: State Agriculture Department

📞 More Information:
• Kisan Call Center: 1800-180-1551
• CSC center or Tehsil office
• Website: agricoop.gov.in"""
        }
        
        return {
            "recommendations": [fallback_info.get(language, fallback_info["hindi"])],
            "government_schemes": [{"source": "fallback", "info": "comprehensive_schemes"}]
        }

# =======================
# NEW FERTILIZER & PESTICIDE AGENTS
# =======================

# Agent 7: Fertilizer Recommendation Agent
def fertilizer_recommendation_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Suggest appropriate fertilizers based on crop, soil, and growth stage"""
    logger.info("\n🌱 Fertilizer Recommendation Agent running...")
    
    if state.get("query_type") not in ["fertilizer_recommendation", "soil_management"]:
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    growth_stage = entities.get("growth_stage", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    prompt = f"""You are an expert soil scientist and fertilizer specialist helping farmers optimize their crop nutrition.

Farmer's Question: {user_query}
Crop: {crop if crop else "Not specified"}
Growth Stage: {growth_stage if growth_stage else "Not specified"}
Location: {location.get('city', 'India')}, {location.get('state', 'India')}
Language: {language}

Provide COMPREHENSIVE, SPECIFIC fertilizer recommendations:

**1. Situation Analysis**
- Identify the likely nutrient deficiency or need based on their query
- Consider the crop type and growth stage

**2. Fertilizer Recommendations**

**A) For Chemical Fertilizers:**
- **Primary Recommendation**: Specific fertilizer name (e.g., Urea, DAP, MOP, NPK 10:26:26)
- **NPK Ratio**: Exact numbers
- **Quantity**: Precise amounts (kg/acre or kg/hectare)
- **Cost**: Approximate cost per bag and total
- **Availability**: Where to buy (local dealer, cooperative)

**B) For Organic Alternatives:**
- **Options**: FYM, compost, vermicompost, green manure, bio-fertilizers
- **Quantity**: Specific amounts needed
- **Benefits**: Why organic is beneficial
- **Preparation time**: If home-made

**3. Application Specifics**
- **Timing**: When to apply (days before sowing, at which growth stage)
- **Method**: Broadcasting, basal application, top dressing, foliar spray
- **Precautions**: Rain avoidance, irrigation requirements

**4. Expected Results**
- **Timeline**: When to see improvements (7-10 days, etc.)
- **Yield impact**: Expected increase
- **Visible changes**: What to look for

**5. Additional Tips**
- **Soil testing**: Recommend if needed
- **Micronutrients**: Zinc, boron, etc. if required
- **Cost optimization**: Most economical approach

Be EXTREMELY SPECIFIC with:
- Exact product names (Urea 46-0-0, DAP 18-46-0, etc.)
- Precise quantities (50 kg/acre, not "adequate amount")
- Exact timing (15 days after sowing, not "early stage")
- Actual prices (₹300/bag, not "affordable")

Use clear sections with bullet points and line breaks.
Respond in {language} naturally and professionally.
Maximum 250 words for thorough guidance.
"""
    
    messages = [
        SystemMessage(content="You are an expert fertilizer specialist who provides precise, actionable, accurate recommendations to help farmers maximize yields."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        
        # Generate image queries for fertilizer products
        image_queries = []
        fertilizer_keywords = ["Urea", "DAP", "MOP", "NPK", "SSP", "Potash", "Phosphate"]
        
        # Extract mentioned fertilizers from response
        response_text = response.content.upper()
        for keyword in fertilizer_keywords:
            if keyword.upper() in response_text:
                image_queries.append(f"{keyword} fertilizer bag India")
        
        # If specific crop mentioned, add crop-specific fertilizer images
        if crop:
            image_queries.append(f"{crop} fertilizer application")
        
        # Add generic fertilizer image if no specific products found
        if not image_queries:
            image_queries.append("agricultural fertilizer products India")
        
        return {
            "fertilizer_info": {
                "recommendation": response.content,
                "crop": crop,
                "stage": growth_stage
            },
            "recommendations": [response.content],
            "requires_images": True,
            "image_queries": image_queries[:3],  # Limit to 3 queries
            "image_context": "fertilizer_products",
            "layout_type": "split"
        }
    except Exception as e:
        logger.error(f"Fertilizer recommendation error: {str(e)}")
        
        # Basic fallback
        fallback = {
            "hindi": f"""🌱 **उर्वरक सिफारिश** {f"({crop})" if crop else ""}

**रासायनिक उर्वरक:**
• यूरिया (46-0-0): 50 किलो/एकड़
• DAP (18-46-0): 25 किलो/एकड़ (बुवाई से पहले)
• MOP (0-0-60): 15 किलो/एकड़

**जैविक विकल्प:**
• गोबर की खाद: 5-8 टन/एकड़
• वर्मीकंपोस्ट: 2 टन/एकड़

**लागत:** ₹2,500-3,500/एकड़

📞 अधिक जानकारी: स्थानीय कृषि विभाग या मृदा परीक्षण प्रयोगशाला""",
            
            "english": f"""🌱 **Fertilizer Recommendation** {f"({crop})" if crop else ""}

**Chemical Fertilizers:**
• Urea (46-0-0): 50 kg/acre
• DAP (18-46-0): 25 kg/acre (before sowing)
• MOP (0-0-60): 15 kg/acre

**Organic Options:**
• FYM: 5-8 tons/acre
• Vermicompost: 2 tons/acre

**Cost:** ₹2,500-3,500/acre

📞 More info: Local Agriculture Department or Soil Testing Lab"""
        }
        
        return {
            "fertilizer_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 8: Pesticide Recommendation Agent
def pesticide_recommendation_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Suggest appropriate pesticides and pest management strategies"""
    logger.info("\n🐛 Pesticide Recommendation Agent running...")
    
    if state.get("query_type") != "pesticide_recommendation":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    pest_name = entities.get("pest_name", "")
    symptom = entities.get("symptom", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    prompt = f"""You are an expert entomologist and integrated pest management (IPM) specialist.

Farmer's Question: {user_query}
Crop: {crop if crop else "Not specified"}
Pest/Disease: {pest_name if pest_name else "Not specified"}
Symptoms: {symptom if symptom else "Not specified"}
Location: {location.get('city', 'India')}
Language: {language}

Provide COMPREHENSIVE pest management guidance:

**1. Pest/Disease Identification**
- Identify the likely pest or disease from symptoms
- Confirm if it matches their description

**2. IPM Strategy (Integrated Pest Management)**

**A) Cultural Control (First Priority):**
- Crop rotation, trap crops, field sanitation
- Biological control: Natural predators, neem-based solutions

**B) Chemical Control (If Necessary):**

**Recommended Pesticides:**
• **Product Name**: Exact commercial name (e.g., Chlorpyrifos 20% EC, Imidacloprid 17.8% SL)
• **Target**: What pest it controls
• **Dosage**: mL or grams per liter of water
• **Spray volume**: Liters needed per acre
• **Cost**: Price per bottle/packet
• **PHI**: Pre-Harvest Interval (days before harvest)
• **REI**: Re-entry Interval (safety period)

**Alternative Options:**
- 2-3 alternatives with different chemical groups (to prevent resistance)

**3. Application Guidelines**
- **Timing**: Best time of day (early morning/evening)
- **Weather**: Avoid before rain
- **Equipment**: Sprayer type
- **Mixing**: Order of mixing if tank-mixing

**4. Safety Precautions**
- **PPE**: Mask, gloves, protective clothing
- **Disposal**: Empty container disposal
- **Storage**: How to store remaining pesticide
- **First Aid**: In case of exposure

**5. Organic Alternatives**
- Neem oil, soap solution, pheromone traps
- Bio-pesticides: Bt, NPV, Trichoderma

**6. Monitoring**
- How to check if treatment worked
- Follow-up spray timing if needed

Be EXTREMELY SPECIFIC with:
- Exact product names and formulations
- Precise dosages (2 mL/L, not "as directed")
- Actual prices (₹350/500ml, not "affordable")
- Safety intervals (7 days PHI, not "safe period")

Use clear formatting with sections and bullet points.
Respond in {language} professionally.
Maximum 280 words for thorough guidance.
"""
    
    messages = [
        SystemMessage(content="You are an IPM expert who provides safe, effective, specific pest control recommendations prioritizing farmer safety and environmental protection."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        
        # Generate image queries for pesticide products
        image_queries = []
        pesticide_keywords = ["Chlorpyrifos", "Imidacloprid", "Cypermethrin", "Malathion", 
                             "Monocrotophos", "Profenofos", "Neem", "Lambda", "Acetamiprid"]
        
        # Extract mentioned pesticides from response
        response_text = response.content
        for keyword in pesticide_keywords:
            if keyword.lower() in response_text.lower():
                image_queries.append(f"{keyword} pesticide bottle India")
        
        # Add safety equipment images
        image_queries.append("PPE safety equipment pesticide spraying India")
        
        # Add sprayer equipment if crop mentioned
        if crop:
            image_queries.append(f"pesticide sprayer {crop} application")
        
        # Add generic pesticide image if no specific products found
        if len(image_queries) <= 1:  # Only safety equipment added
            image_queries.append("agricultural pesticides India")
        
        return {
            "pesticide_info": {
                "recommendation": response.content,
                "crop": crop,
                "pest": pest_name
            },
            "recommendations": [response.content],
            "requires_images": True,
            "image_queries": image_queries[:3],  # Limit to 3 queries
            "image_context": "pesticide_products",
            "layout_type": "split"
        }
    except Exception as e:
        logger.error(f"Pesticide recommendation error: {str(e)}")
        
        fallback = {
            "hindi": f"""🐛 **कीट नियंत्रण सिफारिश** {f"({crop})" if crop else ""}

**एकीकृत कीट प्रबंधन (IPM):**

**1. जैविक नियंत्रण (प्राथमिकता):**
• नीम तेल: 5 mL/लीटर पानी
• साबुन घोल: 10 ग्राम/लीटर
• जैविक कीटनाशक

**2. रासायनिक नियंत्रण (यदि आवश्यक):**
• क्लोरपाइरिफॉस 20% EC: 2-2.5 mL/लीटर
• इमिडाक्लोप्रिड 17.8% SL: 0.5 mL/लीटर
• स्प्रे मात्रा: 200-250 लीटर/एकड़

**सुरक्षा उपाय:**
⚠️ मास्क, दस्ताने, सुरक्षात्मक कपड़े पहनें
⚠️ सुबह या शाम को स्प्रे करें
⚠️ बारिश से पहले स्प्रे न करें
⚠️ कटाई से 7-15 दिन पहले बंद करें

📞 विशेषज्ञ सलाह: किसान कॉल सेंटर 1800-180-1551""",
            
            "english": f"""🐛 **Pest Control Recommendation** {f"({crop})" if crop else ""}

**Integrated Pest Management (IPM):**

**1. Biological Control (Priority):**
• Neem oil: 5 mL/L water
• Soap solution: 10 g/L
• Bio-pesticides

**2. Chemical Control (If necessary):**
• Chlorpyrifos 20% EC: 2-2.5 mL/L
• Imidacloprid 17.8% SL: 0.5 mL/L
• Spray volume: 200-250 L/acre

**Safety Measures:**
⚠️ Wear mask, gloves, protective clothing
⚠️ Spray in morning or evening
⚠️ Avoid spraying before rain
⚠️ Stop 7-15 days before harvest

📞 Expert advice: Kisan Call Center 1800-180-1551"""
        }
        
        return {
            "pesticide_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 9: Application Guide Agent
def application_guide_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide detailed application instructions for fertilizers and pesticides"""
    logger.info("\n📋 Application Guide Agent running...")
    
    if state.get("query_type") != "application_guide":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    # Detect if query is about fertilizer or pesticide application
    query_lower = user_query.lower()
    is_pesticide = any(word in query_lower for word in ["pesticide", "spray", "insecticide", "कीटनाशक", "स्प्रे"])
    
    prompt = f"""You are an agricultural application specialist providing step-by-step guidance.

Farmer's Question: {user_query}
Crop: {crop if crop else "Not specified"}
Application Type: {"Pesticide/Insecticide" if is_pesticide else "Fertilizer"}
Farm Size: Assumed 1-2 acres (ask if more)
Language: {language}

Provide EXTREMELY DETAILED, STEP-BY-STEP application instructions:

**1. Dosage Calculation**
- **For {crop if crop else "typical crop"}:**
  - Product quantity per liter of water: X mL or grams/L
  - Total water needed: Y liters for 1 acre
  - Total product needed: Z mL/kg for 1 acre
  - Cost calculation: Price breakdown

**2. Preparation Steps**
1. **Gather Materials:**
   - List all equipment needed (sprayer, bucket, stirrer, PPE)
   - Safety equipment checklist

2. **Mixing Instructions:**
   - Step 1: Fill half tank with clean water
   - Step 2: Add measured product slowly while stirring
   - Step 3: Add remaining water
   - Step 4: Mix thoroughly for X minutes
   - ⚠️ Never mix dry to dry or concentrate to concentrate

**3. Application Method**
- **Timing:** Best time of day (early morning 6-10 AM or evening 4-6 PM)
- **Weather conditions:** No rain expected for 24 hours, wind < 10 km/h
- **Technique:**
  - Sprayer pressure: X PSI/bar
  - Nozzle height: Y cm above crop
  - Walking speed: Steady pace
  - Coverage: Ensure uniform coating, both sides of leaves

**4. Area-Specific Calculations**
For 1 Acre:
- Product: ___ mL/kg
- Water: ___ liters
- Cost: ₹___

For 2 Acres:
- Product: ___ mL/kg
- Water: ___ liters
- Cost: ₹___

**5. Safety During Application**
- **Before:** Wear mask, gloves, long sleeves, pants, boots
- **During:** Don't eat, drink, or smoke; no children/animals nearby
- **After:** Wash hands, face, equipment thoroughly

**6. Post-Application Care**
- **Waiting period:** 
  - Re-entry interval: __ hours (when it's safe to enter field)
  - Pre-harvest interval: __ days (for pesticides)
  - Irrigation: Wait __ hours before watering
- **Expected results:** Timeline for visible effects
- **Follow-up:** When to apply next dose if needed

**7. Storage & Disposal**
- **Unused product:** Store in original container, cool dry place
- **Empty containers:** Triple rinse and dispose properly (never reuse)
- **Leftover spray:** Don't pour in water bodies

**8. Troubleshooting**
- If rain occurs within 4 hours: May need re-application
- If no effect after X days: Consult expert
- If crop shows stress: Stop and seek advice

Be ULTRA-SPECIFIC with every number, timing, and instruction.
Use clear numbered steps and bullet points.
Respond in {language} with extreme clarity.
Maximum 300 words for complete step-by-step guide.
"""
    
    messages = [
        SystemMessage(content="You are an expert agricultural trainer who provides crystal-clear, step-by-step, safe application instructions that anyone can follow."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "application_guide_info": {
                "guide": response.content,
                "type": "pesticide" if is_pesticide else "fertilizer"
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Application guide error: {str(e)}")
        
        fallback = {
            "hindi": f"""📋 **अनुप्रयोग गाइड** {f"({crop})" if crop else ""}

**मात्रा गणना (1 एकड़):**
• उत्पाद: 500-750 mL/kg
• पानी: 200-250 लीटर
• लागत: ₹200-500

**कदम-दर-कदम:**

**1. तैयारी:**
• स्प्रेयर, बाल्टी, मापने वाला कप
• सुरक्षा उपकरण: मास्क, दस्ताने

**2. मिश्रण:**
1. आधा टैंक साफ पानी भरें
2. उत्पाद धीरे-धीरे डालें
3. अच्छी तरह मिलाएं
4. बाकी पानी डालें

**3. स्प्रे करें:**
• समय: सुबह 6-10 बजे या शाम 4-6 बजे
• दोनों तरफ की पत्तियों पर समान छिड़काव
• 24 घंटे बारिश नहीं होनी चाहिए

**4. सुरक्षा:**
⚠️ स्प्रे के दौरान खाना-पीना नहीं
⚠️ स्प्रे के बाद हाथ-मुंह धोएं
⚠️ खाली डिब्बे सुरक्षित तरीके से फेंकें

**5. प्रतीक्षा अवधि:**
• पुनः प्रवेश: 12-24 घंटे
• कटाई से पहले: 7-15 दिन""",
            
            "english": f"""📋 **Application Guide** {f"({crop})" if crop else ""}

**Dosage Calculation (1 acre):**
• Product: 500-750 mL/kg
• Water: 200-250 liters
• Cost: ₹200-500

**Step-by-Step:**

**1. Preparation:**
• Sprayer, bucket, measuring cup
• Safety gear: Mask, gloves

**2. Mixing:**
1. Fill half tank with clean water
2. Add product slowly
3. Mix thoroughly
4. Add remaining water

**3. Spray:**
• Time: Morning 6-10 AM or evening 4-6 PM
• Uniform coverage on both leaf sides
• No rain for 24 hours

**4. Safety:**
⚠️ No eating/drinking during spray
⚠️ Wash hands/face after spray
⚠️ Dispose empty containers safely

**5. Waiting Period:**
• Re-entry: 12-24 hours
• Before harvest: 7-15 days"""
        }
        
        return {
            "application_guide_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 10: Fertilizer Schedule Planner Agent
def fertilizer_schedule_planner_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Create comprehensive fertilization schedule for entire crop cycle"""
    logger.info("\n📅 Fertilizer Schedule Planner Agent running...")
    
    if state.get("query_type") != "fertilizer_schedule":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    user_query = state.get("user_query", "")
    current_season = get_current_season()
    
    prompt = f"""You are a crop nutrition planning expert creating a complete fertilization schedule.

Farmer's Question: {user_query}
Crop: {crop if crop else "Request specific crop"}
Season: {current_season}
Language: {language}

Create a COMPLETE, STAGE-WISE fertilization schedule for the entire crop lifecycle:

**CROP: {crop if crop else "[Specify Crop]"}**
**Total Duration: [X] days/months**

---

**Stage 1: Land Preparation / Basal Application**
**Timing:** 7-15 days before sowing
**Fertilizers:**
• FYM/Compost: X tons/acre (₹___)
• DAP (18-46-0): Y kg/acre (₹___)
• MOP (0-0-60): Z kg/acre (₹___)
**Method:** Broadcasting + incorporation into soil
**Cost:** ₹___
**Purpose:** Build soil fertility base

---

**Stage 2: At Sowing / Planting**
**Timing:** Day 0 (sowing day)
**Fertilizers:**
• Starter fertilizer: NPK X-X-X @ ___ kg/acre
• Zinc sulfate: ___ kg/acre (if deficient)
**Method:** In furrow or seed placement
**Cost:** ₹___
**Purpose:** Early seedling vigor

---

**Stage 3: Vegetative Stage / First Top Dressing**
**Timing:** [X] days after sowing (DAS)
**Growth Stage:** [Describe stage - tillering, 4-6 leaf, etc.]
**Fertilizers:**
• Urea (46-0-0): ___ kg/acre (₹___)
• or CAN: ___ kg/acre
**Method:** Side dressing + irrigation
**Cost:** ₹___
**Purpose:** Promote vegetative growth

---

**Stage 4: [Critical Growth Stage] / Second Top Dressing**
**Timing:** [Y] DAS
**Growth Stage:** [Flowering, panicle initiation, etc.]
**Fertilizers:**
• Urea: ___ kg/acre
• NPK 19-19-19 (if needed): ___ kg/acre
**Method:** Top dressing or foliar spray
**Cost:** ₹___
**Purpose:** Support flowering/fruiting

---

**Stage 5: [Final Stage] / Third Application (if needed)**
**Timing:** [Z] DAS
**Growth Stage:** [Grain filling, fruit development]
**Fertilizers:**
• Urea: ___ kg/acre
• Potash: ___ kg/acre (for quality)
**Method:** Light top dressing
**Cost:** ₹___
**Purpose:** Improve yield and quality

---

**📊 TOTAL FERTILIZER REQUIREMENT & COST SUMMARY**

**Organic:**
• FYM/Compost: ___ tons @ ₹___

**Chemical:**
• Urea: ___ kg total @ ₹___
• DAP: ___ kg total @ ₹___
• MOP: ___ kg total @ ₹___
• Others: ___ @ ₹___

**Grand Total Cost: ₹___ per acre**

---

**⚠️ IMPORTANT NOTES:**

1. **Irrigation:** Always irrigate after fertilizer application (except before rain)
2. **Soil Testing:** Get soil tested every 2-3 years for precise recommendations
3. **Adjustments:** Reduce by 25-30% if using FYM regularly
4. **Weather:** Don't apply if heavy rain expected within 24 hours
5. **Organic Alternative:** Can substitute 50% chemical with vermicompost/bio-fertilizers

**📈 Expected Results:**
• Yield increase: ___% compared to no fertilizer
• ROI: Return of ₹___ per ₹1 invested in fertilizers
• Quality improvement: Better grade, market price

**📞 Support:**
• Soil Health Card: soilhealth.dac.gov.in
• Kisan Call Center: 1800-180-1551

Be EXTREMELY SPECIFIC with every timing, quantity, and cost.
Use actual numbers based on standard recommendations for {crop}.
Create a complete, practical schedule farmers can pin on their wall.
Respond in {language} with clear formatting.
Maximum 350 words for complete schedule.
"""
    
    messages = [
        SystemMessage(content="You are a crop nutrition expert who creates precise, complete, practical fertilization schedules that farmers can follow throughout the crop season."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "fertilizer_info": {
                "schedule": response.content,
                "crop": crop,
                "season": current_season
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Fertilizer schedule error: {str(e)}")
        
        fallback = {
            "hindi": f"""📅 **उर्वरक अनुसूची** {f"({crop})" if crop else ""}

**चरण 1: भूमि तैयारी (बुवाई से 7-15 दिन पहले)**
• गोबर की खाद: 5-8 टन/एकड़
• DAP: 50 kg/एकड़
• लागत: ₹2,500

**चरण 2: बुवाई के समय (दिन 0)**
• स्टार्टर NPK: 25 kg/एकड़
• लागत: ₹800

**चरण 3: वानस्पतिक अवस्था (20-25 दिन)**
• यूरिया: 50 kg/एकड़
• लागत: ₹400

**चरण 4: फूल आने पर (40-50 दिन)**
• यूरिया: 25 kg/एकड़
• लागत: ₹200

**कुल लागत: ₹3,900/एकड़**
**अपेक्षित उपज वृद्धि: 20-30%**

📞 मृदा परीक्षण के लिए: स्थानीय कृषि विभाग""",
            
            "english": f"""📅 **Fertilizer Schedule** {f"({crop})" if crop else ""}

**Stage 1: Land Preparation (7-15 days before sowing)**
• FYM: 5-8 tons/acre
• DAP: 50 kg/acre
• Cost: ₹2,500

**Stage 2: At Sowing (Day 0)**
• Starter NPK: 25 kg/acre
• Cost: ₹800

**Stage 3: Vegetative Stage (20-25 days)**
• Urea: 50 kg/acre
• Cost: ₹400

**Stage 4: Flowering (40-50 days)**
• Urea: 25 kg/acre
• Cost: ₹200

**Total Cost: ₹3,900/acre**
**Expected Yield Increase: 20-30%**

📞 For soil testing: Local Agriculture Department"""
        }
        
        return {
            "fertilizer_info": {"schedule_fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 11: Irrigation Management Agent
def irrigation_management_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide water management and irrigation scheduling advice"""
    logger.info("\n💧 Irrigation Management Agent running...")
    
    if state.get("query_type") != "irrigation_management":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    growth_stage = entities.get("growth_stage", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    weather_data = state.get("weather_data", {})
    current_season = get_current_season()
    
    prompt = f"""You are an irrigation management expert and water conservation specialist.

Farmer's Question: {user_query}
Crop: {crop if crop else "Not specified"}
Growth Stage: {growth_stage if growth_stage else "General"}
Season: {current_season}
Location: {location.get('city', 'India')}
Current Weather: {weather_data.get('weather', 'Not available') if weather_data else 'Not available'}
Temperature: {weather_data.get('temperature', 'N/A')}°C
Language: {language}

Provide COMPREHENSIVE irrigation management guidance:

**1. Water Requirement Analysis**
- **Crop water need:** ___ mm or liters per day per plant
- **Growth stage factor:** Current stage needs [high/medium/low] water
- **Seasonal adjustment:** {current_season} season considerations
- **Weather impact:** Based on current temperature and humidity

**2. Irrigation Schedule**

**Critical Stages (Must Irrigate):**
1. **Stage:** [e.g., Sowing to germination]
   - **Frequency:** Every __ days
   - **Depth:** __ cm or __ liters per plant
   - **Timing:** Early morning or evening
   
2. **Stage:** [e.g., Flowering]
   - **Frequency:** Every __ days
   - **Why critical:** Directly affects yield
   - **Amount:** Heavier irrigation needed

3. **Stage:** [e.g., Grain filling]
   - **Frequency:** Every __ days
   - **Precaution:** Avoid waterlogging

**Non-Critical Periods:**
- Can skip irrigation if rainfall > __ mm
- Reduce frequency to __ days

**3. Irrigation Methods Comparison**

**A) Flood/Surface Irrigation:**
• Water needed: ___ liters per acre
• Frequency: Every __ days
• Efficiency: 40-60%
• Cost: Low (₹___)
• Best for: Level fields, abundant water

**B) Drip Irrigation:**
• Water needed: ___ liters per acre (30-50% less)
• Frequency: Daily or alternate days
• Efficiency: 90-95%
• Initial cost: ₹35,000-50,000/acre (govt subsidy available)
• Subsidy: Up to 90% under PM-KUSUM
• Operating cost: ₹___/season
• ROI: Payback in 2-3 years
• Best for: Water scarcity, high-value crops

**C) Sprinkler Irrigation:**
• Water needed: ___ liters per acre (20-30% less)
• Efficiency: 70-80%
• Cost: ₹25,000-35,000/acre
• Best for: Uneven terrain, large fields

**4. Water Conservation Techniques**
- **Mulching:** Reduces evaporation by 30-40%
  - Organic mulch: straw, dry leaves (₹500-800/acre)
  - Plastic mulch: Black or silver (₹3,000-5,000/acre)
  
- **Soil moisture retention:**
  - Add FYM: Improves water holding capacity
  - Vermicompost: Retains moisture better
  
- **Timing optimization:**
  - Irrigate in early morning (4-8 AM) or evening (5-8 PM)
  - Avoid midday (loses 40% to evaporation)

**5. Water Quality Considerations**
- **Source:** Well/Canal/Drip water quality matters
- **Salinity:** If EC > 2.0 dS/m, leach with extra water periodically
- **pH:** Ideal 6.5-7.5 for most crops

**6. Drought Management**
- **If water is scarce:**
  - Prioritize critical stages only
  - Use mulching mandatorily
  - Consider deficit irrigation (70% of normal)
  - Antitranspirants can help reduce water loss

**7. Monitoring & Indicators**
- **Signs of under-irrigation:**
  - Leaf wilting in morning
  - Stunted growth
  - Leaf edges browning
  
- **Signs of over-irrigation:**
  - Yellowing leaves
  - Fungal diseases
  - Waterlogged soil

**8. Cost-Benefit Analysis**

**Traditional Flood Irrigation:**
- Water used: ___ liters/acre/season
- Labor cost: ₹___
- Total cost: ₹___

**Drip Irrigation:**
- Water saved: ___% (₹___ in electricity/diesel)
- Yield increase: 20-30%
- Fertilizer savings: 30% (fertigation possible)
- Net benefit: ₹___ more per acre

**9. Government Schemes**
- **PM-KUSUM:** 90% subsidy on solar pumps + drip irrigation
- **PMKSY (Per Drop More Crop):** Subsidy on micro-irrigation
- **Apply:** District Agriculture Office or pmkusum.mnre.gov.in

**10. Smart Irrigation Tips**
- **Check soil moisture:** Dig 4-6 inches deep
  - Dry and dusty → Irrigate now
  - Forms ball when squeezed → Adequate moisture
  - Wet and muddy → Skip irrigation
  
- **Weather-based:** Don't irrigate if rain expected in 24-48 hours
  - Check: IMD app or weather.com
  
- **Use tensiometers:** ₹2,000-3,000, shows exact soil moisture

Be ULTRA-SPECIFIC with quantities, timings, and costs.
Use clear sections and practical examples.
Respond in {language} professionally.
Maximum 400 words for complete irrigation guidance.
"""
    
    messages = [
        SystemMessage(content="You are an irrigation expert who provides precise, water-efficient, economical irrigation strategies that maximize crop yield while conserving water."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "irrigation_info": {
                "recommendation": response.content,
                "crop": crop,
                "season": current_season
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Irrigation management error: {str(e)}")
        
        fallback = {
            "hindi": f"""💧 **सिंचाई प्रबंधन** {f"({crop})" if crop else ""}

**सिंचाई अनुसूची:**
• बुवाई के बाद: तुरंत (हल्की सिंचाई)
• वानस्पतिक अवस्था: हर 7-10 दिन
• फूल आने पर: हर 5-7 दिन (महत्वपूर्ण)
• फल भरने पर: हर 7-10 दिन

**सिंचाई विधियाँ:**

**1. पारंपरिक (बाढ़):**
• पानी: 400-500 लीटर/पौधा
• दक्षता: 40-60%

**2. ड्रिप सिंचाई:**
• पानी: 150-200 लीटर/पौधा (50% बचत)
• लागत: ₹35,000-50,000/एकड़
• सब्सिडी: PM-KUSUM के तहत 90% तक
• ROI: 2-3 साल में

**जल संरक्षण:**
• गीली घास (Mulching): 30% वाष्पीकरण कम
• सुबह या शाम को सिंचाई करें
• मिट्टी की नमी जांचें (4-6 इंच गहराई)

**योजनाएं:**
• PM-KUSUM: सोलर पंप + ड्रिप
• PMKSY: सूक्ष्म सिंचाई सब्सिडी

📞 जिला कृषि कार्यालय: सब्सिडी के लिए""",
            
            "english": f"""💧 **Irrigation Management** {f"({crop})" if crop else ""}

**Irrigation Schedule:**
• After sowing: Immediately (light)
• Vegetative stage: Every 7-10 days
• Flowering: Every 5-7 days (critical)
• Grain filling: Every 7-10 days

**Irrigation Methods:**

**1. Flood Irrigation:**
• Water: 400-500 L/plant
• Efficiency: 40-60%

**2. Drip Irrigation:**
• Water: 150-200 L/plant (50% saving)
• Cost: ₹35,000-50,000/acre
• Subsidy: Up to 90% under PM-KUSUM
• ROI: 2-3 years

**Water Conservation:**
• Mulching: 30% less evaporation
• Irrigate morning or evening
• Check soil moisture (4-6 inch depth)

**Schemes:**
• PM-KUSUM: Solar pump + drip
• PMKSY: Micro-irrigation subsidy

📞 District Agriculture Office: For subsidy"""
        }
        
        return {
            "irrigation_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 12: Soil Health Agent
def soil_health_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide comprehensive soil health analysis and improvement strategies"""
    logger.info("\n🌍 Soil Health Agent running...")
    
    if state.get("query_type") != "soil_health":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    prompt = f"""You are a soil science expert and soil health specialist.

Farmer's Question: {user_query}
Location: {location.get('city', 'India')}, {location.get('state', 'India')}
Language: {language}

Provide COMPREHENSIVE soil health management guidance:

**1. Soil Testing Importance & Process**

**Why Test:**
• Know exact nutrient levels (saves money on unnecessary fertilizers)
• Identify deficiencies early
• Optimize pH for crop
• Track soil health over time

**Where to Test:**
• Govt Soil Testing Labs: FREE or ₹20-50/sample
• Private labs: ₹200-500/sample (faster results)
• Find nearest lab: soilhealth.dac.gov.in

**How to Collect Sample:**
1. **Timing:** Before sowing season
2. **Tools:** Clean auger/spade, plastic bucket
3. **Method:**
   - Collect from 8-10 spots in zigzag pattern
   - Depth: 0-6 inches (for most crops)
   - Mix all samples thoroughly
   - Take 500g sample in clean plastic bag
4. **Submit:** To nearest soil testing lab with field details

**Results Timeline:** 7-15 days

**2. Understanding Soil Test Report**

**Key Parameters:**

**A) Soil pH:**
• Ideal range: 6.0-7.5 for most crops
• < 6.0 (Acidic): Add lime (CaCO₃) @ 200-500 kg/acre
• > 8.0 (Alkaline): Add gypsum (CaSO₄) @ 200-400 kg/acre or sulfur

**B) Organic Carbon (OC):**
• Good: > 0.75%
• Low: < 0.5% → Add FYM, compost, green manure

**C) Macronutrients:**
• **Nitrogen (N):** Low < 250 kg/ha → Apply urea
• **Phosphorus (P):** Low < 12 kg/ha → Apply DAP/SSP
• **Potassium (K):** Low < 120 kg/ha → Apply MOP/SOP

**D) Micronutrients:**
• **Zinc (Zn):** Low < 0.6 ppm → Zinc sulfate 25 kg/acre
• **Iron (Fe):** Low < 4.5 ppm → Iron sulfate
• **Boron (B):** Low < 0.5 ppm → Borax 10 kg/acre

**3. Soil Health Improvement Strategies**

**A) Organic Matter Addition (PRIORITY):**

**1. FYM (Farmyard Manure):**
• Quantity: 5-10 tons/acre annually
• Benefits: Improves structure, water retention, nutrients
• Cost: ₹2,000-4,000/acre
• Application: Before land preparation

**2. Vermicompost:**
• Quantity: 2-3 tons/acre
• Benefits: Rich in microbes, better than FYM
• Cost: ₹8,000-12,000/acre or make your own
• DIY: 8x4x2 ft pit, kitchen waste + cow dung + earthworms

**3. Green Manure:**
• Crops: Dhaincha, sunhemp, cowpea
• Method: Sow, let grow 40-50 days, plow back before flowering
• Benefits: Adds 40-60 kg N/acre, improves structure
• Cost: ₹500-800/acre (seeds only)

**B) pH Management:**

**For Acidic Soil (pH < 6.0):**
• **Lime (CaCO₃):** 200-500 kg/acre
  - Apply 30 days before sowing
  - Mix into top 6 inches
  - Cost: ₹1,500-3,000

**For Alkaline Soil (pH > 8.0):**
• **Gypsum:** 200-400 kg/acre
• **Sulfur:** 50-100 kg/acre
• **FYM:** Helps naturally lower pH
• Cost: ₹1,000-2,500

**C) Nutrient Deficiency Correction:**

**Nitrogen Deficiency (Yellow leaves, stunted growth):**
• **Quick fix:** Urea 50 kg/acre + irrigation
• **Long-term:** FYM + legume rotation

**Phosphorus Deficiency (Purple/dark leaves):**
• **Application:** DAP 50-100 kg/acre or SSP 150-200 kg/acre
• **With FYM for better availability**

**Potassium Deficiency (Leaf edge burning):**
• **Application:** MOP 25-50 kg/acre
• **Wood ash:** Good organic source (50-100 kg/acre)

**Zinc Deficiency (White/yellow bands between veins):**
• **Soil application:** Zinc sulfate 25 kg/acre
• **Foliar spray:** 0.5% ZnSO₄ solution (500g per 100L water)

**4. Soil Structure Improvement**

**For Clay Soil (Heavy, waterlogged):**
• Add FYM: 8-10 tons/acre
• Gypsum: 400 kg/acre
• Deep plowing in summer
• Raised bed cultivation

**For Sandy Soil (Light, low water retention):**
• FYM: 10-15 tons/acre (higher amount)
• Mulching: Retains moisture
• Clay addition if feasible
• Frequent but light irrigation

**5. Soil Conservation Practices**

• **Contour plowing:** On slopes to prevent erosion
• **Mulching:** Crop residue, straw (prevents crusting)
• **Crop rotation:** Legume → Cereal → Oilseed
• **Cover crops:** In off-season prevents nutrient loss
• **Avoid burning residue:** Destroys soil microbes

**6. Soil Biological Health**

**Beneficial Microbes:**
• **Rhizobium:** For legumes (fixes N)
• **Azotobacter:** Free-living N fixer
• **PSB (Phosphate Solubilizing Bacteria):** Makes P available
• **Trichoderma:** Controls soil-borne diseases

**Application:** Mix with FYM or apply with seeds
**Cost:** ₹50-100/packet (200g)

**7. Season-wise Soil Care**

**Summer (Apr-May):**
• Deep plowing (exposes pests/diseases to sun)
• Add FYM before monsoon
• pH correction if needed

**Monsoon (Jun-Sep):**
• Control erosion
• Proper drainage
• Green manure crops

**Winter (Oct-Mar):**
• Crop rotation planning
• Soil sampling (best time)

**8. Cost-Benefit of Soil Health Investment**

**Annual Investment:**
• FYM: ₹3,000/acre
• Soil testing: ₹50/acre
• pH correction (if needed): ₹2,000/acre (one-time every 3-4 years)
• Bio-fertilizers: ₹200/acre
**Total: ₹3,250-5,250/acre**

**Returns:**
• 20-40% yield increase
• 30% fertilizer saving over 2-3 years
• Better soil structure & water retention
• Disease reduction
**ROI: ₹5-10 return per ₹1 invested**

**9. Soil Health Card Scheme**

**What:** Free soil testing by government
**Benefits:**
• Nutrient status report
• Crop-specific fertilizer recommendations
• Issued every 2 years

**How to Get:**
• Contact village agriculture officer
• Or register: soilhealth.dac.gov.in
• Sample collected from your field
• Report within 15-30 days

**10. Warning Signs of Poor Soil Health**

⚠️ **Take Action If:**
• Crops grow poorly despite fertilizers
• Waterlogging or excessive drying
• Soil crust formation
• Increased pest/disease problems
• Yield declining year-on-year

**Immediate Steps:**
1. Get soil tested
2. Add FYM (minimum 5 tons/acre)
3. Stop excessive chemical use
4. Plant green manure crop

Be EXTREMELY DETAILED and SPECIFIC with all recommendations.
Use real numbers, costs, and practical examples.
Respond in {language} with clear formatting.
Maximum 450 words for comprehensive soil health guidance.
"""
    
    messages = [
        SystemMessage(content="You are a soil health expert who provides comprehensive, scientifically accurate, practical advice to help farmers build and maintain healthy, productive soils."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "soil_health_info": {
                "analysis": response.content
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Soil health error: {str(e)}")
        
        fallback = {
            "hindi": f"""🌍 **मृदा स्वास्थ्य प्रबंधन**

**मृदा परीक्षण:**
• कहाँ: जिला कृषि विभाग की प्रयोगशाला
• लागत: मुफ्त या ₹20-50
• वेबसाइट: soilhealth.dac.gov.in

**मृदा सुधार रणनीतियाँ:**

**1. जैविक पदार्थ जोड़ें:**
• गोबर की खाद: 5-10 टन/एकड़ (₹2,000-4,000)
• वर्मीकंपोस्ट: 2-3 टन/एकड़ (₹8,000-12,000)
• हरी खाद: ढैंचा, सनई (₹500-800)

**2. pH प्रबंधन:**
• अम्लीय मिट्टी (pH < 6): चूना 200-500 kg/एकड़
• क्षारीय मिट्टी (pH > 8): जिप्सम 200-400 kg/एकड़

**3. पोषक तत्व:**
• नाइट्रोजन कमी: यूरिया 50 kg/एकड़
• फॉस्फोरस: DAP 50-100 kg/एकड़
• जिंक: जिंक सल्फेट 25 kg/एकड़

**4. मिट्टी संरक्षण:**
• जलाने से बचें (सूक्ष्मजीवों को नष्ट करता है)
• फसल चक्र: दलहन → अनाज → तिलहन
• गीली घास (Mulching)

**लाभ:**
• उपज में 20-40% वृद्धि
• उर्वरक बचत: 30%
• ROI: ₹5-10 प्रति ₹1 निवेश

📞 मृदा स्वास्थ्य कार्ड: ग्राम कृषि अधिकारी से संपर्क करें""",
            
            "english": f"""🌍 **Soil Health Management**

**Soil Testing:**
• Where: District Agriculture Department lab
• Cost: Free or ₹20-50
• Website: soilhealth.dac.gov.in

**Soil Improvement Strategies:**

**1. Add Organic Matter:**
• FYM: 5-10 tons/acre (₹2,000-4,000)
• Vermicompost: 2-3 tons/acre (₹8,000-12,000)
• Green manure: Dhaincha, sunhemp (₹500-800)

**2. pH Management:**
• Acidic soil (pH < 6): Lime 200-500 kg/acre
• Alkaline soil (pH > 8): Gypsum 200-400 kg/acre

**3. Nutrients:**
• Nitrogen deficiency: Urea 50 kg/acre
• Phosphorus: DAP 50-100 kg/acre
• Zinc: Zinc sulfate 25 kg/acre

**4. Soil Conservation:**
• Avoid burning (destroys microbes)
• Crop rotation: Legume → Cereal → Oilseed
• Mulching

**Benefits:**
• 20-40% yield increase
• Fertilizer savings: 30%
• ROI: ₹5-10 per ₹1 invested

📞 Soil Health Card: Contact village agriculture officer"""
        }
        
        return {
            "soil_health_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 13: Crop Calendar Agent
def crop_calendar_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Provide complete crop lifecycle calendar and management schedule"""
    logger.info("\n📅 Crop Calendar Agent running...")
    
    if state.get("query_type") != "crop_calendar":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    current_season = get_current_season()
    
    prompt = f"""You are an agricultural calendar expert providing complete crop lifecycle guidance.

Farmer's Question: {user_query}
Crop: {crop if crop else "Request specific crop"}
Season: {current_season}
Location: {location.get('city', 'India')}, {location.get('state', 'India')}
Language: {language}

Provide a COMPLETE, month-by-month crop lifecycle calendar with all activities, timings, and costs.
Include land preparation, sowing, fertilization schedule, irrigation, pest management, and harvesting.
Be EXTREMELY SPECIFIC with dates, quantities, costs, and methods.
Create a practical calendar farmers can follow throughout the season.

Respond in {language} with clear month-by-month breakdown.
Maximum 400 words for complete lifecycle guidance.
"""
    
    messages = [
        SystemMessage(content="You are a crop calendar expert who provides precise, complete, month-by-month guidance for entire crop lifecycle."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "crop_calendar_info": {
                "calendar": response.content,
                "crop": crop,
                "season": current_season
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Crop calendar error: {str(e)}")
        
        fallback = {
            "hindi": f"""📅 **फसल कैलेंडर** {f"({crop})" if crop else ""}

**माह 1: भूमि तैयारी और बुवाई**
• गहरी जुताई: 2-3 बार
• गोबर की खाद: 5-8 टन/एकड़
• बुवाई: सही समय पर

**माह 2: अंकुरण और विकास**
• पहली निराई: 15-20 दिन
• पहली टॉप ड्रेसिंग: यूरिया 50 kg

**माह 3: वानस्पतिक विकास**
• दूसरी निराई
• दूसरी टॉप ड्रेसिंग
• कीट निगरानी

**माह 4: फूल आना**
• नियमित सिंचाई
• कीट/रोग नियंत्रण

**माह 5-6: परिपक्वता और कटाई**
• अंतिम सिंचाई बंद
• कटाई

**कुल लागत:** ₹12,000-18,000/एकड़
📞 1800-180-1551""",
            
            "english": f"""📅 **Crop Calendar** {f"({crop})" if crop else ""}

**Month 1: Land Prep & Sowing**
• Deep plowing: 2-3 times
• FYM: 5-8 tons/acre
• Sowing: At right time

**Month 2: Germination & Growth**
• First weeding: 15-20 days
• First top dressing: Urea 50 kg

**Month 3: Vegetative Growth**
• Second weeding
• Second top dressing
• Pest monitoring

**Month 4: Flowering**
• Regular irrigation
• Pest/disease control

**Month 5-6: Maturity & Harvest**
• Stop irrigation
• Harvesting

**Total Cost:** ₹12,000-18,000/acre
📞 1800-180-1551"""
        }
        
        return {
            "crop_calendar_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 14: Input Cost Calculator Agent
def cost_calculator_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Calculate farming input costs and ROI"""
    logger.info("\n💰 Input Cost Calculator Agent running...")
    
    if state.get("query_type") != "cost_calculation":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    prompt = f"""You are a farm economics expert providing detailed cost-benefit analysis.

Farmer's Question: {user_query}
Crop: {crop if crop else "General farming"}
Location: {location.get('city', 'India')}
Language: {language}

Provide DETAILED cost breakdown for farming inputs, expected revenue, profit calculation, and ROI analysis.
Include all costs: land prep, seeds, fertilizers, pesticides, irrigation, labor, harvesting.
Calculate expected income based on yield and market prices.
Suggest cost optimization strategies and financing options.

Be EXTREMELY SPECIFIC with all costs and calculations.
Use realistic 2024-2025 prices.

Respond in {language} with clear cost breakdown and profit analysis.
Maximum 400 words for complete financial analysis.
"""
    
    messages = [
        SystemMessage(content="You are a farm economics expert who provides detailed, accurate cost-benefit analysis to help farmers make informed financial decisions."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "cost_info": {
                "analysis": response.content,
                "crop": crop
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Cost calculator error: {str(e)}")
        
        fallback = {
            "hindi": f"""💰 **लागत विश्लेषण** {f"({crop})" if crop else ""} (प्रति एकड़)

**कुल निवेश:** ₹22,500
• भूमि तैयारी: ₹1,500
• बीज: ₹1,500
• उर्वरक: ₹5,000
• कीटनाशक: ₹2,000
• सिंचाई: ₹2,000
• श्रम: ₹9,000
• अन्य: ₹1,500

**अपेक्षित आय:** ₹30,000-50,000
**शुद्ध लाभ:** ₹7,500-27,500
**ROI:** 33-122%

**लागत बचत:**
• मृदा परीक्षण: ₹1,000 बचत
• जैविक खाद: ₹1,500 बचत
• IPM: ₹800 बचत

**वित्त:** किसान क्रेडिट कार्ड: 4% ब्याज
📞 1800-180-1551""",
            
            "english": f"""💰 **Cost Analysis** {f"({crop})" if crop else ""} (Per Acre)

**Total Investment:** ₹22,500
• Land prep: ₹1,500
• Seeds: ₹1,500
• Fertilizers: ₹5,000
• Pesticides: ₹2,000
• Irrigation: ₹2,000
• Labor: ₹9,000
• Others: ₹1,500

**Expected Income:** ₹30,000-50,000
**Net Profit:** ₹7,500-27,500
**ROI:** 33-122%

**Cost Savings:**
• Soil testing: ₹1,000 saved
• Organic manure: ₹1,500 saved
• IPM: ₹800 saved

**Financing:** Kisan Credit Card: 4% interest
📞 1800-180-1551"""
        }
        
        return {
            "cost_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 15: Emergency Response Agent
def emergency_response_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Handle urgent agricultural emergencies"""
    logger.info("\n🚨 Emergency Response Agent running...")
    
    if state.get("query_type") != "emergency_response":
        return {}
    
    language = state.get("language", "hindi")
    entities = state.get("parsed_entities", {})
    crop = entities.get("crop", "")
    symptom = entities.get("symptom", "")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    prompt = f"""You are an agricultural emergency response specialist handling URGENT farming issues.

🚨 EMERGENCY: {user_query}
Crop: {crop if crop else "Not specified"}
Symptoms: {symptom if symptom else "Not specified"}
Location: {location.get('city', 'India')}
Language: {language}

This is an EMERGENCY. Provide IMMEDIATE, ACTIONABLE response with:
1. Immediate actions (next 2-4 hours)
2. Damage control measures
3. Emergency contacts (Kisan Call Center 1800-180-1551, etc.)
4. Monitoring and follow-up steps
5. Prevention for future

Be ULTRA-SPECIFIC with immediate actionable steps.
Prioritize speed and effectiveness.

Respond in {language} with maximum urgency and clarity.
Maximum 350 words for emergency guidance.
"""
    
    messages = [
        SystemMessage(content="You are an emergency agricultural response specialist who provides IMMEDIATE, SPECIFIC, ACTIONABLE guidance for urgent crop problems."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "emergency_info": {
                "response": response.content,
                "severity": "high",
                "urgent": True
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Emergency response error: {str(e)}")
        
        fallback = {
            "hindi": f"""🚨 **आपातकालीन सहायता**

**तुरंत कार्रवाई:**
1. प्रभावित हिस्सा अलग करें
2. उपयुक्त कीटनाशक/फफूंदनाशक
3. आज शाम से पहले स्प्रे करें

**📞 तुरंत संपर्क:**
किसान कॉल सेंटर: 1800-180-1551 (24x7)
फसल बीमा: 72 घंटे में रिपोर्ट करें

**अगले 24-48 घंटे:**
हर 4-6 घंटे जांचें

⚠️ देरी न करें - हर घंटा महत्वपूर्ण है!""",
            
            "english": f"""🚨 **Emergency Help**

**Immediate Action:**
1. Isolate affected area
2. Appropriate pesticide/fungicide
3. Spray before sunset today

**📞 Contact Now:**
Kisan Call Center: 1800-180-1551 (24x7)
Crop Insurance: Report within 72 hours

**Next 24-48 Hours:**
Check every 4-6 hours

⚠️ Don't Delay - Every Hour Counts!"""
        }
        
        return {
            "emergency_info": {"fallback": True, "urgent": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent 16: Local Expert Connection Agent
def expert_connection_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Connect farmers to local agricultural experts and resources"""
    logger.info("\n👨‍🌾 Expert Connection Agent running...")
    
    if state.get("query_type") != "expert_connection":
        return {}
    
    language = state.get("language", "hindi")
    user_query = state.get("user_query", "")
    location = state.get("location", {})
    
    prompt = f"""You are a local agricultural resource connector helping farmers access expert help.

Farmer's Request: {user_query}
Location: {location.get('city', 'India')}, {location.get('state', 'India')}, {location.get('district', '')}
Language: {language}

Provide COMPREHENSIVE local expert connection information including:
1. Kisan Call Center (1800-180-1551, 24x7)
2. District Agriculture Office contacts
3. Krishi Vigyan Kendra (KVK) - how to find nearest via kvk.icar.gov.in
4. Village Agriculture Officer
5. Digital resources (mKisan app, Kisan Suvidha app)
6. Market support (eNAM: 1800-270-0224)
7. How to get best help (prepare photos, documents, etc.)

Be SPECIFIC with contact numbers and steps to reach experts.

Respond in {language} with clear organization.
Maximum 350 words for comprehensive expert connection guide.
"""
    
    messages = [
        SystemMessage(content="You are a local agricultural resource expert who connects farmers to the right agricultural experts and support systems."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "expert_contact_info": {
                "resources": response.content,
                "location": location.get('district', location.get('city', 'India'))
            },
            "recommendations": [response.content]
        }
    except Exception as e:
        logger.error(f"Expert connection error: {str(e)}")
        
        fallback = {
            "hindi": f"""👨‍🌾 **कृषि विशेषज्ञ संपर्क**

**📞 तत्काल सहायता (24x7):**
किसान कॉल सेंटर: 1800-180-1551

**🏛️ सरकारी कार्यालय:**
• जिला कृषि कार्यालय
• कृषि विज्ञान केंद्र (KVK): kvk.icar.gov.in
• ग्राम कृषि अधिकारी

**📱 ऐप्स:**
• mKisan, किसान सुविधा, मेघदूत
• eNAM (मंडी): 1800-270-0224

**💡 सर्वश्रेष्ठ मदद:**
1. तस्वीरें लें
2. जमीन के कागजात रखें
3. पहले हेल्पलाइन कॉल करें
4. KVK विजिट करें

Google: "{location.get('district', 'आपका जिला')} KVK contact"
या farmer.gov.in""",
            
            "english": f"""👨‍🌾 **Agricultural Expert Contacts**

**📞 Immediate Help (24x7):**
Kisan Call Center: 1800-180-1551

**🏛️ Government Offices:**
• District Agriculture Office
• Krishi Vigyan Kendra (KVK): kvk.icar.gov.in
• Village Agriculture Officer

**📱 Apps:**
• mKisan, Kisan Suvidha, Meghdoot
• eNAM (Market): 1800-270-0224

**💡 Best Help:**
1. Take photos
2. Keep land documents
3. Call helpline first
4. Visit KVK

Google: "{location.get('district', 'your district')} KVK contact"
Or farmer.gov.in"""
        }
        
        return {
            "expert_contact_info": {"fallback": True},
            "recommendations": [fallback.get(language, fallback["hindi"])]
        }

# Agent: Image Retrieval Agent
def image_retrieval_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Retrieve relevant images based on image queries from previous agents"""
    logger.info("\n🖼️ Image Retrieval Agent running...")
    
    requires_images = state.get("requires_images", False)
    image_queries = state.get("image_queries", [])
    image_context = state.get("image_context", "")
    
    # Skip if images not required
    if not requires_images or not image_queries:
        logger.info("Images not required, skipping image retrieval")
        return {}
    
    # Import image search service
    from image_search_service import image_search_service
    
    all_images = []
    
    try:
        # Search images for each query
        for query in image_queries:
            logger.info(f"Searching images for: {query}")
            
            # Use specialized search methods based on context
            if image_context == "fertilizer_products":
                images = image_search_service.search_fertilizer_images(query.split()[0])
            elif image_context == "pesticide_products":
                images = image_search_service.search_pesticide_images(query.split()[0])
            elif image_context == "disease_symptoms":
                images = image_search_service.search_images(query, num_images=2)
            elif image_context == "crop_varieties":
                images = image_search_service.search_crop_images(query.split()[0])
            elif image_context == "equipment":
                images = image_search_service.search_equipment_images(query)
            elif image_context == "soil_testing":
                images = image_search_service.search_soil_images()
            else:
                # Generic search
                images = image_search_service.search_images(query, num_images=2)
            
            all_images.extend(images)
            
            # Limit total images
            if len(all_images) >= 4:
                break
        
        # Validate and filter images
        validated_images = image_search_service.filter_and_validate_images(all_images)
        
        logger.info(f"Retrieved {len(validated_images)} validated images")
        
        return {
            "image_urls": validated_images[:4]  # Maximum 4 images
        }
        
    except Exception as e:
        logger.error(f"Image retrieval error: {str(e)}")
        # Return empty images on error - don't break the flow
        return {
            "image_urls": []
        }

# Continue with remaining agents in next part...
def response_generation_agent(state: KisaanAgentState) -> KisaanAgentState:
    """Generate final consolidated response - simplified to preserve agent responses"""
    logger.info("\n📝 Response Generation Agent running...")
    
    query_type = state.get("query_type", "")
    language = state.get("language", "hindi")
    recommendations = state.get("recommendations", [])
    pest_disease_info = state.get("pest_disease_info", {})
    
    # Check if camera action is needed
    if pest_disease_info.get("action") == "open_camera":
        return {
            "final_response": pest_disease_info.get("prompt", ""),
            "requires_camera": True
        }
    
    # If we have recommendations from specialized agents, use them DIRECTLY
    # This preserves the accuracy and completeness of agent responses
    if recommendations:
        # Use the first (and typically only) recommendation
        final_response = recommendations[0]
        
        logger.info(f"✅ Final response ready ({len(final_response)} chars)")
        
        return {"final_response": final_response}
    
    # Fallback only if no recommendations were generated
    logger.warning("No recommendations generated by any agent")
    
    fallback_messages = {
        "hindi": "क्षमा करें, मुझे आपके प्रश्न का उत्तर देने में कठिनाई हो रही है। कृपया अपना सवाल फिर से पूछें या अधिक जानकारी दें।",
        "english": "Sorry, I'm having difficulty answering your question. Please rephrase your question or provide more details."
    }
    
    return {"final_response": fallback_messages.get(language, fallback_messages["hindi"])}


# Build LangGraph flow
def build_kisaan_graph():
    """Build the multi-agent workflow graph"""
    builder = StateGraph(KisaanAgentState)
    
    # Add all agents as nodes
    builder.add_node("query_understanding", query_understanding_agent)
    builder.add_node("crop_selection", crop_selection_agent)
    builder.add_node("crop_disease", crop_disease_agent)
    builder.add_node("weather_advisory", weather_advisory_agent)
    builder.add_node("soil_management", soil_management_agent)
    builder.add_node("general_advisory", general_advisory_agent)
    builder.add_node("market_price", market_price_agent)
    builder.add_node("government_schemes", government_schemes_agent)
    
    # NEW AGENTS - Fertilizer & Pesticide Management
    builder.add_node("fertilizer_recommendation", fertilizer_recommendation_agent)
    builder.add_node("pesticide_recommendation", pesticide_recommendation_agent)
    builder.add_node("application_guide", application_guide_agent)
    builder.add_node("fertilizer_schedule", fertilizer_schedule_planner_agent)
    
    # NEW AGENTS - Resource Management
    builder.add_node("irrigation_management", irrigation_management_agent)
    builder.add_node("soil_health", soil_health_agent)
    builder.add_node("crop_calendar", crop_calendar_agent)
    
    # NEW AGENTS - Financial & Support
    builder.add_node("cost_calculation", cost_calculator_agent)
    builder.add_node("emergency_response", emergency_response_agent)
    builder.add_node("expert_connection", expert_connection_agent)
    
    # Image Retrieval Agent
    builder.add_node("image_retrieval", image_retrieval_agent)
    
    builder.add_node("response_generation", response_generation_agent)
    
    # Define workflow
    builder.set_entry_point("query_understanding")
    
    # Multi-agent routing based on query type
    def route_by_query_type(state):
        query_type = state.get("query_type", "general_advisory")
        
        # Primary routing based on query type
        if query_type == "crop_selection":
            return "crop_selection"
        elif query_type == "crop_cultivation":
            return "general_advisory"
        elif query_type == "crop_disease":
            return "crop_disease"
        elif query_type == "weather_advisory":
            return "weather_advisory"
        elif query_type == "market_price":
            return "market_price"
        elif query_type == "soil_management":
            return "soil_management"
        elif query_type == "irrigation":
            return "general_advisory"
        elif query_type == "government_schemes":
            return "government_schemes"
        # NEW ROUTING - Fertilizer & Pesticide
        elif query_type == "fertilizer_recommendation":
            return "fertilizer_recommendation"
        elif query_type == "pesticide_recommendation":
            return "pesticide_recommendation"
        elif query_type == "application_guide":
            return "application_guide"
        elif query_type == "fertilizer_schedule":
            return "fertilizer_schedule"
        # NEW ROUTING - Resource Management
        elif query_type == "irrigation_management":
            return "irrigation_management"
        elif query_type == "soil_health":
            return "soil_health"
        elif query_type == "crop_calendar":
            return "crop_calendar"
        # NEW ROUTING - Financial & Support
        elif query_type == "cost_calculation":
            return "cost_calculation"
        elif query_type == "emergency_response":
            return "emergency_response"
        elif query_type == "expert_connection":
            return "expert_connection"
        else:
            return "general_advisory"
    
    builder.add_conditional_edges(
        "query_understanding",
        route_by_query_type,
        {
            "crop_selection": "crop_selection",
            "crop_disease": "crop_disease",
            "weather_advisory": "weather_advisory",
            "soil_management": "soil_management",
            "general_advisory": "general_advisory",
            "market_price": "market_price",
            "government_schemes": "government_schemes",
            # NEW ROUTES - Fertilizer & Pesticide
            "fertilizer_recommendation": "fertilizer_recommendation",
            "pesticide_recommendation": "pesticide_recommendation",
            "application_guide": "application_guide",
            "fertilizer_schedule": "fertilizer_schedule",
            # NEW ROUTES - Resource Management
            "irrigation_management": "irrigation_management",
            "soil_health": "soil_health",
            "crop_calendar": "crop_calendar",
            # NEW ROUTES - Financial & Support
            "cost_calculation": "cost_calculation",
            "emergency_response": "emergency_response",
            "expert_connection": "expert_connection"
        }
    )
    
    # All specialized agents flow to conditional image routing
    # Agents that may need images go through conditional edge
    def route_for_images(state):
        """Route to image retrieval if requires_images is True, otherwise to response generation"""
        if state.get("requires_images", False):
            return "image_retrieval"
        return "response_generation"
    
    # Agents that support images use conditional routing
    builder.add_conditional_edges(
        "fertilizer_recommendation",
        route_for_images,
        {
            "image_retrieval": "image_retrieval",
            "response_generation": "response_generation"
        }
    )
    builder.add_conditional_edges(
        "pesticide_recommendation",
        route_for_images,
        {
            "image_retrieval": "image_retrieval",
            "response_generation": "response_generation"
        }
    )
    builder.add_conditional_edges(
        "crop_disease",
        route_for_images,
        {
            "image_retrieval": "image_retrieval",
            "response_generation": "response_generation"
        }
    )
    
    # Other agents go directly to response generation
    builder.add_edge("crop_selection", "response_generation")
    builder.add_edge("weather_advisory", "response_generation")
    builder.add_edge("soil_management", "response_generation")
    builder.add_edge("general_advisory", "response_generation")
    builder.add_edge("market_price", "response_generation")
    builder.add_edge("government_schemes", "response_generation")
    
    # NEW EDGES - Application Guide & Schedule
    builder.add_edge("application_guide", "response_generation")
    builder.add_edge("fertilizer_schedule", "response_generation")
    
    # NEW EDGES - Resource Management
    builder.add_edge("irrigation_management", "response_generation")
    builder.add_edge("soil_health", "response_generation")
    builder.add_edge("crop_calendar", "response_generation")
    
    # NEW EDGES - Financial & Support
    builder.add_edge("cost_calculation", "response_generation")
    builder.add_edge("emergency_response", "response_generation")
    builder.add_edge("expert_connection", "response_generation")
    
    # Image retrieval always flows to response generation
    builder.add_edge("image_retrieval", "response_generation")
    
    builder.add_edge("response_generation", END)
    
    return builder.compile()