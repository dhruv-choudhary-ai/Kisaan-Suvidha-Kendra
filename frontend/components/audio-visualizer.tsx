"use client"

interface AudioVisualizerProps {
  isActive: boolean
  level: number
}

export default function AudioVisualizer({ isActive, level }: AudioVisualizerProps) {
  const bars = Array.from({ length: 32 }, (_, i) => i)

  return (
    <div className="relative">
      <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 via-green-500/20 to-teal-500/20 blur-3xl" />

      <div className="relative flex items-center justify-center gap-1.5 h-32 px-8 py-6 rounded-2xl bg-gradient-to-br from-white/80 to-green-50/80 backdrop-blur-sm border-2 border-green-200/50 shadow-lg shadow-green-500/10">
        {bars.map((i) => {
          const baseHeight = 20 + Math.sin(i * 0.5) * 10
          const activeHeight = baseHeight + level * 70

          return (
            <div
              key={i}
              className={`w-1.5 rounded-full transition-all duration-100 ${isActive ? "animate-wave" : ""}`}
              style={{
                height: isActive ? `${activeHeight}%` : `${baseHeight}%`,
                animationDelay: `${i * 0.05}s`,
                background: `linear-gradient(to top, 
                  hsl(${140 + i}, 65%, ${45 + i * 0.5}%), 
                  hsl(${160 + i}, 70%, ${55 + i * 0.5}%))`,
                opacity: isActive ? 0.8 + level * 0.2 : 0.4,
              }}
            />
          )
        })}
      </div>

      {isActive && (
        <div className="absolute -top-2 -right-2">
          <div className="relative">
            <div className="absolute inset-0 bg-green-500/50 rounded-full blur-md animate-pulse" />
            <div className="relative h-4 w-4 bg-green-500 rounded-full animate-pulse" />
          </div>
        </div>
      )}
    </div>
  )
}
