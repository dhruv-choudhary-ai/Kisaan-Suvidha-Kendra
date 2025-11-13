import { motion, AnimatePresence } from 'framer-motion'
import { Play, Bot, Info } from 'lucide-react'
import InfoPanel from './InfoPanel'
import './AvatarZone.css'

const AvatarZone = ({ isStarted, onStart, activePanelIndex, onPanelChange }) => {
  const infoPanels = [
    {
      id: 'about',
      icon: Info,
      title: 'About NASSCOM CoE',
      content: {
        description: "India's premier deep tech innovation hub, established in partnership with MeitY and state governments since 2016.",
        highlights: [
          'Accelerating digital transformation',
          'Strategic partnerships across sectors',
          '200+ prototypes developed',
          '50+ successful deployments'
        ],
        metrics: [
          { label: 'Locations', value: '4 Cities' },
          { label: 'Enterprises', value: '1000+' },
          { label: 'Prototypes', value: '200+' },
          { label: 'Deployments', value: '50+' }
        ]
      }
    },
    {
      id: 'programs',
      icon: Bot,
      title: 'Key Programs',
      content: {
        programs: [
          {
            name: 'GrowX Acceleration',
            description: 'Complete startup acceleration with labs, funding, and mentorship',
            features: ['AI/ML Labs', 'Co-working Spaces', '₹25L Funding', 'Expert Mentorship']
          },
          {
            name: 'AI Innovation Challenge',
            description: 'Connecting startups with real-world challenges',
            features: ['Agriculture', 'Healthcare', 'Manufacturing', 'Governance']
          }
        ]
      }
    },
    {
      id: 'success',
      icon: Bot,
      title: 'Success Stories',
      content: {
        featured: {
          title: 'AI Grain Quality Assessment',
          description: 'Computer vision solution deployed at Gujarat APMCs, evaluating grain quality in 30 seconds',
          impact: [
            { label: 'Farmers Empowered', value: '1000+' },
            { label: 'Trade Value', value: '₹700+ Cr' },
            { label: 'Processing Time', value: '30 sec' }
          ]
        },
        overall: [
          '200+ prototypes developed',
          '50+ successful deployments',
          '1000+ enterprises engaged',
          '500+ students trained annually'
        ]
      }
    },
    {
      id: 'experience',
      icon: Bot,
      title: 'AI Experience Zone',
      content: {
        sectors: [
          {
            name: '🏥 Healthcare AI',
            solutions: ['Medical Imaging', 'Patient Monitoring', 'AI Diagnostics']
          },
          {
            name: '⚙️ Manufacturing',
            solutions: ['AI Quality Inspection', 'Predictive Maintenance', 'IoT Monitoring']
          },
          {
            name: '🌾 Agriculture',
            solutions: ['Grain Quality Assessment', 'Crop Monitoring', 'Smart Farming']
          }
        ]
      }
    }
  ]

  return (
    <motion.div 
      className="avatar-zone"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      {/* Background Effects */}
      <div className="avatar-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      {/* Mira Indicator */}
      <AnimatePresence>
        {isStarted && (
          <motion.div 
            className="mira-indicator"
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -50, opacity: 0 }}
            transition={{ type: 'spring', damping: 15 }}
          >
            <Bot className="mira-icon" />
            <span>Hi, I'm Mira! Your AI Assistant</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Video Container */}
      <div className="video-container">
        <video 
          id="avatar-video" 
          autoPlay 
          playsInline 
          muted
          className="avatar-video"
        />
        
        {/* Video Placeholder */}
        {!isStarted && (
          <div className="video-placeholder">
            <motion.div 
              className="placeholder-avatar"
              animate={{ 
                scale: [1, 1.05, 1],
                rotate: [0, 2, -2, 0]
              }}
              transition={{ 
                duration: 4,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
            >
              <Bot size={80} />
            </motion.div>
          </div>
        )}
      </div>

      {/* Start Button */}
      <AnimatePresence>
        {!isStarted && (
          <motion.button
            className="start-button"
            onClick={onStart}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: 'spring', damping: 10 }}
          >
            <Play size={28} />
            <span>Start Your Journey</span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Info Panels */}
      <AnimatePresence mode="wait">
        {isStarted && activePanelIndex !== null && (
          <InfoPanel 
            key={infoPanels[activePanelIndex].id}
            panel={infoPanels[activePanelIndex]}
            onClose={() => onPanelChange(null)}
          />
        )}
      </AnimatePresence>

      {/* Quick Info Toggle */}
      {isStarted && (
        <motion.button
          className="quick-info-toggle"
          onClick={() => onPanelChange(activePanelIndex === null ? 0 : null)}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Info size={20} />
          <span>Explore CoE</span>
        </motion.button>
      )}
    </motion.div>
  )
}

export default AvatarZone




