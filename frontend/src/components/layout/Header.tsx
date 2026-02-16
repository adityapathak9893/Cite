interface HeaderProps {
  title: string
  actions?: React.ReactNode
}

export function Header({ title, actions }: HeaderProps) {
  return (
    <header className="z-10 flex h-16 shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-primary)]/80 pl-14 pr-4 lg:px-6 backdrop-blur-md">
      <h1 className="min-w-0 truncate text-xl font-semibold text-[var(--text-primary)] font-body lg:overflow-visible lg:whitespace-normal">
        {title}
      </h1>
      {actions && <div className="ml-2 flex shrink-0 items-center gap-3">{actions}</div>}
    </header>
  )
}
