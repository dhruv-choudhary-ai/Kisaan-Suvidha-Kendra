/**
 * AI Service for Kisaan Suvidha Kendra - Agriculture Voice Assistant
 * Integrates with Kisaan backend for farmer assistance
 * Handles multilingual support and agricultural queries
 */

import kisaanService from './kisaanService'

// Kisaan Suvidha Kendra context and knowledge base
const KISAAN_CONTEXT = `
You are a helpful assistant at Kisaan Suvidha Kendra (Farmer Service Center).

ABOUT KISAAN SUVIDHA KENDRA:
- Government initiative to support farmers across India
- Provides agricultural information, market prices, weather forecasts
- Helps with crop disease diagnosis, fertilizer recommendations
- Connects farmers to government schemes and subsidies
- Available in multiple regional languages (Hindi, Punjabi, Marathi, Gujarati, Tamil, Telugu, Kannada, Bengali)

KEY SERVICES:
1. Crop Advisory - Best practices, sowing times, harvest guidance
2. Disease Detection - Camera-based crop disease diagnosis
3. Market Information - Real-time mandi prices, commodity rates
4. Weather Forecasts - Localized weather predictions
5. Government Schemes - PM-KISAN, crop insurance, subsidies
6. Fertilizer & Pesticide Recommendations - Soil-specific guidance

PERSONA AWARENESS:
- Farmers: Focus on practical farming advice, local market prices, weather
- Agriculture Officers: Policy information, scheme implementation, area statistics
- Traders/Buyers: Market trends, commodity availability, wholesale rates
- Students/Researchers: Agricultural techniques, crop science, research data

CONVERSATION STYLE:
- Warm, respectful, and supportive (treat farmers with dignity)
- Keep responses BRIEF: Default to 2-3 sentences
- Use simple language appropriate for rural audiences
- Only provide detailed explanations when explicitly requested
- Remember context from previous interactions
- Ask clarifying questions when needed

CRITICAL SPEECH OUTPUT RULES:
- DO NOT use markdown formatting (no **, *, _, etc.)
- DO NOT use emojis of any kind
- DO NOT use special characters like #, ###, >, -, •, etc.
- Use plain text only for natural speech
- Write numbers as words when appropriate
`

// Conversation memory storage
class ConversationMemory {
  constructor() {
    this.sessions = new Map()
  }

  getSession(sessionId) {
    if (!this.sessions.has(sessionId)) {
      this.sessions.set(sessionId, {
        messages: [],
        userInfo: {},
        detectedPersona: null,
        context: {},
        createdAt: new Date(),
        lastActivity: new Date()
      })
    }
    return this.sessions.get(sessionId)
  }

  addMessage(sessionId, role, content) {
    const session = this.getSession(sessionId)
    session.messages.push({
      role,
      content,
      timestamp: new Date()
    })
    session.lastActivity = new Date()
    
    // Keep only last 20 messages for context window management
    if (session.messages.length > 20) {
      session.messages = session.messages.slice(-20)
    }
  }

  updateUserInfo(sessionId, info) {
    const session = this.getSession(sessionId)
    session.userInfo = { ...session.userInfo, ...info }
  }

  updatePersona(sessionId, persona) {
    const session = this.getSession(sessionId)
    session.detectedPersona = persona
  }

  getConversationHistory(sessionId) {
    const session = this.getSession(sessionId)
    return session.messages
  }

  clearSession(sessionId) {
    this.sessions.delete(sessionId)
  }

  // Clean up old sessions (older than 24 hours)
  cleanup() {
    const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000)
    for (const [sessionId, session] of this.sessions.entries()) {
      if (session.lastActivity < cutoff) {
        this.sessions.delete(sessionId)
      }
    }
  }
}

// Global memory instance
const conversationMemory = new ConversationMemory()

// Clean up old sessions periodically
setInterval(() => {
  conversationMemory.cleanup()
}, 60 * 60 * 1000) // Every hour

/**
 * Generate session ID - uses Kisaan backend session
 */
