"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Camera, X, Loader2, CheckCircle, AlertCircle } from "lucide-react"

interface CameraDiseaseDetectorProps {
  sessionId: string
  language: string
  onClose: () => void
  onDiagnosisComplete: (diagnosis: string, audio: string) => void
}

export default function CameraDiseaseDetector({
  sessionId,
  language,
  onClose,
  onDiagnosisComplete,
}: CameraDiseaseDetectorProps) {
  const [status, setStatus] = useState<"idle" | "camera_active" | "countdown" | "checking" | "diagnosing">("idle")
  const [countdown, setCountdown] = useState(3)
  const [message, setMessage] = useState("")
  const [retryCount, setRetryCount] = useState(0)
  const [stream, setStream] = useState<MediaStream | null>(null)

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const messages = {
    hindi: {
      instruction: "पत्ती को कैमरे के सामने रखें",
      countdown: "सेकंड में फोटो ली जाएगी...",
      checking: "पत्ती की जाँच हो रही है...",
      diagnosing: "रोग का निदान हो रहा है...",
      noLeaf: "पत्ती को कैमरे के सामने अच्छे से रखिए",
      retry: "फिर से प्रयास करें",
    },
    english: {
      instruction: "Hold the leaf in front of camera",
      countdown: "Photo will be taken in seconds...",
      checking: "Checking for leaf...",
      diagnosing: "Diagnosing disease...",
      noLeaf: "Please hold the leaf properly in front of camera",
      retry: "Try again",
    },
  }

  const msg = messages[language as keyof typeof messages] || messages.hindi

  useEffect(() => {
    startCamera()
    return () => {
      stopCamera()
    }
  }, [])

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: 1280, height: 720 },
        audio: false,
      })

      setStream(mediaStream)

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        await videoRef.current.play()
      }

      setStatus("camera_active")
      setMessage(msg.instruction)

      // Auto-capture after 3 seconds
      setTimeout(() => {
        startCountdown()
      }, 2000)
    } catch (error) {
      console.error("[Camera] Error accessing camera:", error)
      setMessage("कैमरा एक्सेस नहीं हो सका / Camera access denied")
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      setStream(null)
    }
  }

  const startCountdown = () => {
    setStatus("countdown")
    let count = 3

    const interval = setInterval(() => {
      setCountdown(count)
      count--

      if (count < 0) {
        clearInterval(interval)
        captureImage()
      }
    }, 1000)
  }

  const captureImage = async () => {
    if (!videoRef.current || !canvasRef.current) return

    setStatus("checking")
    setMessage(msg.checking)

    const canvas = canvasRef.current
    const video = videoRef.current

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    ctx.drawImage(video, 0, 0)

    // Convert to base64
    const imageBase64 = canvas.toDataURL("image/jpeg", 0.8).split(",")[1]

    // Check if leaf is present
    await checkLeafPresence(imageBase64)
  }

  const checkLeafPresence = async (imageBase64: string) => {
    try {
      const response = await fetch(`${API_BASE}/camera/check-leaf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_base64: imageBase64,
          language: language,
        }),
      })

      const data = await response.json()

      if (data.is_leaf_present) {
        // Leaf found, proceed to diagnosis
        setStatus("diagnosing")
        setMessage(msg.diagnosing)
        await diagnoseDisease(imageBase64)
      } else {
        // No leaf found
        setMessage(msg.noLeaf)
        setRetryCount((prev) => prev + 1)

        if (retryCount >= 2) {
          // After 3 attempts, fall back to voice
          setMessage("आवाज़ में बताएं / Please describe verbally")
          setTimeout(() => {
            onClose()
          }, 3000)
        } else {
          // Retry after 2 seconds
          setTimeout(() => {
            setStatus("camera_active")
            setMessage(msg.instruction)
            setTimeout(() => startCountdown(), 2000)
          }, 2000)
        }
      }
    } catch (error) {
      console.error("[Camera] Leaf check error:", error)
      setMessage("त्रुटि / Error occurred")
    }
  }

  const diagnoseDisease = async (imageBase64: string) => {
    try {
      const response = await fetch(`${API_BASE}/camera/diagnose-disease`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          image_base64: imageBase64,
          language: language,
        }),
      })

      const data = await response.json()

      if (data.success) {
        stopCamera()
        onDiagnosisComplete(data.text, data.audio)
        onClose()
      } else {
        setMessage(data.text || "निदान में त्रुटि / Diagnosis error")
      }
    } catch (error) {
      console.error("[Camera] Diagnosis error:", error)
      setMessage("निदान में त्रुटि / Diagnosis error")
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <Card className="w-full max-w-2xl p-6 relative bg-white/95 backdrop-blur-xl border-2 border-green-200">
        <Button 
          variant="ghost" 
          size="icon" 
          className="absolute top-4 right-4 z-10 hover:bg-green-100 text-gray-700 rounded-full" 
          onClick={onClose}
        >
          <X className="h-6 w-6" />
        </Button>

        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-800">📷 Crop Disease Detection</h3>
            <p className="text-gray-600 mt-2 font-medium">{message}</p>
          </div>

          <div className="relative aspect-video bg-black rounded-lg overflow-hidden border-4 border-green-200/50">
            <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />

            {status === "countdown" && (
              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-green-900/70 to-emerald-900/70 backdrop-blur-sm">
                <div className="text-9xl font-bold text-white animate-pulse drop-shadow-2xl">{countdown}</div>
              </div>
            )}

            {status === "checking" && (
              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-green-900/70 to-emerald-900/70 backdrop-blur-sm">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="h-16 w-16 text-white animate-spin" />
                  <p className="text-white text-lg font-medium drop-shadow">{msg.checking}</p>
                </div>
              </div>
            )}

            {status === "diagnosing" && (
              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-green-900/70 to-emerald-900/70 backdrop-blur-sm">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="h-16 w-16 text-white animate-spin" />
                  <p className="text-white text-lg font-medium drop-shadow">{msg.diagnosing}</p>
                </div>
              </div>
            )}
          </div>

          <canvas ref={canvasRef} className="hidden" />

          {status === "camera_active" && (
            <div className="flex items-center justify-center gap-4">
              <Button 
                size="lg" 
                onClick={() => startCountdown()}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl transition-all"
              >
                <Camera className="mr-2 h-5 w-5" />
                Capture Now
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
