import { Globe } from "lucide-react"

interface DomainContextPanelProps {
  content: string
}

/**
 * Fenced panel for research-mode domain knowledge — content that goes
 * beyond the uploaded documents. Rendered below the main answer and
 * above the citation chips.
 */
export function DomainContextPanel({ content }: DomainContextPanelProps) {
  return (
    <div className="mt-2 rounded-lg border border-dashed border-[var(--border-secondary)] bg-[var(--bg-secondary)] px-3 py-2.5 animate-[slide-up_200ms_var(--ease-out)]">
      <p className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-tertiary)]">
        <Globe size={12} strokeWidth={1.75} className="shrink-0" />
        Domain context — beyond your documents
      </p>
      <p className="mt-1.5 whitespace-pre-wrap text-sm leading-relaxed text-[var(--text-secondary)]">
        {content}
      </p>
    </div>
  )
}
