import logging
import uuid

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import AppException, get_current_user, get_supabase
from app.models.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge-bases"])

MAX_KB_PER_USER = 10


def _row_to_response(row: dict, document_count: int) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        description=row.get("description"),
        is_public=row.get("is_public", False),
        suggested_questions=row.get("suggested_questions"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        document_count=document_count,
    )


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[KnowledgeBaseResponse]:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        kb_result = (
            supabase.table("knowledge_bases")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        kbs = kb_result.data or []

        if not kbs:
            return []

        kb_ids = [kb["id"] for kb in kbs]

        # Count documents per KB in a single query
        docs_result = (
            supabase.table("documents")
            .select("knowledge_base_id")
            .in_("knowledge_base_id", kb_ids)
            .execute()
        )

        doc_counts: dict[str, int] = {}
        for doc in docs_result.data or []:
            kb_id = doc["knowledge_base_id"]
            doc_counts[kb_id] = doc_counts.get(kb_id, 0) + 1

        return [
            _row_to_response(kb, doc_counts.get(kb["id"], 0))
            for kb in kbs
        ]

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to list knowledge bases | user_id=%s | error=%s | request_id=%s",
            user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to retrieve knowledge bases.",
            request_id=request_id,
        ) from exc


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    body: KnowledgeBaseCreate,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> KnowledgeBaseResponse:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        # Check KB limit before inserting
        count_result = (
            supabase.table("knowledge_bases")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )

        current_count = count_result.count if count_result.count is not None else 0

        if current_count >= MAX_KB_PER_USER:
            raise AppException(
                status_code=429,
                code="KB_LIMIT_REACHED",
                message=f"You can create a maximum of {MAX_KB_PER_USER} knowledge bases.",
                request_id=request_id,
            )

        insert_data: dict[str, str | None] = {
            "user_id": user_id,
            "name": body.name.strip(),
        }
        if body.description is not None:
            insert_data["description"] = body.description.strip()

        result = (
            supabase.table("knowledge_bases")
            .insert(insert_data)
            .execute()
        )

        kb = result.data[0]

        logger.info(
            "Created knowledge base | kb_id=%s | user_id=%s | request_id=%s",
            kb["id"], user_id, request_id,
        )

        return _row_to_response(kb, 0)

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to create knowledge base | user_id=%s | error=%s | request_id=%s",
            user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to create knowledge base.",
            request_id=request_id,
        ) from exc


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> KnowledgeBaseResponse:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        result = (
            supabase.table("knowledge_bases")
            .select("*")
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

        kb = result.data[0]

        doc_count_result = (
            supabase.table("documents")
            .select("id", count="exact")
            .eq("knowledge_base_id", kb_id)
            .execute()
        )

        doc_count = doc_count_result.count if doc_count_result.count is not None else 0

        return _row_to_response(kb, doc_count)

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to get knowledge base | kb_id=%s | user_id=%s | error=%s | request_id=%s",
            kb_id, user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to retrieve knowledge base.",
            request_id=request_id,
        ) from exc


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    body: KnowledgeBaseUpdate,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> KnowledgeBaseResponse:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        # Verify ownership
        existing = (
            supabase.table("knowledge_bases")
            .select("id")
            .eq("id", kb_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not existing.data:
            raise AppException(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Knowledge base not found.",
                request_id=request_id,
            )

        update_data: dict[str, str] = {}
        if body.name is not None:
            update_data["name"] = body.name.strip()
        if body.description is not None:
            update_data["description"] = body.description.strip()

        if not update_data:
            # Nothing to update — return the existing KB
            return await get_knowledge_base(kb_id, user, supabase)

        result = (
            supabase.table("knowledge_bases")
            .update(update_data)
            .eq("id", kb_id)
            .eq("user_id", user_id)
            .execute()
        )

        kb = result.data[0]

        doc_count_result = (
            supabase.table("documents")
            .select("id", count="exact")
            .eq("knowledge_base_id", kb_id)
            .execute()
        )

        doc_count = doc_count_result.count if doc_count_result.count is not None else 0

        logger.info(
            "Updated knowledge base | kb_id=%s | user_id=%s | request_id=%s",
            kb_id, user_id, request_id,
        )

        return _row_to_response(kb, doc_count)

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to update knowledge base | kb_id=%s | user_id=%s | error=%s | request_id=%s",
            kb_id, user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to update knowledge base.",
            request_id=request_id,
        ) from exc


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: str,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> None:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        # Verify ownership
        existing = (
            supabase.table("knowledge_bases")
            .select("id")
            .eq("id", kb_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not existing.data:
            raise AppException(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Knowledge base not found.",
                request_id=request_id,
            )

        # Delete KB — cascades to documents, chunks, conversations, messages via FK
        (
            supabase.table("knowledge_bases")
            .delete()
            .eq("id", kb_id)
            .eq("user_id", user_id)
            .execute()
        )

        logger.info(
            "Deleted knowledge base | kb_id=%s | user_id=%s | request_id=%s",
            kb_id, user_id, request_id,
        )

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to delete knowledge base | kb_id=%s | user_id=%s | error=%s | request_id=%s",
            kb_id, user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to delete knowledge base.",
            request_id=request_id,
        ) from exc
