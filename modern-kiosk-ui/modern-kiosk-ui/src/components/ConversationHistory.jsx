import { motion } from 'framer-motion'
import { X, MessageCircle, User, Bot, Brain, Clock, UserCheck } from 'lucide-react'
import { useState, useEffect } from 'react'
import { getConversationHistory, isReturningUser } from '../services/aiService'
import './ConversationHistory.css'

const ConversationHistory = ({ history, onClose, detectedPersona, userContext = {} }) => {
  const [fullHistory, setFullHistory] = useState([])
  const [sessionInfo, setSessionInfo] = useState({})
  
  useEffect(() => {
    // Load full conversation history from AI service
    const loadFullHistory = async () => {
      try {
        const aiHistory = getConversationHistory()
        setFullHistory(aiHistory)
        
        // Get session info
        setSessionInfo({
          isReturning: isReturningUser(),
          persona: detectedPersona,
          userInfo: userContext
        })
      } catch (error) {
        console.error('Error loading conversation history:', error)
      }
    }
    
    loadFullHistory()
  }, [detectedPersona, userContext])
  return (
    <>
      {/* Backdrop */}
      <motion.div
        className="history-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />

      {/* History Panel */}
      <motion.div
        className="history-panel"
        initial={{ x: -500, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: -500, opacity: 0 }}
        transition={{ type: 'spring', damping: 25 }}
      >
        {/* Header */}
        <div className="history-header">
          <div className="history-title-section">
            <MessageCircle size={24} />
            <h2 className="history-title">Conversation</h2>
            {sessionInfo.isReturning && (
              <span className="returning-badge">
                <UserCheck size={16} />
                Returning User
              </span>
            )}
          </div>
          <button className="history-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        {/* Session Info */}
        {(detectedPersona || userContext.name) && (
          <div className="session-info">
            {userContext.name && (
              <div className="session-detail">
                <User size={16} />
                <span>Hello, {userContext.name}!</span>
              </div>
            )}
            {detectedPersona && (
              <div className="session-detail">
                <Brain size={16} />
                <span>Persona: {detectedPersona}</span>
              </div>
            )}
            <div className="session-detail">
              <Clock size={16} />
              <span>{history.length + fullHistory.length} messages</span>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="history-content">
          {history.length === 0 && fullHistory.length === 0 ? (
            <div className="history-empty">
              <Bot size={64} className="empty-icon" />
              <p>No conversation yet</p>
              <span>Start speaking to see your conversation history</span>
            </div>
          ) : (
            <>
              {/* Show full AI service history first */}
              {fullHistory.map((item, index) => (
                <motion.div
                  key={`ai-${index}`}
                  className={`history-item ${item.role === 'user' ? 'user' : 'assistant'} ${item.isAI ? 'ai-response' : ''}`}
                  initial={{ x: -30, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: index * 0.03 }}
                >
                  <div className="item-icon">
                    {item.role === 'user' ? (
                      <User size={18} />
                    ) : (
                      <Bot size={18} className={item.isAI ? 'ai-bot' : ''} />
                    )}
                  </div>
                  <div className="item-content">
                    <div className="item-header">
                      <span className="item-speaker">
                        {item.role === 'user' ? 
                          (userContext.name || 'You') : 
                          'Mira AI'
                        }
                      </span>
                      <span className="item-time">
                        {item.timestamp ? 
                          new Date(item.timestamp).toLocaleTimeString() : 
                          'Recent'
                        }
                      </span>
                      {item.isAI && (
                        <span className="ai-badge">AI</span>
                      )}
                    </div>
                    <div className="item-text">{item.content}</div>
                  </div>
                </motion.div>
              ))}
              
              {/* Show current session history */}
              {history.map((item, index) => (
                <motion.div
                  key={`session-${index}`}
                  className={`history-item ${item.speaker} ${item.isAI ? 'ai-response' : ''}`}
                  initial={{ x: -30, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: (fullHistory.length + index) * 0.03 }}
                >
                  <div className="item-icon">
                    {item.speaker === 'user' ? (
                      <User size={18} />
                    ) : (
                      <Bot size={18} className={item.isAI ? 'ai-bot' : ''} />
                    )}
                  </div>
                  <div className="item-content">
                    <div className="item-header">
                      <span className="item-speaker">
                        {item.speaker === 'user' ? 
                          (userContext.name || 'You') : 
                          'Mira AI'
                        }
                      </span>
                      <span className="item-time">{item.timestamp}</span>
                      {item.isAI && (
                        <span className="ai-badge">AI</span>
                      )}
                    </div>
                    <div className="item-text">{item.text}</div>
                  </div>
                </motion.div>
              ))}
            </>
          )}
        </div>
      </motion.div>
    </>
  )
}

export default ConversationHistory

