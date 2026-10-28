"""Document upload endpoints for expanding the scheme knowledge base."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from document_service import read_uploaded_file, save_scheme_document
from schemas import DocumentTextRequest, DocumentUploadResponse

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a scheme document (.txt, .md, or .pdf)",
)
async def upload_document_file(
    file: UploadFile = File(
        ...,
        description="Scheme document file (.txt, .md, or text-based .pdf)",
    ),
    name: str | None = Form(
        default=None,
        description="Display name for the scheme document",
    ),
    category: str | None = Form(
        default=None,
        description="Optional category metadata",
    ),
    doc_id: str | None = Form(
        default=None,
        description="Optional custom document id",
    ),
):
    raw = await file.read()

    try:
        content = read_uploaded_file(file.filename or "", raw)
        document_name = (name or file.filename or "Uploaded Scheme").strip()
        # Strip extension from default name
        if name is None and file.filename and "." in document_name:
            document_name = document_name.rsplit(".", 1)[0]

        result = save_scheme_document(
            name=document_name,
            content=content,
            category=category,
            doc_id=doc_id,
            source_filename=file.filename,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store document: {error}",
        ) from error

    return DocumentUploadResponse(**result)


@router.post(
    "/text",
    response_model=DocumentUploadResponse,
    summary="Add a scheme document from JSON text",
)
def upload_document_text(request: DocumentTextRequest):
    try:
        result = save_scheme_document(
            name=request.name,
            content=request.content,
            category=request.category,
            doc_id=request.doc_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store document: {error}",
        ) from error

    return DocumentUploadResponse(**result)
