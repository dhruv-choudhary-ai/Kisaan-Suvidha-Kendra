# Kisaan Suvidha Kendra - Kiosk UI Integration Guide

## Overview
This document describes the integration between the modern-kiosk-ui frontend and the Kisaan Suvidha Kendra backend for voice-enabled agricultural assistance.

## Architecture

```
┌─────────────────────────────────────┐
│    Modern Kiosk UI (React + Vite)   │
│         Port: 3000                   │
│  - Voice Input/Output                │
│  - Avatar Display (WebRTC)           │
│  - Camera Disease Detection          │
│  - Multilingual Support              │
└──────────────┬──────────────────────┘
               │
               │ HTTP/WebSocket
               ▼
┌─────────────────────────────────────┐
│   Kisaan Backend (FastAPI)          │
│         Port: 8000                   │
│  - Voice Processing                  │
│  - LangGraph Agents                  │
│  - Disease Detection                 │
│  - Market Prices                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Avatar Service (RunPod/WebRTC)     │
│  - Real-time Avatar Animation        │
│  - Text-to-Speech                    │
└─────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.10+
- RunPod avatar service (or local alternative)

### Backend Setup

1. **Navigate to backend directory:**
```powershell
cd backend
```

2. **Install Python dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Configure environment variables (.env):**
```env
# API Keys
GEMINI_API_KEY=your_gemini_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ASSEMBLYAI_API_KEY=your_assemblyai_key
OPENWEATHER_API_KEY=your_openweather_key

# Database (SQLite by default)
DB_TYPE=sqlite
SQLITE_DB_PATH=kisaan_assist.db

# Frontend Origin
FRONTEND_ORIGIN=http://localhost:3000
```

4. **Initialize database:**
```powershell
python init_sqlite_db.py
```

5. **Start backend server:**
```powershell
python main.py
```

Backend will run on `http://localhost:8000`

### Frontend Setup

1. **Navigate to kiosk UI directory:**
```powershell
cd modern-kiosk-ui\modern-kiosk-ui
```

2. **Install dependencies:**
```powershell
pnpm install
```

3. **Configure environment (optional .env):**
```env
# If you want to override defaults
VITE_BACKEND_URL=http://localhost:8000
```

4. **Start development server:**
```powershell
pnpm dev
```

Frontend will run on `http://localhost:3000`

## Key Integration Points

### 1. API Endpoints

#### Voice Interaction
- `POST /voice/start-session` - Initialize new session with greeting
- `POST /voice/select-language` - Select user language
- `POST /voice/detect-language` - Auto-detect language from audio
- `POST /voice/query` - Send voice query and get response
- `WS /ws/voice` - WebSocket for real-time voice streaming

#### Camera/Disease Detection
- `POST /camera/check-leaf` - Verify leaf is present in image
- `POST /camera/diagnose-disease` - Diagnose crop disease from image

#### Session Management
- `GET /session/{session_id}/history` - Get conversation history
- `DELETE /session/{session_id}` - End session

### 2. Service Architecture

#### Frontend Services

**kisaanService.js**
- Main integration layer with backend
- Handles session management
- Voice query processing
- Disease diagnosis

**aiService.js**
- Maintains conversation context
- Persona detection (farmer, trader, officer, etc.)
- Integrates with kisaanService for backend calls

**api.js**
- Low-level API communication
- Avatar service integration
- HTTP client wrapper

#### Backend Agents (LangGraph)

1. **Router Agent** - Classifies query type
2. **Crop Advisory Agent** - Farming advice
3. **Market Price Agent** - Mandi bhav
4. **Weather Agent** - Weather forecasts
5. **Disease Detection Agent** - Crop diseases
6. **Government Schemes Agent** - Subsidy info
7. **Fertilizer/Pesticide Agent** - Product recommendations

### 3. Language Support

Supported languages:
- Hindi (हिंदी) - Default
- English
- Punjabi (ਪੰਜਾਬੀ)
- Marathi (मराठी)
- Gujarati (ગુજરાતી)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Kannada (ಕನ್ನಡ)
- Bengali (বাংলা)

Language detection:
- Automatic from voice input
- Manual selection via UI
- Maintained across session

### 4. Persona Detection

