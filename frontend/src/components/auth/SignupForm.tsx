import { type FormEvent, useState } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"

export function SignupForm() {
  const { signUp } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.")
      return
    }

    setLoading(true)
    const { error: signUpError } = await signUp(email, password)

    if (signUpError) {
      setError(signUpError)
      setLoading(false)
    } else {
      setSuccess(true)
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="space-y-4 text-center">
        <div className="rounded-md bg-[var(--color-success-light)] border border-[var(--color-success)]/20 px-3.5 py-4 text-sm text-[var(--color-success)]">
          Check your email for a confirmation link to complete your registration.
        </div>
        <p className="text-sm text-[var(--text-secondary)]">
          Already confirmed?{" "}
          <Link
            to="/login"
            className="font-medium text-[var(--accent-primary)] hover:text-[var(--accent-primary-hover)] transition-colors duration-150"
          >
            Sign in
          </Link>
        </p>
      </div>
    )
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
          placeholder="At least 6 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="new-password"
          minLength={6}
          className="h-11 bg-[var(--bg-primary)] border-[var(--border-secondary)] shadow-[var(--shadow-input)] focus:border-[var(--border-focus)] focus:shadow-[var(--shadow-focus)]"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirm-password" className="text-sm font-medium text-[var(--text-secondary)]">
          Confirm Password
        </Label>
        <Input
          id="confirm-password"
          type="password"
          placeholder="Repeat your password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          autoComplete="new-password"
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
          "Create account"
        )}
      </Button>

      <p className="text-center text-sm text-[var(--text-secondary)]">
        Already have an account?{" "}
        <Link
          to="/login"
          className="font-medium text-[var(--accent-primary)] hover:text-[var(--accent-primary-hover)] transition-colors duration-150"
        >
          Sign in
        </Link>
      </p>
    </form>
  )
}
