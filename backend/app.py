"""
GovScheme AI — FastAPI backend (Step 7)

Integrates the Gemini agent, RAG/ChromaDB tools, and document upload.
Swagger UI: /docs
ReDoc: /redoc
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import chat, documents, schemes

app = FastAPI(
    title="GovScheme AI API",
    description=(
        "Indian Government Schemes AI Assistant API.\n\n"
        "Provides chat with a Gemini tool-using agent, scheme search/list/"
        "eligibility endpoints, and document upload into the ChromaDB RAG store."
    ),
    version="0.7.0",
    contact={"name": "GovScheme AI"},
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


app.include_router(chat.router)
app.include_router(schemes.router)
app.include_router(documents.router)
