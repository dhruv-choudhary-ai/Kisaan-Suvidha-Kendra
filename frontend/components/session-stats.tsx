"use client"

import { Card } from "@/components/ui/card"
import { MessageSquare, Clock, Mic } from "lucide-react"

interface Message {
  id: string
  text: string
  audio?: string
  sender: "user" | "assistant"
  timestamp: Date
}

interface SessionStatsProps {
  messages: Message[]
  sessionId: string | null
}

export default function SessionStats({ messages, sessionId }: SessionStatsProps) {
  const userMessages = messages.filter((m) => m.sender === "user").length
  const assistantMessages = messages.filter((m) => m.sender === "assistant").length
  const totalMessages = messages.length

  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      <Card className="p-4 bg-gradient-to-br from-green-100 to-green-50 border-2 border-green-200/50 hover:shadow-lg transition-all">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-200/50">
            <MessageSquare className="h-5 w-5 text-green-700" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{totalMessages}</p>
            <p className="text-xs text-gray-600">Total Messages</p>
          </div>
        </div>
      </Card>

      <Card className="p-4 bg-gradient-to-br from-emerald-100 to-emerald-50 border-2 border-emerald-200/50 hover:shadow-lg transition-all">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-200/50">
            <Mic className="h-5 w-5 text-emerald-700" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{userMessages}</p>
            <p className="text-xs text-gray-600">Your Queries</p>
          </div>
        </div>
      </Card>

      <Card className="p-4 bg-gradient-to-br from-teal-100 to-teal-50 border-2 border-teal-200/50 hover:shadow-lg transition-all">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-teal-200/50">
            <Clock className="h-5 w-5 text-teal-700" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{assistantMessages}</p>
            <p className="text-xs text-gray-600">Responses</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
