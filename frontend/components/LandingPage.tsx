'use client'

import { useState } from 'react'
import { Bot, FileText, Search, Brain, Zap, ArrowRight, CheckCircle2, Database, Globe, BookOpen, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function LandingPage() {
  const [isNavigating, setIsNavigating] = useState(false)
  const router = useRouter()

  const features = [
    {
      icon: FileText,
      title: 'Document Processing',
      description: 'Upload and process PDF documents with advanced parsing and indexing capabilities using TensorLake.',
    },
    {
      icon: Search,
      title: 'Intelligent Search',
      description: 'Multi-source research combining document analysis, web search via Firecrawl, and academic research.',
    },
    {
      icon: Brain,
      title: 'AI Agents',
      description: 'Powered by CrewAI with specialized agents for research, analysis, and synthesis.',
    },
    {
      icon: Database,
      title: 'Vector Database',
      description: 'Efficient semantic search using Qdrant vector database with Voyage AI embeddings.',
    },
    {
      icon: BookOpen,
      title: 'Memory & Context',
      description: 'Persistent conversation memory and context management powered by Zep Cloud.',
    },
    {
      icon: Zap,
      title: 'Fast & Accurate',
      description: 'Real-time responses with citations and source attribution for research integrity.',
    },
  ]

  const techStack = [
    { name: 'TensorLake', description: 'Document Processing' },
    { name: 'Voyage AI', description: 'Embeddings' },
    { name: 'Zep Cloud', description: 'Memory Layer' },
    { name: 'Firecrawl', description: 'Web Search' },
    { name: 'CrewAI', description: 'Multi-Agent Framework' },
    { name: 'Qdrant', description: 'Vector Database' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Navigation */}
      <nav className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            <span className="text-xl font-bold text-slate-900 dark:text-white">
              AI Research Assistant
            </span>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 max-w-7xl text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            <span>Powered by Advanced AI Technology</span>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white mb-6 leading-tight">
            Context Engineering
            <br />
            <span className="text-primary-600 dark:text-primary-400">Research Assistant</span>
          </h1>
          
          <p className="text-xl text-slate-600 dark:text-slate-300 mb-8 leading-relaxed">
            Transform your research workflow with AI-powered document analysis, intelligent search, 
            and multi-agent collaboration. Get comprehensive answers with citations and source attribution.
          </p>

          <div className="flex justify-center items-center">
            <button
              onClick={() => {
                setIsNavigating(true)
                router.push('/app')
              }}
              disabled={isNavigating}
              className="px-8 py-4 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-500 disabled:cursor-wait text-white rounded-lg font-semibold text-lg transition-all transform hover:scale-105 disabled:transform-none flex items-center gap-2 shadow-lg disabled:opacity-75"
            >
              {isNavigating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  Start Researching
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20 max-w-7xl">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Powerful Features
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300">
            Everything you need for comprehensive research and analysis
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg border border-slate-200 dark:border-slate-700 hover:shadow-xl transition-shadow"
              >
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-300">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="container mx-auto px-4 py-20 max-w-7xl">
        <div className="bg-gradient-to-r from-primary-600 to-blue-600 rounded-2xl p-12 text-white">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Built with Modern Technology</h2>
            <p className="text-xl text-primary-100">
              Leveraging cutting-edge AI and data processing tools
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {techStack.map((tech, index) => (
              <div
                key={index}
                className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center hover:bg-white/20 transition-colors"
              >
                <p className="font-semibold text-lg mb-1">{tech.name}</p>
                <p className="text-sm text-primary-100">{tech.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="container mx-auto px-4 py-20 max-w-7xl">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            How It Works
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300">
            Simple steps to get started with your research
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="text-center">
            <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
              1
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              Upload Document
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Upload your PDF document. Our system will process and index it for semantic search.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
              2
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              Ask Questions
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Ask research questions. Our AI agents will search documents, web, and academic sources.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
              3
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              Get Answers
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Receive comprehensive answers with citations and source attribution.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 max-w-7xl">
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 dark:from-slate-800 dark:to-slate-700 rounded-2xl p-12 text-center text-white">
          <h2 className="text-4xl font-bold mb-4">Ready to Transform Your Research?</h2>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Start using the AI Research Assistant today and experience the future of research and analysis.
          </p>
          <button
            onClick={() => {
              setIsNavigating(true)
              router.push('/app')
            }}
            disabled={isNavigating}
            className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-500 disabled:cursor-wait text-white rounded-lg font-semibold text-lg transition-all transform hover:scale-105 disabled:transform-none shadow-lg disabled:opacity-75"
          >
            {isNavigating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                Get Started Now
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-12 max-w-7xl border-t border-slate-200 dark:border-slate-700">
        <div className="text-center text-slate-600 dark:text-slate-400">
          <p className="mb-2">© 2025 AI Research Assistant. Built with Next.js, FastAPI, and CrewAI.</p>
          <p className="text-sm">
            Context Engineering Workflow with RAG, Web Search, Memory & Academic Research
          </p>
        </div>
      </footer>
    </div>
  )
}

