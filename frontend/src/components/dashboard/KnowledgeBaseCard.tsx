import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { BookOpen, FileText, Trash2 } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { useDeleteKnowledgeBase } from "@/hooks/useKnowledgeBases"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { KnowledgeBase } from "@/types"

interface KnowledgeBaseCardProps {
  kb: KnowledgeBase
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function KnowledgeBaseCard({ kb }: KnowledgeBaseCardProps) {
  const navigate = useNavigate()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const deleteMutation = useDeleteKnowledgeBase()

  function handleDelete() {
    deleteMutation.mutate(kb.id, {
      onSuccess: () => {
        setConfirmOpen(false)
        toast.success("Knowledge base deleted.")
      },
      onError: (error) => {
        toast.error(error.message)
      },
    })
  }

  return (
    <>
      <article
        onClick={() => navigate(`/knowledge-base/${kb.id}`)}
        className={cn(
          "group relative cursor-pointer rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-6",
          "shadow-[var(--shadow-sm)] transition-all duration-200",
          "hover:border-[var(--border-secondary)] hover:shadow-[var(--shadow-md)] hover:-translate-y-px"
        )}
      >
        {/* Delete button — top-right on hover */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            setConfirmOpen(true)
          }}
          className={cn(
            "absolute top-4 right-4 p-1.5 rounded-md opacity-0 transition-all duration-150",
            "text-[var(--text-tertiary)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-light)]",
            "group-hover:opacity-100"
          )}
          aria-label={`Delete ${kb.name}`}
        >
          <Trash2 size={16} strokeWidth={1.75} />
        </button>

        {/* Icon + Title */}
        <div className="flex items-start gap-3 mb-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--accent-primary-ghost)]">
            <BookOpen size={18} strokeWidth={1.75} className="text-[var(--accent-primary)]" />
          </div>
          <h3 className="text-base font-semibold text-[var(--text-primary)] font-body leading-snug pt-1 pr-6 line-clamp-1">
            {kb.name}
          </h3>
        </div>

        {/* Description */}
        {kb.description && (
          <p className="text-sm text-[var(--text-secondary)] line-clamp-2 mb-4 leading-relaxed">
            {kb.description}
          </p>
        )}
        {!kb.description && <div className="mb-4" />}

        {/* Metadata footer */}
        <div className="flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
          <span className="flex items-center gap-1">
            <FileText size={13} strokeWidth={1.75} />
            {kb.document_count} {kb.document_count === 1 ? "doc" : "docs"}
          </span>
          <span aria-hidden="true">·</span>
          <span>Created {formatDate(kb.created_at)}</span>
        </div>
      </article>

      {/* Delete confirmation dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete knowledge base</DialogTitle>
            <DialogDescription>
              Are you sure? This will permanently delete this knowledge base and
              all its documents. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
