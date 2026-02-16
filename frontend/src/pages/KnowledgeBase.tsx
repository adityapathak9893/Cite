import { useCallback, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, FileText, MessageSquare } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Header } from "@/components/layout/Header"
import { Button } from "@/components/ui/button"
import { DocumentUpload } from "@/components/documents/DocumentUpload"
import { DocumentList } from "@/components/documents/DocumentList"
import { ChatWindow } from "@/components/chat/ChatWindow"
import { cn } from "@/lib/utils"
import type { KnowledgeBase as KBType, UploadingFile } from "@/types"

type Tab = "documents" | "chat"

export default function KnowledgeBase() {
  const { id } = useParams<{ id: string }>()
  const kbId = id!
  const [activeTab, setActiveTab] = useState<Tab>("documents")
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])

  const handleUploadStart = useCallback((tempId: string, fileName: string) => {
    setUploadingFiles((prev) => [...prev, { tempId, fileName }])
  }, [])

  const handleUploadEnd = useCallback((tempId: string) => {
    setUploadingFiles((prev) => prev.filter((f) => f.tempId !== tempId))
  }, [])

  const { data: kb } = useQuery<KBType>({
    queryKey: ["knowledge-base", kbId],
    queryFn: () => api.get<KBType>(`/api/v1/knowledge-bases/${kbId}`),
    enabled: !!kbId,
  })

  return (
    <>
      {/* Page header — fixed height, never shrinks */}
      <Header
        title={kb?.name ?? "Knowledge Base"}
        actions={
          <Button variant="outline" asChild>
            <Link to="/dashboard">
              <ArrowLeft size={16} strokeWidth={1.75} />
              <span className="hidden sm:inline">Back</span>
            </Link>
          </Button>
        }
      />

      {/* Mobile/Tablet tab switcher — hidden on desktop */}
      <div className="flex shrink-0 border-b border-[var(--border-primary)] lg:hidden">
        <button
          type="button"
          onClick={() => setActiveTab("documents")}
          className={cn(
            "flex flex-1 items-center justify-center gap-2 py-3 text-sm font-medium transition-colors duration-150",
            activeTab === "documents"
              ? "border-b-2 border-[var(--accent-primary)] text-[var(--accent-primary)]"
              : "text-[var(--text-secondary)]"
          )}
        >
          <FileText size={16} strokeWidth={1.75} />
          Documents
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("chat")}
          className={cn(
            "flex flex-1 items-center justify-center gap-2 py-3 text-sm font-medium transition-colors duration-150",
            activeTab === "chat"
              ? "border-b-2 border-[var(--accent-primary)] text-[var(--accent-primary)]"
              : "text-[var(--text-secondary)]"
          )}
        >
          <MessageSquare size={16} strokeWidth={1.75} />
          Chat
        </button>
      </div>

      {/* Main content — takes ALL remaining height, never overflows */}
      <div className="mx-auto flex w-full max-w-[1200px] flex-1 overflow-hidden">
        {/* Left panel: Documents — scrolls independently */}
        <div
          className={cn(
            "flex-col gap-5 overflow-y-auto p-6 lg:flex lg:w-[420px] lg:shrink-0",
            activeTab === "documents" ? "flex w-full" : "hidden"
          )}
        >
          <DocumentUpload
            kbId={kbId}
            onUploadStart={handleUploadStart}
            onUploadEnd={handleUploadEnd}
          />
          <DocumentList kbId={kbId} uploadingFiles={uploadingFiles} />
        </div>

        {/* Right panel: Chat — flex column so header/messages/input stack */}
        <div
          className={cn(
            "min-w-0 flex-col pt-6 pr-6 pb-6 lg:flex lg:flex-1",
            activeTab === "chat" ? "flex flex-1 pl-6" : "hidden",
            // On desktop, no left padding — gap from documents panel is enough
            "lg:pl-0"
          )}
        >
          <ChatWindow
            kbId={kbId}
            kbName={kb?.name ?? "Knowledge Base"}
          />
        </div>
      </div>
    </>
  )
}
