'use client'

import { useState } from 'react'
import { 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  ExternalLink, 
  TrendingUp,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Brain,
  Globe,
  Library
} from 'lucide-react'
import { QueryResponse } from '../lib/api'
import { cn } from '../lib/utils'
import CitationsDisplay from './CitationsDisplay'

interface ResponseDisplayProps {
  response: QueryResponse
}

export default function ResponseDisplay({ response }: ResponseDisplayProps) {
  const { status, answer, citations, confidence, missing, source_used, context_sources, evaluation_result } = response
  const [showCitations, setShowCitations] = useState(false)

  return (
    <div className="space-y-4 mt-4">
      {/* Status Badges */}
      <div className="flex flex-wrap items-center gap-3">
        {status === 'OK' ? (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-semibold">Sufficient Context</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-4 py-2 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 rounded-lg">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">Insufficient Context</span>
          </div>
        )}
        
        {/* Confidence Score */}
        <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-lg">
          <TrendingUp className="w-5 h-5" />
          <span className="font-semibold">
            Confidence: {(confidence * 100).toFixed(1)}%
          </span>
        </div>

        {/* Source Badge */}
        <div className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg">
          <span className="text-sm font-medium">Source: {source_used}</span>
        </div>
      </div>

      {/* Answer */}
      {answer && (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Answer
          </h2>
          <div className="prose prose-slate dark:prose-invert max-w-none">
            <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
              {answer}
            </p>
          </div>
        </div>
      )}

      {/* Citations Toggle */}
      {(citations?.length > 0 || context_sources || evaluation_result) && (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
          <button
            onClick={() => setShowCitations(!showCitations)}
            className="w-full flex items-center justify-between p-6 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
          >
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              Sources & Citations
              {citations && citations.length > 0 && (
                <span className="text-sm font-normal text-slate-500 dark:text-slate-400">
                  ({citations.length})
                </span>
              )}
            </h2>
            {showCitations ? (
              <ChevronUp className="w-5 h-5 text-slate-500 dark:text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-500 dark:text-slate-400" />
            )}
          </button>

          {showCitations && (
            <div className="px-6 pb-6 space-y-6">
              {/* Source Relevance Summary */}
              {evaluation_result && (
                <div className="border-b border-slate-200 dark:border-slate-700 pb-4">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
                    Source Relevance Summary
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Relevant Sources:
                      </p>
                      <ul className="space-y-1">
                        {evaluation_result.relevant_sources?.map((source, idx) => {
                          const score = evaluation_result.relevance_scores?.[source]
                          return (
                            <li key={idx} className="text-sm text-slate-600 dark:text-slate-400">
                              • <span className="font-medium">{source}</span>
                              {score !== undefined && (
                                <span className="ml-2">({(score * 100).toFixed(1)}%)</span>
                              )}
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Reasoning:
                      </p>
                      <p className="text-sm text-slate-600 dark:text-slate-400 italic">
                        {evaluation_result.reasoning || 'No reasoning provided'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Citations Display */}
              <CitationsDisplay
                citations={citations || []}
                contextSources={context_sources}
                evaluationResult={evaluation_result}
              />
            </div>
          )}
        </div>
      )}

      {/* Missing Information */}
      {missing && missing.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl shadow-lg p-6 border border-yellow-200 dark:border-yellow-800">
          <h2 className="text-xl font-semibold text-yellow-900 dark:text-yellow-200 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Missing Information
          </h2>
          <ul className="list-disc list-inside space-y-2 text-yellow-800 dark:text-yellow-300">
            {missing.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
