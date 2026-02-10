import { BookOpen, Plus } from "lucide-react"
import { Header } from "@/components/layout/Header"
import { Button } from "@/components/ui/button"

export default function Dashboard() {
  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6">
        <div className="mx-auto max-w-[1200px]">
          {/* Empty state — vertically centered in content area */}
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--accent-primary-ghost)] mb-5">
              <BookOpen size={28} strokeWidth={1.75} className="text-[var(--accent-primary)]" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)] font-body mb-2">
              No knowledge bases yet
            </h2>
            <p className="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
              Upload your documents and start asking questions. Create your first knowledge base to get started.
            </p>
            <Button>
              <Plus size={16} strokeWidth={2} />
              Create Knowledge Base
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
