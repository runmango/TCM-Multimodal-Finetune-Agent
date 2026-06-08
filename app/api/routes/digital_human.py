from fastapi import APIRouter

from app.schemas.digital_human import DigitalHumanRequest, DigitalHumanResponse, DigitalHumanSpeakRequest, DigitalHumanSpeakResponse
from app.services.digital_human_service import build_digital_human_response, build_speak_response


router = APIRouter()


@router.post("/speak", response_model=DigitalHumanSpeakResponse)
async def speak(request: DigitalHumanSpeakRequest) -> DigitalHumanSpeakResponse:
    result = await build_speak_response(scene=request.scene, text=request.text, voice=request.voice)
    return DigitalHumanSpeakResponse(**result)


@router.post("/talk", response_model=DigitalHumanResponse, deprecated=True)
async def talk(request: DigitalHumanRequest) -> DigitalHumanResponse:
    result = await build_digital_human_response(query=request.query, voice=request.voice)
    return DigitalHumanResponse(**result)
