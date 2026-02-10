import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"

export default function Landing() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Navigation */}
      <nav className="sticky top-0 z-20 flex h-[72px] items-center justify-between px-6 lg:px-12 bg-[var(--bg-primary)]/80 backdrop-blur-xl border-b border-[var(--border-primary)]">
        <Link to="/" className="font-display text-2xl font-bold text-[var(--text-primary)] tracking-tight">
          Cite
        </Link>
        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button
              variant="ghost"
              className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
            >
              Log in
            </Button>
          </Link>
          <Link to="/signup">
            <Button className="h-10 px-5 bg-[var(--accent-primary)] hover:bg-[var(--accent-primary-hover)] text-white font-semibold text-sm transition-all duration-150 active:scale-[0.98]">
              Get Started Free
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-[1200px] px-6 pt-20 pb-24 lg:pt-32 lg:pb-32 text-center">
        <h1 className="font-display text-4xl lg:text-5xl xl:text-6xl font-bold text-[var(--text-primary)] tracking-tight leading-tight max-w-3xl mx-auto">
          Your documents, instantly searchable.
        </h1>
        <p className="mt-6 text-lg text-[var(--text-secondary)] leading-relaxed max-w-xl mx-auto font-body">
          AI-powered answers with source citations from your uploaded files. No hallucinations. Every claim traced back to the source.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link to="/signup">
            <Button className="h-12 px-7 bg-[var(--accent-primary)] hover:bg-[var(--accent-primary-hover)] text-white font-semibold text-base transition-all duration-150 active:scale-[0.98] shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)]">
              Get Started Free
            </Button>
          </Link>
        </div>
      </section>
    </div>
  )
}
