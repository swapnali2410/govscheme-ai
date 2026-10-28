"""
Shared RAG helpers for ChromaDB retrieval and Gemini embeddings.
Reused by the RAG chatbot and the AI agent tools.
"""

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
CHROMA_PATH = str(BACKEND_DIR / "chroma_db")
COLLECTION_NAME = "rag_demo_schemes"
EMBEDDING_MODEL = "gemini-embedding-001"
CHAT_MODEL = "gemini-3.1-flash-lite"
# Used when the primary chat model times out or errors.
FALLBACK_CHAT_MODEL = "gemini-3.5-flash-lite"
CHAT_TIMEOUT_SECONDS = 45

_gemini_client = None
_collection = None


def get_gemini_client():
    """Return a shared Gemini client."""
    global _gemini_client

    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing")
        _gemini_client = genai.Client(api_key=api_key)

    return _gemini_client


def get_collection():
    """Return the RAG schemes ChromaDB collection (create if missing)."""
    global _collection

    if _collection is None:
        db = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = db.get_or_create_collection(name=COLLECTION_NAME)

    return _collection


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    """Create a Gemini embedding for a query or document."""
    gemini = get_gemini_client()
    response = gemini.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return response.embeddings[0].values


def retrieve_documents(
    question: str,
    n_results: int = 2,
    category: str | None = None,
) -> dict:
    """
    Semantic search over stored scheme documents.

    Returns ChromaDB query results with documents and metadatas.
    """
    collection = get_collection()
    query_embedding = embed_text(question, task_type="RETRIEVAL_QUERY")

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": max(1, min(n_results, 10)),
        "include": ["documents", "metadatas", "distances"],
    }

    if category:
        query_kwargs["where"] = {"category": category.lower().strip()}

    return collection.query(**query_kwargs)


def get_scheme_by_id(scheme_id: str) -> dict | None:
    """Fetch one scheme document by its ChromaDB id."""
    collection = get_collection()
    result = collection.get(
        ids=[scheme_id],
        include=["documents", "metadatas"],
    )

    if not result["ids"]:
        return None

    return {
        "id": result["ids"][0],
        "document": result["documents"][0],
        "metadata": result["metadatas"][0] or {},
    }


def list_schemes(category: str | None = None) -> list[dict]:
    """List stored schemes, optionally filtered by category metadata."""
    collection = get_collection()

    if category:
        result = collection.get(
            where={"category": category.lower().strip()},
            include=["documents", "metadatas"],
        )
    else:
        result = collection.get(include=["documents", "metadatas"])

    schemes = []
    for scheme_id, document, metadata in zip(
        result["ids"],
        result["documents"],
        result["metadatas"],
    ):
        schemes.append(
            {
                "id": scheme_id,
                "document": document,
                "metadata": metadata or {},
            }
        )

    return schemes


def format_retrieval_results(results: dict) -> list[dict]:
    """Normalize ChromaDB query output into a list of scheme hits."""
    if not results.get("ids") or not results["ids"][0]:
        return []

    formatted = []
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = (results.get("distances") or [[]])[0]

    for index, scheme_id in enumerate(ids):
        entry = {
            "id": scheme_id,
            "document": documents[index],
            "metadata": metadatas[index] or {},
        }
        if distances:
            entry["distance"] = distances[index]
        formatted.append(entry)

    return formatted


def upsert_document(
    doc_id: str,
    document: str,
    metadata: dict | None = None,
) -> dict:
    """Embed and upsert a document into the RAG schemes collection."""
    if not doc_id or not doc_id.strip():
        raise ValueError("doc_id is required")
    if not document or not document.strip():
        raise ValueError("document text is required")

    collection = get_collection()
    clean_id = doc_id.strip()
    clean_text = document.strip()
    meta = metadata or {}

    embedding = embed_text(clean_text, task_type="RETRIEVAL_DOCUMENT")

    collection.upsert(
        ids=[clean_id],
        documents=[clean_text],
        embeddings=[embedding],
        metadatas=[meta],
    )

    return {
        "id": clean_id,
        "document": clean_text,
        "metadata": meta,
    }
