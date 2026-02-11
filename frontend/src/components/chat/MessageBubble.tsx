import { useMemo } from "react"
import Markdown from "react-markdown"
import { cn } from "@/lib/utils"
import type { Message, Source } from "@/types"
import { SourceCitation } from "./SourceCitation"

/** Strip inline [Source: filename, Section N] citations from assistant text. */
const SOURCE_CITATION_RE = /\s*\[Source:\s*[^\]]+\]/g

function stripSourceCitations(text: string): string {
  return text.replace(SOURCE_CITATION_RE, "").trim()
}

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
}

export function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === "user"

  const displayContent = useMemo(
    () => (isUser ? message.content : stripSourceCitations(message.content)),
    [isUser, message.content]
  )

  return (
    <div
      className={cn(
        "flex animate-[slide-up_200ms_var(--ease-out)]",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "relative",
          isUser ? "max-w-[75%]" : "max-w-[85%]"
        )}
      >
        <div
          className={cn(
            "px-4 py-3 text-base leading-relaxed",
            isUser
              ? "rounded-[16px_16px_4px_16px] bg-[var(--chat-user-bg)] text-[var(--chat-user-text)] shadow-sm"
              : "rounded-[16px_16px_16px_4px] border border-[var(--border-primary)] bg-[var(--chat-assistant-bg)] text-[var(--chat-assistant-text)]"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{displayContent}</p>
          ) : (
            <div className="prose-chat">
              <Markdown
                components={{
                  p: ({ children }) => (
                    <p className="mb-2 last:mb-0">{children}</p>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold">{children}</strong>
                  ),
                  ul: ({ children }) => (
                    <ul className="mb-2 ml-4 list-disc space-y-1 last:mb-0">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="mb-2 ml-4 list-decimal space-y-1 last:mb-0">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => <li>{children}</li>,
                  code: ({ children, className, node }) => {
                    // Block code: rendered inside <pre><code>
                    const isBlock =
                      node?.position &&
                      node.position.start.line !== node.position.end.line
                    if (isBlock || className?.includes("language-")) {
                      return (
                        <code
                          className={cn(
                            "block overflow-x-auto rounded-md bg-[var(--bg-tertiary)] p-3 font-mono text-sm",
                            className
                          )}
                        >
                          {children}
                        </code>
                      )
                    }
                    return (
                      <code className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 font-mono text-sm">
                        {children}
                      </code>
                    )
                  },
                  pre: ({ children }) => (
                    <pre className="mb-2 last:mb-0">{children}</pre>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="mb-2 border-l-3 border-[var(--accent-primary)] pl-3 italic text-[var(--text-secondary)] last:mb-0">
                      {children}
                    </blockquote>
                  ),
                }}
              >
                {displayContent}
              </Markdown>
              {isStreaming && (
                <span className="inline-block h-5 w-0.5 translate-y-0.5 animate-cursor-blink bg-[var(--accent-primary)]" />
              )}
            </div>
          )}
        </div>

        {/* Source citations — only for assistant messages with sources */}
        {!isUser && message.sources.length > 0 && !isStreaming && (
          <div className="mt-2 space-y-1.5">
            {message.sources.map((source: Source, i: number) => (
              <SourceCitation key={i} source={source} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface StreamingBubbleProps {
  content: string
  sources: Source[]
  showSources: boolean
}

export function StreamingBubble({
  content,
  sources,
  showSources,
}: StreamingBubbleProps) {
  const message: Message = {
    id: "streaming",
    conversation_id: "",
    role: "assistant",
    content,
    sources: showSources ? sources : [],
    created_at: new Date().toISOString(),
  }

  return <MessageBubble message={message} isStreaming={!showSources} />
}
