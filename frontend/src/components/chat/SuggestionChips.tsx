import { MessageSquare } from "lucide-react"

interface SuggestionChipsProps {
  onSelect: (message: string) => void
  disabled?: boolean
}

const SUGGESTIONS = [
  "Summarize the key points",
  "What are the main topics covered?",
  "Find important dates and deadlines",
  "List the key terms and definitions",
]

export function SuggestionChips({ onSelect, disabled }: SuggestionChipsProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6">
      <MessageSquare
        size={32}
        strokeWidth={1.75}
        className="mb-3 text-[var(--text-tertiary)]"
      />
      <p className="text-sm font-medium text-[var(--text-secondary)]">
        Ask anything about your documents
      </p>
      <p className="mt-1 text-xs text-[var(--text-tertiary)]">
        Get AI-powered answers with source citations
      </p>

      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((suggestion, i) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSelect(suggestion)}
            disabled={disabled}
            className="rounded-full border border-[var(--border-secondary)] bg-transparent px-4 py-2 text-sm font-medium text-[var(--text-secondary)] transition-all duration-150 ease-[var(--ease-default)] animate-[slide-up_200ms_var(--ease-bounce)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
            style={{
              animationDelay: `${i * 100}ms`,
              animationFillMode: "both",
            }}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}
