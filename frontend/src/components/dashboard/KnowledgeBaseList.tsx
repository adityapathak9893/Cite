import { BookOpen, Plus } from "lucide-react"
import { useKnowledgeBases } from "@/hooks/useKnowledgeBases"
import { KnowledgeBaseCard } from "./KnowledgeBaseCard"
import { Button } from "@/components/ui/button"

interface KnowledgeBaseListProps {
  onCreateClick: () => void
}

function SkeletonCard() {
  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-6 animate-pulse">
      <div className="flex items-start gap-3 mb-3">
        <div className="h-9 w-9 rounded-lg bg-[var(--bg-tertiary)]" />
        <div className="h-5 w-32 rounded bg-[var(--bg-tertiary)] mt-1" />
      </div>
      <div className="space-y-2 mb-4">
        <div className="h-3.5 w-full rounded bg-[var(--bg-tertiary)]" />
        <div className="h-3.5 w-2/3 rounded bg-[var(--bg-tertiary)]" />
      </div>
      <div className="flex items-center gap-3">
        <div className="h-3 w-16 rounded bg-[var(--bg-tertiary)]" />
        <div className="h-3 w-24 rounded bg-[var(--bg-tertiary)]" />
      </div>
    </div>
  )
}

export function KnowledgeBaseList({ onCreateClick }: KnowledgeBaseListProps) {
  const { data: knowledgeBases, isLoading, isError, error } = useKnowledgeBases()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <p className="text-sm text-[var(--color-error)]">
          {error?.message ?? "Failed to load knowledge bases."}
        </p>
      </div>
    )
  }

  if (!knowledgeBases || knowledgeBases.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--accent-primary-ghost)] mb-5">
          <BookOpen size={28} strokeWidth={1.75} className="text-[var(--accent-primary)]" />
        </div>
        <h2 className="text-lg font-semibold text-[var(--text-primary)] font-body mb-2">
          No knowledge bases yet
        </h2>
        <p className="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
          Upload your documents and start asking questions. Create your first
          knowledge base to get started.
        </p>
        <Button onClick={onCreateClick}>
          <Plus size={16} strokeWidth={2} />
          Create Knowledge Base
        </Button>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
      {knowledgeBases.map((kb) => (
        <KnowledgeBaseCard key={kb.id} kb={kb} />
      ))}
    </div>
  )
}
