from fastapi import APIRouter

from app.schemas.digital_human import ConstitutionInferRequest, ConstitutionInferResponse
from app.services.inference_service import infer_constitution


router = APIRouter()


@router.post("/infer", response_model=ConstitutionInferResponse)
def infer(request: ConstitutionInferRequest) -> ConstitutionInferResponse:
    result = infer_constitution(query=request.query, backend=request.backend)
    return ConstitutionInferResponse(**result)

