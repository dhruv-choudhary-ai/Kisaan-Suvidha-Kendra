"use client"

import { memo, useMemo } from "react"

interface AudioVisualizerProps {
  isActive: boolean
  level: number
}

function AudioVisualizer({ isActive, level }: AudioVisualizerProps) {
  const bars = useMemo(() => Array.from({ length: 24 }, (_, i) => i), []) // Reduced from 32 to 24 for better performance

  const barElements = useMemo(() => {
    return bars.map((i) => {
      const baseHeight = 20 + Math.sin(i * 0.5) * 10
      const activeHeight = baseHeight + level * 60 // Reduced multiplier for smoother animation

      return (
        <div
          key={i}
          className={`w-1.5 rounded-full transition-all duration-75 ${isActive ? "animate-wave" : ""}`} // Reduced duration for snappier feel
          style={{
            height: isActive ? `${activeHeight}%` : `${baseHeight}%`,
            animationDelay: `${i * 0.04}s`, // Slightly faster wave
            background: `linear-gradient(to top, 
              hsl(${140 + i}, 65%, ${45 + i * 0.5}%), 
              hsl(${160 + i}, 70%, ${55 + i * 0.5}%))`,
            opacity: isActive ? Math.max(0.6, 0.8 + level * 0.2) : 0.4,
          }}
        />
      )
    })
  }, [bars, isActive, level])

  return (
    <div className="relative">
      <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 via-green-500/20 to-teal-500/20 blur-3xl" />

      <div className="relative flex items-center justify-center gap-1.5 h-28 px-6 py-4 rounded-2xl bg-gradient-to-br from-white/85 to-green-50/85 backdrop-blur-sm border-2 border-green-200/50 shadow-lg shadow-green-500/10">
        {barElements}
      </div>

      {isActive && (
        <div className="absolute -top-2 -right-2">
          <div className="relative">
            <div className="absolute inset-0 bg-green-500/50 rounded-full blur-md animate-pulse" />
            <div className="relative h-3 w-3 bg-green-500 rounded-full animate-pulse" />
          </div>
        </div>
      )}
    </div>
  )
}

// Memoize the component to prevent unnecessary re-renders
export default memo(AudioVisualizer)
