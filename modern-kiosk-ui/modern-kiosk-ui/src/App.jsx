import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Confetti from 'react-confetti'
import { useWindowSize } from 'react-use'
import KioskHeader from './components/KioskHeader'
import AvatarPanel from './components/AvatarPanel'
import ContentPanel from './components/ContentPanel'
import CompactControls from './components/CompactControls'
import LanguageSelector from './components/LanguageSelector'
import WelcomeScreen from './components/WelcomeScreen'
import TimeoutManager from './components/TimeoutManager'
import CameraCapture from './components/CameraCapture'
import { getAgricultureContent } from './utils/agricultureContentEngine'
import { analyzePersona, shouldInferPersona, getPersonalizedResponse } from './utils/personaDetection'
import { sendTextToAvatar, interruptAvatar } from './utils/avatarStream'
import { getAIResponse, handleWakeWord, clearSession, getCameraRequirement } from './services/aiService'
import apiService from './services/api'
import './App.css'

function App() {
  const { width, height } = useWindowSize()
  const [theme, setTheme] = useState('light') // 'light' or 'dark' - Light is default
  const [showWelcomeScreen, setShowWelcomeScreen] = useState(true)
  const [isStarted, setIsStarted] = useState(false)
  const [showLanguageSelector, setShowLanguageSelector] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState('en')
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [currentSlide, setCurrentSlide] = useState(null)
  const [conversationHistory, setConversationHistory] = useState([])
  const [userMessages, setUserMessages] = useState([]) // Track user messages only for persona detection
  const [detectedPersona, setDetectedPersona] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [showConfetti, setShowConfetti] = useState(false)
  const [lastUserActivity, setLastUserActivity] = useState(Date.now())
  const [showTimeout, setShowTimeout] = useState(false)
  const [avatarSpeaking, setAvatarSpeaking] = useState(false)
  const [conversationMode, setConversationMode] = useState('wake-word') // 'wake-word' or 'continuous'
  const [webrtcReady, setWebrtcReady] = useState(false)
  const [showCamera, setShowCamera] = useState(false)
  const [kisaanSessionId, setKisaanSessionId] = useState(null)
  const [useWebSocketVoice, setUseWebSocketVoice] = useState(false) // Toggle for WebSocket vs Speech Recognition
  
  // Use refs to track latest state values in event handlers
  const isListeningRef = useRef(isListening)
  const conversationModeRef = useRef(conversationMode)
  const webrtcReadyRef = useRef(webrtcReady)
  
  useEffect(() => {
    isListeningRef.current = isListening
  }, [isListening])
  
  useEffect(() => {
    conversationModeRef.current = conversationMode
  }, [conversationMode])
  
  useEffect(() => {
    webrtcReadyRef.current = webrtcReady
  }, [webrtcReady])

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const handleWelcomeComplete = () => {
    setShowWelcomeScreen(false)
    setIsStarted(true)
    // SKIP language selector - go directly to avatar
    setShowLanguageSelector(false)
    setConnectionStatus('connecting')
    setShowConfetti(true)

    // Show welcome slide immediately in content panel
    setCurrentSlide(getAgricultureContent('welcome'))

    // CRITICAL: Wait for WebRTC connection before sending welcome message
    const handleWebRTCReady = () => {
      if (webrtcReadyRef.current) {
        console.log('⚠️ WebRTC already handled, skipping duplicate')
        return
      }
      
      console.log('🎉 WebRTC CONNECTED - now safe to send welcome message')
      setWebrtcReady(true)
      setConnectionStatus('connected')
      setTimeout(() => setShowConfetti(false), 3000)
      
      // Wait a bit for session ID to be set in DOM, then send welcome
      setTimeout(() => {
        const sessionId = document.getElementById('sessionid')?.value
        console.log('🔍 Session ID in DOM:', sessionId)
        
        if (sessionId && sessionId !== '0') {
          console.log('✅ Valid session ID found - sending welcome message')
          handleLanguageSelect('en')
        } else {
          console.warn('⚠️ Session ID still not set, waiting longer...')
          setTimeout(() => {
            handleLanguageSelect('en')
          }, 1000)
        }
      }, 500)
      
      // Remove listener after use
      window.removeEventListener('webrtc-connected', handleWebRTCReady)
    }
    
    window.addEventListener('webrtc-connected', handleWebRTCReady)
    
    // NO FALLBACK - Don't send welcome if WebRTC doesn't connect
    // User can manually click mic to interact
  }

  const handleStart = () => {
    // This is now only used if someone manually triggers start
    handleWelcomeComplete()
  }

  const handleLanguageSelect = (lang) => {
    setSelectedLanguage(lang)
    setShowLanguageSelector(false)
    
    // Get personalized welcome message from AI
    const welcomeMessage = handleWakeWord()
    
    // Add welcome message
    setConversationHistory([
      {
        speaker: 'assistant',
        text: welcomeMessage,
        timestamp: new Date().toLocaleTimeString(),
        isAI: true
      }
    ])
    
    // Send welcome message immediately (WebRTC should already be connected at this point)
    console.log('📤 Sending welcome message (WebRTC should be connected)')
    sendTextToAvatar(welcomeMessage).catch(err => {
      console.error('Failed to send welcome to avatar:', err)
    })
  }

  // Listen for avatar speaking events
  useEffect(() => {
    const handleAvatarSpeakingStart = () => {
      console.log('🗣️ Avatar started speaking')
      setAvatarSpeaking(true)
      // CRITICAL: Stop mic immediately when avatar starts speaking
      if (isListening) {
        console.log('🔇 Stopping mic - avatar is speaking')
        handleStopListening()
      }
    }
    
    const handleAvatarSpeakingEnd = () => {
      console.log('✅ Avatar finished speaking')
      setAvatarSpeaking(false)
      
      // Use refs to get current values
      const currentMode = conversationModeRef.current
      
      // CONTINUOUS CONVERSATION MODE: Auto-enable mic after avatar finishes
      if (currentMode === 'continuous') {
        console.log('🎤 AUTO-ENABLING MIC (continuous conversation mode)')
        setTimeout(() => {
          // Check current state using refs
          const stillInContinuousMode = conversationModeRef.current === 'continuous'
          const notCurrentlyListening = !isListeningRef.current
          
          console.log('🔍 Auto-enable check:', {
            mode: conversationModeRef.current,
            isListening: isListeningRef.current,
            willEnable: stillInContinuousMode && notCurrentlyListening
          })
          
          if (stillInContinuousMode && notCurrentlyListening) {
            console.log('▶️ Starting recognition (auto-enable after avatar)')
            setIsListening(true)
            setTranscript('Listening...')
            handleUserActivity()
          } else {
            console.log('⚠️ Cannot auto-enable - already listening or mode changed')
          }
        }, 1000) // Increased delay to ensure avatar is completely done
      } else {
        console.log('👂 Wake word mode - waiting for wake word')
      }
    }
    
    window.addEventListener('avatar-speaking-start', handleAvatarSpeakingStart)
    window.addEventListener('avatar-speaking-end', handleAvatarSpeakingEnd)
    
    return () => {
      window.removeEventListener('avatar-speaking-start', handleAvatarSpeakingStart)
      window.removeEventListener('avatar-speaking-end', handleAvatarSpeakingEnd)
    }
  }, [isStarted, conversationMode]) // Removed isListening and avatarSpeaking to prevent re-creation

  // Expose voice input handler globally for CompactControls
  useEffect(() => {
    window.handleVoiceInput = handleVoiceInput
    
    window.handleWakeWord = () => {
      console.log('👋 Wake word detected - activating mic AND switching to continuous mode')
      if (!isListening && !avatarSpeaking) {
        console.log('🎤 Starting main recognition after wake word')
        // Switch to continuous conversation mode after first wake word
        setConversationMode('continuous')
        console.log('🔄 SWITCHED TO CONTINUOUS CONVERSATION MODE (no more wake words needed!)')
        handleStartListening()
      } else {
        console.log('⚠️ Cannot start - already listening or avatar speaking')
      }
    }
    
    return () => {
      delete window.handleVoiceInput
      delete window.handleWakeWord
    }
  }, [userMessages, detectedPersona, isListening, avatarSpeaking]) // Re-create when dependencies change

  const handleStartListening = () => {
    setIsListening(true)
    setTranscript('Listening...')
    handleUserActivity()
  }

  const handleStopListening = () => {
    setIsListening(false)
    setTimeout(() => setTranscript(''), 2000) // Clear after 2s
  }

  // Start timeout system based on speech interaction only (not touch)
  // Timeout triggers after last voice interaction, not touch events
  useEffect(() => {
    // Only start timeout when:
    // 1. Session is started
    // 2. There's been conversation
    // 3. User is NOT listening
    // 4. Avatar is NOT speaking
    if (isStarted && conversationHistory.length > 0 && !isListening && !avatarSpeaking) {
      console.log('⏲️ Starting 30s timeout timer (no activity)')
      const timer = setTimeout(() => {
        console.log('⚠️ 30 seconds of inactivity - showing timeout warning')
        setShowTimeout(true)
      }, 30000) // Start timeout warnings after 30 seconds of no speech
      
      return () => {
        console.log('⏹️ Clearing timeout timer (activity detected)')
        clearTimeout(timer)
      }
    } else {
      // Reset timeout if there's activity
      if (isListening || avatarSpeaking) {
        console.log('✅ Active interaction - timeout reset')
        setShowTimeout(false)
      }
    }
  }, [isStarted, conversationHistory.length, isListening, avatarSpeaking, lastUserActivity])

  const handleUserActivity = () => {
    setLastUserActivity(Date.now())
    setShowTimeout(false)
  }

  const handleSessionTimeout = () => {
    console.log('🔄 Session timeout - resetting conversation (keeping session active)')
    
    // Clear AI service session
    clearSession()
    
    // Reset conversation state but keep the session active
    setConversationHistory([])
    setUserMessages([])
    setCurrentSlide(null)
    setDetectedPersona(null)
    setTranscript('')
    setIsListening(false)
    setShowTimeout(false)
    
    // Reset back to wake-word mode
    setConversationMode('wake-word')
    console.log('🔄 Reset to wake-word mode - say "Hey Mira" to start again')
    
    // Send welcome message again after a short delay (connection should already be established)
    setTimeout(() => {
      const welcomeMessage = "Welcome back! How may I assist you today?"
      
      setConversationHistory([
        {
          speaker: 'assistant',
          text: welcomeMessage,
          timestamp: new Date().toLocaleTimeString(),
          isAI: true
        }
      ])
      
      // Send welcome message to avatar (session should already exist)
      sendTextToAvatar(welcomeMessage).catch(err => {
        console.error('Failed to send welcome to avatar:', err)
      })
    }, 2000)
  }

  const handleVoiceInput = async (text) => {
    setTranscript(text)
    
    // NOTE: Avatar interruption is now handled automatically by wake word listener
    // when user speaks during avatar speech (see CompactControls.jsx MODE 1)
    
    // Register user activity
    handleUserActivity()
    
    // Add user message to history
    setConversationHistory(prev => [
      ...prev,
      {
        speaker: 'user',
        text: text,
        timestamp: new Date().toLocaleTimeString()
      }
    ])
    
    // Track user messages for persona detection
    const updatedUserMessages = [...userMessages, text]
    setUserMessages(updatedUserMessages)
    
    // Analyze persona for AI service
    let currentPersona = detectedPersona
    if (shouldInferPersona(updatedUserMessages.length)) {
      const analysis = analyzePersona(updatedUserMessages)
      console.log('🎯 Persona Analysis:', analysis)
      
      if (analysis.confidence >= 0.6 && analysis.persona !== detectedPersona) {
        setDetectedPersona(analysis.persona)
        currentPersona = analysis.persona
        console.log(`✅ Persona detected: ${analysis.persona} (${(analysis.confidence * 100).toFixed(0)}% confidence)`)
      }
    }

    try {
      // Get AI response with persona context
      const aiResult = await getAIResponse(text, currentPersona)
      
      // Check if camera is required for disease detection
      if (aiResult.requires_camera) {
        console.log('📷 Camera required for disease detection')
        setShowCamera(true)
        return
      }
      
      // Get relevant content slide for UI display
      const content = getAgricultureContent(text, aiResult.responseData)
      
      // Add product images if available (from fertilizer/pesticide queries)
      if (aiResult.requires_images && aiResult.image_urls && aiResult.image_urls.length > 0) {
        console.log('🖼️ Adding product images to content:', aiResult.image_urls.length)
        content.images = aiResult.image_urls.map(img => ({
          url: img.url || `http://localhost:8000/products/${img.filename}`,
          title: img.title || img.product_name,
          description: img.description,
          source: img.source
        }))
      }
      
      setCurrentSlide(content)
      
      // Send AI response to avatar for speech
      sendTextToAvatar(aiResult.response).catch(err => {
        console.error('Failed to send to avatar:', err)
      })
      
      // Add AI response to history
      setTimeout(() => {
        setConversationHistory(prev => [
          ...prev,
          {
            speaker: 'assistant',
            text: aiResult.response,
            timestamp: new Date().toLocaleTimeString(),
            isAI: true // Mark as AI response
          }
        ])
      }, 500)
      
    } catch (error) {
      console.error('AI Response Error:', error)
      
      // Fallback to static content if AI fails
      const content = getAgricultureContent(text)
      setCurrentSlide(content)
      
      sendTextToAvatar(content.summary).catch(err => {
        console.error('Failed to send to avatar:', err)
      })
      
      setTimeout(() => {
        setConversationHistory(prev => [
          ...prev,
          {
            speaker: 'assistant',
            text: content.summary,
            timestamp: new Date().toLocaleTimeString()
          }
        ])
      }, 500)
    }
  }

  const handleCameraCapture = async (imageBase64) => {
    try {
      console.log('📸 Processing captured image...')
      
      // Diagnose disease from image
      const diagnosis = await apiService.diagnoseCropDisease(
        kisaanSessionId,
        imageBase64,
        selectedLanguage
      )
      
      // Close camera
      setShowCamera(false)
      
      if (diagnosis.success && diagnosis.text) {
        // Add diagnosis to conversation
        setConversationHistory(prev => [
          ...prev,
          {
            speaker: 'assistant',
            text: diagnosis.text,
            timestamp: new Date().toLocaleTimeString(),
            isAI: true,
            type: 'diagnosis'
          }
        ])
        
        // Send diagnosis to avatar for speech
        if (diagnosis.audio) {
          // Backend provides audio directly
          sendTextToAvatar(diagnosis.text).catch(err => {
            console.error('Failed to send diagnosis to avatar:', err)
          })
        }
        
        // Show disease detection content
        setCurrentSlide(getAgricultureContent('disease detection'))
      } else {
        console.error('Diagnosis failed:', diagnosis)
      }
    } catch (error) {
      console.error('Error processing camera image:', error)
      setShowCamera(false)
    }
  }

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  return (
    <div className={`app ${theme}`}>
      {/* Welcome Screen */}
      <AnimatePresence>
        {showWelcomeScreen && (
          <WelcomeScreen onComplete={handleWelcomeComplete} />
        )}
      </AnimatePresence>

      {/* Confetti Effect */}
      {showConfetti && (
        <Confetti
          width={width}
          height={height}
          recycle={false}
          numberOfPieces={200}
          gravity={0.1}
          colors={['#0066cc', '#4fc3f7', '#8e44ad', '#e74c3c', '#f39c12']}
        />
      )}

      <KioskHeader
        connectionStatus={connectionStatus}
        theme={theme}
        onThemeToggle={toggleTheme}
      />

      <div className={`kiosk-main ${currentSlide ? 'content-active' : ''}`}>
        {/* Left Side - Avatar (full width when no content) */}
        <AvatarPanel
          isStarted={isStarted}
          onStart={handleStart}
          isListening={isListening}
        />

        {/* Right Side - Content Slides (slides in from right) */}
        <ContentPanel
          currentSlide={currentSlide}
          isStarted={isStarted}
          onClose={() => setCurrentSlide(null)}
          language={selectedLanguage}
        />
      </div>

      {/* Bottom Compact Controls */}
      <CompactControls
        isListening={isListening}
        transcript={transcript}
        onStartListening={handleStartListening}
        onStopListening={handleStopListening}
        isStarted={isStarted}
        avatarSpeaking={avatarSpeaking}
        conversationMode={conversationMode}
        useWebSocket={useWebSocketVoice}
        sessionId={kisaanSessionId}
        language={selectedLanguage}
      />

      {/* Timeout Manager */}
      <TimeoutManager
        isActive={showTimeout}
        onTimeout={handleSessionTimeout}
        onUserActivity={handleUserActivity}
        isListening={isListening}
        avatarSpeaking={avatarSpeaking}
      />

      {/* Camera Capture for Disease Detection */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
          language={selectedLanguage}
        />
      )}

      <AnimatePresence>
        {showLanguageSelector && (
          <LanguageSelector
            onSelect={handleLanguageSelect}
            onClose={() => setShowLanguageSelector(false)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
