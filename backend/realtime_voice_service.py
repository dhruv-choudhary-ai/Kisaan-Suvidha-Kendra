"""
Real-time Voice Service with AssemblyAI WebSocket for live transcription
"""

import os
import asyncio
import base64
import json
import logging
from typing import Optional, Callable
import assemblyai as aai
from config import Config
from voice_service import voice_service

logger = logging.getLogger(__name__)

# Initialize AssemblyAI
aai.settings.api_key = Config.ASSEMBLYAI_API_KEY


class RealtimeVoiceService:
    """Real-time voice transcription and TTS using AssemblyAI WebSocket"""
    
    def __init__(self):
        self.transcriber: Optional[aai.RealtimeTranscriber] = None
        self.is_active = False
        self.on_transcript_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        self.language = "hi"  # Default to Hindi
        
        logger.info("🎤 Real-time Voice Service initialized")
    
    def set_callbacks(
        self, 
        on_transcript: Callable[[str, bool], None],
        on_error: Optional[Callable[[str], None]] = None
    ):
        """
        Set callback functions for transcription events
        
        Args:
            on_transcript: Called when transcript is received (text, is_final)
            on_error: Called when error occurs (error_message)
        """
        self.on_transcript_callback = on_transcript
        self.on_error_callback = on_error
    
    def set_language(self, language: str):
        """
        Set the language for transcription
        
        Args:
            language: Language code (hindi, english, etc.)
        """
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
        self.language = lang_map.get(language, 'hi')
        logger.info(f"Language set to: {language} ({self.language})")
    
    async def start(self):
        """Start real-time transcription"""
        if self.is_active:
            logger.warning("Real-time transcription already active")
            return
        
        try:
            logger.info("Starting AssemblyAI real-time transcription...")
            
            # Create transcriber configuration
            self.transcriber = aai.RealtimeTranscriber(
                sample_rate=16000,
                on_data=self._on_data,
                on_error=self._on_error,
                on_open=self._on_open,
                on_close=self._on_close,
                language_code=self.language,
                encoding=aai.AudioEncoding.pcm_s16le
            )
            
            # Connect to AssemblyAI
            self.transcriber.connect()
            self.is_active = True
            
            logger.info("✅ Real-time transcription started")
            
        except Exception as e:
            logger.error(f"Error starting real-time transcription: {str(e)}")
            self.is_active = False
            if self.on_error_callback:
                await self.on_error_callback(str(e))
    
    async def stop(self):
        """Stop real-time transcription"""
        if not self.is_active:
            return
        
        try:
            logger.info("Stopping real-time transcription...")
            
            if self.transcriber:
                self.transcriber.close()
                self.transcriber = None
            
            self.is_active = False
            logger.info("✅ Real-time transcription stopped")
            
        except Exception as e:
            logger.error(f"Error stopping real-time transcription: {str(e)}")
    
    async def send_audio(self, audio_data: bytes):
        """
        Send audio data to AssemblyAI for transcription
        
        Args:
            audio_data: Raw audio bytes (PCM 16-bit, 16kHz)
        """
        if not self.is_active or not self.transcriber:
            logger.warning("Transcriber not active, cannot send audio")
            return
        
        try:
            self.transcriber.stream(audio_data)
        except Exception as e:
            logger.error(f"Error sending audio: {str(e)}")
            if self.on_error_callback:
                await self.on_error_callback(str(e))
    
    def _on_open(self, session_opened: aai.RealtimeSessionOpened):
        """Called when WebSocket connection is opened"""
        logger.info(f"✅ AssemblyAI session opened: {session_opened.session_id}")
    
    def _on_data(self, transcript: aai.RealtimeTranscript):
        """Called when transcript data is received"""
        if not transcript.text:
            return
        
        try:
            is_final = isinstance(transcript, aai.RealtimeFinalTranscript)
            
            logger.info(f"{'📝 Final' if is_final else '👂 Partial'} transcript: {transcript.text}")
            
            # Call the callback if set
            if self.on_transcript_callback:
                asyncio.create_task(
                    self.on_transcript_callback(transcript.text, is_final)
                )
        
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
    
    def _on_error(self, error: aai.RealtimeError):
        """Called when an error occurs"""
        logger.error(f"❌ AssemblyAI error: {error}")
        
        if self.on_error_callback:
            asyncio.create_task(
                self.on_error_callback(str(error))
            )
    
    def _on_close(self):
        """Called when WebSocket connection is closed"""
        logger.info("AssemblyAI session closed")
        self.is_active = False


# Global realtime voice service instance
realtime_voice_service = RealtimeVoiceService()
