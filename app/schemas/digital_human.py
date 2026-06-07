from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ConstitutionInferRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    backend: Literal["rule", "rag", "lora"] = "rule"


class ConstitutionInferResponse(BaseModel):
    constitution: str
    reason: str
    advice: str
    safety_notice: str


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    voice: str = "zh-CN-XiaoxiaoNeural"


class TTSResponse(BaseModel):
    audio_url: Optional[str] = None
    text: str
    tts_status: str = "success"
    message: Optional[str] = None


class DigitalHumanRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    voice: str = "zh-CN-XiaoxiaoNeural"


class AvatarState(BaseModel):
    closed: str
    open: str
    status: str


class SubtitleItem(BaseModel):
    start: float
    end: float
    text: str


class DigitalHumanResponse(BaseModel):
    text: str
    constitution: str
    audio_url: Optional[str] = None
    avatar: AvatarState
    subtitles: List[SubtitleItem]
    safety_notice: str
    tts_status: str = "success"
    message: Optional[str] = None
