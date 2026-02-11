import { useState } from "react"
import { CheckCircle2, FileText, Loader2, Trash2, XCircle } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { useDocuments, useDeleteDocument } from "@/hooks/useDocuments"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { Document, UploadingFile } from "@/types"

interface DocumentListProps {
  kbId: string
  uploadingFiles?: UploadingFile[]
}

function StatusBadge({ status }: { status: Document["status"] }) {
  switch (status) {
    case "uploading":
      return (
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-warning)]">
          <Loader2 size={13} strokeWidth={2} className="animate-spin" />
          Uploading
        </span>
      )
    case "processing":
      return (
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-warning)]">
          <Loader2 size={13} strokeWidth={2} className="animate-spin" />
          Processing
        </span>
      )
    case "ready":
      return (
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-success)]">
          <CheckCircle2 size={13} strokeWidth={2} />
          Ready
        </span>
      )
    case "failed":
      return (
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-error)]">
          <XCircle size={13} strokeWidth={2} />
          Failed
        </span>
      )
  }
}

function DocumentRow({
  doc,
  kbId,
}: {
  doc: Document
  kbId: string
}) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const deleteMutation = useDeleteDocument(kbId)

  function handleDelete() {
    deleteMutation.mutate(doc.id, {
      onSuccess: () => {
        setConfirmOpen(false)
        toast.success("Document deleted.")
      },
      onError: (error) => {
        toast.error(error.message)
      },
    })
  }

  return (
    <>
      <div
        className={cn(
          "group flex items-center gap-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3",
          "transition-colors duration-150 hover:border-[var(--border-secondary)]"
        )}
      >
        {/* File icon */}
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[var(--accent-primary-ghost)]">
          <FileText
            size={16}
            strokeWidth={1.75}
            className="text-[var(--accent-primary)]"
          />
        </div>

        {/* Name + error message */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--text-primary)] truncate">
            {doc.file_name}
          </p>
          {doc.status === "failed" && doc.error_message && (
            <p className="text-xs text-[var(--color-error)] mt-0.5 truncate">
              {doc.error_message}
            </p>
          )}
        </div>

        {/* Chunk count (when ready) */}
        {doc.status === "ready" && doc.chunk_count > 0 && (
          <span className="text-xs text-[var(--text-tertiary)] shrink-0">
            {doc.chunk_count} {doc.chunk_count === 1 ? "section" : "sections"}
          </span>
        )}

        {/* Status badge */}
        <div className="shrink-0">
          <StatusBadge status={doc.status} />
        </div>

        {/* Delete button — visible on hover */}
        <button
          type="button"
          onClick={() => setConfirmOpen(true)}
          className={cn(
            "shrink-0 p-1.5 rounded-md opacity-0 transition-all duration-150",
            "text-[var(--text-tertiary)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-light)]",
            "group-hover:opacity-100"
          )}
          aria-label={`Delete ${doc.file_name}`}
        >
          <Trash2 size={14} strokeWidth={1.75} />
        </button>
      </div>

      {/* Delete confirmation */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{doc.file_name}"? This will
              remove the document and all its indexed content. This action cannot
              be undone.
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

function UploadingRow({ file }: { file: UploadingFile }) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3",
        "transition-colors duration-150"
      )}
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[var(--accent-primary-ghost)]">
        <FileText
          size={16}
          strokeWidth={1.75}
          className="text-[var(--accent-primary)]"
        />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[var(--text-primary)] truncate">
          {file.fileName}
        </p>
      </div>
      <div className="shrink-0">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-warning)]">
          <Loader2 size={13} strokeWidth={2} className="animate-spin" />
          Uploading
        </span>
      </div>
    </div>
  )
}

export function DocumentList({ kbId, uploadingFiles = [] }: DocumentListProps) {
  const { data: documents, isLoading } = useDocuments(kbId)

  if (isLoading) {
    return (
      <div className="space-y-2">
        {uploadingFiles.map((file) => (
          <UploadingRow key={file.tempId} file={file} />
        ))}
        {[1, 2].map((i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-lg border border-[var(--border-primary)] px-4 py-3 animate-pulse"
          >
            <div className="h-8 w-8 rounded-md bg-[var(--bg-tertiary)]" />
            <div className="flex-1 space-y-1.5">
              <div className="h-3.5 w-40 rounded bg-[var(--bg-tertiary)]" />
            </div>
            <div className="h-3 w-16 rounded bg-[var(--bg-tertiary)]" />
          </div>
        ))}
      </div>
    )
  }

  if ((!documents || documents.length === 0) && uploadingFiles.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      {uploadingFiles.map((file) => (
        <UploadingRow key={file.tempId} file={file} />
      ))}
      {documents?.map((doc) => (
        <DocumentRow key={doc.id} doc={doc} kbId={kbId} />
      ))}
    </div>
  )
}
