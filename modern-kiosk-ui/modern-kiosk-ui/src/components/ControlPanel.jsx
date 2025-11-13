import { motion } from 'framer-motion'
import { Mic, MicOff } from 'lucide-react'
import './ControlPanel.css'

const ControlPanel = ({ 
  isListening, 
  transcript, 
  onStartListening, 
  onStopListening,
  currentState,
  isStarted
}) => {
  const progressSteps = [
    'Welcome',
    'Language',
    'Greeting',
    'Understanding',
    'Information',
    'Meeting',
    'Feedback'
  ]

  const currentStepIndex = progressSteps.findIndex(
    step => step.toLowerCase() === currentState.toLowerCase()
  )

  const handleMicClick = () => {
    if (isListening) {
      onStopListening()
    } else {
      onStartListening()
    }
  }

  if (!isStarted) {
    return null
  }

  return (
    <motion.div 
      className="control-panel"
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.2 }}
    >
      {/* Transcript Display */}
      <motion.div 
        className={`transcript-box ${transcript ? 'active' : ''}`}
        animate={{ 
          scale: transcript ? 1 : 0.95,
          opacity: transcript ? 1 : 0.7
        }}
      >
        {transcript || 'Tap microphone to speak'}
      </motion.div>

      {/* Voice Controls */}
      <div className="voice-controls">
        <motion.button
          className={`mic-button ${isListening ? 'listening' : ''}`}
          onClick={handleMicClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          animate={isListening ? {
            scale: [1, 1.1, 1],
            boxShadow: [
              '0 0 0 0 rgba(239, 68, 68, 0.7)',
              '0 0 0 40px rgba(239, 68, 68, 0)',
              '0 0 0 0 rgba(239, 68, 68, 0.7)'
            ]
          } : {}}
          transition={isListening ? {
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut'
          } : {}}
        >
          {isListening ? <MicOff size={48} /> : <Mic size={48} />}
        </motion.button>
      </div>

      {/* Progress Indicator */}
      <div className="progress-section">
        <div className="progress-label">
          {currentStepIndex >= 0 ? progressSteps[currentStepIndex] : 'Ready'}
        </div>
        
        <div className="progress-dots">
          {progressSteps.map((step, index) => (
            <motion.div
              key={step}
              className={`progress-dot ${
                index < currentStepIndex ? 'completed' : 
                index === currentStepIndex ? 'active' : ''
              }`}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: index * 0.1 }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default ControlPanel




