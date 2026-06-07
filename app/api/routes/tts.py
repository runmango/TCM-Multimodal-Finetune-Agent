from fastapi import APIRouter

from app.schemas.digital_human import TTSRequest, TTSResponse
from app.services.tts_service import generate_tts


router = APIRouter()


@router.post("/generate", response_model=TTSResponse)
async def generate(request: TTSRequest) -> TTSResponse:
    result = await generate_tts(text=request.text, voice=request.voice)
    return TTSResponse(**result)

