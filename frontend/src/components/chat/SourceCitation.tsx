import { FileText } from "lucide-react"
import type { Source } from "@/types"

interface SourceCitationProps {
  source: Source
  index: number
}

export function SourceCitation({ source, index }: SourceCitationProps) {
  return (
    <div
      className="flex items-start gap-2.5 rounded-md border-l-3 border-[var(--accent-primary)] bg-[var(--chat-citation-bg)] px-3 py-2.5 animate-[slide-up_200ms_var(--ease-out)] cursor-pointer transition-colors duration-150 hover:bg-[var(--accent-primary-ghost)]"
      style={{ animationDelay: `${index * 50}ms`, animationFillMode: "both" }}
    >
      <FileText
        size={14}
        strokeWidth={1.75}
        className="mt-0.5 shrink-0 text-[var(--chat-citation-text)]"
      />
      <div className="min-w-0 flex-1">
        <p className="text-xs text-[var(--chat-citation-text)]">
          {source.file_name}
          <span className="ml-1.5 opacity-75">
            Section {source.chunk_index}
          </span>
        </p>
        {source.title ? (
          <p className="mt-0.5 text-sm font-semibold text-[var(--chat-citation-text)]">
            {source.title}
          </p>
        ) : source.content ? (
          <p className="mt-1 line-clamp-2 font-mono text-xs italic text-[var(--text-secondary)]">
            &ldquo;{source.content}&rdquo;
          </p>
        ) : null}
      </div>
    </div>
  )
}
