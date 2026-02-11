import { useCallback, useRef, useState } from "react"
import { Upload } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { useUploadDocument } from "@/hooks/useDocuments"

interface DocumentUploadProps {
  kbId: string
  onUploadStart?: (tempId: string, fileName: string) => void
  onUploadEnd?: (tempId: string) => void
}

const ACCEPTED_TYPES = ".pdf,.txt,.md"
const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50 MB

export function DocumentUpload({ kbId, onUploadStart, onUploadEnd }: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const uploadMutation = useUploadDocument(kbId)

  const handleFiles = useCallback(
    (files: FileList | File[]) => {
      const fileArray = Array.from(files)

      for (const file of fileArray) {
        // Client-side validation (backend validates too)
        if (file.size > MAX_FILE_SIZE) {
          toast.error(`${file.name} exceeds the 50MB limit.`)
          continue
        }

        const ext = file.name.split(".").pop()?.toLowerCase()
        if (!ext || !["pdf", "txt", "md"].includes(ext)) {
          toast.error(
            `${file.name} is not supported. Please upload PDF, TXT, or MD files.`
          )
          continue
        }

        // Show temp "Uploading" entry immediately
        const tempId = crypto.randomUUID()
        onUploadStart?.(tempId, file.name)

        uploadMutation.mutate(file, {
          onSuccess: () => {
            // Real document is already in the query cache (set by the hook).
            // Remove the temp entry — the transition is seamless.
            onUploadEnd?.(tempId)
          },
          onError: (error) => {
            onUploadEnd?.(tempId)
            toast.error(error.message)
          },
        })
      }
    },
    [uploadMutation, onUploadStart, onUploadEnd]
  )

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files)
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(false)
  }

  function handleClick() {
    inputRef.current?.click()
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files)
      // Reset input so same file can be re-uploaded
      e.target.value = ""
    }
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") handleClick()
      }}
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-10 cursor-pointer transition-all duration-200",
        isDragOver
          ? "border-[var(--accent-primary)] bg-[var(--accent-primary-ghost)] scale-[1.01]"
          : "border-[var(--border-secondary)] bg-[var(--bg-secondary)] hover:border-[var(--border-focus)]"
      )}
    >
      <Upload
        size={32}
        strokeWidth={1.75}
        className={cn(
          "transition-colors duration-200",
          isDragOver
            ? "text-[var(--accent-primary)]"
            : "text-[var(--text-tertiary)]"
        )}
      />
      <div className="text-center">
        <p className="text-sm font-medium text-[var(--text-secondary)]">
          Drop files here, or click to browse
        </p>
        <p className="text-xs text-[var(--text-tertiary)] mt-1">
          Supports PDF, TXT, MD · Max 50MB
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        multiple
        onChange={handleInputChange}
        className="hidden"
        aria-label="Upload documents"
      />
    </div>
  )
}
