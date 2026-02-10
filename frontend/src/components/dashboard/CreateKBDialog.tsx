import { useState } from "react"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"
import { useCreateKnowledgeBase } from "@/hooks/useKnowledgeBases"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

interface CreateKBDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const MAX_DESCRIPTION_LENGTH = 500

export function CreateKBDialog({ open, onOpenChange }: CreateKBDialogProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [nameError, setNameError] = useState("")
  const createMutation = useCreateKnowledgeBase()

  function resetForm() {
    setName("")
    setDescription("")
    setNameError("")
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      resetForm()
    }
    onOpenChange(nextOpen)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const trimmedName = name.trim()
    if (!trimmedName) {
      setNameError("Name is required.")
      return
    }

    setNameError("")

    createMutation.mutate(
      {
        name: trimmedName,
        description: description.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success("Knowledge base created.")
          handleOpenChange(false)
        },
        onError: (error) => {
          toast.error(error.message)
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create knowledge base</DialogTitle>
            <DialogDescription>
              Upload your documents and start asking questions.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-5 space-y-4">
            {/* Name field */}
            <div className="space-y-1.5">
              <Label htmlFor="kb-name" className="text-sm font-medium text-[var(--text-secondary)]">
                Name
              </Label>
              <Input
                id="kb-name"
                placeholder="e.g. Company Handbook"
                value={name}
                onChange={(e) => {
                  setName(e.target.value)
                  if (nameError) setNameError("")
                }}
                maxLength={100}
                autoFocus
                aria-invalid={!!nameError}
              />
              {nameError && (
                <p className="text-xs text-[var(--color-error)]">{nameError}</p>
              )}
            </div>

            {/* Description field */}
            <div className="space-y-1.5">
              <Label htmlFor="kb-description" className="text-sm font-medium text-[var(--text-secondary)]">
                Description
                <span className="text-[var(--text-tertiary)] font-normal ml-1">(optional)</span>
              </Label>
              <Textarea
                id="kb-description"
                placeholder="What documents will this knowledge base contain?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={MAX_DESCRIPTION_LENGTH}
                rows={3}
                className="resize-none"
              />
              <p className="text-xs text-[var(--text-tertiary)] text-right">
                {description.length}/{MAX_DESCRIPTION_LENGTH}
              </p>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Creating...
                </>
              ) : (
                "Create"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
