/**
 * TimeoutManager Component
 * Implements voice-based timeout system: Avatar asks if user is still there
 * Resets conversation instead of reloading page
 * Timeout is triggered by lack of speech interaction (not touch)
 */

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, X, AlertTriangle } from 'lucide-react'
import { sendTextToAvatar } from '../utils/avatarStream'
import './TimeoutManager.css'

const TIMEOUT_STAGES = {
  STAGE_1: { 
    duration: 30000, // 30 seconds of no speech
    message: "Are you still there? I'll wait a bit longer...",
    avatarMessage: "Are you still there? I'll wait a bit longer for your response."
  },
  STAGE_2: { 
    duration: 15000, // 15 more seconds
    message: "Hello? Please respond if you're still here.",
    avatarMessage: "Hello? Please let me know if you're still here. Just say something."
  },
  STAGE_3: { 
    duration: 15000, // Final 15 seconds
    message: "I'll reset our conversation in a moment...",
    avatarMessage: "I haven't heard from you. I'll reset our conversation in a moment if you don't respond."
  }
}

const TimeoutManager = ({ 
  isActive = false, 
  onTimeout, 
  onUserActivity, 
  isListening = false,
  avatarSpeaking = false
}) => {
  const [currentStage, setCurrentStage] = useState(0)
  const [showWarning, setShowWarning] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [timeoutId, setTimeoutId] = useState(null)
  const [intervalId, setIntervalId] = useState(null)

  // Reset timeout when user is active
  const resetTimeout = useCallback(() => {
    console.log('🔄 Resetting timeout - user activity detected')
    
    // Clear existing timers
    if (timeoutId) {
      clearTimeout(timeoutId)
      setTimeoutId(null)
    }
    if (intervalId) {
      clearInterval(intervalId)
      setIntervalId(null)
    }

    // Reset state
    setCurrentStage(0)
    setShowWarning(false)
    setCountdown(0)
  }, [timeoutId, intervalId])

  // Start a specific timeout stage
  const startTimeoutStage = useCallback((stage) => {
    console.log(`⏱️ Starting timeout stage ${stage}`)
    
    const stageKey = `STAGE_${stage}`
    const stageConfig = TIMEOUT_STAGES[stageKey]
    
    if (!stageConfig) {
      // No more stages - trigger timeout
      console.log('❌ All timeout stages completed - resetting conversation')
      handleTimeout()
      return
    }

    setCurrentStage(stage)
    setShowWarning(true)
    setCountdown(Math.ceil(stageConfig.duration / 1000))

    // Avatar speaks the timeout message
    console.log(`🗣️ Avatar asking: "${stageConfig.avatarMessage}"`)
    sendTextToAvatar(stageConfig.avatarMessage).catch(err => {
      console.error('Failed to send timeout message to avatar:', err)
    })

    // Start countdown display
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(interval)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    setIntervalId(interval)

    // Start timeout timer for this stage
    const timeout = setTimeout(() => {
      console.log(`⌛ Stage ${stage} timeout reached`)
      setShowWarning(false)
      
      if (stage < 3) {
        // Move to next stage
        startTimeoutStage(stage + 1)
      } else {
        // Final stage completed - reset conversation
        handleTimeout()
      }
    }, stageConfig.duration)
    
    setTimeoutId(timeout)
  }, [])

  // Handle final timeout - Reset conversation instead of reloading
  const handleTimeout = useCallback(() => {
    console.log('🔄 Session timeout - resetting conversation (no page reload)')
    
    // Avatar announces the reset
    sendTextToAvatar("Thank you for visiting. I'm resetting our conversation now. Feel free to start again anytime!").catch(err => {
      console.error('Failed to send reset message to avatar:', err)
    })
    
    // Clear all timers
    if (timeoutId) clearTimeout(timeoutId)
    if (intervalId) clearInterval(intervalId)
    
    // Reset state
    setCurrentStage(0)
    setShowWarning(false)
    setCountdown(0)
    
    // Trigger timeout callback (this should reset conversation, not reload page)
    onTimeout && onTimeout()
  }, [timeoutId, intervalId, onTimeout])

  // Handle user activity
  const handleUserActivity = useCallback(() => {
    console.log('👆 User activity detected')
    resetTimeout()
    onUserActivity && onUserActivity()
  }, [resetTimeout, onUserActivity])

  // Start/stop timeout based on active state, listening, and avatar speaking
  useEffect(() => {
    // CRITICAL: Reset timeout completely when avatar is speaking or user is listening (active interaction)
    if (isListening || avatarSpeaking) {
      console.log('🔄 Resetting timeout - active interaction detected')
      // Clear all timers
      if (timeoutId) {
        clearTimeout(timeoutId)
        setTimeoutId(null)
      }
      if (intervalId) {
        clearInterval(intervalId)
        setIntervalId(null)
      }
      // Reset to initial state
      setCurrentStage(0)
      setShowWarning(false)
      setCountdown(0)
      return
    }
    
    // Start timeout system only when truly inactive (no listening, no avatar speaking)
    if (isActive && !isListening && !avatarSpeaking) {
      // Only start if we're at stage 0
      if (currentStage === 0) {
        console.log('⏱️ Starting timeout countdown (no activity)')
        const delay = setTimeout(() => {
          startTimeoutStage(1)
        }, 2000)
        
        return () => clearTimeout(delay)
      }
    } else if (!isActive) {
      // Only reset stage if not active
      if (timeoutId) clearTimeout(timeoutId)
      if (intervalId) clearInterval(intervalId)
      setCurrentStage(0)
      setShowWarning(false)
      setCountdown(0)
    }
  }, [isActive, isListening, avatarSpeaking, currentStage, timeoutId, intervalId, startTimeoutStage])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutId) clearTimeout(timeoutId)
      if (intervalId) clearInterval(intervalId)
    }
  }, [timeoutId, intervalId])

  // Get current stage message
  const getCurrentStageMessage = () => {
    const stageKey = `STAGE_${currentStage}`
    return TIMEOUT_STAGES[stageKey]?.message || ''
  }

  // Handle dismiss warning
  const handleDismissWarning = () => {
    handleUserActivity()
  }

  if (!showWarning) return null

  return (
    <AnimatePresence>
      <motion.div
        className="timeout-manager"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -50 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      >
        <div className="timeout-content">
          <div className="timeout-icon">
            {currentStage === 3 ? (
              <AlertTriangle size={24} className="warning-icon" />
            ) : (
              <Clock size={24} className="clock-icon" />
            )}
          </div>
          
          <div className="timeout-message">
            <h3 className="timeout-title">
              {currentStage === 3 ? 'Session Ending Soon' : 'Are You Still There?'}
            </h3>
            <p className="timeout-text">
              {getCurrentStageMessage()}
            </p>
          </div>
          
          <div className="timeout-countdown">
            <div className="countdown-circle">
              <motion.div
                className="countdown-progress"
                initial={{ pathLength: 1 }}
                animate={{ 
                  pathLength: countdown / Math.ceil(TIMEOUT_STAGES[`STAGE_${currentStage}`]?.duration / 1000 || 1)
                }}
                transition={{ duration: 1, ease: 'linear' }}
              >
                <svg width="60" height="60" viewBox="0 0 60 60">
                  <circle
                    cx="30"
                    cy="30"
                    r="25"
                    fill="none"
                    stroke="rgba(99, 102, 241, 0.2)"
                    strokeWidth="3"
                  />
                  <motion.circle
                    cx="30"
                    cy="30"
                    r="25"
                    fill="none"
                    stroke={currentStage === 3 ? "#ef4444" : "#6366f1"}
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeDasharray={157} // 2 * π * r = 2 * 3.14159 * 25
                    strokeDashoffset={157 * (1 - (countdown / Math.ceil(TIMEOUT_STAGES[`STAGE_${currentStage}`]?.duration / 1000 || 1)))}
                    transform="rotate(-90 30 30)"
                  />
                </svg>
              </motion.div>
              <span className="countdown-number">{countdown}</span>
            </div>
          </div>
          
          <div className="timeout-actions">
            <div className="voice-instruction">
              <p>🎤 Please speak to continue</p>
              <p className="instruction-subtext">Touch buttons are disabled - use voice only</p>
            </div>
          </div>
        </div>

        {/* Stage Indicator */}
        <div className="stage-indicator">
          {[1, 2, 3].map((stage) => (
            <div
              key={stage}
              className={`stage-dot ${stage === currentStage ? 'active' : ''} ${stage < currentStage ? 'completed' : ''}`}
            />
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  )
}

export default TimeoutManager
