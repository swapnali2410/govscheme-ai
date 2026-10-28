"""Scheme discovery, detail, search, and eligibility endpoints."""

from fastapi import APIRouter, HTTPException, Query

from agent_tools import (
    check_eligibility,
    get_scheme_info,
    list_available_schemes,
    search_schemes,
)
from schemas import (
    EligibilityRequest,
    EligibilityResponse,
    SchemeDetail,
    SchemeInfoResponse,
    SchemeListResponse,
    SchemeSearchRequest,
    SchemeSearchResponse,
    SchemeSummary,
)

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])


@router.get(
    "",
    response_model=SchemeListResponse,
    summary="List schemes in the knowledge base",
)
def list_schemes_endpoint(
    category: str | None = Query(
        default=None,
        description="Optional category filter: education, agriculture, business, housing",
    ),
):
    result = list_available_schemes(category=category)
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to list schemes."),
        )

    schemes = [
        SchemeSummary(
            id=item["id"],
            name=item.get("name") or item["id"],
            category=item.get("category"),
            record_type=item.get("record_type"),
            official_portal=item.get("official_portal"),
            application_url=item.get("application_url"),
            source=item.get("source"),
        )
        for item in result.get("schemes", [])
    ]

    return SchemeListResponse(
        success=True,
        count=len(schemes),
        category_filter=category,
        schemes=schemes,
        note=result.get("note"),
    )


@router.post(
    "/search",
    response_model=SchemeSearchResponse,
    summary="Semantic search for schemes (RAG)",
)
def search_schemes_endpoint(request: SchemeSearchRequest):
    result = search_schemes(
        query=request.query,
        category=request.category,
        n_results=request.n_results,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Scheme search failed."),
        )

    schemes = [
        SchemeDetail(
            id=item["id"],
            document=item.get("document", ""),
            metadata=item.get("metadata") or {},
            distance=item.get("distance"),
        )
        for item in result.get("schemes", [])
    ]

    return SchemeSearchResponse(
        success=True,
        query=result.get("query", request.query),
        category_filter=result.get("category_filter"),
        count=len(schemes),
        schemes=schemes,
        note=result.get("note"),
    )


@router.get(
    "/{scheme_id}",
    response_model=SchemeInfoResponse,
    summary="Get scheme details by id or name",
)
def get_scheme_endpoint(scheme_id: str):
    result = get_scheme_info(scheme_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Scheme not found."),
        )

    scheme = result["scheme"]
    return SchemeInfoResponse(
        success=True,
        match_type=result.get("match_type"),
        scheme=SchemeDetail(
            id=scheme["id"],
            document=scheme.get("document", ""),
            metadata=scheme.get("metadata") or {},
            distance=scheme.get("distance"),
        ),
        note=result.get("note"),
    )


@router.post(
    "/eligibility",
    response_model=EligibilityResponse,
    summary="Check scheme relevance/eligibility from stored data",
)
def check_eligibility_endpoint(request: EligibilityRequest):
    result = check_eligibility(
        scheme_query=request.scheme_query,
        age=request.age,
        occupation=request.occupation,
        gender=request.gender,
        income_level=request.income_level,
        state=request.state,
        additional_details=request.additional_details,
    )

    if not result.get("success"):
        status_code = 404 if result.get("status") == "unavailable" else 400
        raise HTTPException(
            status_code=status_code,
            detail=result.get("error", "Eligibility check failed."),
        )

    return EligibilityResponse(**result)
