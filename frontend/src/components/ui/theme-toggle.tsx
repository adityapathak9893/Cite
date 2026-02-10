import { Moon, Sun } from "lucide-react"
import { cn } from "@/lib/utils"

interface ThemeToggleProps {
  theme: "light" | "dark"
  onToggle: () => void
  collapsed?: boolean
}

export function ThemeToggle({ theme, onToggle, collapsed = false }: ThemeToggleProps) {
  const isDark = theme === "dark"

  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn(
        "relative flex items-center rounded-full transition-colors duration-200",
        "bg-[var(--bg-tertiary)]",
        collapsed ? "h-9 w-9 justify-center" : "h-9 w-[72px] p-1"
      )}
      aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
    >
      {collapsed ? (
        /* Collapsed: just show the icon */
        <span className="flex items-center justify-center text-[var(--text-secondary)]">
          {isDark ? (
            <Sun size={18} strokeWidth={1.75} />
          ) : (
            <Moon size={18} strokeWidth={1.75} />
          )}
        </span>
      ) : (
        <>
          {/* Sun icon (left) */}
          <span
            className={cn(
              "absolute left-2 top-1/2 -translate-y-1/2 transition-opacity duration-200",
              isDark ? "opacity-40" : "opacity-0"
            )}
          >
            <Sun size={14} strokeWidth={1.75} className="text-[var(--text-tertiary)]" />
          </span>

          {/* Moon icon (right) */}
          <span
            className={cn(
              "absolute right-2 top-1/2 -translate-y-1/2 transition-opacity duration-200",
              isDark ? "opacity-0" : "opacity-40"
            )}
          >
            <Moon size={14} strokeWidth={1.75} className="text-[var(--text-tertiary)]" />
          </span>

          {/* Sliding pill */}
          <span
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-full shadow-sm",
              "bg-[var(--bg-elevated)] border border-[var(--border-primary)]",
              "transition-all duration-300",
              isDark ? "translate-x-[36px]" : "translate-x-0"
            )}
            style={{ transitionTimingFunction: "cubic-bezier(0.34, 1.56, 0.64, 1)" }}
          >
            {isDark ? (
              <Moon size={14} strokeWidth={1.75} className="text-[var(--accent-primary)]" />
            ) : (
              <Sun size={14} strokeWidth={1.75} className="text-[var(--accent-primary)]" />
            )}
          </span>
        </>
      )}
    </button>
  )
}