The system detects user type for personalized responses:

- **Farmer** - Practical farming advice, local market prices
- **Agriculture Officer** - Policy info, scheme implementation
- **Trader/Buyer** - Market trends, commodity availability
- **Student** - Agricultural research, learning material
- **General** - Basic information

## Workflow Example

### 1. User Starts Session
```javascript
// Frontend initializes session
const session = await kisaanService.initializeSession()
// Returns: { sessionId, greeting, audio, language }

// Avatar speaks greeting
await sendTextToAvatar(session.greeting)
```

### 2. User Asks Question
```javascript
// User speaks: "Gehu ki mandi bhav kya hai?"
const response = await kisaanService.sendTextQuery(userText)
// Backend processes through LangGraph agents
// Returns: { response, audio, requiresCamera }

// Display response and play audio
conversationHistory.push(response)
await sendTextToAvatar(response.response)
```

### 3. Disease Detection (if needed)
```javascript
// Backend response includes requiresCamera: true
if (response.requiresCamera) {
  // Capture image from camera
  const imageBase64 = await captureCamera()
  
  // Check for leaf
  const leafCheck = await kisaanService.checkLeaf(imageBase64)
  
  if (leafCheck.hasLeaf) {
    // Diagnose disease
    const diagnosis = await kisaanService.diagnoseCropDisease(imageBase64)
    // Returns: { success, diagnosis, audio }
    
    // Show diagnosis
    await sendTextToAvatar(diagnosis.diagnosis)
  }
}
```

## Development Tips

### Running Both Services Together

**Terminal 1 - Backend:**
```powershell
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd modern-kiosk-ui\modern-kiosk-ui
pnpm dev
```

### Testing API Endpoints

```powershell
# Test health
curl http://localhost:8000/health

# Test session start
curl -X POST http://localhost:8000/voice/start-session

# Test backend with frontend
# Open browser: http://localhost:3000
```

### Common Issues

**CORS Errors:**
- Check `FRONTEND_ORIGIN` in backend config.py
- Should be `http://localhost:3000`

**Session Not Found:**
- Ensure backend session is initialized
- Check sessionId is passed correctly

**Avatar Not Speaking:**
- Verify RunPod service is running
- Check WebRTC connection in browser console
- Ensure `/offer` endpoint is accessible

**Language Detection Fails:**
- Check audio format (base64 encoded)
- Verify language code matches backend list
- Test with known language samples

## Future Enhancements

### Planned Features
- [ ] WebSocket streaming for real-time transcription
- [ ] Offline mode with cached responses
- [ ] Video recording for detailed diagnosis
- [ ] Multi-crop tracking per session
- [ ] SMS/WhatsApp integration
- [ ] Print receipt functionality

### Performance Optimizations
- [ ] Response caching for common queries
- [ ] Audio compression
- [ ] Image preprocessing on client
- [ ] Session persistence to database
- [ ] Load balancing for multiple kiosks

## API Reference

### Voice Query Request
```json
{
  "session_id": "session_uuid",
  "audio_base64": "base64_encoded_audio",
  "language": "hindi"
}
```

### Voice Query Response
```json
{
  "text_response": "गेहूं का मंडी भाव ₹2500 प्रति क्विंटल है",
  "audio_base64": "base64_encoded_audio",
  "language": "hindi",
  "session_id": "session_uuid",
  "user_text": "Gehu ki mandi bhav kya hai?",
  "requires_camera": false
}
```

### Disease Diagnosis Response
```json
{
  "success": true,
  "text": "आपकी फसल में ब्लास्ट रोग है। उपचार...",
  "audio": "base64_encoded_audio",
  "language": "hindi"
}
```

## Troubleshooting

### Enable Debug Logging

**Backend:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// In browser console
localStorage.setItem('debug', 'kisaan:*')
```

### Check Service Health

```powershell
# Backend health
curl http://localhost:8000/health

# Frontend (browser)
fetch('http://localhost:3000/health')
```

## Contributing

When making changes:
1. Update both frontend and backend in sync
2. Test voice flow end-to-end
3. Verify language detection works
4. Check camera integration
5. Update this documentation

## License
Part of Kisaan Suvidha Kendra project

## Support
For issues or questions, contact the development team.
