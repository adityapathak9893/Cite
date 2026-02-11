interface HeaderProps {
  title: string
  actions?: React.ReactNode
}

export function Header({ title, actions }: HeaderProps) {
  return (
    <header className="z-10 flex h-16 shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-primary)]/80 px-6 backdrop-blur-md">
      <h1 className="text-xl font-semibold text-[var(--text-primary)] font-body">
        {title}
      </h1>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </header>
  )
}
