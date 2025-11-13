import { motion } from 'framer-motion'
import { Image as ImageIcon, ZoomIn } from 'lucide-react'
import { useState } from 'react'
import './ProductImageCard.css'

const ProductImageCard = ({ images, onImageClick, language = 'hindi' }) => {
  const [loadedImages, setLoadedImages] = useState({})
  const [failedImages, setFailedImages] = useState({})

  const messages = {
    hindi: {
      viewImages: 'चित्र देखें',
      products: 'उत्पाद',
      clickToView: 'देखने के लिए क्लिक करें'
    },
    english: {
      viewImages: 'View Images',
      products: 'Products',
      clickToView: 'Click to view'
    }
  }

  const msg = messages[language] || messages.hindi

  if (!images || images.length === 0) {
    return null
  }

  const handleImageLoad = (index) => {
    setLoadedImages(prev => ({ ...prev, [index]: true }))
  }

  const handleImageError = (index) => {
    setFailedImages(prev => ({ ...prev, [index]: true }))
  }

  const displayImages = images.slice(0, 4)

  return (
    <div className="product-image-card">
      <div className="product-card-header">
        <ImageIcon size={20} />
        <span>{msg.products}</span>
        <span className="image-count">{images.length}</span>
      </div>

      <div className="product-grid">
        {displayImages.map((img, index) => (
          <motion.div
            key={index}
            className="product-item"
            onClick={() => onImageClick && onImageClick(index)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="product-image-wrapper">
              {!loadedImages[index] && !failedImages[index] && (
                <div className="image-skeleton">
                  <div className="skeleton-shimmer"></div>
                </div>
              )}

              {failedImages[index] ? (
                <div className="image-fallback">
                  <ImageIcon size={32} />
                  <span>Image not available</span>
                </div>
              ) : (
                <img
                  src={img.url}
                  alt={img.title || `Product ${index + 1}`}
                  onLoad={() => handleImageLoad(index)}
                  onError={() => handleImageError(index)}
                  style={{ display: loadedImages[index] ? 'block' : 'none' }}
                />
              )}

              <div className="image-overlay">
                <ZoomIn size={24} />
                <span>{msg.clickToView}</span>
              </div>
            </div>

            {img.title && (
              <div className="product-title">
                {img.title}
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {images.length > 4 && (
        <div className="more-images-notice">
          +{images.length - 4} more images
        </div>
      )}
    </div>
  )
}

export default ProductImageCard
