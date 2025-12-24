'use client'

import { useState, useEffect } from 'react'
import { Bot, FileText, CheckCircle2, AlertCircle, ArrowLeft, Loader2 } from 'lucide-react'
import ChatInterface from '../../components/ChatInterface'
import DocumentUpload from '../../components/DocumentUpload'
import { initializeAssistant, getAssistantStatus, AssistantStatus } from '../../lib/api'
import Link from 'next/link'

export default function AppPage() {
  const [assistantStatus, setAssistantStatus] = useState<AssistantStatus>({
    initialized: false,
    document_processed: false,
  })
  const [initializing, setInitializing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check assistant status on mount
    const loadStatus = async () => {
      setIsLoading(true)
      await checkStatus()
      setIsLoading(false)
    }
    loadStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const status = await getAssistantStatus()
      setAssistantStatus(status)
    } catch (err) {
      console.error('Failed to check status:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleInitialize = async () => {
    setInitializing(true)
    setError(null)
    try {
      const status = await initializeAssistant()
      setAssistantStatus(status)
    } catch (err: any) {
      setError(err.message || 'Failed to initialize assistant')
    } finally {
      setInitializing(false)
    }
  }

  const handleUploadSuccess = (documentName: string) => {
    setAssistantStatus((prev) => ({
      ...prev,
      document_processed: true,
      current_document: documentName,
    }))
  }

  const handleReset = () => {
    setAssistantStatus((prev) => ({
      ...prev,
      document_processed: false,
      current_document: undefined,
    }))
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-primary-600 dark:text-primary-400 animate-spin" />
          <p className="text-lg text-slate-600 dark:text-slate-400">Loading Research Assistant...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Header with Back Button */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>
          
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Bot className="w-10 h-10 text-primary-600 dark:text-primary-400" />
              <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
                AI Research Assistant
              </h1>
            </div>
            <p className="text-slate-600 dark:text-slate-300 text-lg">
              Context Engineering Workflow with RAG, Web Search, Memory & Academic Research
            </p>
            <div className="flex items-center justify-center gap-6 mt-4 text-sm text-slate-500 dark:text-slate-400">
              <span>Powered by TensorLake</span>
              <span>•</span>
              <span>Zep Memory</span>
              <span>•</span>
              <span>Firecrawl</span>
              <span>•</span>
              <span>CrewAI</span>
              <span>•</span>
              <span>Qdrant</span>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Assistant Status */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Assistant Status
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Initialized:</span>
                  {assistantStatus.initialized ? (
                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                      <CheckCircle2 className="w-4 h-4" />
                      <span className="text-sm font-medium">Online</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                      <AlertCircle className="w-4 h-4" />
                      <span className="text-sm font-medium">Offline</span>
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Document:</span>
                  {assistantStatus.document_processed ? (
                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                      <CheckCircle2 className="w-4 h-4" />
                      <span className="text-sm font-medium">Ready</span>
                    </div>
                  ) : (
                    <span className="text-sm text-slate-500 dark:text-slate-500">Not processed</span>
                  )}
                </div>
              </div>

              {!assistantStatus.initialized && (
                <button
                  onClick={handleInitialize}
                  disabled={initializing}
                  className="w-full mt-4 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                >
                  {initializing ? 'Initializing...' : 'Initialize Assistant'}
                </button>
              )}

              {error && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
              )}
            </div>

            {/* Document Upload */}
            {assistantStatus.initialized && (
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-200 dark:border-slate-700">
                <DocumentUpload
                  onUploadSuccess={handleUploadSuccess}
                  currentDocument={assistantStatus.current_document}
                />
              </div>
            )}
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 h-[calc(100vh-12rem)] flex flex-col">
              {assistantStatus.initialized ? (
                <ChatInterface
                  documentProcessed={assistantStatus.document_processed}
                  onReset={handleReset}
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full p-8">
                  <AlertCircle className="w-16 h-16 text-slate-400 mb-4" />
                  <p className="text-lg text-slate-600 dark:text-slate-400 mb-2">
                    Assistant not initialized
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-500 mb-4">
                    Please initialize the assistant using the sidebar to begin
                  </p>
                  <button
                    onClick={handleInitialize}
                    disabled={initializing}
                    className="px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                  >
                    {initializing ? 'Initializing...' : 'Initialize Assistant'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

