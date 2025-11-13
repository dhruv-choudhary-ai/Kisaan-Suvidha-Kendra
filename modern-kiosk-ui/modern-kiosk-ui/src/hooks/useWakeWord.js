/**
 * Wake Word Detection Hook
 * Listens for "Hi Mira" and "Hey Mira" wake words
 * Uses Web Speech API for continuous speech recognition
 */

import { useState, useEffect, useRef } from 'react'

const WAKE_WORDS = ['hi mira', 'hey mira', 'hello mira']

export function useWakeWord({ onWakeWordDetected, isEnabled = true }) {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [error, setError] = useState(null)
  const recognitionRef = useRef(null)
  const lastDetectionRef = useRef(0)

  // Check if Speech Recognition is supported
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    setIsSupported(!!SpeechRecognition)
    
    if (!SpeechRecognition) {
      setError('Speech Recognition not supported in this browser')
      return
    }

    // Initialize speech recognition
    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.maxAlternatives = 1

    recognitionRef.current = recognition

    return () => {
      if (recognition) {
        recognition.stop()
      }
    }
  }, [])

  // Set up speech recognition event handlers
  useEffect(() => {
    const recognition = recognitionRef.current
    if (!recognition) return

    const handleResult = (event) => {
      const lastResult = event.results[event.results.length - 1]
      
      if (lastResult.isFinal) {
        const transcript = lastResult[0].transcript.toLowerCase().trim()
        console.log('🎤 Wake word detection heard:', transcript)

        // Check for wake words
        const wakeWordDetected = WAKE_WORDS.some(wakeWord => 
          transcript.includes(wakeWord)
        )

        if (wakeWordDetected) {
          // Prevent multiple rapid detections
          const now = Date.now()
          if (now - lastDetectionRef.current > 3000) { // 3 second cooldown
            lastDetectionRef.current = now
            console.log('✅ Wake word detected:', transcript)
            onWakeWordDetected && onWakeWordDetected(transcript)
          }
        }
      }
    }

    const handleError = (event) => {
      console.error('Wake word recognition error:', event.error)
      
      // Handle specific error types
      switch (event.error) {
        case 'network':
          setError('Network error - please check your connection')
          break
        case 'not-allowed':
          setError('Microphone access denied - please allow microphone permission')
          break
        case 'no-speech':
          // This is normal for continuous listening, restart silently
          if (isEnabled && isListening) {
            setTimeout(() => {
              try {
                recognition.start()
              } catch (e) {
                // Ignore if already started
              }
            }, 100)
          }
          return
        default:
          setError(`Speech recognition error: ${event.error}`)
      }
      
      setIsListening(false)
    }

    const handleStart = () => {
      console.log('🎤 Wake word detection started')
      setIsListening(true)
      setError(null)
    }

    const handleEnd = () => {
      console.log('🎤 Wake word detection stopped')
      setIsListening(false)
      
      // Restart if still enabled (for continuous listening)
      if (isEnabled) {
        setTimeout(() => {
          try {
            recognition.start()
          } catch (e) {
            // Ignore if already started
          }
        }, 100)
      }
    }

    recognition.addEventListener('result', handleResult)
    recognition.addEventListener('error', handleError)
    recognition.addEventListener('start', handleStart)
    recognition.addEventListener('end', handleEnd)

    return () => {
      recognition.removeEventListener('result', handleResult)
      recognition.removeEventListener('error', handleError)
      recognition.removeEventListener('start', handleStart)
      recognition.removeEventListener('end', handleEnd)
    }
  }, [onWakeWordDetected, isEnabled, isListening])

  // Start/stop recognition based on enabled state
  useEffect(() => {
    const recognition = recognitionRef.current
    if (!recognition || !isSupported) return

    if (isEnabled && !isListening) {
      try {
        recognition.start()
      } catch (error) {
        // May already be started
        console.log('Wake word recognition already active')
      }
    } else if (!isEnabled && isListening) {
      recognition.stop()
    }

    return () => {
      if (recognition && isListening) {
        recognition.stop()
      }
    }
  }, [isEnabled, isSupported, isListening])

  const startListening = () => {
    const recognition = recognitionRef.current
    if (!recognition || !isSupported) return false

    try {
      recognition.start()
      return true
    } catch (error) {
      console.error('Failed to start wake word detection:', error)
      setError('Failed to start wake word detection')
      return false
    }
  }

  const stopListening = () => {
    const recognition = recognitionRef.current
    if (!recognition) return

    recognition.stop()
    setIsListening(false)
  }

  return {
    isListening,
    isSupported,
    error,
    startListening,
    stopListening
  }
}

export default useWakeWord



