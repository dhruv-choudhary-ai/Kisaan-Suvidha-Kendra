import { motion, AnimatePresence } from 'framer-motion'
import { useRef, useState, useEffect } from 'react'
import { FileText, CheckCircle, Award, Rocket, MapPin, DollarSign, X } from 'lucide-react'
import ProductImageCard from './ProductImageCard'
import ImageGallery from './ImageGallery'
import './ContentPanel.css'

const ContentPanel = ({ currentSlide, isStarted, onClose, language = 'hindi' }) => {
  const panelRef = useRef(null)
  const [scrollProgress, setScrollProgress] = useState(0)
  const [showImageGallery, setShowImageGallery] = useState(false)
  const [galleryStartIndex, setGalleryStartIndex] = useState(0)

  // Handle scroll progress indicator
  useEffect(() => {
    const el = panelRef.current
    if (!el) return

    const handleScroll = () => {
      const pct = (el.scrollTop / (el.scrollHeight - el.clientHeight)) * 100 || 0
      setScrollProgress(pct)
    }

    el.addEventListener('scroll', handleScroll)
    handleScroll() // Init
    return () => el.removeEventListener('scroll', handleScroll)
  }, [currentSlide])

  if (!isStarted) {
    return null // Don't render anything if not started
  }

  if (!currentSlide) {
    return null // Panel is hidden when no content (avatar takes full width)
  }

  const handleImageClick = (startIndex = 0) => {
    setGalleryStartIndex(startIndex)
    setShowImageGallery(true)
  }

  return (
    <>
      <div className="content-panel" ref={panelRef}>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentSlide.id}
            className="content-slide"
            initial={{ x: 540, opacity: 0 }} // Slide in from right (540px = panel width)
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 540, opacity: 0 }} // Slide out to right
            transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }} // Smooth cubic-bezier
          >
            {/* Close Button */}
            <button className="slide-close-btn" onClick={onClose} title="Close content panel">
              <X size={24} />
            </button>

            {/* Slide Header */}
            <div className="slide-header">
              <h1 className="slide-title">{currentSlide.title}</h1>
              {currentSlide.subtitle && (
                <p className="slide-subtitle">{currentSlide.subtitle}</p>
              )}
            </div>

            {/* Product Images (if available) */}
            {currentSlide.images && currentSlide.images.length > 0 && (
              <ProductImageCard
                images={currentSlide.images}
                onImageClick={handleImageClick}
                language={language}
              />
            )}

            {/* Slide Content */}
            <div className="slide-content">
              {currentSlide.sections.map((section, index) => (
                <motion.div
                  key={index}
                  initial={{ y: 40, opacity: 0, scale: 0.95 }}
                  animate={{ y: 0, opacity: 1, scale: 1 }}
                  transition={{ 
                    delay: 0.3 + (index * 0.2), // Stagger by 200ms per section
                    duration: 0.6,
                    ease: [0.4, 0, 0.2, 1]
                  }}
                >
                  {renderSection(section, index)}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Scroll Progress Indicator */}
        <div className="progress-track">
          <div className="panel-progress" style={{ height: `${scrollProgress}%` }} />
        </div>
      </div>

      {/* Image Gallery Modal */}
      {showImageGallery && currentSlide.images && (
        <ImageGallery
          images={currentSlide.images}
          onClose={() => setShowImageGallery(false)}
          language={language}
        />
      )}
    </>
  )
}

