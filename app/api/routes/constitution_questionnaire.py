from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas.constitution_questionnaire import QuestionnaireResponse, QuestionnaireSubmitRequest, QuestionnaireSubmitResponse
from app.services.constitution_questionnaire_service import get_questionnaire, run_full_constitution_infer
from app.repositories.constitution_record_repository import (
    count_constitution_records,
    get_analytics_summary,
    get_constitution_distribution,
    get_constitution_record,
    list_constitution_records,
)


router = APIRouter()


@router.get("/questionnaire", response_model=QuestionnaireResponse)
def questionnaire() -> QuestionnaireResponse:
    return QuestionnaireResponse(**get_questionnaire())


@router.post("/questionnaire/submit", response_model=QuestionnaireSubmitResponse)
def submit_questionnaire(request: QuestionnaireSubmitRequest) -> QuestionnaireSubmitResponse:
    result = _run_full_infer(request)
    return QuestionnaireSubmitResponse(**result)


@router.post("/full-infer", response_model=QuestionnaireSubmitResponse)
def full_infer(request: QuestionnaireSubmitRequest) -> QuestionnaireSubmitResponse:
    result = _run_full_infer(request)
    return QuestionnaireSubmitResponse(**result)


@router.get("/analytics/summary")
def analytics_summary() -> dict:
    return get_analytics_summary()


@router.get("/analytics/distribution")
def analytics_distribution() -> dict:
    return get_constitution_distribution()


@router.get("/records")
def records(
    limit: int = 20,
    offset: int = 0,
    primary_constitution: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    items = list_constitution_records(
        limit=limit,
        offset=offset,
        primary_constitution=primary_constitution,
        date_from=date_from,
        date_to=date_to,
    )
    total = count_constitution_records(
        primary_constitution=primary_constitution,
        date_from=date_from,
        date_to=date_to,
    )
    return {"total": total, "limit": limit, "offset": offset, "items": items, "records": items}


@router.get("/records/{session_id}")
def record_detail(session_id: str) -> dict:
    record = get_constitution_record(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="record not found")
    return record


def _run_full_infer(request: QuestionnaireSubmitRequest) -> dict:
    tongue_features = request.tongue_features
    if tongue_features:
        tongue_feature_payload = tongue_features.model_dump() if hasattr(tongue_features, "model_dump") else tongue_features.dict()
    else:
        tongue_feature_payload = None
    return run_full_constitution_infer(
        answers=[answer.model_dump() if hasattr(answer, "model_dump") else answer.dict() for answer in request.answers],
        tongue_image_url=request.tongue_image_url,
        tongue_features=tongue_feature_payload,
        top_k=request.top_k,
        gender=request.gender,
    )
