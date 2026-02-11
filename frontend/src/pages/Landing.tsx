import { useCallback, useEffect, useRef, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import {
  ArrowDown,
  ArrowUp,
  FileText,
  Menu,
  MessageSquare,
  Quote,
  X,
} from "lucide-react"
import { useAuth } from "@/hooks/useAuth"
import { cn } from "@/lib/utils"

export default function Landing() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const mainRef = useRef<HTMLDivElement>(null)

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!loading && user) {
      navigate("/dashboard", { replace: true })
    }
  }, [user, loading, navigate])

  // Track scroll for navbar style
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  // Scroll-reveal observer
  useEffect(() => {
    const root = mainRef.current
    if (!root) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed")
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
    )

    root
      .querySelectorAll("[data-reveal]")
      .forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [loading])

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : ""
    return () => {
      document.body.style.overflow = ""
    }
  }, [menuOpen])

  const scrollTo = useCallback((id: string) => {
    setMenuOpen(false)
    setTimeout(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })
    }, 10)
  }, [])

  // Show nothing while checking auth (resolves almost instantly from localStorage)
  if (loading) return null

  return (
    <div ref={mainRef} className="min-h-screen bg-[var(--bg-primary)]">
      {/* ────────────────────────── NAVBAR ────────────────────────── */}
      <nav
        className={cn(
          "fixed top-0 z-50 flex h-16 w-full items-center justify-between px-6 lg:px-12",
          "transition-all duration-300 ease-[var(--ease-default)]",
          scrolled
            ? "border-b border-[var(--border-primary)] bg-[var(--bg-primary)]/80 backdrop-blur-xl"
            : "bg-transparent"
        )}
      >
        <Link to="/" className="flex items-baseline gap-2">
          <span className="font-display text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            Cite
          </span>
          <span className="text-xs font-medium text-[var(--text-tertiary)]">
            by Weaverbit
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-1 md:flex">
          <button
            type="button"
            onClick={() => scrollTo("features")}
            className="rounded-lg px-4 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors duration-150 hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
          >
            Features
          </button>
          <button
            type="button"
            onClick={() => scrollTo("how-it-works")}
            className="rounded-lg px-4 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors duration-150 hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
          >
            How it Works
          </button>

          <div className="ml-3 h-5 w-px bg-[var(--border-primary)]" />

          <Link
            to="/login"
            className="ml-3 rounded-lg px-4 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors duration-150 hover:text-[var(--text-primary)]"
          >
            Sign In
          </Link>
          <Link
            to="/signup"
            className="ml-2 inline-flex h-10 items-center rounded-lg bg-[var(--accent-primary)] px-5 text-sm font-semibold text-white shadow-[var(--shadow-sm)] transition-all duration-150 hover:bg-[var(--accent-primary-hover)] hover:shadow-[var(--shadow-md)] active:scale-[0.98]"
          >
            Get Started
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={() => setMenuOpen(true)}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-tertiary)] md:hidden"
          aria-label="Open menu"
        >
          <Menu size={20} strokeWidth={1.75} />
        </button>
      </nav>

      {/* ────────────────────── MOBILE MENU OVERLAY ────────────────────── */}
      {menuOpen && (
        <div className="fixed inset-0 z-[60] flex flex-col bg-[var(--bg-primary)]">
          <div className="flex h-16 items-center justify-between px-6">
            <span className="font-display text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Cite
            </span>
            <button
              type="button"
              onClick={() => setMenuOpen(false)}
              className="flex h-10 w-10 items-center justify-center rounded-lg text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-tertiary)]"
              aria-label="Close menu"
            >
              <X size={20} strokeWidth={1.75} />
            </button>
          </div>

          <div className="flex flex-1 flex-col items-center justify-center gap-6">
            <button
              type="button"
              onClick={() => scrollTo("features")}
              className="text-lg font-medium text-[var(--text-primary)]"
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => scrollTo("how-it-works")}
              className="text-lg font-medium text-[var(--text-primary)]"
            >
              How it Works
            </button>
            <Link
              to="/login"
              className="text-lg font-medium text-[var(--text-secondary)]"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="mt-4 inline-flex h-12 items-center rounded-lg bg-[var(--accent-primary)] px-8 text-base font-semibold text-white"
            >
              Get Started
            </Link>
          </div>
        </div>
      )}

      {/* ────────────────────────── HERO ────────────────────────── */}
      <section className="relative flex min-h-[90vh] items-center justify-center overflow-hidden pt-16">
        {/* Dot grid background */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.04] dark:opacity-[0.07]"
          style={{
            backgroundImage:
              "radial-gradient(circle, var(--accent-primary) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />

        <div className="relative mx-auto max-w-[1200px] px-6 text-center">
          {/* Pill badge */}
          <div
            className="animate-reveal-up"
            style={{ animationDelay: "0ms" }}
          >
            <span className="inline-flex items-center rounded-full border border-[var(--border-primary)] bg-[var(--accent-primary-ghost)] px-4 py-1.5 text-sm font-medium text-[var(--accent-primary)]">
              AI-Powered Document Intelligence
            </span>
          </div>

          {/* Headline */}
          <h1
            className="mx-auto mt-8 max-w-3xl animate-reveal-up font-display text-4xl font-bold tracking-tight text-[var(--text-primary)] lg:text-6xl"
            style={{ animationDelay: "100ms", lineHeight: 1.1 }}
          >
            Ask your documents anything.
          </h1>

          {/* Subheadline */}
          <p
            className="mx-auto mt-6 max-w-2xl animate-reveal-up text-lg leading-relaxed text-[var(--text-secondary)] lg:text-xl"
            style={{ animationDelay: "200ms" }}
          >
            Upload PDFs, manuals, or reports. Get instant, accurate answers with
            source citations. Built for teams who need answers, not search
            results.
          </p>

          {/* CTAs */}
          <div
            className="mt-10 flex animate-reveal-up flex-wrap items-center justify-center gap-4"
            style={{ animationDelay: "300ms" }}
          >
            <Link
              to="/signup"
              className="inline-flex h-12 items-center rounded-lg bg-[var(--accent-primary)] px-8 text-base font-semibold text-white shadow-[var(--shadow-sm)] transition-all duration-150 hover:bg-[var(--accent-primary-hover)] hover:shadow-[var(--shadow-md)] active:scale-[0.98]"
            >
              Get Started Free
            </Link>
            <button
              type="button"
              onClick={() => scrollTo("how-it-works")}
              className="inline-flex h-12 items-center gap-2 rounded-lg border border-[var(--border-secondary)] px-8 text-base font-semibold text-[var(--text-primary)] transition-all duration-150 hover:bg-[var(--bg-tertiary)]"
            >
              See How It Works
              <ArrowDown size={16} strokeWidth={2} />
            </button>
          </div>
        </div>
      </section>

      {/* ────────────────────────── FEATURES ────────────────────────── */}
      <section id="features" className="py-24">
        <div className="mx-auto max-w-[1200px] px-6">
          <div className="text-center">
            <p
              data-reveal
              className="text-sm font-medium uppercase tracking-[0.05em] text-[var(--accent-primary)]"
            >
              Features
            </p>
            <h2
              data-reveal
              className="mt-3 font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] lg:text-4xl"
              style={{ transitionDelay: "100ms" }}
            >
              Everything you need to understand your documents
            </h2>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-3">
            {FEATURES.map((f, i) => (
              <div
                key={f.title}
                data-reveal
                style={{ transitionDelay: `${i * 100}ms` }}
              >
                <div className="h-full rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-8 transition-all duration-200 ease-[var(--ease-default)] hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)]">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--accent-primary-light)]">
                    <f.icon
                      size={24}
                      strokeWidth={1.75}
                      className="text-[var(--accent-primary)]"
                    />
                  </div>
                  <h3 className="mt-5 text-lg font-semibold text-[var(--text-primary)] font-body">
                    {f.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                    {f.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ────────────────────────── HOW IT WORKS ────────────────────────── */}
      <section id="how-it-works" className="bg-[var(--bg-secondary)] py-24">
        <div className="mx-auto max-w-[1200px] px-6">
          <div className="text-center">
            <p
              data-reveal
              className="text-sm font-medium uppercase tracking-[0.05em] text-[var(--accent-primary)]"
            >
              How it Works
            </p>
            <h2
              data-reveal
              className="mt-3 font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] lg:text-4xl"
              style={{ transitionDelay: "100ms" }}
            >
              From upload to insight in three steps
            </h2>
          </div>

          <div className="relative mt-16">
            {/* Connecting line — desktop only */}
            <div className="pointer-events-none absolute top-8 right-[16.67%] left-[16.67%] hidden h-px bg-[var(--accent-primary)] opacity-20 lg:block" />

            <div className="grid gap-12 lg:grid-cols-3 lg:gap-8 lg:text-center">
              {STEPS.map((s, i) => (
                <div
                  key={s.number}
                  data-reveal
                  style={{ transitionDelay: `${i * 100}ms` }}
                >
                  <span className="font-display text-5xl font-bold text-[var(--accent-primary)]">
                    {s.number}
                  </span>
                  <h3 className="mt-4 text-xl font-semibold text-[var(--text-primary)] font-body">
                    {s.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)] lg:mx-auto lg:max-w-[280px]">
                    {s.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ────────────────────── INTERACTIVE PREVIEW ────────────────────── */}
      <section className="py-24">
        <div className="mx-auto max-w-[1200px] px-6">
          <h2
            data-reveal
            className="text-center font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] lg:text-4xl"
          >
            See it in action
          </h2>

          <div
            data-reveal
            className="mt-16 flex justify-center"
            style={{ perspective: "1000px", transitionDelay: "150ms" }}
          >
            <div className="w-full max-w-3xl transition-transform duration-500 ease-[var(--ease-default)] [transform:rotateY(-2deg)] hover:[transform:rotateY(0deg)]">
              <div className="overflow-hidden rounded-2xl border border-[var(--border-primary)] shadow-[var(--shadow-xl)]">
                {/* Window chrome */}
                <div className="flex items-center gap-2 border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-3">
                  <div className="h-3 w-3 rounded-full bg-[#FF5F57]" />
                  <div className="h-3 w-3 rounded-full bg-[#FEBC2E]" />
                  <div className="h-3 w-3 rounded-full bg-[#28C840]" />
                  <span className="flex-1 text-center text-xs font-medium text-[var(--text-tertiary)]">
                    Cite — Employee Handbook
                  </span>
                  <div className="w-[52px]" />
                </div>

                {/* Chat messages */}
                <div className="space-y-4 bg-[var(--bg-primary)] p-6">
                  {/* User message */}
                  <div className="flex justify-end">
                    <div className="max-w-[75%] rounded-[16px_16px_4px_16px] bg-[var(--chat-user-bg)] px-4 py-3 text-sm text-[var(--chat-user-text)]">
                      What are the main compliance requirements?
                    </div>
                  </div>

                  {/* Assistant message */}
                  <div className="flex justify-start">
                    <div className="max-w-[85%] space-y-3">
                      <div className="rounded-[16px_16px_16px_4px] border border-[var(--border-primary)] bg-[var(--chat-assistant-bg)] px-5 py-4 text-sm leading-relaxed text-[var(--chat-assistant-text)]">
                        Based on your Employee Handbook, the main compliance
                        requirements include:
                        <br />
                        <br />
                        <strong>1)</strong> Annual ethics training completion for
                        all employees by Q1 each year...
                        <br />
                        <strong>2)</strong> Data privacy protocols following GDPR
                        guidelines for customer data handling...
                        <br />
                        <strong>3)</strong> Mandatory incident reporting within
                        24 hours of discovery...
                      </div>

                      {/* Citation chip */}
                      <div className="inline-flex items-center gap-2 rounded-md border-l-[3px] border-l-[var(--accent-primary)] bg-[var(--chat-citation-bg)] px-3 py-2 text-xs font-medium text-[var(--chat-citation-text)]">
                        <FileText size={14} strokeWidth={1.75} />
                        Employee-Handbook.pdf · Section 3
                      </div>
                    </div>
                  </div>
                </div>

                {/* Fake input */}
                <div className="border-t border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 rounded-xl border border-[var(--border-secondary)] bg-[var(--bg-secondary)] px-4 py-3 text-sm text-[var(--text-tertiary)]">
                      Ask a question about your documents...
                    </div>
                    <div className="flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-full bg-[var(--accent-primary)] opacity-40">
                      <ArrowUp
                        size={18}
                        strokeWidth={2}
                        className="text-white"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ────────────────────────── CTA ────────────────────────── */}
      <section className="relative py-24">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse at center, var(--accent-primary) 0%, transparent 70%)",
            opacity: 0.03,
          }}
        />

        <div className="relative mx-auto max-w-[1200px] px-6 text-center">
          <h2
            data-reveal
            className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)] lg:text-4xl"
          >
            Ready to unlock your documents?
          </h2>
          <p
            data-reveal
            className="mx-auto mt-4 max-w-lg text-lg text-[var(--text-secondary)]"
            style={{ transitionDelay: "100ms" }}
          >
            Start asking questions in minutes. No credit card required.
          </p>
          <div data-reveal className="mt-8" style={{ transitionDelay: "200ms" }}>
            <Link
              to="/signup"
              className="inline-flex h-14 items-center rounded-lg bg-[var(--accent-primary)] px-10 text-lg font-semibold text-white shadow-[var(--shadow-sm)] transition-all duration-150 hover:bg-[var(--accent-primary-hover)] hover:shadow-[var(--shadow-md)] active:scale-[0.98]"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </section>

      {/* ────────────────────────── FOOTER ────────────────────────── */}
      <footer className="border-t border-[var(--border-primary)] py-12">
        <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-6 px-6 text-center md:flex-row md:justify-between md:text-left">
          <div className="flex items-baseline gap-2">
            <span className="font-display text-lg font-bold tracking-tight text-[var(--text-primary)]">
              Cite
            </span>
            <span className="text-xs text-[var(--text-tertiary)]">
              Built by Weaverbit
            </span>
          </div>

          <p className="text-xs text-[var(--text-tertiary)]">
            &copy; 2026 Weaverbit LLC. All rights reserved.
          </p>

          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => scrollTo("features")}
              className="text-xs text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => scrollTo("how-it-works")}
              className="text-xs text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
            >
              How it Works
            </button>
            <a
              href="mailto:hello@weaverbit.com"
              className="text-xs text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
            >
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}

/* ────────────────────────── Static data ────────────────────────── */

const FEATURES = [
  {
    icon: FileText,
    title: "Smart Document Processing",
    description:
      "Upload PDFs, TXT, and Markdown files. Documents are automatically chunked and indexed for intelligent retrieval.",
  },
  {
    icon: MessageSquare,
    title: "AI-Powered Q&A",
    description:
      "Ask questions in natural language. Get accurate answers powered by Claude AI with real-time streaming responses.",
  },
  {
    icon: Quote,
    title: "Source Citations",
    description:
      "Every answer includes exact source citations with section references. Verify answers against original documents.",
  },
] as const

const STEPS = [
  {
    number: "01",
    title: "Create a Knowledge Base",
    description:
      "Organize your documents by topic, project, or department.",
  },
  {
    number: "02",
    title: "Upload Your Documents",
    description:
      "Drag and drop PDFs, text files, or markdown. Processing happens automatically in the background.",
  },
  {
    number: "03",
    title: "Start Asking Questions",
    description:
      "Get instant answers with source citations. Follow up naturally\u2009\u2014\u2009the AI remembers context.",
  },
] as const
