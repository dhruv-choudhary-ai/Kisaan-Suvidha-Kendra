/**
 * Kisaan Service - Agriculture Assistant Integration
 * Handles voice queries to Kisaan Suvidha Kendra backend
 */

import apiService from './api'

class KisaanService {
  constructor() {
    this.currentSessionId = null
    this.currentLanguage = 'hindi'
    this.conversationHistory = []
  }

  /**
   * Initialize a new session with the backend
   */
  async initializeSession() {
    try {
      console.log('🌾 Initializing Kisaan session...')
      const response = await apiService.startVoiceSession()
      
      this.currentSessionId = response.session_id
      this.currentLanguage = response.language || 'hindi'
      
      console.log(`✅ Session started: ${this.currentSessionId}`)
      
      return {
        sessionId: this.currentSessionId,
        greeting: response.text,
        audio: response.audio,
        language: response.language
      }
    } catch (error) {
      console.error('Failed to initialize session:', error)
      throw error
    }
  }

  /**
   * Select language for the session
   */
  async selectLanguage(language) {
    if (!this.currentSessionId) {
      throw new Error('No active session. Call initializeSession first.')
    }

    try {
      console.log(`🗣️ Selecting language: ${language}`)
      const response = await apiService.selectLanguage(this.currentSessionId, language)
      
      this.currentLanguage = language
      
      return {
        confirmation: response.text,
        audio: response.audio,
        language: response.language
      }
    } catch (error) {
      console.error('Failed to select language:', error)
      throw error
    }
  }

  /**
   * Send text query to Kisaan backend
   * Note: This converts text to the format expected by the voice API
   */
  async sendTextQuery(text, language = null) {
    if (!this.currentSessionId) {
      await this.initializeSession()
    }

    const queryLanguage = language || this.currentLanguage

    try {
      console.log(`📤 Sending query: ${text} (${queryLanguage})`)
      
      // For text queries, we'll encode as empty audio and use the text directly
      // In a real implementation, you might want to add a text-only endpoint
      const response = await apiService.sendVoiceQuery(
        this.currentSessionId,
        '', // Empty audio for text queries
        queryLanguage
      )

      // Add to conversation history
      this.conversationHistory.push({
        user: text,
        assistant: response.text_response,
        timestamp: new Date().toISOString()
      })

      return {
        response: response.text_response,
        audio: response.audio_base64,
        userText: text,
        requiresCamera: response.requires_camera || false,
        requiresImages: response.requires_images || false,
        imageUrls: response.image_urls || [],
        responseData: response,
        language: response.language
      }
    } catch (error) {
      console.error('Failed to send query:', error)
      throw error
    }
  }

  /**
   * Send voice query (audio) to backend
   */
  async sendVoiceQuery(audioBase64, language = null) {
    if (!this.currentSessionId) {
      await this.initializeSession()
    }

    const queryLanguage = language || this.currentLanguage

    try {
      console.log(`🎤 Sending voice query (${queryLanguage})`)
      
      const response = await apiService.sendVoiceQuery(
        this.currentSessionId,
        audioBase64,
        queryLanguage
      )

      // Add to conversation history
      this.conversationHistory.push({
        user: response.user_text || '[Voice input]',
        assistant: response.text_response,
        timestamp: new Date().toISOString()
      })

      return {
        response: response.text_response,
        audio: response.audio_base64,
        userText: response.user_text,
        requiresCamera: response.requires_camera || false,
        requiresImages: response.requires_images || false,
        imageUrls: response.image_urls || [],
        responseData: response,
        language: response.language
      }
    } catch (error) {
      console.error('Failed to send voice query:', error)
      throw error
    }
  }

  /**
   * Check if image contains a leaf
   */
  async checkLeaf(imageBase64, language = null) {
    const queryLanguage = language || this.currentLanguage

    try {
      console.log('🍃 Checking for leaf in image...')
      const response = await apiService.checkLeafPresence(imageBase64, queryLanguage)
      
      return {
        hasLeaf: response.leaf_detected || false,
        message: response.message || '',
        confidence: response.confidence || 0
      }
    } catch (error) {
      console.error('Failed to check leaf:', error)
      throw error
    }
  }

  /**
   * Diagnose crop disease from image
   */
  async diagnoseCropDisease(imageBase64, language = null) {
    if (!this.currentSessionId) {
      await this.initializeSession()
    }

    const queryLanguage = language || this.currentLanguage

    try {
      console.log('🔬 Diagnosing crop disease...')
      const response = await apiService.diagnoseCropDisease(
        this.currentSessionId,
        imageBase64,
        queryLanguage
      )

      // Add to conversation history
      if (response.success) {
        this.conversationHistory.push({
          user: '📷 [Camera diagnosis]',
          assistant: response.text,
          timestamp: new Date().toISOString()
        })
      }

      return {
        success: response.success || false,
        diagnosis: response.text || '',
        audio: response.audio || '',
        language: response.language || queryLanguage
      }
    } catch (error) {
      console.error('Failed to diagnose disease:', error)
      throw error
    }
  }

  /**
   * Get conversation history
   */
  getHistory() {
    return this.conversationHistory
  }

  /**
   * Clear session
   */
  async clearSession() {
    if (this.currentSessionId) {
      try {
        await apiService.endSession(this.currentSessionId)
      } catch (error) {
        console.warn('Failed to end session on backend:', error)
      }
    }

    this.currentSessionId = null
    this.conversationHistory = []
    this.currentLanguage = 'hindi'
    
    console.log('🔄 Session cleared')
  }

  /**
   * Get current session info
   */
  getSessionInfo() {
    return {
      sessionId: this.currentSessionId,
      language: this.currentLanguage,
      messageCount: this.conversationHistory.length
    }
  }
}

// Export singleton instance
const kisaanService = new KisaanService()
export default kisaanService
