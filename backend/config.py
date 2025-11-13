import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # postgresql or sqlite
    DB_NAME = os.getenv("DB_NAME", "kisaan_assist")
    DB_USER = os.getenv("DB_USER", "dhruv")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    
    # SQLite Configuration (for testing)
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "kisaan_assist.db")
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
    
    # Frontend Configuration
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")  # Updated for modern-kiosk-ui
    
    # Voice Configuration
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Default Hindi voice
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "gtts")  # Options: "elevenlabs", "gtts", or "azure"
    
    # Language Configuration
    SUPPORTED_LANGUAGES = {
        'hindi': {'code': 'hi', 'name': 'Hindi'},
        'english': {'code': 'en', 'name': 'English'},
        'punjabi': {'code': 'pa', 'name': 'Punjabi'},
        'marathi': {'code': 'mr', 'name': 'Marathi'},
        'gujarati': {'code': 'gu', 'name': 'Gujarati'},
        'tamil': {'code': 'ta', 'name': 'Tamil'},
        'telugu': {'code': 'te', 'name': 'Telugu'},
        'kannada': {'code': 'kn', 'name': 'Kannada'},
        'bengali': {'code': 'bn', 'name': 'Bengali'}
    }
    
    DEFAULT_LANGUAGE = 'hindi'
    
    # Agriculture API Configuration
    AGMARKNET_API_BASE = "https://api.data.gov.in/resource"
    DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")