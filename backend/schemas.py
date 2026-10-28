"""Pydantic request/response models for the FastAPI API."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User message for the GovScheme AI agent",
        examples=["Find education schemes for college students"],
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Existing chat session id. Omit to start a new conversation.",
    )


class ChatResponse(BaseModel):
    session_id: str
    message: str
    reply: str


class StructuredSchemeInfo(BaseModel):
    """One scheme card extracted from the agent reply."""

    name: Optional[str] = Field(
        default=None,
        description="Official scheme name if known",
    )
    category: Optional[str] = Field(
        default=None,
        description="Scheme category when known",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Short description of the scheme",
    )
    benefits: list[str] = Field(
        default_factory=list,
        description="Benefit points from tool/knowledge-base data only",
    )
    eligibility: list[str] = Field(
        default_factory=list,
        description="Eligibility points from tool/knowledge-base data only",
    )
    documents: list[str] = Field(
        default_factory=list,
        description="Required documents when mentioned",
    )
    official_portal: Optional[str] = Field(
        default=None,
        description="Official portal URL when present",
    )
    application_url: Optional[str] = Field(
        default=None,
        description="Application URL when present",
    )
    how_to_apply: Optional[str] = Field(
        default=None,
        description="How to apply, only if stated in the source reply",
    )
    data_available: bool = Field(
        default=True,
        description="False when scheme details were unavailable",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Field names that could not be filled from the reply",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Caveats or verification reminders",
    )


class StructuredChatPayload(BaseModel):
    """Validated structured JSON produced by the output parser."""

    answer_summary: str = Field(
        ...,
        description="Short plain-language summary of the assistant answer",
    )
    schemes: list[StructuredSchemeInfo] = Field(
        default_factory=list,
        description="Zero or more schemes mentioned in the answer",
    )
    follow_up_question: Optional[str] = Field(
        default=None,
        description="Optional clarifying question for the user",
    )
    disclaimer: str = Field(
        default=(
            "Verify scheme details on the official portal before applying. "
            "Rules can change."
        ),
        description="Safety disclaimer for the user",
    )
    source_note: Optional[str] = Field(
        default=None,
        description="Note when answer came from an uploaded document",
    )


class StructuredChatResponse(BaseModel):
    session_id: str
    message: str
    reply: str
    structured: StructuredChatPayload
    parse_success: bool = True
    parse_error: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    message: str = "Chat session created."


class SchemeSummary(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    record_type: Optional[str] = None
    official_portal: Optional[str] = None
    application_url: Optional[str] = None
    source: Optional[str] = None


class SchemeDetail(BaseModel):
    id: str
    document: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    distance: Optional[float] = None


class SchemeListResponse(BaseModel):
    success: bool
    count: int
    category_filter: Optional[str] = None
    schemes: list[SchemeSummary]
    note: Optional[str] = None
    error: Optional[str] = None


class SchemeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = Field(
        default=None,
        description="Optional category: education, agriculture, business, housing",
    )
    n_results: int = Field(default=3, ge=1, le=5)


class SchemeSearchResponse(BaseModel):
    success: bool
    query: str
    category_filter: Optional[str] = None
    count: int
    schemes: list[SchemeDetail]
    note: Optional[str] = None
    error: Optional[str] = None


class SchemeInfoResponse(BaseModel):
    success: bool
    match_type: Optional[str] = None
    scheme: Optional[SchemeDetail] = None
    note: Optional[str] = None
    error: Optional[str] = None


class EligibilityRequest(BaseModel):
    scheme_query: str = Field(..., min_length=1, max_length=200)
    age: Optional[int] = Field(default=None, ge=0, le=120)
    occupation: Optional[str] = Field(default=None, max_length=100)
    gender: Optional[str] = Field(default=None, max_length=50)
    income_level: Optional[str] = Field(default=None, max_length=50)
    state: Optional[str] = Field(default=None, max_length=100)
    additional_details: Optional[str] = Field(default=None, max_length=500)


class EligibilityResponse(BaseModel):
    success: bool
    scheme_id: Optional[str] = None
    scheme_name: Optional[str] = None
    eligible: Optional[bool] = None
    status: Optional[str] = None
    summary: Optional[str] = None
    relevance_signals: list[str] = Field(default_factory=list)
    mismatch_signals: list[str] = Field(default_factory=list)
    user_profile: dict[str, Any] = Field(default_factory=dict)
    scheme_document: Optional[str] = None
    is_official: Optional[bool] = None
    official_portal: Optional[str] = None
    application_url: Optional[str] = None
    disclaimer: Optional[str] = None
    error: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    success: bool
    id: str
    name: str
    category: Optional[str] = None
    characters: int
    message: str


class DocumentTextRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=50000)
    category: Optional[str] = Field(default=None, max_length=50)
    doc_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional custom document id. Auto-generated if omitted.",
    )
