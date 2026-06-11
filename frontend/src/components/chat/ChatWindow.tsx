import { useCallback, useEffect, useRef, useState } from "react"
import { FileText } from "lucide-react"
import { useDocuments } from "@/hooks/useDocuments"
import { useChatMessages, useConversations, useSendMessage } from "@/hooks/useChat"
import { ChatInput } from "./ChatInput"
import { MessageBubble, StreamingBubble } from "./MessageBubble"
import { StreamingIndicator } from "./StreamingIndicator"
import { SuggestionChips } from "./SuggestionChips"

interface ChatWindowProps {
  kbId: string
  kbName: string
  suggestedQuestions?: string[] | null
}

export function ChatWindow({ kbId, kbName, suggestedQuestions }: ChatWindowProps) {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: documents } = useDocuments(kbId)
  const { data: conversations } = useConversations(kbId)
  const { data: messages = [], isLoading: isLoadingMessages } =
    useChatMessages(conversationId)
  const { sendMessage, isStreaming, streamingContent, streamingSources, pendingUserMessage } =
    useSendMessage(kbId)

  // Delay showing the loading skeleton by 300ms to avoid flicker on fast loads
  const [showSkeleton, setShowSkeleton] = useState(false)
  useEffect(() => {
    if (!isLoadingMessages) {
      setShowSkeleton(false)
      return
    }
    const timer = setTimeout(() => setShowSkeleton(true), 300)
    return () => clearTimeout(timer)
  }, [isLoadingMessages])

  // Auto-select the most recent conversation on initial load
  const hasInitialized = useRef(false)
  useEffect(() => {
    if (hasInitialized.current) return
    if (conversations && conversations.length > 0) {
      setConversationId(conversations[0].id)
      hasInitialized.current = true
    }
  }, [conversations])

  const readyDocCount =
    documents?.filter((d) => d.status === "ready").length ?? 0
  // Show pending user message if it's not already in the messages list (new conversation)
  const showPendingBubble =
    pendingUserMessage != null &&
    !messages.some((m) => m.id === pendingUserMessage.id)

  const hasMessages = messages.length > 0 || isStreaming || showPendingBubble

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: isStreaming ? "instant" : "smooth",
    })
  }, [messages.length, streamingContent, isStreaming])

  // Scroll to bottom instantly when messages finish loading
  const prevLoadingRef = useRef(isLoadingMessages)
  useEffect(() => {
    const wasLoading = prevLoadingRef.current
    prevLoadingRef.current = isLoadingMessages
    if (wasLoading && !isLoadingMessages && messages.length > 0) {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "instant" })
      })
    }
  }, [isLoadingMessages, messages.length])

  const handleSend = useCallback(
    async (content: string) => {
      const result = await sendMessage(content, conversationId)
      if (result && !conversationId) {
        setConversationId(result.conversationId)
      }
    },
    [sendMessage, conversationId]
  )

  return (
    <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)]">
      {/* Chat header — fixed, never shrinks */}
      <div className="flex shrink-0 items-center justify-between border-b border-[var(--border-primary)] px-4 py-3 sm:px-5">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-[var(--text-primary)] font-[var(--font-body)]">
            {kbName}
          </h3>
          <p className="flex items-center gap-1 text-xs text-[var(--text-tertiary)]">
            <FileText size={12} strokeWidth={1.75} />
            {readyDocCount} document{readyDocCount !== 1 ? "s" : ""} indexed
          </p>
        </div>

        {/* Conversation selector */}
        {conversations && conversations.length > 0 && (
          <div className="ml-3 flex items-center gap-2">
            <select
              value={conversationId ?? ""}
              onChange={(e) =>
                setConversationId(e.target.value || null)
              }
              className="rounded-md border border-[var(--border-secondary)] bg-[var(--bg-secondary)] px-2 py-1 text-xs text-[var(--text-secondary)] focus:border-[var(--border-focus)] focus:outline-none"
            >
              <option value="">New conversation</option>
              {conversations.map((conv) => (
                <option key={conv.id} value={conv.id}>
                  {conv.title ?? "Untitled"}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Messages — scrollable, takes all remaining space */}
      <div className="flex-1 overflow-y-auto">
        {readyDocCount === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-6">
            <FileText
              size={32}
              strokeWidth={1.75}
              className="mb-3 text-[var(--text-tertiary)]"
            />
            <p className="text-sm font-medium text-[var(--text-secondary)]">
              Upload some documents first to start chatting
            </p>
            <p className="mt-1 text-xs text-[var(--text-tertiary)]">
              Your documents need to be processed before you can ask questions.
            </p>
          </div>
        ) : showSkeleton ? (
          <div className="space-y-4 p-4 sm:p-6">
            <div className="flex justify-end">
              <div className="h-10 w-[55%] animate-pulse rounded-[16px_16px_4px_16px] bg-[var(--bg-tertiary)]" />
            </div>
            <div className="flex justify-start">
              <div className="w-[70%] space-y-2">
                <div className="h-20 animate-pulse rounded-[16px_16px_16px_4px] bg-[var(--bg-tertiary)]" />
                <div className="h-5 w-36 animate-pulse rounded-md bg-[var(--bg-tertiary)]" />
              </div>
            </div>
            <div className="flex justify-end">
              <div className="h-10 w-[40%] animate-pulse rounded-[16px_16px_4px_16px] bg-[var(--bg-tertiary)]" />
            </div>
          </div>
        ) : isLoadingMessages ? (
          null
        ) : !hasMessages ? (
          <SuggestionChips
            onSelect={handleSend}
            disabled={isStreaming}
            suggestions={suggestedQuestions}
          />
        ) : (
          <div className="space-y-4 p-4 sm:p-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {showPendingBubble && (
              <MessageBubble key={pendingUserMessage!.id} message={pendingUserMessage!} />
            )}

            {isStreaming && !streamingContent && <StreamingIndicator />}
            {isStreaming && streamingContent && (
              <StreamingBubble
                content={streamingContent}
                sources={streamingSources}
                showSources={false}
              />
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input — fixed at bottom, NEVER cut off */}
      <ChatInput
        onSend={handleSend}
        disabled={isStreaming || readyDocCount === 0}
      />
    </div>
  )
}
