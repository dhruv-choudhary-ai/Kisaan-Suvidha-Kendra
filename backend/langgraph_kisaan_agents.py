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
    query_type: str  # crop_selection, crop_cultivation, crop_disease, weather_advisory, market_price, soil_management, irrigation, government_schemes, general_advisory
    parsed_entities: Dict[str, Any]
    crop_info: List[Dict]
    weather_data: Dict
    market_data: List[Dict]
    government_schemes: List[Dict]
    pest_disease_info: Dict
    recommendations: List[str]
    final_response: str
    requires_camera: bool  # New field for camera trigger
    seasonal_info: Dict[str, Any]  # Current season and suitable crops
    agent_flow: List[str]  # Track which agents to use for multi-routing

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
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
- soil_management: soil testing, fertilizer, soil health, nutrients
- irrigation: watering, drip irrigation, water management
- government_schemes: ANY mention of schemes, subsidies, loans, PM-Kisan, insurance, credit card, government support, योजना
- general_advisory: other farming questions

JSON format:
{{
    "query_type": "category_name",
    "entities": {{
        "crop": "crop name if mentioned or empty string",
        "symptom": "symptoms if mentioned or empty string",
        "location": "location if mentioned or empty string"
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

# Agent 6: Response Generation Agent - IMPROVED
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
            "government_schemes": "government_schemes"
        }
    )
    
    # All specialized agents flow to response generation
    builder.add_edge("crop_selection", "response_generation")
    builder.add_edge("crop_disease", "response_generation")
    builder.add_edge("weather_advisory", "response_generation")
    builder.add_edge("soil_management", "response_generation")
    builder.add_edge("general_advisory", "response_generation")
    builder.add_edge("market_price", "response_generation")
    builder.add_edge("government_schemes", "response_generation")
    builder.add_edge("response_generation", END)
    
    return builder.compile()