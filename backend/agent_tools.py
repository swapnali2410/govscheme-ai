"""
Gemini function-calling tools for GovScheme AI.

These tools search and read scheme data from the existing
ChromaDB RAG collection. They do not invent scheme details.
"""

from rag_service import (
    format_retrieval_results,
    get_scheme_by_id,
    list_schemes,
    retrieve_documents,
)


def search_schemes(
    query: str,
    category: str | None = None,
    n_results: int = 3,
) -> dict:
    """Search government schemes in the knowledge base using semantic RAG.

    Use this when the user asks to find schemes by topic, need, or keywords
    (for example education, farmers, housing, women entrepreneurship).

    Args:
        query: Natural language search query describing the user's need.
        category: Optional category filter. Allowed values:
            education, agriculture, business, housing, health, energy, general.
        n_results: Number of schemes to return (1-5).

    Returns:
        A dictionary with matched schemes from the vector database.
    """
    if not query or not query.strip():
        return {
            "success": False,
            "error": "Search query is required.",
            "schemes": [],
        }

    try:
        results = retrieve_documents(
            question=query.strip(),
            n_results=max(1, min(n_results, 5)),
            category=category,
        )
        schemes = format_retrieval_results(results)

        return {
            "success": True,
            "query": query.strip(),
            "category_filter": category,
            "count": len(schemes),
            "schemes": schemes,
            "note": (
                "Results come from the shared knowledge base, which includes "
                "official schemes and user uploads (record_type may be "
                "official or upload). Prefer official portals when present, "
                "but do use uploaded documents when they match the query. "
                "Do not invent details beyond these records."
            ),
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "schemes": [],
        }


def get_scheme_info(scheme_query: str) -> dict:
    """Retrieve detailed information for a specific scheme.

    Looks up a scheme by exact id first, then falls back to semantic search
    by name or description. Use this for questions about benefits,
    description, or documents for one scheme.

    Args:
        scheme_query: Scheme id (for example demo_student) or scheme name.

    Returns:
        Scheme document and metadata from ChromaDB, or an unavailable notice.
    """
    if not scheme_query or not scheme_query.strip():
        return {
            "success": False,
            "error": "scheme_query is required.",
        }

    query = scheme_query.strip()

    try:
        # Exact id lookup first
        by_id = get_scheme_by_id(query)
        if by_id:
            return {
                "success": True,
                "match_type": "id",
                "scheme": by_id,
                "note": (
                    "Information is limited to the stored document. "
                    "Do not invent missing fields. "
                    "Verify on the official portal before advising the user to apply."
                ),
            }

        # Semantic fallback by name / description
        results = retrieve_documents(question=query, n_results=1)
        schemes = format_retrieval_results(results)

        if not schemes:
            return {
                "success": False,
                "error": (
                    f"No scheme found for '{query}'. "
                    "Information is unavailable in the knowledge base. "
                    "Do not invent a scheme. Suggest myScheme.gov.in or the "
                    "relevant ministry portal for further discovery."
                ),
            }

        return {
            "success": True,
            "match_type": "semantic",
            "scheme": schemes[0],
            "note": (
                "Best semantic match from stored documents. "
                "Do not invent missing fields. "
                "If the match looks weak, say so and ask the user to verify."
            ),
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }


