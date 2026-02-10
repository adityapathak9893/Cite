import { useCallback, useEffect, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
import { LayoutDashboard, LogOut, Moon, Sun, Menu, X } from "lucide-react"
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
  const [collapsed, setCollapsed] = useState(false)
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
                "flex items-center gap-2.5 h-9 rounded-md px-2 text-sm font-medium transition-[background-color] duration-150",
                isActive
                  ? "bg-[var(--accent-primary-ghost)] text-[var(--accent-primary)] border-l-2 border-[var(--accent-primary)]"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
              )}
            >
              <Icon size={18} strokeWidth={1.75} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-2 pb-3 space-y-2 border-t border-[var(--border-primary)] pt-3">
        {/* Theme toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          className="flex items-center gap-2.5 w-full h-9 rounded-md px-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-[background-color] duration-150"
          aria-label={`Switch to ${resolvedTheme === "light" ? "dark" : "light"} theme`}
        >
          {resolvedTheme === "light" ? (
            <Moon size={18} strokeWidth={1.75} />
          ) : (
            <Sun size={18} strokeWidth={1.75} />
          )}
          {!collapsed && (
            <span>{resolvedTheme === "light" ? "Dark mode" : "Light mode"}</span>
          )}
        </button>

        {/* User area */}
        {user && (
          <div className="flex items-center gap-2.5 px-2">
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
          "fixed top-0 left-0 z-40 h-screen bg-[var(--bg-secondary)] border-r border-[var(--border-primary)] transition-all duration-200",
          // Mobile: hidden by default, slides in
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          "lg:translate-x-0 lg:static",
          collapsed ? "w-16" : "w-[260px]"
        )}
      >
        {sidebarContent}
      </aside>
    </>
  )
}
