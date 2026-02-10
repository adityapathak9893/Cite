import { type FormEvent, useState } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"

export function LoginForm() {
  const { signIn } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const { error: signInError } = await signIn(email, password)

    if (signInError) {
      setError(signInError)
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="email" className="text-sm font-medium text-[var(--text-secondary)]">
          Email
        </Label>
        <Input
          id="email"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          className="h-11 bg-[var(--bg-primary)] border-[var(--border-secondary)] shadow-[var(--shadow-input)] focus:border-[var(--border-focus)] focus:shadow-[var(--shadow-focus)]"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password" className="text-sm font-medium text-[var(--text-secondary)]">
          Password
        </Label>
        <Input
          id="password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          minLength={6}
          className="h-11 bg-[var(--bg-primary)] border-[var(--border-secondary)] shadow-[var(--shadow-input)] focus:border-[var(--border-focus)] focus:shadow-[var(--shadow-focus)]"
        />
      </div>

      {error && (
        <div className="rounded-md bg-[var(--color-error-light)] border border-[var(--color-error)]/20 px-3.5 py-2.5 text-sm text-[var(--color-error)]">
          {error}
        </div>
      )}

      <Button
        type="submit"
        disabled={loading}
        className="w-full h-10 bg-[var(--accent-primary)] hover:bg-[var(--accent-primary-hover)] text-white font-semibold text-sm transition-all duration-150 active:scale-[0.98]"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          "Sign in"
        )}
      </Button>

      <p className="text-center text-sm text-[var(--text-secondary)]">
        Don&apos;t have an account?{" "}
        <Link
          to="/signup"
          className="font-medium text-[var(--accent-primary)] hover:text-[var(--accent-primary-hover)] transition-colors duration-150"
        >
          Sign up
        </Link>
      </p>
    </form>
  )
}
