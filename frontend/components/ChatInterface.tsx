'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, RefreshCw, FileText, Bot, User } from 'lucide-react'
import { searchQuery, QueryResponse } from '@/lib/api'
import ResponseDisplay from './ResponseDisplay'
import { cn } from '@/lib/utils'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  response?: QueryResponse
  timestamp: Date
}

interface ChatInterfaceProps {
  documentProcessed: boolean
  onReset?: () => void
}

export default function ChatInterface({ documentProcessed, onReset }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await searchQuery(userMessage.content)
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.final_response || response.answer || 'No response available',
        response: response,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      setError(err.message || 'An error occurred while processing your query')
      console.error('Query error:', err)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleReset = () => {
    setMessages([])
    setError(null)
    onReset?.()
  }

  if (!documentProcessed) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <FileText className="w-16 h-16 text-slate-400 mb-4" />
        <p className="text-lg text-slate-600 dark:text-slate-400 mb-2">
          No document processed yet
        </p>
        <p className="text-sm text-slate-500 dark:text-slate-500">
          Please upload and process a document first using the sidebar
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Bot className="w-5 h-5" />
          Research Chat
        </h2>
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Reset Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <p className="text-lg mb-2">Start a conversation</p>
            <p className="text-sm">Ask questions about your document below</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-3',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
            )}
            <div
              className={cn(
                'max-w-[80%] rounded-lg px-4 py-3 overflow-hidden',
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700'
              )}
            >
              <div className="flex items-start gap-2">
                {message.role === 'user' && (
                  <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="whitespace-pre-wrap break-words overflow-wrap-anywhere">{message.content}</p>
                  {message.role === 'assistant' && message.response && (
                    <div className="mt-4">
                      <ResponseDisplay response={message.response} />
                    </div>
                  )}
                </div>
              </div>
            </div>
            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center">
                <User className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-lg px-4 py-3 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary-600 dark:text-primary-400" />
                <span className="text-slate-600 dark:text-slate-400">Researching your question...</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-200 dark:border-slate-700 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about your document..."
            disabled={loading}
            className="flex-1 px-4 py-3 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className={cn(
              'px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2',
              loading || !input.trim()
                ? 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-primary-600 hover:bg-primary-700 text-white'
            )}
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

