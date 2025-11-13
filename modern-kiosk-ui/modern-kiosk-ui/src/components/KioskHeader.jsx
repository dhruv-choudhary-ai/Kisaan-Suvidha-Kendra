import { motion } from 'framer-motion'
import { Sun, Moon, Wifi, WifiOff } from 'lucide-react'
import nassicomLogo from '../assets/logo-1.jpg'
import './KioskHeader.css'

const KioskHeader = ({ connectionStatus, theme, onThemeToggle }) => {
  const status = connectionStatus === 'connected' ? 'Connected' : 
                 connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'
  
  const StatusIcon = connectionStatus === 'disconnected' ? WifiOff : Wifi
  const statusColor = connectionStatus === 'connected' ? '#10b981' : 
                      connectionStatus === 'connecting' ? '#f59e0b' : '#ef4444'

  return (
    <motion.header 
      className="kiosk-header"
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="header-content">
        {/* Left - NASSCOM Logo */}
        <div className="header-brand">
          <div className="brand-logo">
            <img src={nassicomLogo} alt="NASSCOM Centre of Excellence - IoT & AI" />
          </div>
        </div>

        {/* Center - Title */}
        <div className="header-title">
          <span>AI & IoT Centre of Excellence</span>
          <p className="header-subtitle">GIFT City, Gandhinagar, Gujarat</p>
        </div>

        {/* Right - Status & Theme */}
        <div className="header-actions">
          <div className="status-badge" style={{ '--status-color': statusColor }}>
            <StatusIcon size={16} />
            <span>{status}</span>
          </div>
          
          <button className="theme-toggle" onClick={onThemeToggle} aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>
      </div>
    </motion.header>
  )
}

export default KioskHeader

