"use client"

import { useEffect, useRef, memo, useCallback } from "react"
import { Volume2, User, Bot, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'

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

function MessageList({ messages, isThinking, isListening, isSpeaking, currentTranscript }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Use requestAnimationFrame for smoother scrolling
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
    }
    requestAnimationFrame(scrollToBottom)
  }, [messages.length]) // Only depend on message count, not content

  const playAudio = useCallback((base64Audio: string) => {
    const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`)
    audio.preload = 'auto' // Preload for faster playback
    audio.play().catch(console.error)
  }, [])

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
    <div className="space-y-4 max-h-[450px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-primary/20 scrollbar-track-transparent">
      {messages.map((message, index) => (
        <div
          key={message.id}
          className={`flex gap-3 ${message.sender === "user" ? "flex-row-reverse" : "flex-row"} animate-in fade-in slide-in-from-bottom-2 duration-300`}
          style={{ animationDelay: `${Math.min(index * 30, 300)}ms` }} // Cap delay for better performance
        >
          <Avatar
            className={`h-9 w-9 shrink-0 border-2 ${message.sender === "user" ? "bg-gradient-to-br from-green-600 to-green-700 border-green-200" : "bg-gradient-to-br from-green-600 to-emerald-600 border-green-200"}`}
          >
            <AvatarFallback className="text-white">
              {message.sender === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </AvatarFallback>
          </Avatar>

          <div className={`flex flex-col gap-1.5 max-w-[75%] ${message.sender === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`rounded-2xl px-4 py-3 shadow-md transition-all duration-200 hover:shadow-lg ${
                message.sender === "user"
                  ? "bg-gradient-to-br from-green-600 to-green-700 text-white rounded-tr-sm border border-green-300/30"
                  : "bg-gradient-to-br from-green-50 to-emerald-50 text-gray-800 border border-green-200/50 rounded-tl-sm"
              }`}
            >
              {message.sender === "assistant" ? (
                <div className={`prose prose-sm max-w-none ${message.isStreaming ? "animate-in fade-in duration-200" : ""}`}>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeSanitize]}
                    components={{
                      // Style headers
                      h1: ({node, ...props}) => <h1 className="text-lg font-bold text-green-800 mt-2 mb-1" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-base font-bold text-green-700 mt-2 mb-1" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-sm font-bold text-green-700 mt-1 mb-0.5" {...props} />,
                      // Style paragraphs
                      p: ({node, ...props}) => <p className="text-sm leading-relaxed mb-2 last:mb-0 text-gray-800" {...props} />,
                      // Style lists
                      ul: ({node, ...props}) => <ul className="list-none space-y-1 my-2" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-1 my-2 ml-2" {...props} />,
                      li: ({node, ...props}) => <li className="text-sm leading-relaxed text-gray-800" {...props} />,
                      // Style strong/bold
                      strong: ({node, ...props}) => <strong className="font-bold text-green-800" {...props} />,
                      // Style emphasis/italic
                      em: ({node, ...props}) => <em className="italic text-gray-700" {...props} />,
                      // Style code
                      code: ({node, inline, ...props}: any) => 
                        inline ? (
                          <code className="bg-green-100 text-green-800 px-1 py-0.5 rounded text-xs font-mono" {...props} />
                        ) : (
                          <code className="block bg-green-100 text-green-800 p-2 rounded text-xs font-mono my-1 overflow-x-auto" {...props} />
                        ),
                      // Style links
                      a: ({node, ...props}) => <a className="text-green-600 hover:text-green-700 underline font-medium" target="_blank" rel="noopener noreferrer" {...props} />,
                      // Style blockquotes
                      blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-green-500 pl-3 my-2 italic text-gray-700" {...props} />,
                    }}
                  >
                    {message.text}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className={`text-pretty leading-relaxed text-sm ${message.isStreaming ? "animate-in fade-in duration-200" : ""}`}>
                  {message.text}
                </p>
              )}

              {message.audio && message.sender === "assistant" && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => playAudio(message.audio!)}
                  className="mt-2 h-7 px-2.5 hover:bg-green-200/50 rounded-full transition-all hover:scale-105 text-green-700"
                >
                  <Volume2 className="h-3 w-3 mr-1" />
                  <span className="text-xs font-medium">Play</span>
                </Button>
              )}
            </div>

            <p className="text-xs text-gray-500 px-2 flex items-center gap-1 hidden">
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

// Export memoized component
export default memo(MessageList)
