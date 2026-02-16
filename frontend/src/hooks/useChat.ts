import { useCallback, useEffect, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { supabase } from "@/lib/supabase"
import { api } from "@/lib/api"
import { toast } from "sonner"
import type { Conversation, Message, Source } from "@/types"

const API_URL = import.meta.env.VITE_API_URL as string

/** Timeout for first SSE token (ms). */
const FIRST_TOKEN_TIMEOUT = 60_000

export function useConversations(kbId: string) {
  return useQuery<Conversation[]>({
    queryKey: ["conversations", kbId],
    queryFn: () =>
      api.get<Conversation[]>(
        `/api/v1/knowledge-bases/${kbId}/conversations`
      ),
    enabled: !!kbId,
    staleTime: 30_000,
  })
}

export function useChatMessages(conversationId: string | null) {
  return useQuery<Message[]>({
    queryKey: ["messages", conversationId],
    queryFn: () =>
      api.get<Message[]>(
        `/api/v1/conversations/${conversationId}/messages`
      ),
    enabled: !!conversationId,
    staleTime: 30_000,
  })
}

interface SendMessageResult {
  conversationId: string
}

export function useSendMessage(kbId: string) {
  const queryClient = useQueryClient()
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const [streamingSources, setStreamingSources] = useState<Source[]>([])
  const [pendingUserMessage, setPendingUserMessage] = useState<Message | null>(null)

  const isStreamingRef = useRef(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Abort any in-flight stream on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
    }
  }, [])

  const sendMessage = useCallback(
    async (
      content: string,
      conversationId: string | null
    ): Promise<SendMessageResult | null> => {
      if (isStreamingRef.current) return null

      isStreamingRef.current = true
      setIsStreaming(true)
      setStreamingContent("")
      setStreamingSources([])

      // Abort previous stream if somehow still active
      abortControllerRef.current?.abort()
      const controller = new AbortController()
      abortControllerRef.current = controller

      // Optimistically add user message to cache
      const tempUserMsg: Message = {
        id: `temp-user-${Date.now()}`,
        conversation_id: conversationId || "",
        role: "user",
        content,
        sources: [],
        created_at: new Date().toISOString(),
      }

      // Always expose the pending message so it renders during streaming
      setPendingUserMessage(tempUserMsg)

      if (conversationId) {
        queryClient.setQueryData<Message[]>(
          ["messages", conversationId],
          (old) => [...(old || []), tempUserMsg]
        )
      }

      try {
        const { data: sessionData } = await supabase.auth.getSession()
        const token = sessionData.session?.access_token

        // Timeout for initial connection + first token
        const timeoutId = setTimeout(
          () => controller.abort(),
          FIRST_TOKEN_TIMEOUT
        )

        const response = await fetch(
          `${API_URL}/api/v1/knowledge-bases/${kbId}/chat`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
              message: content,
              conversation_id: conversationId,
            }),
            signal: controller.signal,
          }
        )

        if (!response.ok) {
          clearTimeout(timeoutId)
          const errorData = await response.json().catch(() => null)
          const errorMessage =
            errorData?.error?.message ?? "Failed to send message."

          if (response.status === 401) {
            await supabase.auth.signOut()
            window.location.href = "/login"
          }

          throw new Error(errorMessage)
        }

        if (!response.body) {
          clearTimeout(timeoutId)
          throw new Error("No response stream received.")
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ""
        let fullContent = ""
        let sources: Source[] = []
        let newConversationId = conversationId
        let receivedFirstToken = false

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          // Clear the initial timeout once we start receiving data
          if (!receivedFirstToken) {
            receivedFirstToken = true
            clearTimeout(timeoutId)
          }

          buffer += decoder.decode(value, { stream: true })
          const events = buffer.split("\n\n")
          buffer = events.pop()!

          for (const event of events) {
            const dataLine = event
              .split("\n")
              .find((l) => l.startsWith("data: "))
            if (!dataLine) continue

            let data: Record<string, unknown>
            try {
              data = JSON.parse(dataLine.slice(6))
            } catch {
              continue
            }

            if (data.error) {
              throw new Error(data.error as string)
            }

            if (data.done) {
              sources = (data.sources as Source[]) || []
              newConversationId =
                (data.conversation_id as string) || conversationId
              setStreamingSources(sources)
            } else {
              fullContent += data.token as string
              setStreamingContent(fullContent)
            }
          }
        }

        // Strip ---SOURCES--- block from cached content (backend saves clean text)
        const cleanContent = fullContent
          .replace(/\s*---SOURCES---[\s\S]*?---END_SOURCES---\s*/g, "")
          .trimEnd()

        // Build the complete assistant message
        const assistantMsg: Message = {
          id: `msg-${Date.now()}`,
          conversation_id: newConversationId || "",
          role: "assistant",
          content: cleanContent,
          sources,
          created_at: new Date().toISOString(),
        }

        // For new conversations, set both messages directly
        if (!conversationId && newConversationId) {
          queryClient.setQueryData<Message[]>(
            ["messages", newConversationId],
            [tempUserMsg, assistantMsg]
          )
        } else if (newConversationId) {
          queryClient.setQueryData<Message[]>(
            ["messages", newConversationId],
            (old) => [...(old || []), assistantMsg]
          )
        }

        // Refresh conversations list
        queryClient.invalidateQueries({ queryKey: ["conversations", kbId] })

        return { conversationId: newConversationId || "" }
      } catch (error) {
        // Don't show error for intentional abort (unmount / navigation)
        if (controller.signal.aborted) return null

        // Rollback optimistic user message
        if (conversationId) {
          queryClient.setQueryData<Message[]>(
            ["messages", conversationId],
            (old) => (old || []).filter((m) => m.id !== tempUserMsg.id)
          )
        }

        const message =
          error instanceof Error
            ? error.message
            : "Something went wrong. Please try again."
        toast.error(message)
        return null
      } finally {
        isStreamingRef.current = false
        abortControllerRef.current = null
        setIsStreaming(false)
        setStreamingContent("")
        setStreamingSources([])
        setPendingUserMessage(null)
      }
    },
    [kbId, queryClient]
  )

  return { sendMessage, isStreaming, streamingContent, streamingSources, pendingUserMessage }
}
