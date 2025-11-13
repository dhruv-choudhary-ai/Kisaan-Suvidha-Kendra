/**
 * Avatar Video Stream Integration
 * Connects React UI to avatar video stream
 */

/**
 * Sanitize text for speech output
 * Removes markdown, emojis, and special characters that mess up speech
 * @param {string} text - Text to sanitize
 * @returns {string} Clean text for speech
 */
function sanitizeForSpeech(text) {
  if (!text) return ''
  
  let cleaned = text
  
  // Remove markdown bold/italic
  cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, '$1') // **text** -> text
  cleaned = cleaned.replace(/\*([^*]+)\*/g, '$1')     // *text* -> text
  cleaned = cleaned.replace(/__([^_]+)__/g, '$1')     // __text__ -> text
  cleaned = cleaned.replace(/_([^_]+)_/g, '$1')       // _text_ -> text
  
  // Remove markdown headers
  cleaned = cleaned.replace(/^#{1,6}\s+/gm, '')       // ### Header -> Header
  
  // Remove bullet points and list markers
  cleaned = cleaned.replace(/^[\s]*[-*•]\s+/gm, '')   // - item -> item
  cleaned = cleaned.replace(/^\d+\.\s+/gm, '')        // 1. item -> item
  
  // Remove emojis (most common ranges)
  cleaned = cleaned.replace(/[\u{1F600}-\u{1F64F}]/gu, '') // Emoticons
  cleaned = cleaned.replace(/[\u{1F300}-\u{1F5FF}]/gu, '') // Symbols & Pictographs
  cleaned = cleaned.replace(/[\u{1F680}-\u{1F6FF}]/gu, '') // Transport & Map
  cleaned = cleaned.replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '') // Flags
  cleaned = cleaned.replace(/[\u{2600}-\u{26FF}]/gu, '')   // Misc symbols
  cleaned = cleaned.replace(/[\u{2700}-\u{27BF}]/gu, '')   // Dingbats
  cleaned = cleaned.replace(/[\u{1F900}-\u{1F9FF}]/gu, '') // Supplemental Symbols
  cleaned = cleaned.replace(/[\u{1FA70}-\u{1FAFF}]/gu, '') // Symbols and Pictographs Extended-A
  
  // Remove other markdown syntax
  cleaned = cleaned.replace(/`([^`]+)`/g, '$1')       // `code` -> code
  cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // [text](url) -> text
  
  // Replace "CoE" with "COE" for proper pronunciation
  cleaned = cleaned.replace(/\bCoE\b/g, 'COE')
  
  // Replace rupee symbol with word
  cleaned = cleaned.replace(/₹(\d+)/g, '$1 rupees')   // ₹25 -> 25 rupees
  cleaned = cleaned.replace(/₹/g, 'rupees')           // ₹ -> rupees
  
  // Replace common abbreviations for better speech
  cleaned = cleaned.replace(/\bGovt\./g, 'Government')
  cleaned = cleaned.replace(/\bHon'ble\b/g, 'Honourable')
  cleaned = cleaned.replace(/\bMoU\b/g, 'M O U')
  cleaned = cleaned.replace(/\bMSMEs\b/g, 'M S M Es')
  cleaned = cleaned.replace(/\bAI\b/g, 'A I')
  cleaned = cleaned.replace(/\bIoT\b/g, 'I o T')
  cleaned = cleaned.replace(/\bGTM\b/g, 'Go To Market')
  cleaned = cleaned.replace(/\bIP\b/g, 'Intellectual Property')
  
  // Remove extra whitespace and newlines
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n')        // Max 2 newlines
  cleaned = cleaned.replace(/[ \t]{2,}/g, ' ')        // Single spaces only
  cleaned = cleaned.trim()
  
  return cleaned
}

// Configuration
const STREAM_CONFIG = {
  // WebRTC Stream URL - RunPod deployment
  streamUrl: 'https://jltzsxc1c8xlp3-8010.proxy.runpod.net/live/livestream.flv',
  
  // Alternative URLs depending on your setup:
  // HLS: 'https://jltzsxc1c8xlp3-8010.proxy.runpod.net/live/livestream.m3u8'
  // WebRTC: 'webrtc://jltzsxc1c8xlp3-8010.proxy.runpod.net/live/livestream'
  
  // Avatar API endpoint - RunPod deployment
  apiEndpoint: 'https://jltzsxc1c8xlp3-8010.proxy.runpod.net',
  
  // Session ID for multi-user support
  sessionId: 0
}

/**
 * Initialize avatar video stream
 * @param {HTMLVideoElement} videoElement - The video element to attach stream
 * @returns {Promise<void>}
 */
export async function initializeAvatarStream(videoElement) {
  if (!videoElement) {
    console.error('Video element not provided')
    return
  }

  try {
    console.log('🎥 Initializing avatar video stream...')
    
    // Check if using WebRTC
    if (window.SrsRtcPlayerAsync) {
      await initWebRTCStream(videoElement)
    } else {
      // Fallback to standard video source
      await initStandardStream(videoElement)
    }
    
    console.log('✅ Avatar stream initialized')
  } catch (error) {
    console.error('❌ Failed to initialize avatar stream:', error)
    throw error
  }
}

/**
 * Initialize WebRTC stream
 */
async function initWebRTCStream(videoElement) {
  console.log('📡 Setting up WebRTC stream...')
  
  // Load SRS SDK if not already loaded
  if (!window.SrsRtcPlayerAsync) {
    await loadSrsSDK()
  }
  
  const sdk = new window.SrsRtcPlayerAsync()
  
  return new Promise((resolve, reject) => {
    sdk.play('webrtc://jltzsxc1c8xlp3-8010.proxy.runpod.net/live/livestream').then((session) => {
      console.log('✅ WebRTC session established:', session)
      
      // Attach stream to video element
      videoElement.srcObject = session.stream
      videoElement.play()
      
      resolve()
    }).catch((error) => {
      console.error('WebRTC connection failed:', error)
      reject(error)
    })
  })
}

/**
 * Initialize standard video stream (HLS/FLV fallback)
 */
async function initStandardStream(videoElement) {
  console.log('📺 Setting up standard video stream...')
  
  // For HLS streams
  if (window.Hls && window.Hls.isSupported()) {
    const hls = new window.Hls()
    hls.loadSource('https://jltzsxc1c8xlp3-8010.proxy.runpod.net/live/livestream.m3u8')
    hls.attachMedia(videoElement)
    
    return new Promise((resolve, reject) => {
      hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
        videoElement.play()
        resolve()
      })
      
      hls.on(window.Hls.Events.ERROR, (event, data) => {
        console.error('HLS Error:', data)
        reject(data)
      })
    })
  }
  
  // Fallback: Direct video source
  videoElement.src = STREAM_CONFIG.streamUrl
  await videoElement.play()
}

/**
 * Load SRS SDK dynamically
 */
function loadSrsSDK() {
  return new Promise((resolve, reject) => {
    if (window.SrsRtcPlayerAsync) {
      resolve()
      return
    }
    
    const script = document.createElement('script')
    script.src = '/srs.sdk.js' // Make sure this file is in public folder
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

/**
 * Get the current session ID from the hidden input (set by client.js during WebRTC negotiation)
 * @returns {number}
 */
export function getSessionId() {
  const sessionIdElement = document.getElementById('sessionid')
  if (!sessionIdElement) {
    console.warn('⚠️ Session ID element not found in DOM!')
    return 0
  }
  
  const rawValue = sessionIdElement.value
  const sessionId = parseInt(rawValue, 10)
  
  console.log('🔍 getSessionId() - Raw value:', rawValue, '-> Parsed:', sessionId, '-> Valid:', !isNaN(sessionId))
  
  // Return 0 if parsing failed or value is NaN
  return isNaN(sessionId) ? 0 : sessionId
}

/**
 * Send text to avatar for speech synthesis
 * @param {string} text - Text to speak
 * @param {number} sessionId - Session ID (optional, will auto-detect from DOM if not provided)
 * @returns {Promise<void>}
 */
export async function sendTextToAvatar(text, sessionId = null) {
  try {
    // Sanitize text for speech (remove markdown, emojis, etc.)
    const cleanText = sanitizeForSpeech(text)
    
    if (!cleanText) {
      console.warn('⚠️ No text to send after sanitization')
      return
    }
    
    // Auto-detect session ID from DOM if not provided
    let actualSessionId = sessionId
    
    if (sessionId === null) {
      actualSessionId = getSessionId()
      
      // Extra debugging: Check DOM directly
      const elem = document.getElementById('sessionid')
      console.log('🔍 Direct DOM check - element exists:', !!elem, 'value:', elem?.value)
    }
    
    // CRITICAL: Don't send if session ID is 0 or invalid
    if (!actualSessionId || actualSessionId === 0) {
      console.error('❌ Cannot send text - invalid session ID:', actualSessionId)
      console.error('❌ WebRTC may not be connected yet. Wait for valid session ID.')
      // Don't emit speaking event if we can't send
      return
    }
    
    console.log('🗣️ Original text:', text)
    console.log('🧹 Sanitized text:', cleanText)
    console.log('📋 Using sessionid:', actualSessionId)

    // Detect language for speech synthesis
    const containsHindiChars = /[\u0900-\u097F]/.test(cleanText)
    const containsEnglishChars = /[a-zA-Z]/.test(cleanText)
    const speechLanguage = containsHindiChars ? 'hi' : 'en' // Hindi for Hinglish, English for pure English

    console.log('🌐 Text language analysis:', {
      containsHindi: containsHindiChars,
      containsEnglish: containsEnglishChars,
      speechLanguage: speechLanguage === 'hi' ? 'Hindi (for Hinglish)' : 'English'
    })
    
    // Emit avatar-speaking-start event
    window.dispatchEvent(new CustomEvent('avatar-speaking-start'))
    
    const response = await fetch(`${STREAM_CONFIG.apiEndpoint}/human`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: cleanText, // Use sanitized text
        type: 'echo',
        interrupt: true,
        sessionid: actualSessionId,
        language: speechLanguage // Use detected language (hi for Hinglish, en for English)
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ Text sent successfully:', data)
    
    // Start monitoring avatar speaking status
    monitorAvatarSpeaking(actualSessionId)
    
    return data
  } catch (error) {
    console.error('❌ Error sending text to avatar:', error)
    // Emit avatar-speaking-end event on error
    window.dispatchEvent(new CustomEvent('avatar-speaking-end'))
    throw error
  }
}

/**
 * Monitor avatar speaking status and emit event when finished
 * @param {number} sessionId - Session ID
 */
let monitoringInterval = null
let hasEmittedEndEvent = false // Flag to prevent multiple event emissions

function monitorAvatarSpeaking(sessionId) {
  // Clear any existing monitoring
  if (monitoringInterval) {
    clearInterval(monitoringInterval)
    monitoringInterval = null
  }
  
  // Reset flag when starting new monitoring
  hasEmittedEndEvent = false
  
  let checkCount = 0
  let consecutiveNotSpeaking = 0
  const maxChecks = 200 // Max 200 checks (100 seconds at 500ms intervals)
  const requiredNotSpeakingChecks = 3 // Require 3 consecutive "not speaking" checks to confirm finished
  
  // Wait 1 second before starting to monitor (give avatar time to start speaking)
  setTimeout(() => {
    if (hasEmittedEndEvent) {
      console.log('⚠️ Already emitted end event, skipping monitoring')
      return
    }
    
    monitoringInterval = setInterval(async () => {
      checkCount++
      
      const speaking = await isAvatarSpeaking(sessionId)
      console.log(`🔍 Avatar speaking status: ${speaking} (check ${checkCount})`)
      
      if (!speaking) {
        consecutiveNotSpeaking++
        console.log(`⏳ Not speaking count: ${consecutiveNotSpeaking}/${requiredNotSpeakingChecks}`)
        
        // Only emit finished event after multiple consecutive checks confirm it
        if (consecutiveNotSpeaking >= requiredNotSpeakingChecks || checkCount >= maxChecks) {
          if (!hasEmittedEndEvent) {
            console.log('✅ Avatar finished speaking (confirmed)')
            hasEmittedEndEvent = true
            clearInterval(monitoringInterval)
            monitoringInterval = null
            
            // Emit avatar-speaking-end event ONCE
            window.dispatchEvent(new CustomEvent('avatar-speaking-end'))
          }
        }
      } else {
        // Reset counter if avatar is speaking
        consecutiveNotSpeaking = 0
      }
    }, 800) // Check every 800ms (slower to reduce false positives)
  }, 1000) // Wait 1 second before starting monitoring
}

/**
 * Check if avatar is currently speaking
 * @param {number} sessionId - Session ID (optional, will auto-detect from DOM if not provided)
 * @returns {Promise<boolean>}
 */
export async function isAvatarSpeaking(sessionId = null) {
  try {
    // Auto-detect session ID from DOM if not provided
    const actualSessionId = sessionId !== null ? sessionId : getSessionId()
    
    // Don't check if session ID is 0 or invalid
    if (!actualSessionId || actualSessionId === 0) {
      console.warn('⚠️ Invalid session ID, assuming not speaking')
      return false
    }
    
    const response = await fetch(`${STREAM_CONFIG.apiEndpoint}/is_speaking`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ sessionid: actualSessionId })
    })
    
    if (!response.ok) {
      console.warn(`⚠️ /is_speaking returned ${response.status}, assuming not speaking`)
      return false
    }
    
    const data = await response.json()
    return data.code === 0 ? data.data : false
  } catch (error) {
    console.warn('⚠️ Error checking avatar status (assuming not speaking):', error.message)
    return false
  }
}

/**
 * Wait for avatar to finish speaking
 * @param {number} sessionId - Session ID (optional, will auto-detect from DOM if not provided)
 * @param {number} maxAttempts - Maximum polling attempts
 * @returns {Promise<void>}
 */
export async function waitForAvatarToFinish(sessionId = null, maxAttempts = 100) {
  let attempts = 0
  // Auto-detect session ID from DOM if not provided
  const actualSessionId = sessionId !== null ? sessionId : getSessionId()
  
  return new Promise((resolve) => {
    const checkStatus = async () => {
      if (attempts >= maxAttempts) {
        console.warn('⏰ Avatar check timeout')
        resolve()
        return
      }
      
      const speaking = await isAvatarSpeaking(actualSessionId)
      
      if (!speaking) {
        console.log('✅ Avatar finished speaking')
        resolve()
      } else {
        attempts++
        setTimeout(checkStatus, 300)
      }
    }
    
    setTimeout(checkStatus, 800)
  })
}

/**
 * Send text and wait for avatar to finish speaking
 * @param {string} text - Text to speak
 * @param {number} sessionId - Session ID (optional, will auto-detect from DOM if not provided)
 * @returns {Promise<void>}
 */
export async function speakAndWait(text, sessionId = null) {
  // Auto-detect session ID from DOM if not provided
  const actualSessionId = sessionId !== null ? sessionId : getSessionId()
  await sendTextToAvatar(text, actualSessionId)
  await waitForAvatarToFinish(actualSessionId)
}

/**
 * Interrupt/stop avatar speaking
 * @param {number} sessionId - Session ID (optional, will auto-detect from DOM if not provided)
 * @returns {Promise<void>}
 */
export async function interruptAvatar(sessionId = null) {
  try {
    // Auto-detect session ID from DOM if not provided
    const actualSessionId = sessionId !== null ? sessionId : getSessionId()
    
    console.log('⏸️ Interrupting avatar speech...')
    
    // Clear monitoring interval
    if (monitoringInterval) {
      clearInterval(monitoringInterval)
      monitoringInterval = null
    }
    
    // Send empty text with interrupt flag to stop current speech
    const response = await fetch(`${STREAM_CONFIG.apiEndpoint}/human`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: '',
        type: 'echo',
        interrupt: true,
        sessionid: actualSessionId
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    console.log('✅ Avatar interrupted')
    
    // Emit avatar-speaking-end event
    window.dispatchEvent(new CustomEvent('avatar-speaking-end'))
    
    return await response.json()
  } catch (error) {
    console.error('❌ Error interrupting avatar:', error)
    throw error
  }
}

export default {
  initializeAvatarStream,
  sendTextToAvatar,
  isAvatarSpeaking,
  waitForAvatarToFinish,
  speakAndWait,
  getSessionId,
  interruptAvatar,
  STREAM_CONFIG
}

