"use client"

import { useEffect, useRef } from "react"
import { Volume2, User, Bot, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

interface Message {
  id: string
  text: string
  audio?: string
  sender: "user" | "assistant"
  timestamp: Date
  isStreaming?: boolean
}

interface MessageListProps {
  messages: Message[]
  isThinking?: boolean
  isListening?: boolean
  isSpeaking?: boolean
  currentTranscript?: string
}

export default function MessageList({ messages, isThinking, isListening, isSpeaking, currentTranscript }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, currentTranscript])

  const playAudio = (base64Audio: string) => {
    const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`)
    audio.play()
  }

  const TypingIndicator = () => (
    <div className="flex gap-3 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <Avatar className="h-10 w-10 shrink-0 bg-gradient-to-br from-green-600 to-emerald-600 border-2 border-green-200">
        <AvatarFallback className="text-white">
          <Bot className="h-5 w-5" />
        </AvatarFallback>
      </Avatar>

      <div className="flex flex-col gap-2 max-w-[75%]">
        <div className="rounded-2xl px-5 py-4 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200/50 rounded-tl-sm shadow-lg">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="h-2 w-2 rounded-full bg-green-600 animate-bounce" style={{ animationDelay: "0ms" }} />
              <div className="h-2 w-2 rounded-full bg-green-600 animate-bounce" style={{ animationDelay: "150ms" }} />
              <div className="h-2 w-2 rounded-full bg-green-600 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            <span className="text-sm text-green-700 font-medium">
              {isSpeaking ? "AI is speaking..." : "AI is thinking..."}
            </span>
          </div>
        </div>
      </div>
    </div>
  )

  const LiveTranscript = () => (
    <div className="flex gap-3 flex-row-reverse animate-in fade-in slide-in-from-bottom-4 duration-300">
      <Avatar className="h-10 w-10 shrink-0 bg-gradient-to-br from-green-600 to-green-700 border-2 border-green-200">
        <AvatarFallback className="text-white">
          <User className="h-5 w-5" />
        </AvatarFallback>
      </Avatar>

      <div className="flex flex-col gap-2 max-w-[75%] items-end">
        <div className="rounded-2xl px-5 py-3.5 bg-gradient-to-br from-green-600 to-green-700 text-white rounded-tr-sm shadow-lg border-2 border-green-300/30">
          <div className="flex items-center gap-3">
            <Loader2 className="h-4 w-4 animate-spin" />
            <p className="text-pretty leading-relaxed text-[15px]">Listening...</p>
          </div>
        </div>
        <p className="text-xs text-gray-600 px-2 flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
          Recording (will auto-stop on silence)
        </p>
      </div>
    </div>
  )

  if (messages.length === 0 && !isThinking && !isListening) return null

  return (
    <div className="space-y-6 max-h-[500px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-primary/20 scrollbar-track-transparent">
      {messages.map((message, index) => (
        <div
          key={message.id}
          className={`flex gap-3 ${message.sender === "user" ? "flex-row-reverse" : "flex-row"} animate-in fade-in slide-in-from-bottom-4 duration-500`}
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <Avatar
            className={`h-10 w-10 shrink-0 border-2 ${message.sender === "user" ? "bg-gradient-to-br from-green-600 to-green-700 border-green-200" : "bg-gradient-to-br from-green-600 to-emerald-600 border-green-200"}`}
          >
            <AvatarFallback className="text-white">
              {message.sender === "user" ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
            </AvatarFallback>
          </Avatar>

          <div className={`flex flex-col gap-2 max-w-[75%] ${message.sender === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`rounded-2xl px-5 py-3.5 shadow-lg transition-all duration-300 hover:shadow-xl ${
                message.sender === "user"
                  ? "bg-gradient-to-br from-green-600 to-green-700 text-white rounded-tr-sm border-2 border-green-300/30"
                  : "bg-gradient-to-br from-green-50 to-emerald-50 text-gray-800 border-2 border-green-200/50 rounded-tl-sm"
              }`}
            >
              <p
                className={`text-pretty leading-relaxed text-[15px] ${message.isStreaming ? "animate-in fade-in duration-300" : ""}`}
              >
                {message.text}
              </p>

              {message.audio && message.sender === "assistant" && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => playAudio(message.audio!)}
                  className="mt-3 h-8 px-3 hover:bg-green-200/50 rounded-full transition-all hover:scale-105 text-green-700"
                >
                  <Volume2 className="h-3.5 w-3.5 mr-1.5" />
                  <span className="text-xs font-medium">Play Audio</span>
                </Button>
              )}
            </div>

            <p className="text-xs text-gray-500 px-2 flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-green-400" />
              {message.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </div>
      ))}

      {isListening && <LiveTranscript />}

      {isThinking && <TypingIndicator />}

      <div ref={messagesEndRef} />
    </div>
  )
}
