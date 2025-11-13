import { motion, AnimatePresence } from 'framer-motion'
import { Play, Bot, Sparkles } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import './AvatarPanel.css'

const AvatarPanel = ({ isStarted, onStart, isListening }) => {
  const videoRef = useRef(null)
  const [isLoadingAvatar, setIsLoadingAvatar] = useState(false)
  const [connectionError, setConnectionError] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [hasUserInteracted, setHasUserInteracted] = useState(false)
  const [isVideoMuted, setIsVideoMuted] = useState(true)
  
  // Debug log connection status changes
  useEffect(() => {
    console.log('🔌 AvatarPanel connectionStatus changed:', connectionStatus)
  }, [connectionStatus])

  // Detect user interaction for autoplay policy compliance
  useEffect(() => {
    const handleUserInteraction = () => {
      if (!hasUserInteracted) {
        console.log('👆 User interaction detected - safe to unmute video')
        setHasUserInteracted(true)

        // Try to unmute video if it's connected
        if (connectionStatus === 'connected' && videoRef.current) {
          console.log('🔄 Attempting to unmute video after user interaction')
          console.log('Video element before unmute:', {
            muted: videoRef.current.muted,
            volume: videoRef.current.volume,
            srcObject: !!videoRef.current.srcObject
          })

                          videoRef.current.muted = false
                          videoRef.current.volume = 1.0 // Ensure volume is at max
                          setIsVideoMuted(false)
                          console.log('🔊 Video unmuted after user interaction')
                          console.log('Video element after unmute:', {
                            muted: videoRef.current.muted,
                            volume: videoRef.current.volume
                          })
        }
      }
    }

    // Listen for various user interaction events
    const events = ['click', 'touchstart', 'keydown', 'scroll']
    events.forEach(event => {
      document.addEventListener(event, handleUserInteraction, { once: true })
    })

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserInteraction)
      })
    }
  }, []) // Remove dependencies to ensure listeners are set up once

  // Try to unmute when connection is established and user has interacted
  useEffect(() => {
    if (connectionStatus === 'connected' && hasUserInteracted && videoRef.current && isVideoMuted) {
      console.log('🔄 Connection established and user interacted - attempting to unmute')
      try {
        videoRef.current.muted = false
        setIsVideoMuted(false)
        console.log('✅ Video unmuted successfully')
      } catch (error) {
        console.error('❌ Failed to unmute video:', error)
      }
    }
  }, [connectionStatus, hasUserInteracted, isVideoMuted])

  // Listen for WebRTC events
  useEffect(() => {
    const handleWebRTCError = (event) => {
      console.error('WebRTC Error:', event.detail)
      setConnectionError(event.detail.message)
      setConnectionStatus('error')
      setIsLoadingAvatar(false)
    }

    const handleWebRTCConnected = () => {
      console.log('WebRTC Connected!')
      setConnectionStatus('connected')
      setConnectionError(null)
      setIsLoadingAvatar(false)
      
    // Video will be played later in the main connection logic with proper autoplay handling
    }

    const handleWebRTCFailed = () => {
      console.error('WebRTC Connection Failed')
      setConnectionStatus('failed')
      setConnectionError('WebRTC connection failed')
      setIsLoadingAvatar(false)
    }

    window.addEventListener('webrtc-error', handleWebRTCError)
    window.addEventListener('webrtc-connected', handleWebRTCConnected)
    window.addEventListener('webrtc-connection-failed', handleWebRTCFailed)

    return () => {
      window.removeEventListener('webrtc-error', handleWebRTCError)
      window.removeEventListener('webrtc-connected', handleWebRTCConnected)
      window.removeEventListener('webrtc-connection-failed', handleWebRTCFailed)
    }
  }, [])

  // Debug video element creation and stream attachment
  useEffect(() => {
    if (videoRef.current) {
      console.log('🎥 Video element created:', videoRef.current)
      console.log('Video element properties:', {
        id: videoRef.current.id,
        readyState: videoRef.current.readyState,
        videoWidth: videoRef.current.videoWidth,
        videoHeight: videoRef.current.videoHeight,
        srcObject: !!videoRef.current.srcObject,
        autoplay: videoRef.current.autoplay,
        muted: videoRef.current.muted
      })
      
      // Monitor for srcObject changes
      const checkSrcObject = setInterval(() => {
        if (videoRef.current && videoRef.current.srcObject) {
          console.log('✅ srcObject attached to video element!', videoRef.current.srcObject)
          const tracks = videoRef.current.srcObject.getTracks()
          console.log('📺 All tracks:', tracks.map(t => ({
            kind: t.kind,
            enabled: t.enabled,
            readyState: t.readyState,
            muted: t.muted
          })))

          const audioTracks = tracks.filter(t => t.kind === 'audio')
          const videoTracks = tracks.filter(t => t.kind === 'video')
          console.log(`🎵 Audio tracks: ${audioTracks.length}, 📹 Video tracks: ${videoTracks.length}`)

          if (audioTracks.length === 0) {
            console.warn('⚠️ No audio tracks found in stream!')
          } else {
            console.log('✅ Audio tracks present in stream')
          }
          clearInterval(checkSrcObject)
        }
      }, 500)
      
      return () => clearInterval(checkSrcObject)
    }
  }, [videoRef.current])

  // Initialize WebRTC connection when started (using client.js)
  useEffect(() => {
    if (isStarted) {
      setIsLoadingAvatar(true)
      setConnectionStatus('connecting')
      setConnectionError(null)
      console.log('🔵 Starting WebRTC connection to RunPod avatar...')

      // Small delay to ensure video element is in DOM
      setTimeout(() => {
        // Call the start() function from client.js (loaded in index.html)
        if (window.start) {
          console.log('▶️ Calling window.start()...')
          window.start()

          // Monitor connection with detailed logging
          let attempts = 0
          const checkInterval = setInterval(() => {
            const video = document.getElementById('avatar-video')
            if (video) {
              console.log(`📹 Video check #${attempts}: readyState=${video.readyState}, videoWidth=${video.videoWidth}`)

              if (video.readyState >= 3 && video.videoWidth > 0) {
                console.log('✅ Video connection established!')
                
                // Log the session ID that was assigned by the backend
                const sessionIdElement = document.getElementById('sessionid')
                const sessionId = sessionIdElement ? sessionIdElement.value : 'unknown'
                console.log('📋 Session ID assigned by backend:', sessionId)
                
                setIsLoadingAvatar(false)
                setConnectionStatus('connected')
                clearInterval(checkInterval)
                
                // Force video to be visible (override Framer Motion if needed)
                setTimeout(() => {
                  if (video) {
                    video.style.setProperty('opacity', '1', 'important')
                    video.style.setProperty('transform', 'scale(1)', 'important')
                    video.style.setProperty('display', 'block', 'important')
                    video.style.setProperty('visibility', 'visible', 'important')
                    video.style.setProperty('z-index', '20', 'important')
                    
                    // Try to play video with audio (like dashboard.html)
                    // If it fails due to autoplay policy, mute and wait for user interaction
                    video.muted = false
                    setIsVideoMuted(false)

                    video.play().then(() => {
                      console.log('▶️ Video.play() called successfully with audio')
                    }).catch(err => {
                      console.warn('⚠️ Video.play() failed (likely autoplay policy):', err.message)

                      // Fallback: mute and try again
                      video.muted = true
                      setIsVideoMuted(true)

                      video.play().then(() => {
                        console.log('✅ Video playing muted - waiting for user interaction to unmute')

                        // Try to unmute if user has already interacted
                        if (hasUserInteracted) {
                          setTimeout(() => {
                            video.muted = false
                            video.volume = 1.0 // Ensure volume is at max
                            setIsVideoMuted(false)
                            console.log('🔊 Video unmuted after user interaction (fallback)')
                          }, 100)
                        }
                      }).catch(err2 => {
                        console.error('❌ Even muted play failed:', err2.message)
                      })
                    })
                    
                    console.log('🎥 Video forced to visible: opacity=1, scale=1, display=block')
                    console.log('📐 Video computed style:', {
                      opacity: window.getComputedStyle(video).opacity,
                      transform: window.getComputedStyle(video).transform,
                      display: window.getComputedStyle(video).display,
                      visibility: window.getComputedStyle(video).visibility,
                      zIndex: window.getComputedStyle(video).zIndex,
                      width: window.getComputedStyle(video).width,
                      height: window.getComputedStyle(video).height
                    })
                    
                    // Check if loading overlay is still present
                    const overlay = document.querySelector('.avatar-loading-overlay')
                    console.log('🔍 Loading overlay still present?', !!overlay)
                    if (overlay) {
                      console.log('⚠️ Loading overlay still in DOM - REMOVING COMPLETELY')
                      overlay.remove() // Remove from DOM entirely
                    }
                    
                    // Double-check video is the top element
                    console.log('📺 Video element z-index:', window.getComputedStyle(video).zIndex)
                    console.log('📺 Video element position in DOM:', video.parentElement)
                    
                    // Check all children in avatar-container
                    const container = video.parentElement
                    if (container) {
                      const children = Array.from(container.children)
                      console.log('🔍 Avatar container children:', children.length)
                      children.forEach((child, idx) => {
                        const styles = window.getComputedStyle(child)
                        console.log(`  Child ${idx}:`, {
                          tag: child.tagName,
                          className: child.className,
                          display: styles.display,
                          opacity: styles.opacity,
                          zIndex: styles.zIndex,
                          position: styles.position
                        })
                      })
                      
                      // Check if there's anything covering the video
                      console.log('🔍 Container z-index:', window.getComputedStyle(container).zIndex)
                      console.log('🔍 Container overflow:', window.getComputedStyle(container).overflow)
                      console.log('🔍 Container dimensions:', {
                        width: window.getComputedStyle(container).width,
                        height: window.getComputedStyle(container).height
                      })
                    }
                    
                    // Try to find any canvas elements that might be covering it
                    const canvases = document.querySelectorAll('canvas')
                    if (canvases.length > 0) {
                      console.log('⚠️ Found canvas elements that might be covering video:', canvases.length)
                      canvases.forEach((canvas, idx) => {
                        console.log(`  Canvas ${idx}:`, {
                          zIndex: window.getComputedStyle(canvas).zIndex,
                          display: window.getComputedStyle(canvas).display
                        })
                      })
                    }
                    
                    // Check avatar-panel dimensions (parent of avatar-container)
                    const avatarPanel = document.querySelector('.avatar-panel')
                    if (avatarPanel) {
                      const panelStyles = window.getComputedStyle(avatarPanel)
                      console.log('🔍 Avatar panel dimensions:', {
                        width: panelStyles.width,
                        height: panelStyles.height,
                        display: panelStyles.display,
                        flex: panelStyles.flex,
                        minWidth: panelStyles.minWidth
                      })
                    }
                    
                    // Check if video has actual pixel dimensions
                    const videoRect = video.getBoundingClientRect()
                    console.log('📐 Video bounding rect:', {
                      width: videoRect.width,
                      height: videoRect.height,
                      top: videoRect.top,
                      left: videoRect.left,
                      right: videoRect.right,
                      bottom: videoRect.bottom
                    })
                    
                    if (videoRect.width === 0 || videoRect.height === 0) {
                      console.error('❌ VIDEO HAS ZERO DIMENSIONS - This is the problem!')
                      console.error('❌ The video element exists but has no size in the viewport')
                      console.error('❌ Check if parent containers have proper dimensions')
                    } else {
                      console.log('✅ Video has proper dimensions:', videoRect.width, 'x', videoRect.height)
                    }
                    
                    // Final check - is video actually in viewport?
                    const inViewport = (
                      videoRect.top >= 0 &&
                      videoRect.left >= 0 &&
                      videoRect.bottom <= window.innerHeight &&
                      videoRect.right <= window.innerWidth
                    )
                    console.log('🔍 Video in viewport?', inViewport)
                    console.log('🔍 Window dimensions:', window.innerWidth, 'x', window.innerHeight)
                  }
                }, 100)
              }
            } else {
              console.warn('⚠️ Video element not found in DOM')
            }

            attempts++
            if (attempts > 30) {
              console.error('❌ Connection timeout after 30 attempts')
              setIsLoadingAvatar(false)
              setConnectionStatus('timeout')
              setConnectionError('Connection timeout - video stream not received within 30 seconds')
              clearInterval(checkInterval)
            }
          }, 1000)
        } else {
          console.error('❌ window.start() not found! Client.js may not be loaded.')
          console.log('Available on window:', Object.keys(window).filter(k => k.includes('start')))
          setIsLoadingAvatar(false)
        }
      }, 500)
    }
  }, [isStarted])

  return (
    <div className="avatar-panel">
      {/* Background Effects */}
      <div className={`avatar-bg ${isStarted ? 'blur-background' : ''}`}>
        <div className="glow-orb orb-1"></div>
        <div className="glow-orb orb-2"></div>
        <div className="glow-orb orb-3"></div>
      </div>

      {/* Mira Badge */}
      {isStarted && (
        <motion.div
          className="mira-badge"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', damping: 15 }}
        >
          <Bot size={20} />
          <span>Mira AI Assistant</span>
        </motion.div>
      )}

      {/* Avatar/Video Container */}
      <div className="avatar-container">
        {isStarted ? (
          <>
            {/* Avatar Loading Animation */}
            <AnimatePresence mode="wait">
              {connectionStatus !== 'connected' && (
                <motion.div
                  key="loading-overlay"
                  className="avatar-loading-overlay"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.5 }}
                >
                  <motion.div
                    className="loading-avatar"
                    animate={{
                      scale: [1, 1.2, 1],
                      rotate: [0, 180, 360]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: 'easeInOut'
                    }}
                  >
                    <Sparkles size={80} />
                  </motion.div>
                  <motion.div
                    className="loading-text"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                  >
                    Connecting to Mira...
                  </motion.div>
                  <motion.div
                    className="loading-spinner"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Video element - will be populated by WebRTC */}
            <video
              ref={videoRef}
              id="avatar-video"
              autoPlay
              playsInline
              className="avatar-video"
              style={{
                opacity: 1,
                transform: 'scale(1)',
                display: 'block',
                visibility: 'visible',
                zIndex: 20,
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                position: 'absolute',
                top: 0,
                left: 0,
                backgroundColor: '#000'
              }}
            />

            {/* Listening Indicator */}
            {isListening && (
              <motion.div
                className="listening-pulse"
                animate={{ scale: [1, 1.2, 1], opacity: [0.7, 1, 0.7] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
              />
            )}

            {/* Connection Status Indicator */}
            <motion.div
              className={`connection-status status-${connectionStatus}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="status-indicator">
                <div className={`status-dot ${connectionStatus}`}></div>
                <span className="status-text">
                  {connectionStatus === 'connecting' && 'Connecting...'}
                  {connectionStatus === 'connected' && (isVideoMuted ? 'Connected (Muted)' : 'Connected')}
                  {connectionStatus === 'error' && 'Connection Error'}
                  {connectionStatus === 'failed' && 'Connection Failed'}
                  {connectionStatus === 'timeout' && 'Connection Timeout'}
                  {connectionStatus === 'disconnected' && 'Disconnected'}
                </span>
                {connectionStatus === 'connected' && isVideoMuted && (
                  <motion.div
                    className="audio-hint"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1, duration: 0.5 }}
                  >
                    <span className="audio-hint-text">
                      {!hasUserInteracted ? 'Click anywhere to enable audio' : 'Click to unmute'}
                    </span>
                    <motion.button
                      className="unmute-button"
                      onClick={() => {
                        if (videoRef.current) {
                          console.log('🔊 Manual unmute clicked - before:', {
                            muted: videoRef.current.muted,
                            volume: videoRef.current.volume,
                            srcObject: !!videoRef.current.srcObject
                          })

                          videoRef.current.muted = false
                          videoRef.current.volume = 1.0 // Ensure volume is at max
                          setIsVideoMuted(false)

                          console.log('🔊 Manual unmute clicked - after:', {
                            muted: videoRef.current.muted,
                            volume: videoRef.current.volume
                          })
                        }
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      🔊
                    </motion.button>
                  </motion.div>
                )}
              </div>
              {connectionError && (
                <div className="error-message">{connectionError}</div>
              )}
            </motion.div>
          </>
        ) : (
          <div className="avatar-placeholder">
            <motion.div
              className="placeholder-icon"
              animate={{
                rotateY: [0, 180, 360],
                scale: [1, 1.1, 1]
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
            >
              <Bot size={120} />
            </motion.div>
          </div>
        )}
      </div>

      {/* Professional Welcome Experience */}
      {!isStarted && (
        <motion.div
          className="welcome-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <div className="welcome-hero">
            {/* Floating Elements */}
            <motion.div
              className="floating-element floating-1"
              animate={{
                y: [0, -20, 0],
                rotate: [0, 5, 0]
              }}
              transition={{
                duration: 6,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
            >
              <div className="floating-circle gradient-primary"></div>
            </motion.div>

            <motion.div
              className="floating-element floating-2"
              animate={{
                y: [0, 15, 0],
                x: [0, -10, 0]
              }}
              transition={{
                duration: 8,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 1
              }}
            >
              <div className="floating-square gradient-accent"></div>
            </motion.div>

            <motion.div
              className="floating-element floating-3"
              animate={{
                y: [0, -25, 0],
                rotate: [0, -10, 0]
              }}
              transition={{
                duration: 7,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 2
              }}
            >
              <div className="floating-triangle gradient-secondary"></div>
            </motion.div>

            {/* Main Content */}
            <div className="hero-content">
              <motion.div
                className="brand-header"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
              >
                <div className="brand-logo">
                  <div className="logo-circle">
                    <span className="logo-text">NASSCOM</span>
                  </div>
                </div>
                <div className="brand-title">
                  <h1 className="brand-name">Centre of Excellence</h1>
                  <p className="brand-tagline">AI & IoT Innovation Hub</p>
                </div>
              </motion.div>

              <motion.div
                className="hero-stats"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                <div className="stat-item">
                  <div className="stat-number">200+</div>
                  <div className="stat-label">Prototypes</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">160+</div>
                  <div className="stat-label">Enterprises</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">50+</div>
                  <div className="stat-label">Deployments</div>
                </div>
              </motion.div>

              <motion.div
                className="hero-description"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.6 }}
              >
                <p className="description-text">
                  Founded in 2016 through MeitY-State Government-NASSCOM partnership.
                  Operating from 4 strategic locations across India.
                </p>
              </motion.div>

              <motion.button
                className="cta-button"
                onClick={onStart}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{
                  scale: 1.05,
                  boxShadow: '0 25px 50px -12px rgba(0, 102, 204, 0.4)'
                }}
                whileTap={{ scale: 0.95 }}
                transition={{
                  duration: 0.8,
                  delay: 0.8,
                  type: 'spring',
                  stiffness: 300,
                  damping: 20
                }}
              >
                <div className="button-content">
                  <motion.div
                    className="button-icon"
                    animate={{ x: [0, 4, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                  >
                    <Play size={24} />
                  </motion.div>
                  <span className="button-text">Begin Experience</span>
                </div>
                <div className="button-glow"></div>
              </motion.button>

              <motion.div
                className="scroll-indicator"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.2 }}
              >
                <div className="scroll-text">Scroll to explore</div>
                <motion.div
                  className="scroll-mouse"
                  animate={{ y: [0, 8, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <div className="mouse-wheel"></div>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default AvatarPanel

