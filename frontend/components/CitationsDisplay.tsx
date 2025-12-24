'use client'

import { useState } from 'react'
import { 
  FileText, 
  Brain, 
  Globe, 
  Library, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Citation {
  label: string
  locator: string
  page_number?: number
  chunk_index?: number
  score?: number
  content?: string
}

interface ContextSources {
  rag_result?: any
  memory_result?: any
  web_result?: any
  tool_result?: any
}

interface EvaluationResult {
  relevant_sources?: string[]
  relevance_scores?: Record<string, number>
  reasoning?: string
}

interface CitationsDisplayProps {
  citations: Citation[]
  contextSources?: ContextSources
  evaluationResult?: EvaluationResult
}

export default function CitationsDisplay({ 
  citations, 
  contextSources, 
  evaluationResult 
}: CitationsDisplayProps) {
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set())

  const toggleSource = (sourceKey: string) => {
    setExpandedSources((prev) => {
      const next = new Set(prev)
      if (next.has(sourceKey)) {
        next.delete(sourceKey)
      } else {
        next.add(sourceKey)
      }
      return next
    })
  }

  const getSourceStatus = (sourceData: any): 'OK' | 'ERROR' | 'INSUFFICIENT_CONTEXT' | 'UNKNOWN' => {
    if (!sourceData) return 'UNKNOWN'
    
    if (sourceData.status === 'OK') return 'OK'
    if (sourceData.status === 'ERROR') return 'ERROR'
    if (sourceData.status === 'INSUFFICIENT_CONTEXT') return 'INSUFFICIENT_CONTEXT'
    
    // Check for implicit OK status
    if (sourceData.search_results || sourceData.answer || sourceData.context) {
      return 'OK'
    }
    
    return 'UNKNOWN'
  }

  const renderSourceContent = (sourceName: string, sourceData: any, status: string) => {
    if (status === 'ERROR') {
      const errorMsg = sourceData.error || sourceData.message || sourceData.answer || 'Unknown error'
      return (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <p className="text-red-800 dark:text-red-200">{errorMsg}</p>
        </div>
      )
    }

    if (status === 'INSUFFICIENT_CONTEXT') {
      return (
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <p className="text-yellow-800 dark:text-yellow-200">
            {sourceData.answer || 'No relevant information found'}
          </p>
        </div>
      )
    }

    if (sourceName === 'Memory (History)') {
      // Try to get context, fallback to answer if context is missing
      const context = sourceData.context || sourceData.answer || ''
      
      // If context is empty or just whitespace, show a message
      if (!context || (typeof context === 'string' && context.trim() === '')) {
        return (
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <p className="text-yellow-800 dark:text-yellow-200">
              Memory context is not available. This may be because no previous conversation history exists.
            </p>
          </div>
        )
      }
      
      return (
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Memory Context:
            </p>
            {Array.isArray(context) ? (
              <ul className="space-y-1">
                {context.slice(0, 6).map((item: any, idx: number) => (
                  <li key={idx} className="text-sm text-slate-600 dark:text-slate-400">
                    • {String(item).substring(0, 200)}
                    {String(item).length > 200 && '...'}
                  </li>
                ))}
                {context.length > 6 && (
                  <li className="text-sm text-slate-500 dark:text-slate-500 italic">
                    ...and {context.length - 6} more items
                  </li>
                )}
              </ul>
            ) : (
              <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">
                {String(context).substring(0, 1000)}
                {String(context).length > 1000 && '...'}
              </p>
            )}
          </div>
          {sourceData.relevance_assessment?.citations && (
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Citations:
              </p>
              <ul className="space-y-1">
                {sourceData.relevance_assessment.citations.map((citation: any, idx: number) => (
                  <li key={idx} className="text-sm text-slate-600 dark:text-slate-400">
                    • <span className="font-medium">{citation.label}</span> ({citation.locator})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )
    }

    if (sourceName === 'Web Search') {
      const searchResults = sourceData.search_results || []
      const answer = sourceData.answer || ''
      
      return (
        <div className="space-y-3">
          {searchResults.length > 0 && (
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Web Search Results:
              </p>
              <ul className="space-y-2">
                {searchResults.slice(0, 3).map((result: any, idx: number) => (
                  <li key={idx} className="text-sm">
                    <a
                      href={result.url || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 dark:text-primary-400 hover:underline font-medium"
                    >
                      {result.title || `Result ${idx + 1}`}
                    </a>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                      {String(result.content || '').substring(0, 150)}...
                    </p>
                  </li>
                ))}
                {searchResults.length > 3 && (
                  <li className="text-sm text-slate-500 dark:text-slate-500 italic">
                    ...and {searchResults.length - 3} more results
                  </li>
                )}
              </ul>
            </div>
          )}
          {answer && searchResults.length === 0 && (
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Web Search Content:
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">
                {answer.substring(0, 1000)}
                {answer.length > 1000 && '...'}
              </p>
            </div>
          )}
        </div>
      )
    }

    if (sourceName === 'RAG (Documents)') {
      const answer = sourceData.answer || ''
      const citations = sourceData.citations || []
      
      return (
        <div className="space-y-3">
          {answer && (
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Retrieved Context:
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {answer.substring(0, 500)}
                {answer.length > 500 && '...'}
              </p>
            </div>
          )}
          {citations.length > 0 && (
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Citations:
              </p>
              <ul className="space-y-1">
                {citations.map((citation: any, idx: number) => (
                  <li key={idx} className="text-sm text-slate-600 dark:text-slate-400">
                    • <span className="font-medium">{citation.label || `Citation ${idx + 1}`}</span>
                    {citation.page_number !== undefined && (
                      <span> (Page {citation.page_number}</span>
                    )}
                    {citation.chunk_index !== undefined && (
                      <span>, Chunk {citation.chunk_index}</span>
                    )}
                    {citation.score !== undefined && (
                      <span>, Score: {citation.score.toFixed(3)}</span>
                    )}
                    {citation.page_number !== undefined && ')'}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )
    }

    return (
      <div>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          {sourceData.answer ? String(sourceData.answer).substring(0, 300) : 'No content available'}
          {sourceData.answer && String(sourceData.answer).length > 300 && '...'}
        </p>
      </div>
    )
  }

  const allSources = [
    { key: 'rag', name: 'RAG (Documents)', icon: FileText, data: contextSources?.rag_result },
    { key: 'memory', name: 'Memory (History)', icon: Brain, data: contextSources?.memory_result },
    { key: 'web', name: 'Web Search', icon: Globe, data: contextSources?.web_result },
    { key: 'tool', name: 'ArXiv Papers', icon: Library, data: contextSources?.tool_result },
  ].filter((source) => source.data)

  const relevantSourceKeys = evaluationResult?.relevant_sources || []
  const filteredSources = relevantSourceKeys.length > 0
    ? allSources.filter((source) => {
        const sourceKeyMap: Record<string, string> = {
          'RAG': 'rag',
          'Memory': 'memory',
          'Web': 'web',
          'ArXiv': 'tool',
        }
        return relevantSourceKeys.some((key) => sourceKeyMap[key] === source.key)
      })
    : allSources

  return (
    <div className="space-y-4">
      {/* Simple Citations List */}
      {citations.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
            Citations ({citations.length})
          </h3>
          <div className="space-y-2">
            {citations.map((citation, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              >
                <ExternalLink className="w-4 h-4 text-primary-600 dark:text-primary-400 mt-1 flex-shrink-0" />
                <div className="flex-1">
                  <p className="font-medium text-slate-900 dark:text-white">
                    {citation.label}
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    {citation.locator}
                    {citation.page_number !== undefined && ` (Page ${citation.page_number})`}
                    {citation.score !== undefined && ` - Score: ${citation.score.toFixed(3)}`}
                  </p>
                  {citation.content && (
                    <p className="text-xs text-slate-500 dark:text-slate-500 mt-2 italic">
                      {citation.content.substring(0, 200)}
                      {citation.content.length > 200 && '...'}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Context Sources */}
      {filteredSources.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
            Context Sources
          </h3>
          <div className="space-y-2">
            {filteredSources.map(({ key, name, icon: Icon, data }) => {
              const status = getSourceStatus(data)
              const isExpanded = expandedSources.has(key)
              
              return (
                <div
                  key={key}
                  className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden"
                >
                  <button
                    onClick={() => toggleSource(key)}
                    className="w-full flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                      <span className="font-medium text-slate-900 dark:text-white">{name}</span>
                      <span
                        className={cn(
                          'px-2 py-1 rounded text-xs font-medium',
                          status === 'OK'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                            : status === 'ERROR'
                            ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                            : status === 'INSUFFICIENT_CONTEXT'
                            ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200'
                            : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
                        )}
                      >
                        {status}
                      </span>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                    )}
                  </button>
                  {isExpanded && (
                    <div className="p-4 border-t border-slate-200 dark:border-slate-700">
                      {renderSourceContent(name, data, status)}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