function generateSessionId() {
  const sessionInfo = kisaanService.getSessionInfo()
  if (sessionInfo.sessionId) {
    return sessionInfo.sessionId
  }
  
  // Fallback to browser session
  if (!sessionStorage.getItem('kioskSessionId')) {
    sessionStorage.setItem('kioskSessionId', 
      'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    )
  }
  return sessionStorage.getItem('kioskSessionId')
}

/**
 * Detect if user is asking for detailed explanation
 */
function isRequestingDetail(message) {
  const detailPhrases = [
    'tell me more',
    'explain in detail',
    'elaborate',
    'expand on',
    'more information',
    'can you explain',
    'tell me about',
    'what are',
    'how does',
    'describe',
    'details about'
  ]
  
  const lowerMessage = message.toLowerCase()
  return detailPhrases.some(phrase => lowerMessage.includes(phrase))
}

/**
 * Extract user information from conversation
 */
function extractUserInfo(message) {
  const info = {}
  
  // Extract name patterns
  const namePatterns = [
    /my name is (\w+)/i,
    /i'm (\w+)/i,
    /call me (\w+)/i,
    /this is (\w+)/i
  ]
  
  for (const pattern of namePatterns) {
    const match = message.match(pattern)
    if (match) {
      info.name = match[1]
      break
    }
  }

  // Extract company/organization
  const companyPatterns = [
    /i work at (\w+)/i,
    /from (\w+) company/i,
    /represent (\w+)/i,
    /i'm with (\w+)/i
  ]
  
  for (const pattern of companyPatterns) {
    const match = message.match(pattern)
    if (match) {
      info.company = match[1]
      break
    }
  }

  return info
}

/**
 * Main AI service function - Now uses Kisaan backend
 */
export async function getAIResponse(userMessage, detectedPersona = null) {
  const sessionId = generateSessionId()
  const session = conversationMemory.getSession(sessionId)
  
  // Update persona if detected
  if (detectedPersona && detectedPersona !== session.detectedPersona) {
    conversationMemory.updatePersona(sessionId, detectedPersona)
  }

  // Extract and store user information
  const userInfo = extractUserInfo(userMessage)
  if (Object.keys(userInfo).length > 0) {
    conversationMemory.updateUserInfo(sessionId, userInfo)
  }

  // Add user message to memory
  conversationMemory.addMessage(sessionId, 'user', userMessage)

  try {
    // Send query to Kisaan backend
    console.log('🌾 Sending query to Kisaan backend:', userMessage)
    const result = await kisaanService.sendTextQuery(userMessage)
    
    // Store AI response in memory
    conversationMemory.addMessage(sessionId, 'assistant', result.response)

    return {
      response: result.response,
      session: session,
      sessionId: sessionId,
      requires_camera: result.requiresCamera || false,
      requires_images: result.requiresImages || false,
      image_urls: result.imageUrls || [],
      responseData: result.responseData || null,
      language: result.language
    }
  } catch (error) {
    console.error('Kisaan backend error:', error)
    
    // Fallback response
    const fallbackResponse = "I'm sorry, I'm having trouble connecting to the service. Please try again."
    conversationMemory.addMessage(sessionId, 'assistant', fallbackResponse)
    
    return {
      response: fallbackResponse,
      session: session,
      sessionId: sessionId,
      requires_camera: false
    }
  }
}

/**
 * Get conversation history for a session
 */
export function getConversationHistory(sessionId = null) {
  if (!sessionId) {
    sessionId = generateSessionId()
  }
  return conversationMemory.getConversationHistory(sessionId)
}

/**
 * Clear conversation session
 */
export function clearSession(sessionId = null) {
  if (!sessionId) {
    sessionId = generateSessionId()
  }
  conversationMemory.clearSession(sessionId)
  sessionStorage.removeItem('kioskSessionId')
  
  // Also clear Kisaan backend session
  kisaanService.clearSession().catch(err => {
    console.warn('Failed to clear Kisaan session:', err)
  })
}

/**
 * Check if user is returning visitor
 */
export function isReturningUser() {
  const sessionInfo = kisaanService.getSessionInfo()
  return sessionInfo.sessionId !== null || sessionStorage.getItem('kioskSessionId') !== null
}

/**
 * Handle wake word detection
 */
export function handleWakeWord() {
  const sessionId = generateSessionId()
  const session = conversationMemory.getSession(sessionId)
  
  // Return appropriate greeting based on context
  if (session.userInfo.name) {
    return `Namaste ${session.userInfo.name}! Main aapki kaise madad kar sakta hoon?`
  } else if (session.messages.length > 0) {
    return "Namaste! Main phir se aapki madad karne ke liye hazir hoon. Kya janna chahte hain?"
  } else {
    return "Namaste! Main Kisaan Suvidha Kendra ka sahayak hoon. Aap mujhse kheti, mandi bhav, mausam ya kisi bhi krishi samasya ke bare mein pooch sakte hain."
  }
}

export default {
  getAIResponse,
  getConversationHistory,
  clearSession,
  isReturningUser,
  handleWakeWord
}
