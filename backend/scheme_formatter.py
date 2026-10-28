"""
Format verified official scheme records into RAG documents.

Keeps retrieval text grounded in sourced fields only.
"""

from typing import Any


def format_scheme_document(scheme: dict[str, Any]) -> str:
    """Build a retrieval document from a structured official scheme record."""

    def bullets(items: list[str] | None) -> str:
        if not items:
            return "Not specified in the stored official summary."
        return "\n".join(f"- {item}" for item in items)

    return f"""
Scheme Name: {scheme['name']}
Scheme ID: {scheme['id']}
Category: {scheme.get('category', 'general')}
Ministry / Agency: {scheme.get('ministry', 'Not specified')}
Official portal: {scheme.get('official_portal', 'Not specified')}
Application / more info: {scheme.get('application_url', 'Not specified')}
Source: {scheme.get('source', 'Official Government of India source')}
Record type: official

Summary:
{scheme.get('summary', '').strip()}

Eligibility:
{bullets(scheme.get('eligibility'))}

Benefits:
{bullets(scheme.get('benefits'))}

Required documents:
{bullets(scheme.get('documents'))}

How to apply:
{scheme.get('how_to_apply', 'Follow the official portal instructions.').strip()}

Notes:
{bullets(scheme.get('notes'))}

Important:
- Use only the information above.
- Do not invent extra eligibility rules, benefit amounts, deadlines, or documents.
- Scheme details can change; verify on the official portal before applying.
""".strip()


def scheme_metadata(scheme: dict[str, Any]) -> dict[str, str | bool]:
    """Chroma-compatible metadata for an official scheme."""
    return {
        "name": scheme["name"],
        "category": str(scheme.get("category", "general")).lower(),
        "ministry": scheme.get("ministry") or "",
        "official_portal": scheme.get("official_portal") or "",
        "application_url": scheme.get("application_url") or "",
        "source": scheme.get("source") or "",
        "record_type": "official",
        "is_official": True,
    }
