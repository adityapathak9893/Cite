import logging
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from supabase import Client

from app.config import get_settings
from app.dependencies import AppException, get_current_user, get_supabase
from app.models.schemas import DocumentResponse
from app.services.chunking import chunk_document
from app.services.embedding import embed_texts
from app.services.extraction import extract_text

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/knowledge-bases/{kb_id}/documents",
    tags=["documents"],
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_DOCUMENTS_PER_KB = 50
MAX_TOTAL_STORAGE = 500 * 1024 * 1024  # 500 MB

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
ALLOWED_MIME_TYPES = {"application/pdf", "text/plain", "text/markdown"}

# Map common content-type variations to our canonical types
MIME_TYPE_MAP: dict[str, str] = {
    "application/pdf": "application/pdf",
    "text/plain": "text/plain",
    "text/markdown": "text/markdown",
    "text/x-markdown": "text/markdown",
    "application/octet-stream": "",  # needs extension check
}

STORAGE_BUCKET = "documents"


def _get_extension(filename: str) -> str:
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


def _resolve_mime_type(content_type: str | None, extension: str) -> str:
    """Determine the real mime type from content-type header and extension."""
    # Extension-based mapping as primary source of truth
    ext_to_mime = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }

    mime_from_ext = ext_to_mime.get(extension, "")

    if content_type:
        canonical = MIME_TYPE_MAP.get(content_type.split(";")[0].strip(), "")
        if canonical:
            return canonical

    return mime_from_ext


def _row_to_response(row: dict) -> DocumentResponse:
    return DocumentResponse(
        id=row["id"],
        knowledge_base_id=row["knowledge_base_id"],
        user_id=row["user_id"],
        file_name=row["file_name"],
        file_path=row["file_path"],
        file_size=row.get("file_size"),
        mime_type=row.get("mime_type"),
        status=row["status"],
        error_message=row.get("error_message"),
        chunk_count=row.get("chunk_count", 0),
        created_at=row["created_at"],
    )


