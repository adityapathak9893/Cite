import { useState } from "react"
import { Plus } from "lucide-react"
import { Header } from "@/components/layout/Header"
import { Button } from "@/components/ui/button"
import { KnowledgeBaseList } from "@/components/dashboard/KnowledgeBaseList"
import { CreateKBDialog } from "@/components/dashboard/CreateKBDialog"

export default function Dashboard() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)

  return (
    <>
      <Header
        title="Knowledge Bases"
        actions={
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus size={16} strokeWidth={2} />
            New Knowledge Base
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-[1200px]">
          <KnowledgeBaseList onCreateClick={() => setCreateDialogOpen(true)} />
        </div>
      </div>

      <CreateKBDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
    </>
  )
}
