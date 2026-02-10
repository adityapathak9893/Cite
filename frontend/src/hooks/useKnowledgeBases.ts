import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { KnowledgeBase } from "@/types"

interface CreateKBInput {
  name: string
  description?: string | null
}

export function useKnowledgeBases() {
  return useQuery<KnowledgeBase[]>({
    queryKey: ["knowledge-bases"],
    queryFn: () => api.get<KnowledgeBase[]>("/api/v1/knowledge-bases"),
  })
}

export function useCreateKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: CreateKBInput) =>
      api.post<KnowledgeBase>("/api/v1/knowledge-bases", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] })
    },
  })
}

export function useDeleteKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/api/v1/knowledge-bases/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] })
    },
  })
}
