import { Navigate, Link } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
import { LoginForm } from "@/components/auth/LoginForm"
import { Loader2 } from "lucide-react"

export default function Login() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--bg-primary)]">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--accent-primary)]" />
      </div>
    )
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-secondary)] px-4">
      <div className="w-full max-w-[400px] rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-8 shadow-[var(--shadow-lg)]">
        <div className="mb-8 text-center">
          <Link to="/" className="inline-block">
            <h1 className="font-display text-3xl font-bold text-[var(--text-primary)] tracking-tight">
              Cite
            </h1>
          </Link>
          <p className="mt-2 text-sm text-[var(--text-secondary)] font-body">
            Sign in to your account
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}
