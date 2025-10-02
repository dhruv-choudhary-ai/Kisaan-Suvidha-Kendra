"use client"

import { useState, useRef, useEffect, useCallback, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Mic, MicOff, Loader2, Settings, Languages, History, Volume2 } from "lucide-react"
import AudioVisualizer from "@/components/audio-visualizer"
import MessageList from "@/components/message-list"
import LanguageSelector from "@/components/language-selector"
import SessionStats from "@/components/session-stats"
import CameraDiseaseDetector from "@/components/camera-disease-detector"

type SessionStatus = "idle" | "awaiting_language" | "active" | "listening" | "processing"

interface Message {
  id: string
  text: string
  audio?: string
  sender: "user" | "assistant"
  timestamp: Date
  isStreaming?: boolean
}

export default function VoiceAssistant() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [status, setStatus] = useState<SessionStatus>("idle")
  const [messages, setMessages] = useState<Message[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [showLanguageSelector, setShowLanguageSelector] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState("English")
  const [showStats, setShowStats] = useState(false)
  const [currentTranscript, setCurrentTranscript] = useState("")
  const [languageRetryCount, setLanguageRetryCount] = useState(0)
  const [isAutoRecording, setIsAutoRecording] = useState(false)
  const [showCamera, setShowCamera] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  
  // Performance optimizations
  const pendingRequests = useRef<Map<string, Promise<any>>>(new Map())
  const lastRequestTime = useRef<number>(0)
  const REQUEST_DEBOUNCE_TIME = 300 // Prevent duplicate requests within 300ms
  
  // Browser capability detection with fallback options
  const getOptimalMediaRecorderOptions = useCallback((): MediaRecorderOptions => {
    const preferredOptions = [
      // Try high quality first
      { mimeType: 'audio/webm;codecs=opus', bitsPerSecond: AUDIO_BITRATE },
      { mimeType: 'audio/webm', bitsPerSecond: AUDIO_BITRATE },
      // Fallback without bitrate specification to avoid clamping
      { mimeType: 'audio/webm;codecs=opus' },
      { mimeType: 'audio/webm' },
      { mimeType: 'audio/mp4' },
      // Last resort with bitrate
      { bitsPerSecond: AUDIO_BITRATE },
      // Final fallback with no options
      {}
    ]
    
    for (const option of preferredOptions) {
      if (!option.mimeType || MediaRecorder.isTypeSupported(option.mimeType)) {
        console.log("[v0] Using MediaRecorder options:", option)
        return option
      }
    }
    
    console.warn("[v0] Using default MediaRecorder options")
    return {}
  }, [])

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const silenceStartTimeRef = useRef<number | null>(null)
  const isRecordingRef = useRef<boolean>(false)
  const animationFrameRef = useRef<number | null>(null)
  const speechDetectedRef = useRef<boolean>(false) // Track if speech has been detected
  const streamRef = useRef<MediaStream | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  // Balanced thresholds for proper microphone behavior
  const SILENCE_THRESHOLD = 0.03 // Balanced threshold for proper silence detection
  const SILENCE_DURATION = 3000 // 3 seconds - more reasonable time for user to think
  const SPEECH_THRESHOLD = 0.05 // Higher threshold to avoid noise detection
  const FALLBACK_TIMEOUT = 10000 // 10 seconds fallback if no speech detected
  
  // Optimized audio settings for better browser compatibility
  const AUDIO_SAMPLE_RATE = 48000 // Use browser's preferred sample rate
  const AUDIO_BITRATE = 256000 // Increased to 256kbps to avoid browser clamping
  const AUDIO_CHUNK_SIZE = 1024 // Optimized chunk size

  // Optimized cleanup and performance monitoring
  useEffect(() => {
    // Suppress MediaRecorder bitrate clamping warnings for cleaner console
    const originalWarn = console.warn
    console.warn = (...args) => {
      const message = args.join(' ')
      if (message.includes('Clamping calculated') && message.includes('bitrate')) {
        return // Suppress these expected warnings
      }
      originalWarn.apply(console, args)
    }

    // Preload audio context for faster first recording
    const initAudioContext = () => {
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        try {
          audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
          // Let browser choose optimal sample rate
        } catch (error) {
          console.warn("[v0] Failed to initialize audio context:", error)
        }
      }
    }

    // Initialize on user interaction for better performance
    const handleUserInteraction = () => {
      initAudioContext()
      document.removeEventListener('click', handleUserInteraction)
      document.removeEventListener('touchstart', handleUserInteraction)
    }

    document.addEventListener('click', handleUserInteraction)
    document.addEventListener('touchstart', handleUserInteraction)

    return () => {
      // Restore original console.warn
      console.warn = originalWarn
      
      // Comprehensive cleanup
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
      }
      
      // Clear caches
      pendingRequests.current.clear()
      
      // Remove event listeners
      document.removeEventListener('click', handleUserInteraction)
      document.removeEventListener('touchstart', handleUserInteraction)
    }
  }, [])

  const startSession = useCallback(async () => {
    try {
      setStatus("processing")
      
      console.log("[v0] Starting new session (no audio caching)")
      
      // Use AbortController for request timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch(`${API_BASE}/voice/start-session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Connection": "keep-alive",
        },
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("[v0] Session start response:", {
        session_id: data.session_id,
        text: data.text,
        hasAudio: !!data.audio,
        audioLength: data.audio ? data.audio.length : 0
      })
      setSessionId(data.session_id)
      
      const greetingMessage: Message = {
        id: Date.now().toString(),
        text: data.text,
        audio: data.audio,
        sender: "assistant",
        timestamp: new Date(),
        isStreaming: true,
      }

      setMessages([greetingMessage])

      // Play audio without waiting and prepare for next step
      if (data.audio) {
        console.log("[v0] Playing greeting audio, length:", data.audio.length)
        playAudio(data.audio).catch(console.error)
      }

      // Wait longer for audio to finish playing before starting language selection
      setTimeout(() => {
        setMessages((prev) => prev.map((msg) => ({ ...msg, isStreaming: false })))
        setStatus("awaiting_language")
        setLanguageRetryCount(0)
        
        // Increased delay to let user understand the greeting
        setTimeout(() => {
          console.log("[v0] Auto-starting language selection recording, sessionId:", data.session_id)
          startRecordingForLanguage(data.session_id)
        }, 2000) // Increased to 2 seconds
      }, 1500) // Increased to 1.5 seconds
    } catch (error) {
      console.error("[v0] Error starting session:", error)
      setStatus("idle")
    }
  }, [])

  const startRecording = useCallback(async () => {
    try {
      console.log("[v0] startRecording called, current status:", status, "sessionId:", sessionId)
      
      if (!sessionId) {
        console.error("[v0] Cannot start recording: no session ID")
        return
      }

      setCurrentTranscript("")

      // Optimized audio constraints for browser compatibility
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1, // Mono for smaller file size
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          // Remove sampleRate constraint to let browser choose optimal rate
        }
      })
      
      // Test if the stream is actually working
      const tracks = stream.getAudioTracks()
      if (tracks.length === 0) {
        throw new Error("No audio tracks available")
      }
      
      console.log("[v0] Audio track settings:", tracks[0].getSettings())
      console.log("[v0] Audio track state:", tracks[0].readyState, tracks[0].enabled)
      
      streamRef.current = stream

      // Reuse existing AudioContext if available and working
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      }
      
      // Resume context if suspended
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume()
      }
      
      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 512 // Balanced for good sensitivity without overprocessing
      analyserRef.current.smoothingTimeConstant = 0.3 // Balanced smoothing
      analyserRef.current.minDecibels = -90
      analyserRef.current.maxDecibels = -10
      source.connect(analyserRef.current)
      
      console.log("[v0] AudioContext state:", audioContextRef.current.state, 
                 "Sample rate:", audioContextRef.current.sampleRate,
                 "Analyser fftSize:", analyserRef.current.fftSize)

      // Get optimal MediaRecorder options for this browser
      const options = getOptimalMediaRecorderOptions()
      
      try {
        mediaRecorderRef.current = new MediaRecorder(stream, options)
        console.log("[v0] MediaRecorder created successfully with options:", options)
      } catch (error) {
        console.warn("[v0] Failed to create MediaRecorder with options:", options, "Error:", error)
        // Fallback to basic MediaRecorder
        mediaRecorderRef.current = new MediaRecorder(stream)
        console.log("[v0] Using fallback MediaRecorder without options")
      }
      
      audioChunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        await sendAudioQuery(audioBlob)
        cleanupStream()
      }

      // Start recording with optimized timeslices
      try {
        mediaRecorderRef.current.start(250)
        setIsRecording(true)
        isRecordingRef.current = true
        setStatus("listening")
        
        console.log("[v0] Recording started successfully with options:", options)
      } catch (startError) {
        console.error("[v0] Failed to start MediaRecorder:", startError)
        cleanupStream()
        throw startError
      }
      
      visualizeAudio()
      startSilenceDetection()
    } catch (error) {
      console.error("[v0] Error starting recording:", error)
      setStatus("active")
      throw error
    }
  }, [sessionId, status])

  const startRecordingForLanguage = useCallback(async (currentSessionId?: string) => {
    try {
      const activeSessionId = currentSessionId || sessionId
      
      if (!activeSessionId) {
        console.error("[v0] No session ID for language selection - showing UI selector as fallback")
        setShowLanguageSelector(true)
        setStatus("awaiting_language")
        setIsAutoRecording(false)
        return
      }
      
      console.log("[v0] Starting language recording with sessionId:", activeSessionId)
      
      setCurrentTranscript("")
      setIsAutoRecording(true)

      // Optimized audio constraints for language detection
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
          // Remove sampleRate constraint for better compatibility
        }
      })
      
      // Test if the stream is actually working for language detection
      const tracks = stream.getAudioTracks()
      if (tracks.length === 0) {
        throw new Error("No audio tracks available for language detection")
      }
      
      console.log("[v0] Language detection audio track settings:", tracks[0].getSettings())
      console.log("[v0] Language detection audio track state:", tracks[0].readyState, tracks[0].enabled)
      
      streamRef.current = stream

      // Reuse existing AudioContext for language detection
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      }
      
      // Resume context if suspended
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume()
      }
      
      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 512 // Balanced for language detection
      analyserRef.current.smoothingTimeConstant = 0.3 // Balanced smoothing
      analyserRef.current.minDecibels = -90
      analyserRef.current.maxDecibels = -10
      source.connect(analyserRef.current)
      
      console.log("[v0] Language AudioContext state:", audioContextRef.current.state, 
                 "Sample rate:", audioContextRef.current.sampleRate)

      // Use optimized options for language recording
      const options = getOptimalMediaRecorderOptions()
      
      try {
        mediaRecorderRef.current = new MediaRecorder(stream, options)
        console.log("[v0] Language MediaRecorder created successfully with options:", options)
      } catch (error) {
        console.warn("[v0] Failed to create language MediaRecorder with options:", options, "Error:", error)
        // Fallback to basic MediaRecorder
        mediaRecorderRef.current = new MediaRecorder(stream)
        console.log("[v0] Using fallback language MediaRecorder without options")
      }
      
      audioChunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        await processLanguageSelection(audioBlob, activeSessionId)
        cleanupStream()
      }

      try {
        mediaRecorderRef.current.start(250)
        setIsRecording(true)
        isRecordingRef.current = true
        setStatus("listening")
        
        console.log("[v0] Language recording started with options:", options)
      } catch (startError) {
        console.error("[v0] Failed to start language MediaRecorder:", startError)
        cleanupStream()
        throw startError
      }
      
      visualizeAudio()
      startSilenceDetection()
    } catch (error) {
      console.error("[v0] Error starting language recording:", error)
      setIsAutoRecording(false)
      if (languageRetryCount >= 2) {
        setShowLanguageSelector(true)
        setStatus("awaiting_language")
      }
    }
  }, [sessionId, languageRetryCount])

  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      console.log("[v0] Stopping recording...")
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      isRecordingRef.current = false
      setStatus("processing")
      setAudioLevel(0)
      
      // Clear silence detection
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
        silenceTimeoutRef.current = null
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }
      silenceStartTimeRef.current = null
    }
  }, [])

  const startSilenceDetection = useCallback(() => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    speechDetectedRef.current = false
    let frameCount = 0
    const startTime = Date.now()
    
    const checkSilence = () => {
      if (!analyserRef.current || !isRecordingRef.current) {
        console.log("[v0] Stopping silence detection")
        return
      }

      frameCount++
      
      // Check every 3rd frame for better performance (still ~20 times per second)
      if (frameCount % 3 === 0) {
        analyserRef.current.getByteFrequencyData(dataArray)
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
        const normalizedLevel = average / 255

        // Debug audio analysis - reduced logging
        if (frameCount % 90 === 0) {
          console.log("[v0] Audio level:", normalizedLevel.toFixed(3), 
                     "Speech detected:", speechDetectedRef.current,
                     "Silence duration:", silenceStartTimeRef.current ? Date.now() - silenceStartTimeRef.current : 0)
        }

        // Check for fallback timeout if no speech detected
        const elapsed = Date.now() - startTime
        if (!speechDetectedRef.current && elapsed > FALLBACK_TIMEOUT) {
          console.log("[v0] Fallback timeout reached, stopping recording (no speech detected)")
          stopRecording()
          return
        }

        // Speech detection with proper threshold
        if (!speechDetectedRef.current && normalizedLevel > SPEECH_THRESHOLD) {
          speechDetectedRef.current = true
          console.log("[v0] Speech detected! Level:", normalizedLevel.toFixed(3), "Threshold:", SPEECH_THRESHOLD)
          silenceStartTimeRef.current = null
        }

        // Alternative detection for very quiet environments - check frequency data
        if (!speechDetectedRef.current && elapsed > 4000) {
          // Check if there's any variation in frequency data (indicating speech/sound)
          const maxValue = Math.max(...dataArray)
          const minValue = Math.min(...dataArray)
          const variation = maxValue - minValue
          
          if (variation > 10) { // Some frequency variation detected
            speechDetectedRef.current = true
            console.log("[v0] Speech detected via frequency variation! Variation:", variation)
            silenceStartTimeRef.current = null
          }
        }

        // Optimized silence detection
        if (speechDetectedRef.current) {
          if (normalizedLevel < SILENCE_THRESHOLD) {
            if (silenceStartTimeRef.current === null) {
              silenceStartTimeRef.current = Date.now()
              console.log("[v0] Silence started (after speech)")
            } else {
              const silenceDuration = Date.now() - silenceStartTimeRef.current
              if (silenceDuration >= SILENCE_DURATION) {
                console.log(`[v0] Silence detected for ${SILENCE_DURATION}ms, auto-stopping recording`)
                stopRecording()
                return
              }
            }
          } else {
            // Reset silence timer on sound
            if (silenceStartTimeRef.current !== null) {
              console.log("[v0] Sound detected, resetting silence timer")
              silenceStartTimeRef.current = null
            }
          }
        }
      }

      // Continue checking
      animationFrameRef.current = requestAnimationFrame(checkSilence)
    }

    checkSilence()
  }, [stopRecording])

  const visualizeAudio = useCallback(() => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    let lastUpdate = 0
    const UPDATE_INTERVAL = 50 // Update every 50ms for smoother but not overwhelming updates

    const updateLevel = (currentTime: number) => {
      if (!analyserRef.current || !isRecordingRef.current) return

      // Throttle updates for better performance
      if (currentTime - lastUpdate >= UPDATE_INTERVAL) {
        analyserRef.current.getByteFrequencyData(dataArray)
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
        setAudioLevel(average / 255)
        lastUpdate = currentTime
      }

      requestAnimationFrame(updateLevel)
    }

    requestAnimationFrame(updateLevel)
  }, [])

  const sendAudioQuery = useCallback(async (audioBlob: Blob) => {
    if (!sessionId) {
      console.error("[v0] Cannot send audio query: no session ID")
      return
    }

    // Debounce requests to prevent spam
    const now = Date.now()
    if (now - lastRequestTime.current < REQUEST_DEBOUNCE_TIME) {
      console.log("[v0] Request debounced, too soon after last request")
      return
    }
    lastRequestTime.current = now

    // Check for pending request to avoid duplicates
    const requestKey = `query-${sessionId}`
    if (pendingRequests.current.has(requestKey)) {
      console.log("[v0] Request already pending, skipping duplicate")
      return
    }

    try {
      console.log("[v0] Sending audio query, sessionId:", sessionId, "language:", selectedLanguage, "blob size:", audioBlob.size)
      
      // Optimized base64 conversion using FileReader promise
      const base64Audio = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const base64 = reader.result as string
          resolve(base64.split(',')[1])
        }
        reader.onerror = reject
        reader.readAsDataURL(audioBlob)
      })

      console.log("[v0] Sending query to backend...")

      // Create and cache the request promise
      const requestPromise = fetch(`${API_BASE}/voice/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Connection": "keep-alive", // Reuse connections
        },
        body: JSON.stringify({
          session_id: sessionId,
          audio_base64: base64Audio,
          language: selectedLanguage.toLowerCase(),
        }),
      })

      pendingRequests.current.set(requestKey, requestPromise)

      const response = await requestPromise
      pendingRequests.current.delete(requestKey)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("[v0] Backend response received:", data)

      // Batch state updates for better performance
      const userMessage: Message = {
        id: Date.now().toString(),
        text: data.user_text || "...",
        sender: "user",
        timestamp: new Date(),
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.text_response || data.text,
        audio: data.audio_base64 || data.audio,
        sender: "assistant",
        timestamp: new Date(),
        isStreaming: true,
      }

      // Single state update for both messages
      setMessages((prev) => [...prev, userMessage, assistantMessage])

      // Play audio immediately without waiting
      if (data.audio_base64 || data.audio) {
        playAudio(data.audio_base64 || data.audio).catch(console.error)
      }

      // Optimize timing for better UX
      setTimeout(() => {
        setMessages((prev) => prev.map((msg) => ({ ...msg, isStreaming: false })))
        
        if (data.requires_camera) {
          setShowCamera(true)
        } else {
          setStatus("active")
        }
      }, 200) // Reduced delay

      setCurrentTranscript("")
    } catch (error) {
      console.error("[v0] Error sending audio query:", error)
      pendingRequests.current.delete(requestKey)
      setStatus("active")
      setCurrentTranscript("")
    }
  }, [sessionId, selectedLanguage])

  const processLanguageSelection = async (audioBlob: Blob, currentSessionId?: string) => {
    // Use passed sessionId or fallback to state
    const activeSessionId = currentSessionId || sessionId
    
    if (!activeSessionId) {
      console.error("[v0] No session ID for language selection - showing UI selector as fallback")
      setStatus("awaiting_language")
      setIsAutoRecording(false)
      setShowLanguageSelector(true)
      return
    }

    try {
      console.log("[v0] Processing language selection, sessionId:", activeSessionId, "audio blob size:", audioBlob.size)
      setStatus("processing")
      setIsAutoRecording(false)
      
      // Audio caching is now disabled globally

      // Convert audio blob to base64
      const reader = new FileReader()
      reader.readAsDataURL(audioBlob)
      
      const base64Audio = await new Promise<string>((resolve) => {
        reader.onloadend = () => {
          const base64 = reader.result as string
          const base64String = base64.split(',')[1]
          resolve(base64String)
        }
      })

      console.log("[v0] Sending to backend for language detection...")

      // Send to backend for language detection
      const response = await fetch(`${API_BASE}/voice/detect-language`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: activeSessionId,
          audio_base64: base64Audio,
        }),
      })

      const data = await response.json()
      console.log("[v0] Language detection response:", {
        language_detected: data.language_detected,
        language: data.language,
        text: data.text,
        hasAudio: !!data.audio,
        audioLength: data.audio ? data.audio.length : 0
      })

      if (data.language_detected && data.language) {
        // Language detected successfully
        const languageMap: { [key: string]: string } = {
          "english": "English",
          "hindi": "Hindi",
          "punjabi": "Punjabi",
          "marathi": "Marathi",
          "gujarati": "Gujarati",
          "tamil": "Tamil",
          "telugu": "Telugu",
          "kannada": "Kannada",
          "bengali": "Bengali",
        }

        const detectedLanguageName = languageMap[data.language] || "Hindi"
        console.log("[v0] Language detected:", data.language, "->", detectedLanguageName)
        setSelectedLanguage(detectedLanguageName)

        const confirmMessage: Message = {
          id: Date.now().toString(),
          text: data.text,
          audio: data.audio,
          sender: "assistant",
          timestamp: new Date(),
          isStreaming: true,
        }

        setMessages((prev) => [...prev, confirmMessage])

        if (data.audio) {
          console.log("[v0] Playing language confirmation audio, length:", data.audio.length)
          await playAudio(data.audio)
        } else {
          console.log("[v0] No audio in language detection response")
        }

        setTimeout(() => {
          setMessages((prev) => prev.map((msg) => ({ ...msg, isStreaming: false })))
          setStatus("active")
          setLanguageRetryCount(0)
          
          // Audio caching is disabled globally
          
          // Don't auto-start recording - let user initiate manually for better control
          // This prevents microphone conflicts and gives user time to understand
          console.log("[v0] Language detection complete - user can now start recording manually")
          // No auto-start recording here
        }, 1000)
      } else {
        // Language not detected, retry
        setLanguageRetryCount((prev) => prev + 1)
        
        if (languageRetryCount >= 2) {
          // After 3 retries, show UI selector
          setShowLanguageSelector(true)
          setStatus("awaiting_language")
          
          const fallbackMessage: Message = {
            id: Date.now().toString(),
            text: "कृपया नीचे दिए गए विकल्पों से अपनी भाषा चुनें। / Please select your language from the options below.",
            sender: "assistant",
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, fallbackMessage])
        } else {
          // Retry voice detection
          const retryMessage: Message = {
            id: Date.now().toString(),
            text: data.text || "कृपया फिर से अपनी भाषा बोलें। / Please speak your language again.",
            audio: data.audio,
            sender: "assistant",
            timestamp: new Date(),
            isStreaming: true,
          }

          setMessages((prev) => [...prev, retryMessage])

          if (data.audio) {
            await playAudio(data.audio)
          }

          setTimeout(() => {
            setMessages((prev) => prev.map((msg) => ({ ...msg, isStreaming: false })))
            setStatus("awaiting_language")
            // Auto-start recording again for retry
            setTimeout(() => {
              startRecordingForLanguage()
            }, 500)
          }, 1000)
        }
      }
    } catch (error) {
      console.error("[v0] Error processing language selection:", error)
      setLanguageRetryCount((prev) => prev + 1)
      
      if (languageRetryCount >= 2) {
        setShowLanguageSelector(true)
        setStatus("awaiting_language")
      } else {
        // Retry
        setTimeout(() => {
          startRecordingForLanguage()
        }, 1000)
      }
    }
  }

  const playAudio = useCallback(async (base64Audio: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      console.log("[v0] Playing audio (no caching), audio length:", base64Audio.length)
      
      // Always create a fresh audio element - no caching
      const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`)
      audio.preload = 'auto'
      
      audio.onplay = () => {
        console.log("[v0] Audio started playing")
        setIsSpeaking(true)
      }
      audio.onended = () => {
        console.log("[v0] Audio finished playing")
        setIsSpeaking(false)
        resolve()
      }
      audio.onerror = (e) => {
        console.error("[v0] Audio playback error:", e)
        setIsSpeaking(false)
        reject(e)
      }
      
      // Play immediately
      audio.play().catch(e => {
        console.error("[v0] Audio play error:", e)
        setIsSpeaking(false)
        reject(e)
      })
    })
  }, [])

  const handleLanguageSelection = async (languageName: string) => {
    if (!sessionId) return

    try {
      setStatus("processing")
      setShowLanguageSelector(false)

      // Map language name to code
      const languageMap: { [key: string]: string } = {
        "English": "english",
        "Hindi": "hindi",
        "Punjabi": "punjabi",
        "Marathi": "marathi",
        "Gujarati": "gujarati",
        "Tamil": "tamil",
        "Telugu": "telugu",
        "Kannada": "kannada",
        "Bengali": "bengali",
        "Malayalam": "malayalam"
      }

      const languageCode = languageMap[languageName] || "hindi"

      const response = await fetch(`${API_BASE}/voice/select-language`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          language: languageCode,
        }),
      })

      const data = await response.json()

      setSelectedLanguage(languageName)

      const confirmMessage: Message = {
        id: Date.now().toString(),
        text: data.text,
        audio: data.audio,
        sender: "assistant",
        timestamp: new Date(),
        isStreaming: true,
      }

      setMessages((prev) => [...prev, confirmMessage])

      if (data.audio) {
        await playAudio(data.audio)
      }

      setTimeout(() => {
        setMessages((prev) => prev.map((msg) => ({ ...msg, isStreaming: false })))
        setStatus("active")
        
        // Don't auto-start recording - let user click the microphone button
        console.log("[v0] Manual language selection complete - ready for user input")
      }, 400) // Reduced for faster flow
    } catch (error) {
      console.error("[v0] Error selecting language:", error)
      setStatus("awaiting_language")
      setShowLanguageSelector(true)
    }
  }

  const handleCameraDiagnosisComplete = async (diagnosis: string, audio: string) => {
    // Add diagnosis message
    const diagnosisMessage: Message = {
      id: Date.now().toString(),
      text: diagnosis,
      audio: audio,
      sender: "assistant",
      timestamp: new Date(),
      isStreaming: true,
    }

    setMessages((prev) => [...prev, diagnosisMessage])

    // Play diagnosis audio
    if (audio) {
      await playAudio(audio)
    }

    setTimeout(() => {
      setMessages((prev) => prev.map((msg) => ({ ...msg, isStreaming: false })))
      setStatus("active")
      setShowCamera(false)
    }, 500)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50/50 to-teal-50 flex items-center justify-center p-4 relative overflow-hidden">
      {showCamera && sessionId && (
        <CameraDiseaseDetector
          sessionId={sessionId}
          language={selectedLanguage.toLowerCase()}
          onClose={() => {
            setShowCamera(false)
            setStatus("active")
          }}
          onDiagnosisComplete={handleCameraDiagnosisComplete}
        />
      )}

      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-green-400/20 rounded-full blur-3xl animate-float" />
        <div
          className="absolute bottom-20 right-10 w-96 h-96 bg-emerald-400/20 rounded-full blur-3xl animate-float"
          style={{ animationDelay: "1s" }}
        />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-teal-400/10 rounded-full blur-3xl animate-pulse" />
      </div>

      <div className="w-full max-w-5xl relative z-10">
        <Card className="bg-white/95 backdrop-blur-xl shadow-2xl overflow-hidden border-2 border-green-200/50">
          <div className="relative bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 p-8 border-b border-white/20">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-30" />

            <div className="relative flex items-center justify-between">
              <div className="flex-1">
                <h1 className="text-4xl font-bold text-white text-balance mb-2 drop-shadow-lg">🌾 किसान सहायक</h1>
                <p className="text-white/95 text-lg text-pretty drop-shadow">AI-Powered Farming Intelligence</p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-white hover:bg-white/20 h-10 w-10 rounded-full"
                  onClick={() => setShowLanguageSelector(!showLanguageSelector)}
                >
                  <Languages className="h-5 w-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-white hover:bg-white/20 h-10 w-10 rounded-full"
                  onClick={() => setShowStats(!showStats)}
                >
                  <History className="h-5 w-5" />
                </Button>
                <Button variant="ghost" size="icon" className="text-white hover:bg-white/20 h-10 w-10 rounded-full">
                  <Settings className="h-5 w-5" />
                </Button>
              </div>
            </div>

            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm border border-white/30">
              <Languages className="h-4 w-4 text-white" />
              <span className="text-sm font-medium text-white">{selectedLanguage}</span>
            </div>
          </div>

          {showLanguageSelector && (
            <LanguageSelector
              selectedLanguage={selectedLanguage}
              onSelectLanguage={async (lang) => {
                await handleLanguageSelection(lang)
              }}
              onClose={() => setShowLanguageSelector(false)}
            />
          )}

          <div className="p-8 space-y-8">
            {status === "idle" ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-8">
                <div className="relative">
                  <div className="absolute inset-0 bg-green-500/30 rounded-full blur-3xl animate-pulse-ring" />
                  <div className="absolute inset-0 bg-emerald-400/20 rounded-full blur-2xl animate-ripple" />

                  <Button
                    size="lg"
                    onClick={startSession}
                    className="relative h-40 w-40 rounded-full text-xl font-bold shadow-2xl hover:shadow-green-500/50 transition-all duration-500 hover:scale-110 bg-gradient-to-br from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white border-4 border-white/30 group"
                  >
                    <div className="flex flex-col items-center gap-3">
                      <div className="relative">
                        <Mic className="h-16 w-16 transition-transform group-hover:scale-110" />
                        <div className="absolute inset-0 bg-white/20 rounded-full blur-xl group-hover:blur-2xl transition-all" />
                      </div>
                      <span className="text-lg drop-shadow-lg">Start</span>
                    </div>
                  </Button>
                </div>

                <div className="text-center space-y-4 max-w-2xl">
                  <p className="text-lg text-gray-700 text-pretty font-medium">
                    Tap the button to begin your conversation with the AI farming assistant
                  </p>

                  <div className="grid grid-cols-3 gap-4 mt-8">
                    <div className="p-4 rounded-xl bg-gradient-to-br from-green-100 to-green-50 border-2 border-green-200/50 hover:border-green-300 transition-all hover:shadow-lg">
                      <Volume2 className="h-8 w-8 text-green-600 mx-auto mb-2" />
                      <p className="text-sm font-semibold text-green-900">Voice First</p>
                      <p className="text-xs text-green-700 mt-1">Natural conversation</p>
                    </div>
                    <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-50 border-2 border-emerald-200/50 hover:border-emerald-300 transition-all hover:shadow-lg">
                      <Languages className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
                      <p className="text-sm font-semibold text-emerald-900">Multi-lingual</p>
                      <p className="text-xs text-emerald-700 mt-1">10+ languages</p>
                    </div>
                    <div className="p-4 rounded-xl bg-gradient-to-br from-teal-100 to-teal-50 border-2 border-teal-200/50 hover:border-teal-300 transition-all hover:shadow-lg">
                      <History className="h-8 w-8 text-teal-600 mx-auto mb-2" />
                      <p className="text-sm font-semibold text-teal-900">Smart Memory</p>
                      <p className="text-xs text-teal-700 mt-1">Context aware</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <>
                {showStats && <SessionStats messages={messages} sessionId={sessionId} />}

                <MessageList
                  messages={messages}
                  isThinking={status === "processing"}
                  isListening={status === "listening"}
                  isSpeaking={isSpeaking}
                  currentTranscript=""
                />

                {(status === "listening" || status === "processing") && (
                  <div className="space-y-4">
                    <AudioVisualizer isActive={status === "listening"} level={audioLevel} />
                    <div className="flex items-center justify-center gap-2">
                      <div
                        className={`h-2 w-2 rounded-full ${status === "listening" ? "bg-green-500 animate-pulse" : "bg-green-600 animate-pulse"}`}
                      />
                      <span className="text-sm font-medium text-gray-700">
                        {status === "listening" ? "Recording..." : "Processing..."}
                      </span>
                    </div>
                  </div>
                )}

                <div className="flex flex-col items-center gap-6 pt-6">
                  <div className="relative">
                    {(isRecording && status === "listening") && (
                      <>
                        <div className="absolute inset-0 bg-green-500/30 rounded-full blur-2xl animate-pulse-ring" />
                        <div className="absolute inset-0 bg-emerald-500/20 rounded-full blur-xl animate-ripple" />
                      </>
                    )}

                    {(status === "processing") ? (
                      <Button size="lg" disabled className="h-24 w-24 rounded-full shadow-xl relative bg-gradient-to-br from-green-600 to-emerald-600 text-white">
                        <Loader2 className="h-10 w-10 animate-spin" />
                      </Button>
                    ) : isSpeaking ? (
                      <Button 
                        size="lg" 
                        disabled 
                        className="h-24 w-24 rounded-full shadow-xl relative bg-gradient-to-br from-blue-600 to-blue-700 text-white opacity-75"
                      >
                        <Volume2 className="h-10 w-10 animate-pulse" />
                      </Button>
                    ) : (
                      <Button
                        size="lg"
                        onClick={isRecording ? stopRecording : startRecording}
                        disabled={isSpeaking}
                        className={`h-24 w-24 rounded-full transition-all duration-300 shadow-xl relative group border-4 border-white/50 ${
                          isRecording && status === "listening"
                            ? "bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white animate-pulse"
                            : "bg-gradient-to-br from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white hover:scale-105 hover:shadow-2xl"
                        } ${isSpeaking ? "opacity-75 cursor-not-allowed" : "opacity-100"}`}
                      >
                        {isRecording && status === "listening" ? (
                          <MicOff className="h-10 w-10 transition-transform group-hover:scale-110" />
                        ) : (
                          <Mic className="h-10 w-10 transition-transform group-hover:scale-110" />
                        )}
                      </Button>
                    )}
                  </div>

                  <div className="text-center space-y-2">
                    <p className="text-base font-semibold text-gray-800">
                      {status === "awaiting_language" && isAutoRecording && "🎤 Listening for your language... (Speak clearly)"}
                      {status === "awaiting_language" && !isAutoRecording && "🌐 Please select your preferred language"}
                      {status === "listening" && "🎤 Listening... (Auto-stop after 3s silence)"}
                      {status === "processing" && "⚡ Processing your request..."}
                      {status === "active" && !isSpeaking && "🎤 Ready to listen - Tap microphone to speak"}
                      {status === "active" && isSpeaking && "🔊 Playing response..."}
                    </p>
                    <p className="text-sm text-gray-600">
                      {status === "active" && !isSpeaking && "Ask about farming, crops, weather, or plant diseases"}
                      {status === "listening" && "Speak clearly - will auto-stop after silence"}
                      {status === "awaiting_language" && isAutoRecording && "Not working? Tap 'Skip' to select manually"}
                      {isSpeaking && "Please wait for response to finish"}
                    </p>
                    
                    {/* Manual language selection fallback */}
                    {status === "awaiting_language" && isAutoRecording && (
                      <div className="mt-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            stopRecording()
                            setIsAutoRecording(false)
                            setShowLanguageSelector(true)
                          }}
                          className="bg-white/80 hover:bg-white border-green-300 text-green-700 hover:text-green-800"
                        >
                          Skip Voice Detection
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
