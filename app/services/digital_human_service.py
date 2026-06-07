from __future__ import annotations

import re
from typing import Any, Dict, List

from app.services.inference_service import SAFETY_NOTICE, infer_constitution
from app.services.tts_service import generate_tts


def build_broadcast_text(inference: Dict[str, str]) -> str:
    return (
        "体质倾向：%s。依据：%s调养建议：%s安全提示：%s"
        % (inference["constitution"], inference["reason"], inference["advice"], inference["safety_notice"])
    )


def build_subtitles(text: str) -> List[Dict[str, Any]]:
    parts = [part.strip() for part in re.split(r"[。！？!?]", text) if part.strip()]
    subtitles: List[Dict[str, Any]] = []
    cursor = 0.0
    for part in parts:
        duration = max(2.0, min(6.0, len(part) / 8.0))
        subtitles.append({"start": round(cursor, 2), "end": round(cursor + duration, 2), "text": part + "。"})
        cursor += duration
    return subtitles


async def build_digital_human_response(query: str, voice: str = "zh-CN-XiaoxiaoNeural") -> Dict[str, Any]:
    inference = infer_constitution(query=query, backend="rule")
    text = build_broadcast_text(inference)
    tts_result = await generate_tts(text=text, voice=voice)
    audio_url = tts_result.get("audio_url")

    return {
        "text": tts_result.get("text") or text,
        "constitution": inference["constitution"],
        "audio_url": audio_url,
        "avatar": {
            "closed": "/static/avatars/doctor_closed.svg",
            "open": "/static/avatars/doctor_open.svg",
            "status": "speaking" if audio_url else "text_only",
        },
        "subtitles": build_subtitles(text),
        "safety_notice": SAFETY_NOTICE,
        "tts_status": tts_result.get("tts_status", "failed"),
        "message": tts_result.get("message"),
    }

