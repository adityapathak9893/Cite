import json
import logging
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from supabase import Client

from app.dependencies import AppException, get_current_user, get_supabase
from app.models.schemas import (
    ChatMessageRequest,
    ConversationResponse,
    MessageResponse,
    SourceItem,
)
from app.services.claude import stream_chat_response
from app.services.embedding import embed_texts
from app.services.rag import (
    build_context,
    get_document_structure,
    is_overview_question,
    search_similar_chunks,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def _verify_kb_ownership(
    supabase: Client, kb_id: str, user_id: str, request_id: str
) -> dict:
    """Verify the user owns the KB. Returns the KB row."""
    result = (
        supabase.table("knowledge_bases")
        .select("id, name, chat_mode, domain_profile")
        .eq("id", kb_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise AppException(
            status_code=404,
            code="RESOURCE_NOT_FOUND",
            message="Knowledge base not found.",
            request_id=request_id,
        )
    return result.data[0]


@router.post("/api/v1/knowledge-bases/{kb_id}/chat")
async def chat(
    kb_id: str,
    body: ChatMessageRequest,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> StreamingResponse:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        # Verify KB ownership and get name
        kb = _verify_kb_ownership(supabase, kb_id, user_id, request_id)
        kb_name = kb["name"]
        chat_mode = kb.get("chat_mode") or "strict"
        domain_profile = kb.get("domain_profile")

        # Check if KB has ready documents
        doc_count_result = (
            supabase.table("documents")
            .select("id", count="exact")
            .eq("knowledge_base_id", kb_id)
            .eq("status", "ready")
            .execute()
        )
        ready_count = doc_count_result.count if doc_count_result.count is not None else 0

        if ready_count == 0:
            raise AppException(
                status_code=422,
                code="VALIDATION_ERROR",
                message="No documents are ready for chat. Upload and process documents first.",
                request_id=request_id,
            )

        # Create or continue conversation
        conversation_id = body.conversation_id
        if not conversation_id:
            conv_result = (
                supabase.table("conversations")
                .insert({
                    "knowledge_base_id": kb_id,
                    "user_id": user_id,
                    "title": body.message[:100],
                })
                .execute()
            )
            conversation_id = conv_result.data[0]["id"]
            logger.info(
                "Created conversation | conv_id=%s | kb_id=%s | request_id=%s",
                conversation_id, kb_id, request_id,
            )
        else:
            # Verify conversation ownership
            conv_check = (
                supabase.table("conversations")
                .select("id")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .eq("knowledge_base_id", kb_id)
                .execute()
            )
            if not conv_check.data:
                raise AppException(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="Conversation not found.",
                    request_id=request_id,
                )

        # Save user message
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "user",
            "content": body.message,
        }).execute()

        # Embed the user's question
        logger.info(
            "Embedding query | text=%s | kb_id=%s | request_id=%s",
            body.message[:100], kb_id, request_id,
        )
        embeddings = await embed_texts([body.message])
        query_embedding = embeddings[0]
        logger.info(
            "Embedding complete | dims=%d | request_id=%s",
            len(query_embedding), request_id,
        )

        # Detect overview questions for enhanced context
        overview = is_overview_question(body.message)

        # Fetch document structure for overview questions
        document_structure = None
        if overview:
            document_structure = get_document_structure(supabase, kb_id)
            logger.info(
                "Overview question detected | kb_id=%s | has_structure=%s | request_id=%s",
                kb_id, document_structure is not None, request_id,
            )

        # Retrieve relevant chunks (hybrid: vector + FTS, RRF-fused)
        chunks = search_similar_chunks(supabase, query_embedding, body.message, kb_id)

        # Build context for Claude
        context = build_context(
            chunks=chunks,
            document_structure=document_structure,
            is_overview=overview,
        )

        # Research mode: zero retrieval still goes to Claude — the contract's
        # postures C/D/E handle conversational, off-topic, and frustrated messages
        if chat_mode == "research" and not context:
            context = (
                "--- Document Knowledge ---\n"
                "No document content was retrieved for this message.\n"
                "--- End Document Knowledge ---"
            )

        # Get last 6 messages for context (current user msg + 5 prior)
        history_result = (
            supabase.table("messages")
            .select("role, content")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(6)
            .execute()
        )
        # Reverse to chronological order
        messages_for_claude = [
            {"role": m["role"], "content": m["content"]}
            for m in reversed(history_result.data or [])
        ]

        logger.info(
            "Chat request | conv_id=%s | kb_id=%s | chunks=%d | overview=%s | history=%d | request_id=%s",
            conversation_id, kb_id, len(chunks), overview, len(messages_for_claude), request_id,
        )

        # Build SSE generator
        async def event_generator():
            try:
                # Strict mode: non-overview questions with zero chunks get a canned
                # response. In research mode this path goes to Claude instead.
                if chat_mode != "research" and not overview and not chunks:
                    canned = (
                        "I wasn't able to find any relevant sections in the documents "
                        "for your question. Could you try rephrasing, or ask about a "
                        "specific topic covered in the uploaded documents?"
                    )
                    yield f"data: {json.dumps({'token': canned, 'done': False})}\n\n"

                    msg_result = (
                        supabase.table("messages")
                        .insert({
                            "conversation_id": conversation_id,
                            "role": "assistant",
                            "content": canned,
                            "sources": [],
                        })
                        .execute()
                    )
                    message_id = msg_result.data[0]["id"]

                    yield f"data: {json.dumps({'token': '', 'done': True, 'sources': [], 'message_id': message_id, 'conversation_id': conversation_id})}\n\n"
                    return

                # Stream Claude's response
                full_response = ""
                sources: list[dict] = []
                domain_context: str | None = None

                async for event in stream_chat_response(
                    kb_name,
                    messages_for_claude,
                    chunks,
                    context,
                    chat_mode=chat_mode,
                    domain_profile=domain_profile,
                ):
                    if event["done"]:
                        sources = event.get("sources", [])
                        domain_context = event.get("domain_context")
                        full_response = event.get("full_response", "")

                        # Save clean text (SOURCES + DOMAIN_CONTEXT blocks already
                        # stripped) + parsed sources + domain context
                        msg_result = (
                            supabase.table("messages")
                            .insert({
                                "conversation_id": conversation_id,
                                "role": "assistant",
                                "content": full_response,
                                "sources": sources,
                                "domain_context": domain_context,
                            })
                            .execute()
                        )
                        message_id = msg_result.data[0]["id"]

                        yield f"data: {json.dumps({'token': '', 'done': True, 'sources': sources, 'domain_context': domain_context, 'message_id': message_id, 'conversation_id': conversation_id})}\n\n"
                    else:
                        yield f"data: {json.dumps({'token': event['token'], 'done': False})}\n\n"

            except Exception as exc:
                logger.error(
                    "SSE stream error | conv_id=%s | kb_id=%s | error=%s | request_id=%s",
                    conversation_id, kb_id, str(exc), request_id,
                )
                error_event = {
                    "token": "",
                    "done": True,
                    "sources": [],
                    "domain_context": None,
                    "error": "Something went wrong while generating the response.",
                    "conversation_id": conversation_id,
                }
                yield f"data: {json.dumps(error_event)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Chat failed | kb_id=%s | user_id=%s | error=%s | request_id=%s",
            kb_id, user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to process chat message.",
            request_id=request_id,
        ) from exc


@router.get(
    "/api/v1/knowledge-bases/{kb_id}/conversations",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    kb_id: str,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[ConversationResponse]:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        _verify_kb_ownership(supabase, kb_id, user_id, request_id)

        result = (
            supabase.table("conversations")
            .select("*")
            .eq("knowledge_base_id", kb_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return [
            ConversationResponse(**row)
            for row in (result.data or [])
        ]

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "List conversations failed | kb_id=%s | error=%s | request_id=%s",
            kb_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to list conversations.",
            request_id=request_id,
        ) from exc


@router.get(
    "/api/v1/conversations/{conv_id}/messages",
    response_model=list[MessageResponse],
)
async def get_messages(
    conv_id: str,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[MessageResponse]:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        # Verify conversation ownership
        conv_result = (
            supabase.table("conversations")
            .select("id")
            .eq("id", conv_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not conv_result.data:
            raise AppException(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Conversation not found.",
                request_id=request_id,
            )

        result = (
            supabase.table("messages")
            .select("*")
            .eq("conversation_id", conv_id)
            .order("created_at")
            .execute()
        )

        return [
            MessageResponse(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                sources=[SourceItem(**s) for s in (row.get("sources") or [])],
                domain_context=row.get("domain_context"),
                created_at=row["created_at"],
            )
            for row in (result.data or [])
        ]

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Get messages failed | conv_id=%s | error=%s | request_id=%s",
            conv_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to retrieve messages.",
            request_id=request_id,
        ) from exc
