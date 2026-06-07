from fastapi import APIRouter

from app.schemas.digital_human import DigitalHumanRequest, DigitalHumanResponse
from app.services.digital_human_service import build_digital_human_response


router = APIRouter()


@router.post("/talk", response_model=DigitalHumanResponse)
async def talk(request: DigitalHumanRequest) -> DigitalHumanResponse:
    result = await build_digital_human_response(query=request.query, voice=request.voice)
    return DigitalHumanResponse(**result)

