'use client'

import { Send, Loader2 } from 'lucide-react'
import { useState } from 'react'

interface QueryInputProps {
  query: string
  setQuery: (query: string) => void
  onSubmit: (e: React.FormEvent) => void
  disabled?: boolean
}

export default function QueryInput({ query, setQuery, onSubmit, disabled }: QueryInputProps) {
  const [isFocused, setIsFocused] = useState(false)

  return (
    <form onSubmit={onSubmit} className="w-full">
      <div
        className={`
          relative flex items-center gap-3
          bg-white dark:bg-slate-800
          rounded-xl shadow-lg
          border-2 transition-all
          ${isFocused ? 'border-primary-500 shadow-primary-200' : 'border-slate-200 dark:border-slate-700'}
        `}
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Ask a question about your research..."
          disabled={disabled}
          className="
            flex-1 px-6 py-4
            bg-transparent
            text-slate-900 dark:text-white
            placeholder-slate-400 dark:placeholder-slate-500
            text-lg
            outline-none
            disabled:opacity-50
          "
        />
        <button
          type="submit"
          disabled={disabled || !query.trim()}
          className={`
            mr-3 p-3 rounded-lg
            transition-all
            ${disabled || !query.trim()
              ? 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700 text-white shadow-md hover:shadow-lg'
            }
          `}
        >
          {disabled ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </form>
  )
}

