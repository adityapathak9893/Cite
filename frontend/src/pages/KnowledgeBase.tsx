import { useParams, Link } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { Header } from "@/components/layout/Header"
import { Button } from "@/components/ui/button"

export default function KnowledgeBase() {
  const { id } = useParams<{ id: string }>()

  return (
    <>
      <Header
        title="Knowledge Base"
        actions={
          <Button variant="outline" asChild>
            <Link to="/dashboard">
              <ArrowLeft size={16} strokeWidth={1.75} />
              Back
            </Link>
          </Button>
        }
      />
      <div className="p-6">
        <div className="mx-auto max-w-[1200px]">
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <p className="text-sm text-[var(--text-secondary)]">
              Knowledge Base Detail — Coming in Phase 3
            </p>
            <p className="text-xs text-[var(--text-tertiary)] mt-2 font-mono">
              ID: {id}
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
