from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uuid
from datetime import datetime
from config import Config
from db import get_db_connection
from models import (
    VoiceQueryRequest, VoiceResponse, LanguageSelectionRequest,
    FarmerProfile, CropInformation, SessionData
)
from voice_service import voice_service
from realtime_voice_service import realtime_voice_service
from langgraph_kisaan_agents import build_kisaan_graph
from crop_disease_camera import CropDiseaseCamera
from typing import Dict
import re
import json
import base64

app = FastAPI(title="Kisaan Voice Assistant API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory session storage (use Redis in production)
active_sessions: Dict[str, SessionData] = {}

# Initialize camera-based disease detector
disease_camera = CropDiseaseCamera()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[Config.FRONTEND_ORIGIN, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "नमस्ते! Welcome to Kisaan Voice Assistant API 🌾"}

@app.post("/voice/start-session")
async def start_voice_session():
    """
    Start a new voice session with greeting
    Returns initial greeting audio
    """
    session_id = str(uuid.uuid4())
    
    # Create new session
    active_sessions[session_id] = SessionData(
        session_id=session_id,
        language=Config.DEFAULT_LANGUAGE,
        conversation_history=[],
        last_activity=datetime.now().isoformat()
    )
    
    # Generate shorter greeting for testing
    greeting_text = voice_service.get_greeting_message("hindi")
    greeting_audio = await voice_service.text_to_speech(greeting_text, "hindi")
    
    logger.info(f"Started new session: {session_id}")
    logger.info(f"Greeting audio size: {len(greeting_audio)} chars")
    
    return JSONResponse(content={
        "session_id": session_id,
        "text": greeting_text,
        "audio": greeting_audio,
        "language": "hindi",
        "status": "awaiting_language_selection"
    })

@app.post("/voice/select-language")
async def select_language(request: LanguageSelectionRequest):
    """
    Process language selection from user
    """
    session_id = request.session_id
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    session.language = request.language
    session.last_activity = datetime.now().isoformat()
    
    # Confirmation message in selected language
    confirmation_messages = {
        'hindi': "अच्छा! अब आप मुझसे खेती के बारे में पूछ सकते हैं।",
        'english': "Great! You can now ask me about farming.",
        'punjabi': "ਬਹੁਤ ਵਧੀਆ! ਹੁਣ ਤੁਸੀਂ ਮੈਨੂੰ ਖੇਤੀ ਬਾਰੇ ਪੁੱਛ ਸਕਦੇ ਹੋ।",
        'marathi': "छान! आता तुम्ही मला शेतीबद्दल विचारू शकता.",
        'gujarati': "સરસ! તમે મને ખેતી વિશે પૂછી શકો છો.",
        'tamil': "சிறப்பு! இப்போது நீங்கள் விவசாயம் பற்றி கேட்கலாம்.",
        'telugu': "మంచిది! మీరు వ్యవసాయం గురించి అడగవచ్చు.",
        'kannada': "ಚೆನ್ನಾಗಿದೆ! ನೀವು ಕೃಷಿಯ ಬಗ್ಗೆ ಕೇಳಬಹುದು.",
        'bengali': "ভালো! এখন আপনি কৃষি সম্পর্কে জিজ্ঞাসা করতে পারেন।"
    }
    
    confirmation_text = confirmation_messages.get(request.language, confirmation_messages['hindi'])
    confirmation_audio = await voice_service.text_to_speech(confirmation_text, request.language)
    
    logger.info(f"Language selected: {request.language}, audio size: {len(confirmation_audio)} chars")
    
    return JSONResponse(content={
        "session_id": session_id,
        "text": confirmation_text,
        "audio": confirmation_audio,
        "language": request.language,
        "status": "ready"
    })

@app.post("/voice/detect-language")
async def detect_language(request: VoiceQueryRequest):
    """
    Detect language from user's voice input
    """
    session_id = request.session_id
    
    if not session_id or session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    # Transcribe audio to text (using default language for transcription)
    transcribed_text = await voice_service.transcribe_audio(
        request.audio_base64, 
        "hindi"  # Use Hindi as base for transcription
    )
    
    logger.info(f"Language detection - Transcribed: {transcribed_text}")
    
    if not transcribed_text:
        # No speech detected
        retry_message = "कृपया फिर से अपनी भाषा बोलें। / Please speak your language again."
        retry_audio = await voice_service.text_to_speech(retry_message, "hindi")
        
        return JSONResponse(content={
            "language_detected": False,
            "text": retry_message,
            "audio": retry_audio,
            "session_id": session_id
        })
    
    # Detect language from transcribed text
    detected_lang = voice_service.detect_language_from_speech(transcribed_text)
    
    if detected_lang:
        # Language detected successfully
        session.language = detected_lang
        session.last_activity = datetime.now().isoformat()
        
        confirmation_messages = {
            'hindi': "अच्छा! अब आप मुझसे खेती के बारे में पूछ सकते हैं।",
            'english': "Great! You can now ask me about farming.",
            'punjabi': "ਬਹੁਤ ਵਧੀਆ! ਹੁਣ ਤੁਸੀਂ ਮੈਨੂੰ ਖੇਤੀ ਬਾਰੇ ਪੁੱਛ ਸਕਦੇ ਹੋ।",
            'marathi': "छान! आता तुम्ही मला शेतीबद्दल विचारू शकता.",
            'gujarati': "સરસ! તમે મને ખેતી વિશે પૂછી શકો છો.",
            'tamil': "சிறப்பு! இப்போது நீங்கள் விவசாயம் பற்றி கேட்கலாம்.",
            'telugu': "మంచిది! మీరు వ్యవసాయం గురించి అడగవచ్చు.",
            'kannada': "ಚೆನ್ನಾಗಿದೆ! ನೀವು ಕೃಷಿಯ ಬಗ್ಗೆ ಕೇಳಬಹುದು.",
            'bengali': "ভালো! এখন আপনি কৃষি সম্পর্কে জিজ্ঞাসা করতে পারেন।"
        }
        
        confirmation_text = confirmation_messages.get(detected_lang, confirmation_messages['hindi'])
        confirmation_audio = await voice_service.text_to_speech(confirmation_text, detected_lang)
        
        logger.info(f"✅ Language detected: {detected_lang}")
        
        return JSONResponse(content={
            "language_detected": True,
            "language": detected_lang,
            "text": confirmation_text,
            "audio": confirmation_audio,
            "session_id": session_id
        })
    else:
        # Language not detected, ask to retry
        retry_message = "कृपया फिर से अपनी भाषा बोलें। / Please speak your language again."
        retry_audio = await voice_service.text_to_speech(retry_message, "hindi")
        
        logger.info(f"❌ Language not detected from: {transcribed_text}")
        
        return JSONResponse(content={
            "language_detected": False,
            "text": retry_message,
            "audio": retry_audio,
            "session_id": session_id
        })


@app.post("/voice/query", response_model=VoiceResponse)
async def process_voice_query(request: VoiceQueryRequest):
    """
    Main endpoint for processing voice queries from farmers
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get or create session
    if session_id not in active_sessions:
        active_sessions[session_id] = SessionData(
            session_id=session_id,
            language=request.language or Config.DEFAULT_LANGUAGE,
            conversation_history=[],
            last_activity=datetime.now().isoformat()
        )
    
    session = active_sessions[session_id]
    
    # Transcribe audio to text
    transcribed_text = await voice_service.transcribe_audio(
        request.audio_base64, 
        request.language or session.language
    )
    
    logger.info(f"Transcribed: {transcribed_text}")
    
    if not transcribed_text:
        error_msg = "मुझे आपकी आवाज़ सुनाई नहीं दी। कृपया फिर से बोलें।" if session.language == "hindi" else "I couldn't hear you. Please speak again."
        error_audio = await voice_service.text_to_speech(error_msg, session.language)
        return VoiceResponse(
            text_response=error_msg,
            audio_base64=error_audio,
            language=session.language,
            session_id=session_id,
            user_text=""
        )
    
    # Detect language selection
    detected_lang = voice_service.detect_language_from_speech(transcribed_text)
    if detected_lang and session.language == Config.DEFAULT_LANGUAGE:
        session.language = detected_lang
        confirmation_messages = {
            'hindi': "बहुत अच्छा! अब आप मुझसे खेती से जुड़े किसी भी सवाल के बारे में पूछ सकते हैं।",
            'english': "Great! You can now ask me any questions about farming.",
            'punjabi': "ਬਹੁਤ ਵਧੀਆ! ਤੁਸੀਂ ਹੁਣ ਮੈਨੂੰ ਖੇਤੀ ਬਾਰੇ ਕੋਈ ਵੀ ਸਵਾਲ ਪੁੱਛ ਸਕਦੇ ਹੋ।"
        }
        confirmation_text = confirmation_messages.get(detected_lang, confirmation_messages['hindi'])
        confirmation_audio = await voice_service.text_to_speech(confirmation_text, detected_lang)
        
        return VoiceResponse(
            text_response=confirmation_text,
            audio_base64=confirmation_audio,
            language=detected_lang,
            session_id=session_id
        )
    
    # Extract location from conversation if available
    location = session.location or extract_location_from_text(transcribed_text)
    if location:
        session.location = location
    
    # Build and run agent graph
    graph = build_kisaan_graph()
    
    # Prepare state for agents
    initial_state = {
        "user_query": transcribed_text,
        "language": session.language,
        "location": location or {"city": "Indore", "state": "Madhya Pradesh"},  # Default fallback
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
    
    # Run the agent workflow
    try:
        final_state = graph.invoke(initial_state)
        response_text = final_state.get("final_response", "मुझे खेद है, मैं आपकी मदद नहीं कर सका।")
        requires_camera = final_state.get("requires_camera", False)
    except Exception as e:
        logger.error(f"Agent workflow error: {str(e)}")
        response_text = "मुझे खेद है, कुछ गलत हो गया। कृपया फिर से प्रयास करें।" if session.language == "hindi" else "Sorry, something went wrong. Please try again."
        requires_camera = False
    
    # Convert response to speech
    response_audio = await voice_service.text_to_speech(response_text, session.language)
    
    # Update conversation history
    session.conversation_history.append({
        "user": transcribed_text,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat(),
        "requires_camera": requires_camera
    })
    session.last_activity = datetime.now().isoformat()
    
    return VoiceResponse(
        text_response=response_text,
        audio_base64=response_audio,
        language=session.language,
        session_id=session_id,
        user_text=transcribed_text,
        requires_camera=requires_camera
    )
    
    # Update conversation history
    session.conversation_history.append({
        "user": transcribed_text,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat()
    })
    session.last_activity = datetime.now().isoformat()
    
    return VoiceResponse(
        text_response=response_text,
        audio_base64=response_audio,
        language=session.language,
        session_id=session_id,
        user_text=transcribed_text  # Add user's transcribed text
    )

def extract_location_from_text(text: str) -> Dict:
    """
    Extract location information from user text
    Simple pattern matching for Indian locations
    """
    # Common Indian cities and states
    cities = ['indore', 'bhopal', 'mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 
              'hyderabad', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'indore']
    states = ['madhya pradesh', 'maharashtra', 'delhi', 'karnataka', 'tamil nadu', 
              'west bengal', 'telangana', 'gujarat', 'rajasthan', 'uttar pradesh']
    
    text_lower = text.lower()
    
    location = {}
    
    for city in cities:
        if city in text_lower:
            location['city'] = city.title()
            break
    
    for state in states:
        if state in text_lower:
            location['state'] = state.title()
            break
    
    return location if location else None

@app.post("/farmer/register")
async def register_farmer(farmer: FarmerProfile):
    """Register a new farmer profile"""
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO farmers (name, phone_number, village, district, state, 
                                land_size_acres, soil_type, irrigation_type, primary_crops)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING farmer_id
        """, (
            farmer.name, farmer.phone_number, farmer.village, farmer.district,
            farmer.state, farmer.land_size_acres, farmer.soil_type,
            farmer.irrigation_type, farmer.primary_crops
        ))
        
        farmer_id = cur.fetchone()[0]
        conn.commit()
        
        return JSONResponse(content={
            "message": "किसान पंजीकरण सफल रहा!" if farmer.primary_crops else "Farmer registered successfully!",
            "farmer_id": farmer_id
        })
    
    except Exception as e:
        logger.error(f"Farmer registration error: {str(e)}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.post("/crop/register")
async def register_crop(crop: CropInformation):
    """Register crop information for a farmer"""
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO crops (farmer_id, crop_name, crop_variety, sowing_date,
                              expected_harvest_date, land_area_acres, current_stage)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING crop_id
        """, (
            crop.farmer_id, crop.crop_name, crop.crop_variety, crop.sowing_date,
            crop.expected_harvest_date, crop.land_area_acres, crop.current_stage
        ))
        
        crop_id = cur.fetchone()[0]
        conn.commit()
        
        return JSONResponse(content={
            "message": "फसल की जानकारी सहेजी गई!",
            "crop_id": crop_id
        })
    
    except Exception as e:
        logger.error(f"Crop registration error: {str(e)}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Crop registration failed")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    return JSONResponse(content={
        "session_id": session_id,
        "language": session.language,
        "conversation_history": session.conversation_history
    })

@app.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a voice session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return JSONResponse(content={"message": "Session ended successfully"})
    
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/camera/check-leaf")
async def check_leaf_presence(request: dict):
    """
    Check if a plant leaf is present in the captured image
    
    Request body:
        - image_base64: Base64 encoded image from camera
        - language: Response language
    """
    try:
        image_base64 = request.get("image_base64", "")
        language = request.get("language", "hindi")
        
        if not image_base64:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Check for leaf presence
        result = disease_camera.check_if_leaf_present(image_base64, language)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Leaf check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/camera/diagnose-disease")
async def diagnose_crop_disease(request: dict):
    """
    Diagnose crop disease from captured leaf image
    
    Request body:
        - session_id: Current session ID
        - image_base64: Base64 encoded image from camera
        - language: Response language
    """
    try:
        session_id = request.get("session_id")
        image_base64 = request.get("image_base64", "")
        language = request.get("language", "hindi")
        
        if not session_id or session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not image_base64:
            raise HTTPException(status_code=400, detail="No image provided")
        
        session = active_sessions[session_id]
        
        # Diagnose disease from image
        diagnosis_result = disease_camera.diagnose_from_base64(image_base64, language)
        
        if not diagnosis_result["success"]:
            error_msg = diagnosis_result.get("diagnosis", "निदान में त्रुटि हुई")
            error_audio = await voice_service.text_to_speech(error_msg, language)
            return JSONResponse(content={
                "success": False,
                "text": error_msg,
                "audio": error_audio
            })
        
        # Convert diagnosis to speech
        diagnosis_text = diagnosis_result["diagnosis"]
        diagnosis_audio = await voice_service.text_to_speech(diagnosis_text, language)
        
        # Update session history
        session.conversation_history.append({
            "user": "📷 Leaf image captured",
            "assistant": diagnosis_text,
            "timestamp": datetime.now().isoformat(),
            "type": "camera_diagnosis"
        })
        session.last_activity = datetime.now().isoformat()
        
        return JSONResponse(content={
            "success": True,
            "text": diagnosis_text,
            "audio": diagnosis_audio,
            "language": language,
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Disease diagnosis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Kisaan Voice Assistant"}


@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice interaction
    
    Protocol:
    - Client connects and sends: {"type": "start", "language": "hindi", "session_id": "..."}
    - Client streams audio: {"type": "audio", "data": "base64_encoded_pcm"}
    - Server sends partial transcripts: {"type": "transcript", "text": "...", "is_final": false}
    - Server sends final transcripts: {"type": "transcript", "text": "...", "is_final": true}
    - Server sends AI response: {"type": "response", "text": "...", "audio": "base64"}
    - Client sends: {"type": "stop"} to end
    """
    await websocket.accept()
    logger.info("🔌 WebSocket connection established")
    
    session_id = None
    language = "hindi"
    graph = build_kisaan_graph()
    
    async def on_transcript(text: str, is_final: bool):
        """Handle transcript from AssemblyAI"""
        try:
            # Send transcript to client
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": is_final
            })
            
            # If final transcript, process with LangGraph
            if is_final and text.strip():
                logger.info(f"Processing final transcript: {text}")
                
                # Get session
                session = active_sessions.get(session_id)
                if not session:
                    logger.warning(f"Session {session_id} not found")
                    return
                
                # Detect language switch
                detected_lang = voice_service.detect_language_from_speech(text)
                if detected_lang:
                    language = detected_lang
                    session.language = language
                    logger.info(f"Language switched to: {language}")
                
                # Create state for LangGraph
                state = {
                    "user_query": text,
                    "language": language,
                    "location": session.farmer_profile.location if session.farmer_profile else {},
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
                    "requires_images": False,
                    "image_queries": [],
                    "image_urls": [],
                    "image_context": "",
                    "layout_type": "chat-only"
                }
                
                # Run through agent graph
                logger.info("Running query through agent graph...")
                result = await graph.ainvoke(state)
                
                # Get response
                response_text = result.get("final_response", "")
                requires_camera = result.get("requires_camera", False)
                image_urls = result.get("image_urls", [])
                requires_images = result.get("requires_images", False)
                
                logger.info(f"Agent response: {response_text[:100]}...")
                
                # Update session history
                session.conversation_history.append({
                    "user": text,
                    "assistant": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "query_type": result.get("query_type", "unknown")
                })
                session.last_activity = datetime.now().isoformat()
                
                # Convert response to speech
                response_audio = await voice_service.text_to_speech(response_text, language)
                
                # Send response to client
                await websocket.send_json({
                    "type": "response",
                    "text": response_text,
                    "audio": response_audio,
                    "requires_camera": requires_camera,
                    "requires_images": requires_images,
                    "image_urls": image_urls,
                    "language": language
                })
                
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
    
    async def on_error(error_msg: str):
        """Handle transcription errors"""
        logger.error(f"Transcription error: {error_msg}")
        await websocket.send_json({
            "type": "error",
            "message": error_msg
        })
    
    try:
        # Set callbacks for realtime service
        realtime_voice_service.set_callbacks(
            on_transcript=on_transcript,
            on_error=on_error
        )
        
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_json()
                msg_type = message.get("type")
                
                if msg_type == "start":
                    # Start new session
                    session_id = message.get("session_id") or str(uuid.uuid4())
                    language = message.get("language", "hindi")
                    
                    # Create or get session
                    if session_id not in active_sessions:
                        active_sessions[session_id] = SessionData(
                            session_id=session_id,
                            language=language,
                            conversation_history=[],
                            last_activity=datetime.now().isoformat()
                        )
                    
                    # Set language and start transcription
                    realtime_voice_service.set_language(language)
                    await realtime_voice_service.start()
                    
                    logger.info(f"Started real-time session: {session_id} ({language})")
                    
                    await websocket.send_json({
                        "type": "started",
                        "session_id": session_id,
                        "language": language
                    })
                
                elif msg_type == "audio":
                    # Receive audio data and stream to AssemblyAI
                    audio_base64 = message.get("data")
                    if audio_base64:
                        # Decode base64 audio
                        audio_bytes = base64.b64decode(audio_base64)
                        # Send to AssemblyAI
                        await realtime_voice_service.send_audio(audio_bytes)
                
                elif msg_type == "stop":
                    # Stop transcription
                    await realtime_voice_service.stop()
                    logger.info("Stopped real-time transcription")
                    
                    await websocket.send_json({
                        "type": "stopped"
                    })
                    break
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    finally:
        # Clean up
        await realtime_voice_service.stop()
        logger.info("🔌 WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)