def _verify_kb_ownership(
    supabase: Client, kb_id: str, user_id: str, request_id: str
) -> None:
    """Verify the user owns the KB. Raises 404 if not found/not owned."""
    result = (
        supabase.table("knowledge_bases")
        .select("id")
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


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    kb_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> DocumentResponse:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        _verify_kb_ownership(supabase, kb_id, user_id, request_id)

        # --- Validation per CLAUDE.md File Upload Validation order ---

        # 1. Check file size (read content)
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size > MAX_FILE_SIZE:
            raise AppException(
                status_code=413,
                code="FILE_TOO_LARGE",
                message="File size exceeds the 50MB limit.",
                request_id=request_id,
            )

        if file_size == 0:
            raise AppException(
                status_code=422,
                code="VALIDATION_ERROR",
                message="File is empty.",
                request_id=request_id,
            )

        # 2. Check file extension
        filename = file.filename or "untitled"
        extension = _get_extension(filename)

        if extension not in ALLOWED_EXTENSIONS:
            raise AppException(
                status_code=415,
                code="FILE_TYPE_NOT_ALLOWED",
                message="This file type is not supported. Please upload PDF, TXT, or MD files.",
                request_id=request_id,
            )

        # 3. Check mime type
        mime_type = _resolve_mime_type(file.content_type, extension)
        if mime_type not in ALLOWED_MIME_TYPES:
            raise AppException(
                status_code=415,
                code="FILE_TYPE_NOT_ALLOWED",
                message="This file type is not supported. Please upload PDF, TXT, or MD files.",
                request_id=request_id,
            )

        # 4. Check document count limit for this KB
        doc_count_result = (
            supabase.table("documents")
            .select("id", count="exact")
            .eq("knowledge_base_id", kb_id)
            .execute()
        )
        current_doc_count = doc_count_result.count if doc_count_result.count is not None else 0

        if current_doc_count >= MAX_DOCUMENTS_PER_KB:
            raise AppException(
                status_code=429,
                code="DOCUMENT_LIMIT_REACHED",
                message=f"Maximum {MAX_DOCUMENTS_PER_KB} documents per knowledge base.",
                request_id=request_id,
            )

        # 5. Check user total storage limit
        storage_result = (
            supabase.table("documents")
            .select("file_size")
            .eq("user_id", user_id)
            .execute()
        )
        total_storage = sum(
            (doc.get("file_size") or 0) for doc in (storage_result.data or [])
        )
        if total_storage + file_size > MAX_TOTAL_STORAGE:
            raise AppException(
                status_code=429,
                code="DOCUMENT_LIMIT_REACHED",
                message="Total storage limit of 500MB exceeded.",
                request_id=request_id,
            )

        # --- Upload to Supabase Storage ---
        doc_id = str(uuid.uuid4())
        storage_path = f"{user_id}/{kb_id}/{doc_id}/{filename}"

        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": mime_type},
        )

        # --- Create document record ---
        doc_row = (
            supabase.table("documents")
            .insert({
                "id": doc_id,
                "knowledge_base_id": kb_id,
                "user_id": user_id,
                "file_name": filename,
                "file_path": storage_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "status": "processing",
            })
            .execute()
        )

        doc = doc_row.data[0]

        logger.info(
            "Document uploaded | doc_id=%s | kb_id=%s | file=%s | size=%d | request_id=%s",
            doc_id, kb_id, filename, file_size, request_id,
        )

        # --- Trigger background processing ---
        settings = get_settings()
        background_tasks.add_task(
            process_document,
            doc_id=doc_id,
            kb_id=kb_id,
            file_bytes=file_bytes,
            file_name=filename,
            mime_type=mime_type,
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )

        return _row_to_response(doc)

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Upload failed | kb_id=%s | user_id=%s | error=%s | request_id=%s",
            kb_id, user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to upload document.",
            request_id=request_id,
        ) from exc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    kb_id: str,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[DocumentResponse]:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        _verify_kb_ownership(supabase, kb_id, user_id, request_id)

        result = (
            supabase.table("documents")
            .select("*")
            .eq("knowledge_base_id", kb_id)
            .order("created_at", desc=True)
            .execute()
        )

        return [_row_to_response(row) for row in (result.data or [])]

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "List documents failed | kb_id=%s | user_id=%s | error=%s | request_id=%s",
            kb_id, user_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to list documents.",
            request_id=request_id,
        ) from exc


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    kb_id: str,
    doc_id: str,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> DocumentResponse:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        _verify_kb_ownership(supabase, kb_id, user_id, request_id)

        result = (
            supabase.table("documents")
            .select("*")
            .eq("id", doc_id)
            .eq("knowledge_base_id", kb_id)
            .execute()
        )

        if not result.data:
            raise AppException(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Document not found.",
                request_id=request_id,
            )

        return _row_to_response(result.data[0])

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Get document failed | doc_id=%s | kb_id=%s | error=%s | request_id=%s",
            doc_id, kb_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to retrieve document.",
            request_id=request_id,
        ) from exc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    kb_id: str,
    doc_id: str,
    user: dict[str, str] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> None:
    request_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        _verify_kb_ownership(supabase, kb_id, user_id, request_id)

        # Get document to find storage path
        result = (
            supabase.table("documents")
            .select("id, file_path")
            .eq("id", doc_id)
            .eq("knowledge_base_id", kb_id)
            .execute()
        )

        if not result.data:
            raise AppException(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Document not found.",
                request_id=request_id,
            )

        file_path = result.data[0]["file_path"]

        # Delete from storage
        try:
            supabase.storage.from_(STORAGE_BUCKET).remove([file_path])
        except Exception as storage_exc:
            logger.warning(
                "Storage delete failed (continuing) | path=%s | error=%s",
                file_path, str(storage_exc),
            )

        # Delete document record (cascades to chunks via FK)
        supabase.table("documents").delete().eq("id", doc_id).execute()

        logger.info(
            "Deleted document | doc_id=%s | kb_id=%s | user_id=%s | request_id=%s",
            doc_id, kb_id, user_id, request_id,
        )

    except AppException:
        raise
    except Exception as exc:
        logger.error(
            "Delete document failed | doc_id=%s | kb_id=%s | error=%s | request_id=%s",
            doc_id, kb_id, str(exc), request_id,
        )
        raise AppException(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Failed to delete document.",
            request_id=request_id,
        ) from exc


