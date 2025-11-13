import { motion } from 'framer-motion'
import { Clock, Wifi, WifiOff, Circle } from 'lucide-react'
import './Header.css'

const Header = ({ connectionStatus, onHistoryToggle }) => {
  const statusConfig = {
    connected: { color: '#10b981', text: 'Connected', icon: Wifi },
    connecting: { color: '#f59e0b', text: 'Connecting...', icon: Wifi },
    disconnected: { color: '#ef4444', text: 'Disconnected', icon: WifiOff }
  }

  const status = statusConfig[connectionStatus] || statusConfig.disconnected
  const StatusIcon = status.icon

  return (
    <motion.header 
      className="header"
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      <div className="header-content">
        <div className="brand-section">
          <motion.div 
            className="brand-logo"
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.2 }}
          >
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="url(#gradient1)" />
                <path d="M2 17L12 22L22 17" stroke="url(#gradient2)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12L12 17L22 12" stroke="url(#gradient2)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <defs>
                  <linearGradient id="gradient1" x1="2" y1="2" x2="22" y2="22">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#ec4899" />
                  </linearGradient>
                  <linearGradient id="gradient2" x1="2" y1="12" x2="22" y2="22">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#ec4899" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </motion.div>
          
          <div className="brand-text">
            <h1 className="brand-title">AI & IoT CoE</h1>
            <p className="brand-subtitle">GIFT City, Gandhinagar, Gujarat</p>
          </div>
        </div>

        <div className="header-actions">
          <motion.button
            className="history-button"
            onClick={onHistoryToggle}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Clock size={20} />
            <span>History</span>
          </motion.button>

          <motion.div 
            className="status-indicator"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, type: 'spring' }}
          >
            <motion.div
              className="status-dot"
              style={{ backgroundColor: status.color }}
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            />
            <StatusIcon size={16} style={{ color: status.color }} />
            <span className="status-text">{status.text}</span>
          </motion.div>
        </div>
      </div>

      {/* Impact Ticker */}
      <div className="impact-ticker-container">
        <motion.div 
          className="impact-ticker"
          animate={{ x: [0, -50] }}
          transition={{ repeat: Infinity, duration: 30, ease: 'linear' }}
        >
          {[...Array(2)].map((_, i) => (
            <div key={i} className="ticker-content">
              <div className="ticker-item">
                <span className="ticker-icon">🏆</span>
                <span>Grain Quality AI: 1000+ farmers, ₹700+ Cr trade</span>
              </div>
              <div className="ticker-item">
                <span className="ticker-icon">📈</span>
                <span>200+ Prototypes | 50+ Deployments | 1000+ Enterprises</span>
              </div>
              <div className="ticker-item">
                <span className="ticker-icon">🏢</span>
                <span>4 Strategic Locations | Leading AI Innovation</span>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </motion.header>
  )
}

export default Header




