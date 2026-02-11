import { useCallback, useRef, useState, type KeyboardEvent } from "react"
import { ArrowUp } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask a question about your documents...",
}: ChatInputProps) {
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const canSend = value.trim().length > 0 && !disabled

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = "auto"
    // Clamp between 1 row (~44px) and 6 rows (~168px)
    textarea.style.height = `${Math.min(textarea.scrollHeight, 168)}px`
  }, [])

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue("")
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
  }, [value, disabled, onSend])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  return (
    <div className="shrink-0 border-t border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-end gap-3">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            setValue(e.target.value)
            adjustHeight()
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={cn(
            "min-w-0 flex-1 resize-none rounded-xl border border-[var(--border-secondary)] bg-[var(--bg-secondary)]",
            "px-4 py-3 text-base text-[var(--text-primary)]",
            "placeholder:text-[var(--text-tertiary)]",
            "shadow-[var(--shadow-input)]",
            "transition-[border-color,box-shadow] duration-200 ease-[var(--ease-default)]",
            "focus:border-[var(--border-focus)] focus:shadow-[var(--shadow-focus)] focus:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50"
          )}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          className={cn(
            "flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-full",
            "bg-[var(--accent-primary)] text-white",
            "transition-all duration-150 ease-[var(--ease-default)]",
            canSend
              ? "hover:bg-[var(--accent-primary-hover)] active:scale-[0.92]"
              : "opacity-40 cursor-not-allowed"
          )}
        >
          <ArrowUp size={18} strokeWidth={2} />
        </button>
      </div>
    </div>
  )
}
