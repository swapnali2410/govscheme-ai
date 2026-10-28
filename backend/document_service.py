"""
Document ingestion for scheme knowledge base uploads.

Supports .txt, .md, and .pdf files. Extracted text is embedded
and stored in the existing ChromaDB RAG collection.
"""

import io
import re
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader

from rag_service import BACKEND_DIR, upsert_document

UPLOADS_DIR = BACKEND_DIR / "uploads"
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_FILE_BYTES = 5_000_000  # 5 MB
MAX_CONTENT_CHARS = 50_000


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    slug = slug.strip("_")
    return slug[:60] or "document"


def ensure_uploads_dir() -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR


def build_document_id(name: str, doc_id: str | None = None) -> str:
    if doc_id and doc_id.strip():
        return _slugify(doc_id)
    return f"upload_{_slugify(name)}_{uuid4().hex[:8]}"


def extract_pdf_text(raw_bytes: bytes) -> str:
    """Extract plain text from a PDF byte payload."""
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
    except Exception as error:
        raise ValueError(
            f"Could not read PDF file. Make sure it is a valid PDF. ({error})"
        ) from error

    if getattr(reader, "is_encrypted", False):
        try:
            unlocked = reader.decrypt("")
        except Exception as error:
            raise ValueError(
                "Encrypted PDFs are not supported. Upload an unlocked PDF."
            ) from error
        if unlocked == 0:
            raise ValueError(
                "Encrypted PDFs are not supported. Upload an unlocked PDF."
            )

    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text.strip())

    text = "\n\n".join(pages).strip()
    if not text:
        raise ValueError(
            "No extractable text found in the PDF. "
            "Scanned image-only PDFs are not supported yet."
        )
    return text


def extract_text_file(raw_bytes: bytes) -> str:
    """Decode a UTF-8 text/markdown upload."""
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("Text files must be UTF-8 encoded.") from error


def save_scheme_document(
    name: str,
    content: str,
    category: str | None = None,
    doc_id: str | None = None,
    source_filename: str | None = None,
) -> dict:
    """Validate, embed, and upsert scheme text into ChromaDB."""
    clean_name = name.strip()
    clean_content = content.strip()

    if not clean_name:
        raise ValueError("Document name is required.")
    if not clean_content:
        raise ValueError("Document content is empty.")
    if len(clean_content) > MAX_CONTENT_CHARS:
        raise ValueError(
            f"Document content exceeds {MAX_CONTENT_CHARS:,} characters."
        )

    document_id = build_document_id(clean_name, doc_id)
    metadata = {
        "name": clean_name,
        "source": "user_upload",
        "record_type": "upload",
        "is_official": False,
    }
    if category and category.strip():
        metadata["category"] = category.strip().lower()
    if source_filename:
        metadata["filename"] = source_filename
        metadata["file_type"] = Path(source_filename).suffix.lower().lstrip(".")

    document_text = f"{clean_name}. {clean_content}"
    stored = upsert_document(
        doc_id=document_id,
        document=document_text,
        metadata=metadata,
    )

    ensure_uploads_dir()
    backup_path = UPLOADS_DIR / f"{document_id}.txt"
    backup_path.write_text(document_text, encoding="utf-8")

    return {
        "success": True,
        "id": stored["id"],
        "name": clean_name,
        "category": metadata.get("category"),
        "characters": len(clean_content),
        "message": "Document embedded and stored in the scheme knowledge base.",
    }


def read_uploaded_file(filename: str, raw_bytes: bytes) -> str:
    """
    Extract text from an uploaded .txt, .md, or .pdf file.

    PDF text is extracted with pypdf, then reused by the same
    embedding / ChromaDB upsert path as plain text uploads.
    """
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Allowed extensions: .txt, .md, .pdf"
        )

    if len(raw_bytes) > MAX_FILE_BYTES:
        raise ValueError(
            f"File too large. Maximum size is {MAX_FILE_BYTES // 1_000_000} MB."
        )

    if not raw_bytes:
        raise ValueError("Uploaded file is empty.")

    if suffix == ".pdf":
        text = extract_pdf_text(raw_bytes)
    else:
        text = extract_text_file(raw_bytes)

    if not text.strip():
        raise ValueError("Uploaded file has no readable text content.")

    return text
