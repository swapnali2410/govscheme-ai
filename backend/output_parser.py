"""
Structured output parser for GovScheme AI.

Takes the existing agent text reply (already grounded by tools/RAG)
and asks Gemini to return JSON matching StructuredChatPayload.
Pydantic validates the result before it is returned to the API.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from google.genai import types
from pydantic import ValidationError

from rag_service import (
    CHAT_MODEL,
    CHAT_TIMEOUT_SECONDS,
    FALLBACK_CHAT_MODEL,
    get_gemini_client,
)
from schemas import StructuredChatPayload, StructuredSchemeInfo

logger = logging.getLogger(__name__)

PARSE_PROMPT = """
Convert the assistant reply into structured JSON for an Indian
government schemes helper.

Rules:
- Use ONLY facts present in the assistant reply. Do not invent schemes,
  benefits, eligibility rules, documents, or URLs.
- If a field is missing, use null / empty list and list the field name
  in missing_fields for that scheme.
- If the reply says information is unavailable, set data_available=false
  and keep schemes empty or mark the scheme accordingly.
- Prefer official portal / application URLs exactly as written.
- Keep answer_summary short and clear.
- Always include a disclaimer reminding the user to verify on the
  official portal.

User question:
{question}

Assistant reply:
{reply}
"""


def _empty_payload(summary: str, note: str | None = None) -> StructuredChatPayload:
    return StructuredChatPayload(
        answer_summary=summary,
        schemes=[],
        follow_up_question=None,
        disclaimer=(
            "Verify scheme details on the official portal before applying. "
            "Rules can change."
        ),
        source_note=note,
    )


def _generate_structured(
    model: str,
    question: str,
    reply: str,
) -> StructuredChatPayload:
    client = get_gemini_client()
    prompt = PARSE_PROMPT.format(question=question.strip(), reply=reply.strip())

    def _call():
        return client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=StructuredChatPayload,
            ),
        )

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call)
        response = future.result(timeout=CHAT_TIMEOUT_SECONDS)

    raw = (response.text or "").strip()
    if not raw:
        raise ValueError("Structured model returned empty JSON.")

    return StructuredChatPayload.model_validate_json(raw)


def parse_agent_reply(question: str, reply: str) -> tuple[StructuredChatPayload, str | None]:
    """
    Parse agent text into StructuredChatPayload.

    Returns (payload, parse_error). parse_error is None on success.
    Falls back to a safe empty payload when parsing fails.
    """
    if not reply or not reply.strip():
        payload = _empty_payload(
            summary="No assistant reply was available to structure.",
            note="Missing agent reply",
        )
        return payload, "Empty agent reply"

    try:
        return _generate_structured(CHAT_MODEL, question, reply), None
    except FuturesTimeoutError:
        primary_error = f"{CHAT_MODEL} structured parse timed out"
    except (ValidationError, ValueError, Exception) as error:
        primary_error = error

    logger.warning(
        "Structured parse with %s failed (%s); trying %s",
        CHAT_MODEL,
        primary_error,
        FALLBACK_CHAT_MODEL,
    )

    try:
        return _generate_structured(FALLBACK_CHAT_MODEL, question, reply), None
    except FuturesTimeoutError as error:
        payload = _empty_payload(
            summary=reply[:500],
            note="Structured parse timed out; returning text-only fallback.",
        )
        return payload, f"Structured parse timed out: {error}"
    except (ValidationError, ValueError) as error:
        payload = _empty_payload(
            summary=reply[:500],
            note="Structured parse validation failed; returning text-only fallback.",
        )
        return payload, f"Structured parse validation failed: {error}"
    except Exception as error:
        payload = _empty_payload(
            summary=reply[:500],
            note="Structured parse failed; returning text-only fallback.",
        )
        return payload, f"Structured parse failed: {error}"


def ensure_missing_fields(payload: StructuredChatPayload) -> StructuredChatPayload:
    """Fill missing_fields for each scheme when lists/URLs are empty."""
    tracked = (
        "summary",
        "benefits",
        "eligibility",
        "documents",
        "official_portal",
        "application_url",
        "how_to_apply",
    )
    updated: list[StructuredSchemeInfo] = []
    for scheme in payload.schemes:
        missing = list(scheme.missing_fields)
        for field in tracked:
            value = getattr(scheme, field)
            empty = value is None or value == "" or value == []
            if empty and field not in missing:
                missing.append(field)
        updated.append(scheme.model_copy(update={"missing_fields": missing}))
    return payload.model_copy(update={"schemes": updated})
