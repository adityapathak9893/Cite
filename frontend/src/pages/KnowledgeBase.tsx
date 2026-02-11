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
      <Header
        title={kb?.name ?? "Knowledge Base"}
        actions={
          <Button variant="outline" asChild>
            <Link to="/dashboard">
              <ArrowLeft size={16} strokeWidth={1.75} />
              Back
            </Link>
          </Button>
        }
      />

      {/* Mobile/Tablet tab switcher — hidden on desktop */}
      <div className="flex border-b border-[var(--border-primary)] lg:hidden">
        <button
          type="button"
          onClick={() => setActiveTab("documents")}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors duration-150",
            activeTab === "documents"
              ? "text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]"
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
            "flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors duration-150",
            activeTab === "chat"
              ? "text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]"
              : "text-[var(--text-secondary)]"
          )}
        >
          <MessageSquare size={16} strokeWidth={1.75} />
          Chat
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-hidden">
        <div className="mx-auto flex h-full max-w-[1200px] gap-6 p-6">
          {/* Left panel: Documents */}
          <div
            className={cn(
              "flex flex-col gap-5 overflow-y-auto lg:w-[420px] lg:shrink-0",
              // Mobile: toggle visibility based on active tab
              activeTab === "documents" ? "w-full" : "hidden"
            )}
          >
            <DocumentUpload
              kbId={kbId}
              onUploadStart={handleUploadStart}
              onUploadEnd={handleUploadEnd}
            />
            <DocumentList kbId={kbId} uploadingFiles={uploadingFiles} />
          </div>

          {/* Right panel: Chat */}
          <div
            className={cn(
              "flex-1 min-h-0 lg:flex",
              activeTab === "chat" ? "flex" : "hidden"
            )}
          >
            <ChatWindow
              kbId={kbId}
              kbName={kb?.name ?? "Knowledge Base"}
            />
          </div>
        </div>
      </div>
    </>
  )
}
