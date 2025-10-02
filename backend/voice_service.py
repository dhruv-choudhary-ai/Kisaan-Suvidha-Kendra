import os
import base64
import asyncio
import aiohttp
import tempfile
from typing import Optional
import assemblyai as aai
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from gtts import gTTS
import io
from config import Config
import logging

logger = logging.getLogger(__name__)

# Initialize API keys
if Config.TTS_PROVIDER == "elevenlabs":
    set_api_key(Config.ELEVENLABS_API_KEY)
aai.settings.api_key = Config.ASSEMBLYAI_API_KEY

class VoiceService:
    def __init__(self):
        self.transcriber = aai.Transcriber()
        self.tts_provider = Config.TTS_PROVIDER
        
        logger.info(f"🎤 Voice Service initialized with TTS provider: {self.tts_provider}")
        
        # Language-specific voice configurations for ElevenLabs
        self.voice_configs = {
            'hindi': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Replace with actual Hindi voice ID
                'model': 'eleven_multilingual_v2'
            },
            'english': {
                'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel voice
                'model': 'eleven_monolingual_v1'
            },
            'punjabi': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_multilingual_v2'
            },
            'marathi': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_multilingual_v2'
            },
            'gujarati': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_multilingual_v2'
            },
            'tamil': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_multilingual_v2'
            },
            'telugu': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_multilingual_v2'
            },
            'kannada': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_multilingual_v2'
            },
            'bengali': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_multilingual_v2'
            }
        }
        
        # Language codes for gTTS
        self.gtts_lang_codes = {
            'hindi': 'hi',
            'english': 'en',
            'punjabi': 'pa',
            'marathi': 'mr',
            'gujarati': 'gu',
            'tamil': 'ta',
            'telugu': 'te',
            'kannada': 'kn',
            'bengali': 'bn'
        }
    
    async def transcribe_audio(self, audio_base64: str, language: str = "hindi") -> str:
        """
        Transcribe audio from base64 encoded data using AssemblyAI
        
        Args:
            audio_base64: Base64 encoded audio data
            language: Language code for transcription
            
        Returns:
            Transcribed text
        """
        try:
            # Decode base64 audio
            audio_data = base64.b64decode(audio_base64)
            
            # Create temporary file (works on Windows and Linux)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                temp_audio_path = temp_file.name
                temp_file.write(audio_data)
            
            logger.info(f"Transcribing audio file: {temp_audio_path}")
            
            # Map language to AssemblyAI language code
            lang_map = {
                'hindi': 'hi',
                'english': 'en',
                'punjabi': 'pa',
                'marathi': 'mr',
                'gujarati': 'gu',
                'tamil': 'ta',
                'telugu': 'te',
                'kannada': 'kn',
                'bengali': 'bn'
            }
            
            assembly_lang = lang_map.get(language, 'hi')
            
            # Transcribe using AssemblyAI
            config = aai.TranscriptionConfig(language_code=assembly_lang)
            transcript = self.transcriber.transcribe(temp_audio_path, config=config)
            
            # Clean up temp file
            try:
                os.remove(temp_audio_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription error: {transcript.error}")
                return ""
            
            logger.info(f"✅ Transcription successful: {transcript.text}")
            return transcript.text
            
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            return ""
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription error: {transcript.error}")
                return ""
            
            return transcript.text
            
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            return ""
    
    async def text_to_speech(self, text: str, language: str = "hindi") -> str:
        """
        Convert text to speech using configured TTS provider and return base64 encoded audio
        
        Args:
            text: Text to convert to speech
            language: Language for TTS
            
        Returns:
            Base64 encoded audio data
        """
        try:
            if self.tts_provider == "gtts":
                return await self._gtts_text_to_speech(text, language)
            else:
                return await self._elevenlabs_text_to_speech(text, language)
        except Exception as e:
            logger.error(f"Error in TTS ({self.tts_provider}): {str(e)}")
            return ""
    
    async def _gtts_text_to_speech(self, text: str, language: str = "hindi") -> str:
        """
        Convert text to speech using gTTS (free, no credits needed)
        
        Args:
            text: Text to convert to speech
            language: Language for TTS
            
        Returns:
            Base64 encoded audio data
        """
        try:
            # Get gTTS language code
            lang_code = self.gtts_lang_codes.get(language, 'hi')
            
            # Create gTTS object
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            # Save to BytesIO object instead of file
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_fp.read()).decode('utf-8')
            
            logger.info(f"✅ gTTS audio generated ({len(audio_base64)} chars)")
            return audio_base64
            
        except Exception as e:
            logger.error(f"Error in gTTS: {str(e)}")
            return ""
    
    async def _elevenlabs_text_to_speech(self, text: str, language: str = "hindi") -> str:
        """
        Convert text to speech using ElevenLabs (paid, uses credits)
        
        Args:
            text: Text to convert to speech
            language: Language for TTS
            
        Returns:
            Base64 encoded audio data
        """
        try:
            voice_config = self.voice_configs.get(language, self.voice_configs['hindi'])
            
            # Generate audio using ElevenLabs
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_config['voice_id'],
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.0,
                        use_speaker_boost=True
                    )
                ),
                model=voice_config['model']
            )
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio).decode('utf-8')
            
            logger.info(f"✅ ElevenLabs audio generated ({len(audio_base64)} chars)")
            return audio_base64
            
        except Exception as e:
            logger.error(f"Error in ElevenLabs TTS: {str(e)}")
            return ""
    
    def get_greeting_message(self, language: str = "hindi") -> str:
        """
        Get greeting message in specified language
        
        Args:
            language: Language for greeting
            
        Returns:
            Greeting message text
        """
        greetings = {
            'hindi': "नमस्ते! मैं किसान सहायक हूं। कृपया अपनी भाषा चुनें।",
            'english': "Hello! I am Kisaan Assistant. Please select your language.",
            'punjabi': "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਕਿਸਾਨ ਸਹਾਇਕ ਹਾਂ।",
            'marathi': "नमस्कार! मी किसान सहायक आहे।",
            'gujarati': "નમસ્તે! હું કિસાન સહાયક છું.",
            'tamil': "வணக்கம்! நான் கிசான் உதவியாளர்.",
            'telugu': "నమస్కారం! నేను కిసాన్ అసిస్టెంట్.",
            'kannada': "ನಮಸ್ಕಾರ! ನಾನು ಕಿಸಾನ್ ಸಹಾಯಕ.",
            'bengali': "নমস্কার! আমি কিষাণ সহায়ক।"
        }
        
        return greetings.get(language, greetings['hindi'])
    
    def detect_language_from_speech(self, text: str) -> Optional[str]:
        """
        Detect language preference from user's speech
        
        Args:
            text: Transcribed text
            
        Returns:
            Detected language or None
        """
        text_lower = text.lower()
        
        language_keywords = {
            'hindi': ['हिंदी', 'hindi', 'हिन्दी'],
            'english': ['english', 'अंग्रेजी', 'angrezī'],
            'punjabi': ['punjabi', 'पंजाबी', 'ਪੰਜਾਬੀ'],
            'marathi': ['marathi', 'मराठी'],
            'gujarati': ['gujarati', 'गुजराती'],
            'tamil': ['tamil', 'तमिल', 'தமிழ்'],
            'telugu': ['telugu', 'तेलुगु', 'తెలుగు'],
            'kannada': ['kannada', 'कन्नड़', 'ಕನ್ನಡ'],
            'bengali': ['bengali', 'बंगाली', 'বাংলা']
        }
        
        for lang, keywords in language_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return lang
        
        return None

# Global voice service instance
voice_service = VoiceService()