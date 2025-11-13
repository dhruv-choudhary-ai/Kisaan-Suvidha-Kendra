import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Camera, X, RotateCcw, CheckCircle } from 'lucide-react'
import './CameraCapture.css'

const CameraCapture = ({ onCapture, onClose, language = 'hindi' }) => {
  const [stream, setStream] = useState(null)
  const [capturedImage, setCapturedImage] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState(null)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)

  const messages = {
    hindi: {
      title: 'पत्ती की तस्वीर लें',
      instructions: 'कृपया प्रभावित पत्ती को कैमरे के सामने स्पष्ट रूप से रखें',
      capture: 'तस्वीर लें',
      retake: 'दोबारा लें',
      confirm: 'पुष्टि करें',
      processing: 'जांच हो रही है...',
      error: 'कैमरा शुरू करने में त्रुटि'
    },
    english: {
      title: 'Capture Leaf Image',
      instructions: 'Please hold the affected leaf clearly in front of the camera',
      capture: 'Capture',
      retake: 'Retake',
      confirm: 'Confirm',
      processing: 'Analyzing...',
      error: 'Error starting camera'
    }
  }

  const msg = messages[language] || messages.hindi

  useEffect(() => {
    startCamera()
    return () => {
      stopCamera()
    }
  }, [])

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      })
      setStream(mediaStream)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
    } catch (err) {
      console.error('Error accessing camera:', err)
      setError(msg.error)
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
  }

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert to base64
    const imageData = canvas.toDataURL('image/jpeg', 0.9)
    setCapturedImage(imageData)

    // Stop camera stream
    stopCamera()
  }

  const retakeImage = () => {
    setCapturedImage(null)
    setError(null)
    startCamera()
  }

  const confirmImage = async () => {
    if (!capturedImage) return

    setIsProcessing(true)
    try {
      // Extract base64 data (remove data:image/jpeg;base64, prefix)
      const base64Data = capturedImage.split(',')[1]
      
      // Call parent handler
      await onCapture(base64Data)
    } catch (err) {
      console.error('Error processing image:', err)
      setError('Processing failed')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        className="camera-capture-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="camera-capture-modal"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
        >
          {/* Header */}
          <div className="camera-header">
            <h2>{msg.title}</h2>
            <button onClick={onClose} className="camera-close-btn">
              <X size={24} />
            </button>
          </div>

          {/* Instructions */}
          <p className="camera-instructions">{msg.instructions}</p>

          {/* Camera/Preview Area */}
          <div className="camera-preview">
            {!capturedImage ? (
              <>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="camera-video"
                />
                <canvas ref={canvasRef} style={{ display: 'none' }} />
                
                {/* Overlay guide */}
                <div className="camera-guide">
                  <div className="guide-frame"></div>
                </div>
              </>
            ) : (
              <img src={capturedImage} alt="Captured leaf" className="captured-image" />
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="camera-error">
              ⚠️ {error}
            </div>
          )}

          {/* Controls */}
          <div className="camera-controls">
            {!capturedImage ? (
              <motion.button
                onClick={captureImage}
                className="camera-btn camera-btn-primary"
                whileTap={{ scale: 0.95 }}
                disabled={!stream || error}
              >
                <Camera size={24} />
                {msg.capture}
              </motion.button>
            ) : (
              <>
                <motion.button
                  onClick={retakeImage}
                  className="camera-btn camera-btn-secondary"
                  whileTap={{ scale: 0.95 }}
                  disabled={isProcessing}
                >
                  <RotateCcw size={20} />
                  {msg.retake}
                </motion.button>
                <motion.button
                  onClick={confirmImage}
                  className="camera-btn camera-btn-success"
                  whileTap={{ scale: 0.95 }}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <>
                      <div className="spinner-small"></div>
                      {msg.processing}
                    </>
                  ) : (
                    <>
                      <CheckCircle size={20} />
                      {msg.confirm}
                    </>
                  )}
                </motion.button>
              </>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default CameraCapture