# ─── Background processing pipeline ───


async def process_document(
    doc_id: str,
    kb_id: str,
    file_bytes: bytes,
    file_name: str,
    mime_type: str,
    supabase_url: str,
    supabase_key: str,
) -> None:
    """Background task: extract → AI chunk → embed (combined text) → store."""
    from supabase import create_client

    supabase = create_client(supabase_url, supabase_key)
    start_time = time.time()

    def _set_status(status: str, error_message: str | None = None, chunk_count: int = 0) -> None:
        update: dict = {"status": status}
        if error_message is not None:
            update["error_message"] = error_message
        if chunk_count > 0:
            update["chunk_count"] = chunk_count
        supabase.table("documents").update(update).eq("id", doc_id).execute()

    try:
        # 1. Extract text
        logger.info("Processing document | doc_id=%s | step=extraction", doc_id)
        text = extract_text(file_bytes, mime_type)

        if not text or not text.strip():
            _set_status(
                "failed",
                "This PDF contains no extractable text. Scanned documents are not supported yet."
                if mime_type == "application/pdf"
                else "The file contains no readable text.",
            )
            logger.warning("No text extracted | doc_id=%s", doc_id)
            return

        # 2. AI-powered intelligent chunking
        logger.info("Processing document | doc_id=%s | step=chunking (AI)", doc_id)
        chunks = await chunk_document(text, file_name)

        if not chunks:
            _set_status("failed", "Could not split document into chunks.")
            logger.warning("No chunks produced | doc_id=%s", doc_id)
            return

        logger.info(
            "Chunking complete | doc_id=%s | chunks=%d | titles=%s",
            doc_id,
            len(chunks),
            [c.get("metadata", {}).get("title", "?") for c in chunks],
        )

        # 3. Generate embeddings using COMBINED text (search_description + content)
        # This improves retrieval because the embedding captures both keywords and full content
        logger.info(
            "Processing document | doc_id=%s | step=embedding | chunks=%d",
            doc_id, len(chunks),
        )
        combined_texts = []
        for c in chunks:
            meta = c.get("metadata", {})
            description = meta.get("search_description", "")
            content = c["content"]
            combined = f"{description}\n\n{content}" if description else content
            combined_texts.append(combined)

        embeddings = await embed_texts(combined_texts)

        # 4. Store chunks + embeddings in document_chunks
        # NOTE: content stores the ORIGINAL section text, not the combined text
        logger.info("Processing document | doc_id=%s | step=storing_chunks", doc_id)
        rows = []
        for chunk, embedding in zip(chunks, embeddings):
            rows.append({
                "document_id": doc_id,
                "knowledge_base_id": kb_id,
                "content": chunk["content"],
                "embedding": embedding,
                "chunk_index": chunk["chunk_index"],
                "metadata": chunk.get("metadata", {}),
            })

        # Insert in batches of 50 to avoid payload size limits
        batch_size = 50
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            supabase.table("document_chunks").insert(batch).execute()

        # 5. Mark as ready
        _set_status("ready", chunk_count=len(chunks))

        duration = time.time() - start_time
        logger.info(
            "Document processed | doc_id=%s | chunks=%d | duration=%.1fs",
            doc_id, len(chunks), duration,
        )

    except Exception as exc:
        duration = time.time() - start_time
        logger.error(
            "Processing failed | doc_id=%s | duration=%.1fs | error=%s",
            doc_id, duration, str(exc),
        )
        _set_status("failed", "Document processing failed. Please try uploading again.")
