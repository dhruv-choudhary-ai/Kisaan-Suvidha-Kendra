import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import nassicomLogo from '../assets/logo-1.jpg'
import './WelcomeScreen.css'

const WelcomeScreen = ({ onComplete }) => {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Auto-start the avatar after a brief welcome display
    const timer = setTimeout(() => {
      setIsLoading(false)
      onComplete()
    }, 3000) // 3 seconds welcome display

    return () => clearTimeout(timer)
  }, [onComplete])

  return (
    <div className="welcome-screen">
      {/* Background with gradient */}
      <div className="welcome-background">
        <div className="gradient-overlay" />
        
        {/* Floating particles animation */}
        <div className="particles">
          {Array.from({ length: 20 }).map((_, i) => (
            <div key={i} className={`particle particle-${i + 1}`} />
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="welcome-content">
        <motion.div
          className="welcome-hero"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
        >
          {/* Logo */}
          <motion.div
            className="welcome-logo"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
          >
            <img src={nassicomLogo} alt="NASSCOM Centre of Excellence" />
          </motion.div>

          {/* Title */}
          <motion.h1
            className="welcome-title"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
          >
            NASSCOM AI Centre of Excellence
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="welcome-subtitle"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.8 }}
          >
            GIFT City, Gandhinagar • Deep Tech Innovation for Digital India
          </motion.p>

          {/* Loading indicator */}
          <motion.div
            className="welcome-loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.5 }}
          >
            <div className="loading-spinner">
              <div className="spinner-ring" />
              <div className="spinner-ring" />
              <div className="spinner-ring" />
            </div>
            <p className="loading-text">Initializing Mira AI Assistant...</p>
          </motion.div>
        </motion.div>

        {/* Welcome stats */}
        <motion.div
          className="welcome-stats"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5, duration: 0.8 }}
        >
          <div className="stat-item">
            <span className="stat-number">160+</span>
            <span className="stat-label">Enterprises</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">200+</span>
            <span className="stat-label">Prototypes</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">50+</span>
            <span className="stat-label">Deployments</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">4</span>
            <span className="stat-label">Cities</span>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default WelcomeScreen
