"""
In-memory conversation sessions for the FastAPI chat endpoint.

Each session holds a Gemini agent chat object so multi-turn
context is preserved across requests.
"""

from threading import Lock
from uuid import uuid4

from agent import create_agent_chat


class ConversationStore:
    """Thread-safe map of session_id -> Gemini chat session."""

    def __init__(self):
        self._sessions = {}
        self._lock = Lock()

    def create_session(self) -> str:
        session_id = str(uuid4())
        chat = create_agent_chat()
        with self._lock:
            self._sessions[session_id] = chat
        return session_id

    def get_or_create(self, session_id: str | None = None) -> tuple[str, object]:
        if session_id:
            with self._lock:
                chat = self._sessions.get(session_id)
            if chat is not None:
                return session_id, chat

        new_id = self.create_session()
        with self._lock:
            return new_id, self._sessions[new_id]

    def replace_chat(self, session_id: str, chat) -> None:
        """Replace the chat object for a session (e.g. after model fallback)."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id] = chat

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)


conversation_store = ConversationStore()
