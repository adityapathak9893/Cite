import { useCallback, useEffect, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
import { LayoutDashboard, LogOut, Menu, X } from "lucide-react"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { cn } from "@/lib/utils"

type Theme = "light" | "dark" | "system"

function getResolvedTheme(stored: Theme): "light" | "dark" {
  if (stored === "dark") return "dark"
  if (stored === "light") return "light"
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

export function Sidebar() {
  const { user, signOut } = useAuth()
  const location = useLocation()
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem("cite-theme") as Theme) ?? "system"
  )
  // TODO: wire up collapse toggle (Phase 2+)
  const [collapsed, _setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const resolvedTheme = getResolvedTheme(theme)

  const applyTheme = useCallback((newTheme: Theme) => {
    setTheme(newTheme)
    localStorage.setItem("cite-theme", newTheme)
    const resolved = getResolvedTheme(newTheme)
    document.documentElement.setAttribute("data-theme", resolved)
  }, [])

  function toggleTheme() {
    applyTheme(resolvedTheme === "light" ? "dark" : "light")
  }

  useEffect(() => {
    const resolved = getResolvedTheme(theme)
    document.documentElement.setAttribute("data-theme", resolved)
  }, [theme])

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  ]

  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* Logo area */}
      <div className="flex h-[60px] items-center px-4 border-b border-[var(--border-primary)]">
        <Link to="/dashboard" className="flex items-center gap-2">
          <span className="font-display text-xl font-bold text-[var(--text-primary)] tracking-tight">
            {collapsed ? "C" : "Cite"}
          </span>
          {!collapsed && (
            <span className="text-xs font-body text-[var(--text-tertiary)] mt-1">
              by Weaverbit
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path
          const Icon = item.icon
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "relative flex items-center gap-2.5 h-9 rounded-md px-3 text-sm font-medium transition-[background-color,color] duration-150",
                isActive
                  ? "bg-[var(--accent-primary-ghost)] text-[var(--accent-primary)]"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
              )}
            >
              {/* Left accent bar for active item */}
              {isActive && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full bg-[var(--accent-primary)]" />
              )}
              <Icon size={18} strokeWidth={1.75} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-3 pb-3 space-y-3 border-t border-[var(--border-primary)] pt-3">
        {/* Theme toggle — pill switch */}
        <div className={cn("flex", collapsed ? "justify-center" : "justify-start")}>
          <ThemeToggle
            theme={resolvedTheme}
            onToggle={toggleTheme}
            collapsed={collapsed}
          />
        </div>

        {/* User area */}
        {user && (
          <div className="flex items-center gap-2.5 px-0.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--accent-primary)] text-white text-xs font-semibold shrink-0">
              {user.email?.charAt(0).toUpperCase()}
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="truncate text-sm font-medium text-[var(--text-primary)]">
                  {user.email}
                </p>
              </div>
            )}
            <button
              type="button"
              onClick={signOut}
              className="shrink-0 p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-[var(--color-error)] hover:bg-[var(--bg-tertiary)] transition-colors duration-150"
              aria-label="Sign out"
            >
              <LogOut size={16} strokeWidth={1.75} />
            </button>
          </div>
        )}
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        type="button"
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-3 left-3 z-50 flex h-10 w-10 items-center justify-center rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] shadow-[var(--shadow-sm)] lg:hidden"
        aria-label="Toggle navigation"
      >
        {mobileOpen ? (
          <X size={20} strokeWidth={1.75} />
        ) : (
          <Menu size={20} strokeWidth={1.75} />
        )}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-[var(--bg-overlay)] lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-40 h-screen bg-[var(--bg-secondary)] border-r border-[var(--border-primary)] transition-transform duration-200",
          // Mobile: hidden by default, slides in — capped at 280px
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          "max-w-[280px] lg:max-w-none lg:translate-x-0 lg:static",
          collapsed ? "w-16" : "w-[260px]"
        )}
      >
        {sidebarContent}
      </aside>
    </>
  )
}
