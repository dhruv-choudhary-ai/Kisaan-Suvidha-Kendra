# Kisaan Suvidha Kendra - Setup Instructions

## Environment Setup

### Backend Setup

1. **Copy the environment template:**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Add your API keys to `.env`:**
   - `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - `ELEVENLABS_API_KEY`: Get from [ElevenLabs](https://elevenlabs.io/)
   - `ASSEMBLYAI_API_KEY`: Get from [AssemblyAI](https://www.assemblyai.com/)
   - `OPENWEATHER_API_KEY`: Get from [OpenWeather](https://openweathermap.org/api)
   - `DATA_GOV_API_KEY`: Get from [Data.gov.in](https://data.gov.in/)
   - `AZURE_SPEECH_KEY`: Get from [Azure Portal](https://portal.azure.com/)

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend:**
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   pnpm install
   ```

2. **Run the development server:**
   ```bash
   pnpm dev
   ```

## Important Notes

⚠️ **Never commit your `.env` file to Git!** 

The `.env` file contains sensitive API keys and should remain private. Always use `.env.example` as a template.

## Features

- 🌾 Multi-agent agricultural assistant
- 🎤 Voice interaction in Hindi and English
- 📊 Real-time weather and market price data
- 🏛️ Government schemes information
- 🌱 Crop selection and cultivation advice
- 💬 Markdown-formatted responses

## Tech Stack

**Backend:**
- FastAPI
- LangGraph
- Google Gemini AI
- Azure Speech Services
- AssemblyAI

**Frontend:**
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
