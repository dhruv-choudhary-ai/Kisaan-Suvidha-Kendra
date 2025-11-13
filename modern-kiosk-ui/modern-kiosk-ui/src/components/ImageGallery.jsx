import { motion, AnimatePresence } from 'framer-motion'
import { X, ZoomIn, ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { useState } from 'react'
import './ImageGallery.css'

const ImageGallery = ({ images, onClose, language = 'hindi' }) => {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isZoomed, setIsZoomed] = useState(false)

  const messages = {
    hindi: {
      title: 'उत्पाद जानकारी',
      close: 'बंद करें',
      zoom: 'बड़ा देखें',
      download: 'डाउनलोड',
      previous: 'पिछला',
      next: 'अगला',
      of: 'में से'
    },
    english: {
      title: 'Product Information',
      close: 'Close',
      zoom: 'Zoom In',
      download: 'Download',
      previous: 'Previous',
      next: 'Next',
      of: 'of'
    }
  }

  const msg = messages[language] || messages.hindi

  if (!images || images.length === 0) {
    return null
  }

  const currentImage = images[selectedIndex]

  const handlePrevious = () => {
    setSelectedIndex((prev) => (prev > 0 ? prev - 1 : images.length - 1))
    setIsZoomed(false)
  }

  const handleNext = () => {
    setSelectedIndex((prev) => (prev < images.length - 1 ? prev + 1 : 0))
    setIsZoomed(false)
  }

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = currentImage.url
    link.download = currentImage.title || `product-${selectedIndex + 1}.jpg`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <AnimatePresence>
      <motion.div
        className="image-gallery-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className={`image-gallery-modal ${isZoomed ? 'zoomed' : ''}`}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="gallery-header">
            <h2>{msg.title}</h2>
            <div className="gallery-actions">
              <button
                onClick={handleDownload}
                className="gallery-action-btn"
                title={msg.download}
              >
                <Download size={20} />
              </button>
              <button
                onClick={() => setIsZoomed(!isZoomed)}
                className="gallery-action-btn"
                title={msg.zoom}
              >
                <ZoomIn size={20} />
              </button>
              <button onClick={onClose} className="gallery-close-btn">
                <X size={24} />
              </button>
            </div>
          </div>

          {/* Main Image Display */}
          <div className="gallery-main-image">
            <motion.img
              key={selectedIndex}
              src={currentImage.url}
              alt={currentImage.title || `Product ${selectedIndex + 1}`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              onClick={() => setIsZoomed(!isZoomed)}
            />

            {/* Navigation Arrows */}
            {images.length > 1 && (
              <>
                <button
                  onClick={handlePrevious}
                  className="gallery-nav-btn prev"
                  aria-label={msg.previous}
                >
                  <ChevronLeft size={32} />
                </button>
                <button
                  onClick={handleNext}
                  className="gallery-nav-btn next"
                  aria-label={msg.next}
                >
                  <ChevronRight size={32} />
                </button>
              </>
            )}
          </div>

          {/* Image Info */}
          <div className="gallery-info">
            <div className="gallery-title">
              {currentImage.title || `Product ${selectedIndex + 1}`}
            </div>
            {currentImage.description && (
              <div className="gallery-description">
                {currentImage.description}
              </div>
            )}
            {currentImage.source && (
              <div className="gallery-source">
                Source: {currentImage.source}
              </div>
            )}
          </div>

          {/* Thumbnail Strip */}
          {images.length > 1 && (
            <div className="gallery-thumbnails">
              {images.map((img, index) => (
                <motion.div
                  key={index}
                  className={`thumbnail ${index === selectedIndex ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedIndex(index)
                    setIsZoomed(false)
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <img src={img.url} alt={img.title || `Thumbnail ${index + 1}`} />
                  {index === selectedIndex && (
                    <div className="thumbnail-indicator"></div>
                  )}
                </motion.div>
              ))}
            </div>
          )}

          {/* Counter */}
          <div className="gallery-counter">
            {selectedIndex + 1} {msg.of} {images.length}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default ImageGallery
