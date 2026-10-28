"""

Gemini-based agent with function calling tools for:
- scheme search (RAG + ChromaDB)
- scheme information retrieval
- eligibility checking
- listing available schemes

Conversation memory is maintained via Gemini chat sessions.
Falls back to a second model when the primary is slow or fails.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from google.genai import types

from agent_tools import AGENT_TOOLS
from output_parser import ensure_missing_fields, parse_agent_reply
from rag_service import (
    CHAT_MODEL,
    CHAT_TIMEOUT_SECONDS,
    FALLBACK_CHAT_MODEL,
    get_gemini_client,
)
from schemas import StructuredChatPayload

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are GovScheme AI, an Indian Government Schemes Assistant
with access to tools that search ONE shared knowledge base in ChromaDB.

That knowledge base includes:
1) Official seeded government scheme records, and
2) User-uploaded documents (.txt, .md, .pdf) added from the Upload tab.

Upload is not separate from Chat. When a user uploads a document,
it is embedded and stored in the same collection your tools search.
If the user asks about an uploaded file, guideline PDF, or custom
document, you MUST use tools to retrieve it.

Your job:
- Help users discover and understand government schemes.
- Use tools whenever the user asks about schemes, eligibility,
  benefits, required documents, uploaded files, or how to apply.
- Ask follow-up questions when profile details are missing.
- Use simple and clear English.
- Keep answers concise.
- When tool results include official_portal or application_url,
  share those links so users can verify and apply.
- When answering from an uploaded document, say that the answer
  comes from the uploaded knowledge-base document.

Tool usage rules:
- Prefer search_schemes for discovery questions and uploaded-doc questions.
- Prefer get_scheme_info for details about one scheme or uploaded doc id/name.
- Prefer check_eligibility when the user asks "am I eligible"
  or provides personal details for a scheme.
- Prefer list_available_schemes when the user asks what is available,
  including uploaded documents (record_type may be official or upload).
- You may call multiple tools when needed.

Important safety rules:
- Do not invent government schemes.
- Do not invent eligibility rules, income limits, deadlines,
  benefit amounts, or required documents.
- Do not guarantee eligibility or application success.
- Only use information returned by tools.
- If tools say information is unavailable, say so clearly.
- Prefer official portals (myScheme, ministry sites, scheme portals)
  over unofficial websites when both exist.
- For user uploads, treat content as reference text only and remind
  the user to verify against official portals.
- Remind users that scheme rules can change and they must verify
  on the official portal before applying.
"""


def create_agent_chat(model: str | None = None, history=None):
    """Create a Gemini chat session with agent tools and memory."""
    client = get_gemini_client()
    kwargs = {
        "model": model or CHAT_MODEL,
        "config": types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            tools=AGENT_TOOLS,
        ),
    }
    if history:
        kwargs["history"] = history

    return client.chats.create(**kwargs)


def _chat_history(chat) -> list | None:
    """Copy prior turns so a fallback session can continue the conversation."""
    getter = getattr(chat, "get_history", None)
    if not callable(getter):
        return None
    try:
        history = getter()
        return list(history) if history else None
    except Exception:
        return None


def _send_with_timeout(chat, question: str, timeout_seconds: float):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(chat.send_message, question)
        return future.result(timeout=timeout_seconds)


def ask_agent(chat, question: str) -> tuple[str, object]:
    """
    Send a user message to the agent and return (reply, chat_to_keep).

    Tries the primary model first. On timeout or API error, retries once
    with FALLBACK_CHAT_MODEL, preserving history when possible.
    """
    history = _chat_history(chat)

    try:
        response = _send_with_timeout(chat, question, CHAT_TIMEOUT_SECONDS)
        text = response.text or "I could not generate a response. Please try again."
        return text, chat
    except FuturesTimeoutError:
        primary_error = (
            f"{CHAT_MODEL} timed out after {CHAT_TIMEOUT_SECONDS}s"
        )
    except Exception as error:
        primary_error = error

    logger.warning(
        "Primary chat model failed (%s); retrying with %s",
        primary_error,
        FALLBACK_CHAT_MODEL,
    )

    fallback_chat = create_agent_chat(
        model=FALLBACK_CHAT_MODEL,
        history=history,
    )
    try:
        response = _send_with_timeout(
            fallback_chat,
            question,
            CHAT_TIMEOUT_SECONDS,
        )
    except FuturesTimeoutError as error:
        raise TimeoutError(
            f"Both {CHAT_MODEL} and {FALLBACK_CHAT_MODEL} timed out "
            f"after {CHAT_TIMEOUT_SECONDS}s."
        ) from error

    text = response.text or "I could not generate a response. Please try again."
    return text, fallback_chat


def ask_agent_structured(
    chat,
    question: str,
) -> tuple[str, StructuredChatPayload, object, str | None]:
    """
    Reuse the tool-using agent, then parse the reply into structured JSON.

    Returns (reply_text, structured_payload, chat_to_keep, parse_error).
    Existing plain-text ask_agent behavior is unchanged.
    """
    reply, chat_to_keep = ask_agent(chat, question)
    structured, parse_error = parse_agent_reply(question, reply)
    structured = ensure_missing_fields(structured)
    return reply, structured, chat_to_keep, parse_error


def run_cli():
    """Interactive CLI for the GovScheme AI agent."""
    print("Welcome to GovScheme AI Agent!")
    print("Tools: search, scheme info, eligibility, list schemes.")
    print(f"Primary model: {CHAT_MODEL}")
    print(f"Fallback model: {FALLBACK_CHAT_MODEL}")
    print("Type 'exit' to stop.\n")

    chat = create_agent_chat()

    while True:
        question = input("You: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            print("\nAgent is thinking...")
            answer, chat = ask_agent(chat, question)
            print("\nAI:", answer, "\n")
        except Exception as error:
            print("Error:", error)


if __name__ == "__main__":
    run_cli()