// Render different section types with animations
function renderSection(section, sectionIndex) {
  switch (section.type) {
    case 'hero':
      return (
        <motion.div 
          className="section-hero"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <h2>{section.content}</h2>
        </motion.div>
      )

    case 'text':
      return (
        <div className="section-text">
          <p>{section.content}</p>
        </div>
      )

    case 'stats':
      return (
        <div className="section-stats">
          {section.items.map((item, i) => (
            <motion.div 
              key={i} 
              className="stat-card"
              initial={{ y: 30, opacity: 0, rotateX: -15 }}
              animate={{ y: 0, opacity: 1, rotateX: 0 }}
              transition={{ 
                delay: i * 0.15,
                duration: 0.5,
                ease: [0.4, 0, 0.2, 1]
              }}
              whileHover={{ 
                y: -8, 
                scale: 1.05,
                transition: { duration: 0.2 }
              }}
            >
              <motion.div 
                className="stat-value"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: i * 0.15 + 0.3, type: 'spring', stiffness: 200 }}
              >
                {item.value}
              </motion.div>
              <motion.div 
                className="stat-label"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.15 + 0.4 }}
              >
                {item.label}
              </motion.div>
            </motion.div>
          ))}
        </div>
      )

    case 'highlights':
    case 'list':
      return (
        <div className="section-list">
          {section.title && (
            <motion.h3 
              className="list-title"
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              {section.title}
            </motion.h3>
          )}
          <ul className="highlight-list">
            {section.items.map((item, i) => (
              <motion.li 
                key={i}
                initial={{ x: -40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ 
                  delay: i * 0.1,
                  duration: 0.5,
                  ease: [0.4, 0, 0.2, 1]
                }}
                whileHover={{ 
                  x: 8,
                  transition: { duration: 0.2 }
                }}
              >
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ delay: i * 0.1 + 0.2, type: 'spring', stiffness: 200 }}
                >
                  <CheckCircle size={20} />
                </motion.div>
                <span>{item}</span>
              </motion.li>
            ))}
          </ul>
        </div>
      )

    case 'achievements':
      return (
        <div className="section-achievements">
          <h3 className="section-title">
            <Award size={24} />
            {section.title}
          </h3>
          <ul className="achievement-list">
            {section.items.map((item, i) => (
              <li key={i}>
                <Award size={18} />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )

    case 'benefits':
    case 'solutions':
      return (
        <div className="section-benefits">
          <h3 className="section-title">
            <Rocket size={24} />
            {section.title}
          </h3>
          <ul className="benefit-list">
            {section.items.map((item, i) => (
              <li key={i}>
                <Rocket size={18} />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )

    case 'case-study':
      return (
        <div className="section-case-study">
          <h3 className="case-title">{section.title}</h3>
          
          <div className="case-problem">
            <h4>Problem</h4>
            <p>{section.problem}</p>
          </div>
          
          <div className="case-solution">
            <h4>Solution</h4>
            <p>{section.solution}</p>
          </div>
          
          <div className="case-impact">
            <h4>Impact</h4>
            <ul>
              {section.impact.map((item, i) => (
                <li key={i}>
                  <CheckCircle size={18} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )

    case 'sectors':
      return (
        <div className="section-sectors">
          <h3 className="section-title">{section.title}</h3>
          <div className="sectors-grid">
            {section.items.map((item, i) => (
              <div key={i} className="sector-card">
                <div className="sector-icon">{item.icon}</div>
                <h4>{item.name}</h4>
                <ul>
                  {item.solutions.map((sol, j) => (
                    <li key={j}>{sol}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )

    case 'incentives':
      return (
        <div className="section-incentives">
          <h3 className="section-title">
            <DollarSign size={24} />
            {section.title}
          </h3>
          <div className="incentives-list">
            {section.items.map((item, i) => (
              <div key={i} className="incentive-card">
                <div className="incentive-header">
                  <h4>{item.name}</h4>
                  <span className="incentive-value">{item.value}</span>
                </div>
                <p>{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      )

    case 'locations':
      return (
        <div className="section-locations">
          <div className="locations-grid">
            {section.items.map((item, i) => (
              <div key={i} className="location-card">
                <MapPin size={24} className="location-icon" />
                <h4>{item.city}, {item.state}</h4>
                <p className="location-place">{item.location}</p>
                <p className="location-highlight">{item.highlight}</p>
              </div>
            ))}
          </div>
        </div>
      )

    default:
      return null
  }
}

export default ContentPanel

