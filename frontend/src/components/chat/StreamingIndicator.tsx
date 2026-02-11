export function StreamingIndicator() {
  return (
    <div className="flex justify-start animate-[slide-up_200ms_var(--ease-out)]">
      <div className="rounded-[16px_16px_16px_4px] border border-[var(--border-primary)] bg-[var(--chat-assistant-bg)] px-5 py-4">
        <div className="flex items-center gap-1.5">
          <span
            className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)] animate-dot-pulse"
            style={{ animationDelay: "0s" }}
          />
          <span
            className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)] animate-dot-pulse"
            style={{ animationDelay: "0.2s" }}
          />
          <span
            className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)] animate-dot-pulse"
            style={{ animationDelay: "0.4s" }}
          />
        </div>
      </div>
    </div>
  )
}
