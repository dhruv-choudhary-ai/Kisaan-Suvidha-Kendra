"""
Centralized error handling for Kisaan Voice Assistant
"""
import logging
from functools import wraps
from fastapi import HTTPException
from typing import Callable

logger = logging.getLogger(__name__)

class KisaanError(Exception):
    """Base exception for Kisaan Assistant"""
    pass

class DatabaseError(KisaanError):
    """Database related errors"""
    pass

class VoiceServiceError(KisaanError):
    """Voice processing errors"""
    pass

class APIError(KisaanError):
    """External API errors"""
    pass

class AgentError(KisaanError):
    """LangGraph agent errors"""
    pass

def handle_errors(func: Callable):
    """Decorator for error handling"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database operation failed")
        except VoiceServiceError as e:
            logger.error(f"Voice service error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Voice processing failed")
        except APIError as e:
            logger.error(f"API error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=503, detail="External service unavailable")
        except AgentError as e:
            logger.error(f"Agent error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="AI processing failed")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
    return wrapper

def get_error_message(language: str, error_type: str) -> str:
    """Get localized error messages"""
    error_messages = {
        "hindi": {
            "voice_error": "आवाज़ की पहचान में समस्या हुई। कृपया फिर से बोलें।",
            "api_error": "सर्विस अभी उपलब्ध नहीं है। कृपया बाद में प्रयास करें।",
            "general_error": "कुछ गलत हो गया। कृपया फिर से प्रयास करें।",
            "database_error": "डेटा सहेजने में समस्या हुई।"
        },
        "english": {
            "voice_error": "Voice recognition failed. Please speak again.",
            "api_error": "Service is currently unavailable. Please try later.",
            "general_error": "Something went wrong. Please try again.",
            "database_error": "Failed to save data."
        }
    }
    
    lang_messages = error_messages.get(language, error_messages["hindi"])
    return lang_messages.get(error_type, lang_messages["general_error"])