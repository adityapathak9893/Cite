import io
import logging

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except Exception as exc:
        logger.error("PDF extraction failed: %s", str(exc))
        raise


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode plain text bytes, with encoding fallback."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def extract_text_from_md(file_bytes: bytes) -> str:
    """Decode markdown bytes (same logic as plain text)."""
    return extract_text_from_txt(file_bytes)


def extract_text(file_bytes: bytes, mime_type: str) -> str:
    """Route to the correct extractor based on mime type."""
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if mime_type in ("text/plain", "text/markdown"):
        return extract_text_from_txt(file_bytes)
    raise ValueError(f"Unsupported mime type: {mime_type}")
