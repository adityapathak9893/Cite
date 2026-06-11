import { useEffect, useRef } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Document } from "@/types"

export function useDocuments(kbId: string) {
  const queryClient = useQueryClient()

  const query = useQuery<Document[]>({
    queryKey: ["documents", kbId],
    queryFn: () =>
      api.get<Document[]>(`/api/v1/knowledge-bases/${kbId}/documents`),
    enabled: !!kbId,
    // Poll every 2s when any document is still processing
    refetchInterval: (query) => {
      const docs = query.state.data
      if (!docs) return false
      const hasProcessing = docs.some(
        (d) => d.status === "uploading" || d.status === "processing"
      )
      return hasProcessing ? 2000 : false
    },
  })

  // When a polled document flips to ready, the KB profile (suggested
  // questions, domain summary) is regenerated server-side — refetch it so
  // suggestion chips don't go stale. Only an observed transition counts;
  // documents that load already-ready don't trigger an invalidation.
  const previousStatuses = useRef(new Map<string, Document["status"]>())
  useEffect(() => {
    const docs = query.data
    if (!docs) return
    const becameReady = docs.some((doc) => {
      const previous = previousStatuses.current.get(doc.id)
      return doc.status === "ready" && previous !== undefined && previous !== "ready"
    })
    previousStatuses.current = new Map(docs.map((doc) => [doc.id, doc.status]))
    if (becameReady) {
      queryClient.invalidateQueries({ queryKey: ["knowledge-base", kbId] })
    }
  }, [query.data, queryClient, kbId])

  return query
}

export function useUploadDocument(kbId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) =>
      api.uploadFile<Document>(
        `/api/v1/knowledge-bases/${kbId}/documents`,
        file
      ),
    onSuccess: (newDoc) => {
      // Add the real document to cache immediately so there's no gap
      // when the temporary uploading entry is removed
      queryClient.setQueryData<Document[]>(["documents", kbId], (old) =>
        old ? [newDoc, ...old] : [newDoc]
      )
      // Update KB list to reflect new document count
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] })
    },
  })
}

export function useDeleteDocument(kbId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (docId: string) =>
      api.delete(`/api/v1/knowledge-bases/${kbId}/documents/${docId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", kbId] })
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] })
    },
  })
}
