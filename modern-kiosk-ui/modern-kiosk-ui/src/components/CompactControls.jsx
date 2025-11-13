import { motion } from 'framer-motion'
import { Mic, MicOff } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import websocketService from '../services/websocketService'
import './CompactControls.css'

const CompactControls = ({ 
  isListening, 
  transcript, 
  onStartListening, 
  onStopListening,
  isStarted,
  avatarSpeaking = false,
  conversationMode = 'wake-word', // 'wake-word' or 'continuous'
  useWebSocket = false, // Toggle WebSocket vs Speech Recognition
  sessionId = null,
  language = 'hindi'
}) => {
  const recognitionRef = useRef(null)
  const wakeWordListenerRef = useRef(null)
  const isListeningRef = useRef(isListening)
  const avatarSpeakingRef = useRef(avatarSpeaking)
  const conversationModeRef = useRef(conversationMode)
  const [wsConnected, setWsConnected] = useState(false)
  const [currentTranscript, setCurrentTranscript] = useState('')
  
  // Keep refs in sync with props
  useEffect(() => {
    isListeningRef.current = isListening
  }, [isListening])
  
  useEffect(() => {
    avatarSpeakingRef.current = avatarSpeaking
  }, [avatarSpeaking])
  
  useEffect(() => {
    conversationModeRef.current = conversationMode
  }, [conversationMode])

  // Initialize Main Speech Recognition (for active listening)
  useEffect(() => {
    if (!isStarted) return

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      console.warn('⚠️ Speech recognition not supported in this browser')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false // Stops after one utterance
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      console.log('🎤 Main recognition started')
      onStartListening()
    }

    recognition.onresult = (event) => {
      let finalTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        }
      }

      if (finalTranscript && window.handleVoiceInput) {
        console.log('🗣️ Final transcript:', finalTranscript)
        window.handleVoiceInput(finalTranscript.trim())
      }
    }

    recognition.onerror = (event) => {
      console.error('❌ Speech recognition error:', event.error)
      // Auto-stop on error
      onStopListening()
    }

    recognition.onend = () => {
      console.log('🎤 Main recognition ended - mic turning OFF')
      // CRITICAL: Always stop listening when recognition ends
      onStopListening()
    }

    recognitionRef.current = recognition

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch (e) {
          // Ignore if already stopped
        }
      }
    }
  }, [isStarted, onStartListening, onStopListening])

  // Initialize Always-On Wake Word Listener (ONLY in wake-word mode)
  useEffect(() => {
    if (!isStarted) return
    
    // ONLY run wake word listener in wake-word mode
    if (conversationMode !== 'wake-word') {
      console.log('⏭️ Skipping wake word listener - in continuous conversation mode')
      // Stop wake word listener if it's running
      if (wakeWordListenerRef.current) {
        try {
          wakeWordListenerRef.current.stop()
          wakeWordListenerRef.current = null
        } catch (e) {
          // Already stopped
        }
      }
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const wakeWordListener = new SpeechRecognition()
    wakeWordListener.continuous = true // Always listening
    wakeWordListener.interimResults = true
    wakeWordListener.lang = 'en-US'

    wakeWordListener.onstart = () => {
      console.log('👂 Wake word listener started (wake-word mode)')
    }

    wakeWordListener.onresult = (event) => {
      // Get current state values using refs
      const currentlyListening = isListeningRef.current
      const currentlySpeaking = avatarSpeakingRef.current
      
      // CRITICAL: Don't process if main recognition is already active
      if (currentlyListening) {
        console.log('⏸️ Wake word listener paused - main recognition is active')
        return
      }

      // CRITICAL: Don't process if avatar is speaking (prevents echo detection)
      if (currentlySpeaking) {
        console.log('⏸️ Wake word listener ignoring input - avatar is speaking (echo prevention)')
        return
      }

      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }

      const combinedTranscript = (finalTranscript + ' ' + interimTranscript).toLowerCase().trim()
      
      // Skip empty or very short transcripts
      if (!combinedTranscript || combinedTranscript.length < 2) {
        return
      }

      // Avatar NOT speaking - Look for wake words to activate
      const wakeWords = ['hey mira', 'hi mira', 'hello mira', 'hey meera', 'hi meera', 'ok mira', 'okay mira']
      const hasWakeWord = wakeWords.some(word => combinedTranscript.includes(word))

      if (hasWakeWord) {
        console.log('🎤 Wake word detected!', combinedTranscript)
        
        // Remove wake word from transcript
        let cleanTranscript = finalTranscript
        wakeWords.forEach(word => {
          cleanTranscript = cleanTranscript.replace(new RegExp(word, 'gi'), '').trim()
        })
        
        // If there's content after wake word, process it directly
        if (cleanTranscript && window.handleVoiceInput) {
          console.log('📝 Processing command after wake word:', cleanTranscript)
          window.handleVoiceInput(cleanTranscript)
        } else if (window.handleWakeWord) {
          // Just wake up the assistant (no command after wake word)
          console.log('👋 Wake word only - activating mic')
          window.handleWakeWord()
        }
      }
    }

    wakeWordListener.onerror = (event) => {
      console.error('❌ Wake word listener error:', event.error)
      // Don't restart on abort - it means we intentionally stopped it
      if (event.error === 'aborted') {
        console.log('👂 Wake word listener aborted - will restart when needed')
        return
      }
      // Auto-restart on other errors
      if (event.error !== 'no-speech') {
        setTimeout(() => {
          try {
            if (wakeWordListenerRef.current && !isListeningRef.current && !avatarSpeakingRef.current) {
              wakeWordListener.start()
            }
          } catch (e) {
            // Ignore
          }
        }, 1000)
      }
    }

    wakeWordListener.onend = () => {
      console.log('👂 Wake word listener ended')
      // Use refs to get current state values
      const currentlyListening = isListeningRef.current
      const currentlySpeaking = avatarSpeakingRef.current
      
      // Only restart if:
      // 1. Main recognition is NOT active (prevents conflict)
      // 2. Avatar is NOT speaking (prevents echo detection)
      if (!currentlyListening && !currentlySpeaking) {
        console.log('🔄 Restarting wake word listener (ready to listen)')
        
        setTimeout(() => {
          try {
            if (wakeWordListenerRef.current && !isListeningRef.current && !avatarSpeakingRef.current) {
              wakeWordListener.start()
            }
          } catch (e) {
            // Ignore if already running
          }
        }, 500)
      } else {
        const reason = currentlyListening ? 'main recognition active' : 'avatar speaking (echo prevention)'
        console.log(`⏸️ Not restarting wake word listener (${reason})`)
      }
    }

    wakeWordListenerRef.current = wakeWordListener

    // Start wake word listener
    try {
      wakeWordListener.start()
    } catch (err) {
      console.error('Error starting wake word listener:', err)
    }

    return () => {
      if (wakeWordListenerRef.current) {
        try {
          wakeWordListenerRef.current.stop()
          wakeWordListenerRef.current = null
        } catch (e) {
          // Ignore
        }
      }
    }
  }, [isStarted, conversationMode]) // Recreate when session starts or mode changes

  // Manage wake word listener based on avatar speaking state (echo prevention)
  // ONLY in wake-word mode
  useEffect(() => {
    if (!wakeWordListenerRef.current || !isStarted || conversationMode !== 'wake-word') return

    if (avatarSpeaking) {
      // Avatar started speaking - STOP wake word listener to prevent echo
      console.log('🔇 Avatar speaking - stopping wake word listener (echo prevention)')
      try {
        wakeWordListenerRef.current.stop()
      } catch (err) {
        // Already stopped, that's ok
      }
    } else if (!isListening) {
      // Avatar finished speaking AND main recognition is NOT active - RESTART wake word listener
      console.log('🔊 Avatar finished - restarting wake word listener (wake-word mode)')
      setTimeout(() => {
        try {
          if (wakeWordListenerRef.current && !isListening && !avatarSpeaking && conversationMode === 'wake-word') {
            wakeWordListenerRef.current.start()
          }
        } catch (err) {
          // Already running or error, that's ok
        }
      }, 500)
    }
  }, [avatarSpeaking, isListening, isStarted, conversationMode])

  // Auto-start/stop main recognition based on isListening state
  // AND manage wake word listener coordination (ONLY in wake-word mode)
  useEffect(() => {
    if (!recognitionRef.current) return

    if (isListening) {
      // Starting main recognition
      const mode = conversationMode === 'wake-word' ? 'wake-word mode' : 'continuous mode'
      console.log(`▶️ Main recognition activated (${mode})`)
      
      // ONLY stop wake word listener in wake-word mode
      if (conversationMode === 'wake-word' && wakeWordListenerRef.current) {
        try {
          wakeWordListenerRef.current.stop()
        } catch (err) {
          // Already stopped, that's ok
        }
      }
      
      // Start main recognition if not already running
      try {
        recognitionRef.current.start()
      } catch (err) {
        // Might already be running, that's ok
        if (err.message && !err.message.includes('already')) {
          console.error('Error auto-starting recognition:', err)
        }
      }
    } else {
      // Stopping main recognition
      console.log('⏹️ Main recognition deactivated')
      
      // Stop main recognition if running
      try {
        recognitionRef.current.stop()
      } catch (err) {
        // Might already be stopped, that's ok
      }
      
      // Restart wake word listener ONLY in wake-word mode
      // AND only if avatar is NOT speaking (to prevent echo)
      if (conversationMode === 'wake-word' && !avatarSpeaking) {
        setTimeout(() => {
          if (wakeWordListenerRef.current && !isListening && !avatarSpeaking) {
            try {
              wakeWordListenerRef.current.start()
              console.log('🔄 Wake word listener restarted after main recognition stopped (wake-word mode)')
            } catch (err) {
              // Already running or error, that's ok
            }
          }
        }, 500)
      }
    }
  }, [isListening, avatarSpeaking, conversationMode])

  // WebSocket Integration for Real-Time Voice
  useEffect(() => {
    if (!useWebSocket || !isStarted || !sessionId) return

    console.log('🔌 Initializing WebSocket for real-time voice')

    // Setup WebSocket callbacks
    websocketService.setCallbacks({
      onTranscript: (text, isFinal) => {
        console.log(`📝 Transcript: ${text} (final: ${isFinal})`)
        setCurrentTranscript(text)
        
        if (isFinal && text.trim() && window.handleVoiceInput) {
          window.handleVoiceInput(text.trim())
          setCurrentTranscript('')
        }
      },

      onResponse: (response) => {
        console.log('🤖 AI Response received via WebSocket')
        // Response is handled by parent component through window.handleVoiceInput
      },

      onError: (error) => {
        console.error('❌ WebSocket error:', error)
        setWsConnected(false)
      },

      onConnected: () => {
        console.log('✅ WebSocket connected')
        setWsConnected(true)
      },

      onDisconnected: () => {
        console.log('🔌 WebSocket disconnected')
        setWsConnected(false)
      }
    })

    // Connect to WebSocket
    websocketService.connect(sessionId, language)

    return () => {
      console.log('🔌 Cleaning up WebSocket')
      websocketService.disconnect()
    }
  }, [useWebSocket, isStarted, sessionId, language])

  // Handle WebSocket recording based on isListening state
  useEffect(() => {
    if (!useWebSocket || !wsConnected) return

    if (isListening) {
      console.log('🎤 Starting WebSocket recording')
      websocketService.startRecording()
    } else {
      console.log('🛑 Stopping WebSocket recording')
      websocketService.stopRecording()
    }
  }, [useWebSocket, wsConnected, isListening])

  if (!isStarted) {
    return null
  }

  const handleMicClick = () => {
    if (useWebSocket) {
      // WebSocket mode - just toggle listening state
      if (isListening) {
        console.log('🔴 Manual stop - WebSocket recording')
        onStopListening()
      } else {
        console.log('🟢 Manual start - WebSocket recording')
        onStartListening()
      }
    } else {
      // Speech Recognition mode (original logic)
      if (isListening) {
        console.log('🔴 Manual stop - user clicked mic off')
        if (recognitionRef.current) {
          try {
            recognitionRef.current.stop()
          } catch (err) {
            console.error('Error stopping recognition:', err)
          }
        }
        onStopListening()
      } else {
        console.log('🟢 Manual start - user clicked mic on')
        if (recognitionRef.current) {
          try {
            recognitionRef.current.start()
            // Note: onStartListening() will be called by recognition.onstart event
          } catch (err) {
            console.error('Error starting recognition:', err)
            // If error, make sure we don't get stuck in listening state
            onStopListening()
          }
        }
      }
    }
  }

  // Use WebSocket transcript if available and in WebSocket mode
  const displayTranscript = useWebSocket && currentTranscript ? currentTranscript : transcript

  return (
    <motion.div 
      className="compact-controls"
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="controls-content">
        <div className={`transcript-display ${displayTranscript ? 'active' : ''}`}>
          {displayTranscript || (useWebSocket && wsConnected ? 'WebSocket ready - Tap microphone to speak' : 'Tap microphone to speak')}
        </div>

        <motion.button
          className={`mic-control ${isListening ? 'listening' : ''} ${useWebSocket && wsConnected ? 'ws-connected' : ''}`}
          onClick={handleMicClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          animate={isListening ? {
            boxShadow: [
              '0 0 0 0 rgba(239, 68, 68, 0.7)',
              '0 0 0 20px rgba(239, 68, 68, 0)',
              '0 0 0 0 rgba(239, 68, 68, 0.7)'
            ]
          } : {}}
          transition={isListening ? {
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut'
          } : {}}
        >
          {isListening ? <MicOff size={28} /> : <Mic size={28} />}
        </motion.button>

        <div className="status-text">
          {isListening ? (
            <span className="listening-text">{useWebSocket ? 'Streaming...' : 'Listening...'}</span>
          ) : (
            <span className="ready-text">{useWebSocket && wsConnected ? 'WebSocket Ready' : 'Ready'}</span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default CompactControls