def check_eligibility(
    scheme_query: str,
    age: int | None = None,
    occupation: str | None = None,
    gender: str | None = None,
    income_level: str | None = None,
    state: str | None = None,
    additional_details: str | None = None,
) -> dict:
    """Check whether a user may be relevant for a scheme using stored data.

    Retrieves the scheme from ChromaDB and compares the provided profile
    against available scheme text/metadata. Does not invent eligibility rules.
    If exact criteria are missing, reports that verification is needed.

    Args:
        scheme_query: Scheme id or name to evaluate.
        age: User age in years, if known.
        occupation: User occupation, for example student, farmer, entrepreneur.
        gender: User gender, if relevant to the scheme.
        income_level: Income description, for example low, middle, high.
        state: Indian state or UT, if provided.
        additional_details: Any other user details that may matter.

    Returns:
        An eligibility assessment grounded only in stored scheme information.
    """
    if not scheme_query or not scheme_query.strip():
        return {
            "success": False,
            "error": "scheme_query is required.",
        }

    scheme_result = get_scheme_info(scheme_query)
    if not scheme_result.get("success"):
        return {
            "success": False,
            "error": scheme_result.get(
                "error",
                "Scheme not found in the knowledge base.",
            ),
            "eligible": None,
            "status": "unavailable",
        }

    scheme = scheme_result["scheme"]
    document_raw = scheme.get("document") or ""
    document = document_raw.lower()
    metadata = scheme.get("metadata") or {}
    category = (metadata.get("category") or "").lower()
    name = metadata.get("name") or scheme.get("id")
    is_official = bool(
        metadata.get("is_official")
        or metadata.get("record_type") == "official"
    )
    official_portal = metadata.get("official_portal") or ""
    application_url = metadata.get("application_url") or ""

    profile = {
        "age": age,
        "occupation": occupation,
        "gender": gender,
        "income_level": income_level,
        "state": state,
        "additional_details": additional_details,
    }
    provided_profile = {
        key: value for key, value in profile.items() if value is not None
    }

    relevance_signals = []
    mismatch_signals = []

    occupation_map = {
        "student": ["education", "student", "college", "scholarship", "nsp"],
        "farmer": ["agriculture", "farmer", "farming", "agricultural", "kisan"],
        "entrepreneur": ["business", "entrepreneur", "mudra", "micro"],
        "business": ["business", "entrepreneur", "mudra", "trading"],
        "homemaker": ["women", "ujjwala", "lpg", "housing"],
        "worker": ["health", "pm-jay", "ayushman", "housing"],
        "unemployed": ["business", "mudra", "scholarship", "education"],
    }

    if occupation:
        occ = occupation.lower().strip()
        keywords = occupation_map.get(occ, [occ])
        if any(word in document or word == category for word in keywords):
            relevance_signals.append(
                f"Occupation '{occupation}' appears relevant to this scheme."
            )
        else:
            mismatch_signals.append(
                f"Occupation '{occupation}' does not clearly match "
                f"scheme category '{category or 'unspecified'}'."
            )

    if income_level and "low" in income_level.lower():
        if any(
            phrase in document
            for phrase in (
                "ews",
                "low-income",
                "low income",
                "poor household",
                "vulnerable",
                "bottom 40%",
            )
        ):
            relevance_signals.append(
                "User income level aligns with low-income / EWS / poor-household wording."
            )

    if gender and "women" in gender.lower():
        if any(word in document for word in ("woman", "women", "ujjwala")):
            relevance_signals.append(
                "Scheme text mentions women beneficiaries."
            )

    if age is not None and age < 18 and "18 years" in document:
        mismatch_signals.append(
            "Stored scheme text mentions an 18+ age condition."
        )

    has_eligibility_section = (
        "eligibility:" in document
        and "eligibility is not specified" not in document
        and "exact eligibility" not in document
    )

    if not provided_profile:
        status = "insufficient_profile"
        eligible = None
        summary = (
            "User profile details are missing. Ask follow-up questions "
            "before assessing eligibility."
        )
    elif mismatch_signals and not relevance_signals:
        status = "likely_not_relevant"
        eligible = False
        summary = (
            "Based on available scheme text, this scheme does not appear "
            "relevant to the provided profile. Present stored criteria only "
            "and do not guarantee ineligibility either without official confirmation."
        )
    elif has_eligibility_section:
        status = "needs_manual_review"
        eligible = None
        summary = (
            "Stored official eligibility criteria are available in the knowledge "
            "base. Compare the user profile with those criteria, list matches "
            "and gaps, and ask the user to confirm on the official portal. "
            "Do not guarantee eligibility."
        )
        if relevance_signals:
            relevance_signals.append(
                "Profile appears directionally related; final decision requires official verification."
            )
    elif relevance_signals:
        status = "possibly_relevant"
        eligible = None
        summary = (
            "The profile appears related to this scheme, but eligibility "
            "details in storage are limited. Do not guarantee eligibility."
        )
    else:
        status = "incomplete_data"
        eligible = None
        summary = (
            "Eligibility conditions are incomplete in the knowledge base. "
            "Recommend checking official government sources."
        )

    disclaimer = (
        "This is not an official eligibility decision. "
        "Verify on official Indian government websites before applying."
    )
    if official_portal:
        disclaimer += f" Official portal: {official_portal}"

    return {
        "success": True,
        "scheme_id": scheme.get("id"),
        "scheme_name": name,
        "eligible": eligible,
        "status": status,
        "summary": summary,
        "relevance_signals": relevance_signals,
        "mismatch_signals": mismatch_signals,
        "user_profile": provided_profile,
        "scheme_document": document_raw,
        "is_official": is_official,
        "official_portal": official_portal or None,
        "application_url": application_url or None,
        "disclaimer": disclaimer,
    }


def list_available_schemes(category: str | None = None) -> dict:
    """List schemes currently stored in the knowledge base.

    Use this when the user asks what schemes are available, or wants a
    catalog filtered by category.

    Args:
        category: Optional category filter. Allowed values:
            education, agriculture, business, housing, health, energy, general.

    Returns:
        A list of scheme ids, names, and categories from ChromaDB.
    """
    try:
        schemes = list_schemes(category=category)
        catalog = []
        for scheme in schemes:
            metadata = scheme.get("metadata") or {}
            catalog.append(
                {
                    "id": scheme["id"],
                    "name": metadata.get("name", scheme["id"]),
                    "category": metadata.get("category"),
                    "record_type": metadata.get("record_type"),
                    "official_portal": metadata.get("official_portal"),
                    "application_url": metadata.get("application_url"),
                    "source": metadata.get("source"),
                }
            )

        return {
            "success": True,
            "category_filter": category,
            "count": len(catalog),
            "schemes": catalog,
            "note": (
                "Prefer schemes with record_type=official. "
                "Share official_portal links. Do not invent schemes."
            ),
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "schemes": [],
        }


# Tools exposed to the Gemini agent
AGENT_TOOLS = [
    search_schemes,
    get_scheme_info,
    check_eligibility,
    list_available_schemes,
]
