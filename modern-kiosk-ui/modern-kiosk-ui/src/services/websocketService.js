/**
 * WebSocket Service for Real-Time Voice Streaming
 * Connects to Kisaan backend /ws/voice endpoint for streaming audio and transcription
 */

class WebSocketVoiceService {
  constructor() {
    this.ws = null
    this.sessionId = null
    this.language = 'hindi'
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 2000
    
    // Callbacks
    this.onTranscriptCallback = null
    this.onResponseCallback = null
    this.onErrorCallback = null
    this.onConnectedCallback = null
    this.onDisconnectedCallback = null
    
    // Audio recording
    this.mediaRecorder = null
    this.audioStream = null
    this.isRecording = false
  }

  /**
   * Set callback functions
   */
  setCallbacks({
    onTranscript = null,
    onResponse = null,
    onError = null,
    onConnected = null,
    onDisconnected = null
  }) {
    this.onTranscriptCallback = onTranscript
    this.onResponseCallback = onResponse
    this.onErrorCallback = onError
    this.onConnectedCallback = onConnected
    this.onDisconnectedCallback = onDisconnected
  }

  /**
   * Connect to WebSocket server
   */
  async connect(sessionId, language = 'hindi') {
    if (this.isConnected) {
      console.log('⚠️ WebSocket already connected')
      return
    }

    this.sessionId = sessionId
    this.language = language

    try {
      // Determine WebSocket URL (ws:// for development, wss:// for production)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}/ws/voice`

      console.log('🔌 Connecting to WebSocket:', wsUrl)

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected')
        this.isConnected = true
        this.reconnectAttempts = 0

        // Send start message with session info
        this.send({
          type: 'start',
          session_id: this.sessionId,
          language: this.language
        })

        if (this.onConnectedCallback) {
          this.onConnectedCallback()
        }
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        if (this.onErrorCallback) {
          this.onErrorCallback('WebSocket connection error')
        }
      }

      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected')
        this.isConnected = false

        if (this.onDisconnectedCallback) {
          this.onDisconnectedCallback()
        }

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`🔄 Reconnecting... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
          setTimeout(() => {
            this.connect(this.sessionId, this.language)
          }, this.reconnectDelay * this.reconnectAttempts)
        }
      }
    } catch (error) {
      console.error('❌ Failed to connect WebSocket:', error)
      if (this.onErrorCallback) {
        this.onErrorCallback('Failed to establish connection')
      }
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(message) {
    console.log('📨 WebSocket message:', message.type)

    switch (message.type) {
      case 'started':
        console.log('✅ Session started:', message.session_id, message.language)
        break

      case 'transcript':
        // Partial or final transcript from speech recognition
        if (this.onTranscriptCallback) {
          this.onTranscriptCallback(message.text, message.is_final)
        }
        break

      case 'response':
        // AI response with audio
        if (this.onResponseCallback) {
          this.onResponseCallback({
            text: message.text,
            audio: message.audio,
            requires_camera: message.requires_camera,
            requires_images: message.requires_images,
            image_urls: message.image_urls,
            language: message.language
          })
        }
        break

      case 'error':
        console.error('❌ Server error:', message.message)
        if (this.onErrorCallback) {
          this.onErrorCallback(message.message)
        }
        break

      case 'stopped':
        console.log('⏹️ Session stopped')
        break

      default:
        console.warn('⚠️ Unknown message type:', message.type)
    }
  }

  /**
   * Send message to WebSocket server
   */
  send(message) {
    if (!this.isConnected || !this.ws) {
      console.error('❌ Cannot send - WebSocket not connected')
      return false
    }

    try {
      this.ws.send(JSON.stringify(message))
      return true
    } catch (error) {
      console.error('❌ Error sending message:', error)
      return false
    }
  }

  /**
   * Start audio recording and streaming
   */
  async startRecording() {
    if (this.isRecording) {
      console.log('⚠️ Already recording')
      return
    }

    try {
      // Request microphone access
      this.audioStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })

      // Create MediaRecorder with appropriate codec
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
        ? 'audio/webm;codecs=opus' 
        : 'audio/webm'
      
      this.mediaRecorder = new MediaRecorder(this.audioStream, {
        mimeType: mimeType,
        audioBitsPerSecond: 16000
      })

      // Send audio chunks to WebSocket
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && this.isConnected) {
          // Convert blob to base64 and send
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1]
            this.send({
              type: 'audio',
              data: base64Audio
            })
          }
          reader.readAsDataURL(event.data)
        }
      }

      this.mediaRecorder.onerror = (error) => {
        console.error('❌ MediaRecorder error:', error)
        this.stopRecording()
      }

      // Start recording with 100ms chunks for real-time streaming
      this.mediaRecorder.start(100)
      this.isRecording = true
      console.log('🎤 Recording started')
    } catch (error) {
      console.error('❌ Error starting recording:', error)
      if (this.onErrorCallback) {
        this.onErrorCallback('Failed to access microphone')
      }
    }
  }

  /**
   * Stop audio recording
   */
  stopRecording() {
    if (!this.isRecording) {
      return
    }

    try {
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop()
      }

      if (this.audioStream) {
        this.audioStream.getTracks().forEach(track => track.stop())
        this.audioStream = null
      }

      this.isRecording = false
      console.log('🛑 Recording stopped')
    } catch (error) {
      console.error('❌ Error stopping recording:', error)
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    this.stopRecording()

    if (this.isConnected && this.ws) {
      // Send stop message
      this.send({ type: 'stop' })
      
      // Close WebSocket
      this.ws.close()
      this.ws = null
      this.isConnected = false
    }

    console.log('🔌 WebSocket disconnected')
  }

  /**
   * Change language mid-session
   */
  changeLanguage(language) {
    this.language = language
    if (this.isConnected) {
      this.send({
        type: 'change_language',
        language: language
      })
    }
  }

  /**
   * Check connection status
   */
  isConnectionActive() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

// Export singleton instance
const websocketService = new WebSocketVoiceService()
export default websocketService
