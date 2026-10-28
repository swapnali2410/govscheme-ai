"""
Seed verified official Indian government scheme data into ChromaDB.

Uses the existing RAG upsert pipeline. Removes legacy fictional demo_*
records so answers stay grounded in official sourced data.
"""

import json
from pathlib import Path

from rag_service import (
    BACKEND_DIR,
    CHROMA_PATH,
    COLLECTION_NAME,
    get_collection,
    upsert_document,
)
from scheme_formatter import format_scheme_document, scheme_metadata

DATA_FILE = BACKEND_DIR / "data" / "official_schemes.json"
DEMO_PREFIXES = ("demo_", "upload_demo_")


def load_official_schemes() -> list[dict]:
    with DATA_FILE.open(encoding="utf-8") as handle:
        schemes = json.load(handle)
    if not isinstance(schemes, list) or not schemes:
        raise ValueError("official_schemes.json must contain a non-empty list")
    return schemes


def remove_fictional_demo_records() -> list[str]:
    """Delete known fictional demo / test upload records from the collection."""
    collection = get_collection()
    existing = collection.get(include=["metadatas"])
    to_delete = []

    for scheme_id, metadata in zip(existing["ids"], existing["metadatas"]):
        meta = metadata or {}
        if scheme_id.startswith(DEMO_PREFIXES):
            to_delete.append(scheme_id)
            continue
        if meta.get("record_type") == "demo" or meta.get("source") == "demo":
            to_delete.append(scheme_id)

    # Explicit legacy demo ids from Step 5 sample data
    legacy_demo_ids = [
        "demo_student",
        "demo_farmer",
        "demo_women",
        "demo_housing",
        "demo_senior_skill_api_test",
    ]
    for scheme_id in legacy_demo_ids:
        if scheme_id in existing["ids"] and scheme_id not in to_delete:
            to_delete.append(scheme_id)

    if to_delete:
        collection.delete(ids=to_delete)

    return to_delete


def ensure_collection():
    """Ensure the RAG collection exists before seeding."""
    import chromadb

    db = chromadb.PersistentClient(path=CHROMA_PATH)
    db.get_or_create_collection(name=COLLECTION_NAME)
    # Reset cached handle so get_collection sees the collection
    import rag_service

    rag_service._collection = None
    return get_collection()


def seed_official_schemes(remove_demos: bool = True) -> dict:
    ensure_collection()
    schemes = load_official_schemes()

    removed = remove_fictional_demo_records() if remove_demos else []
    saved = []

    print(f"Seeding {len(schemes)} official schemes into '{COLLECTION_NAME}'...")
    for scheme in schemes:
        document = format_scheme_document(scheme)
        metadata = scheme_metadata(scheme)
        stored = upsert_document(
            doc_id=scheme["id"],
            document=document,
            metadata=metadata,
        )
        saved.append(stored["id"])
        print(f"Saved: {scheme['name']}")

    collection = get_collection()
    return {
        "saved": saved,
        "removed_demos": removed,
        "total_documents": collection.count(),
        "data_file": str(DATA_FILE),
    }


if __name__ == "__main__":
    result = seed_official_schemes(remove_demos=True)
    print("\nOfficial scheme seeding complete.")
    print("Removed fictional records:", result["removed_demos"])
    print("Saved official ids:", result["saved"])
    print("Total documents in collection:", result["total_documents"])
