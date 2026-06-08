from __future__ import annotations

import re
from typing import Any, Dict, List

from app.services.inference_service import SAFETY_NOTICE
from app.services.tts_service import generate_tts


def build_subtitles(text: str) -> List[Dict[str, Any]]:
    parts = [part.strip() for part in re.split(r"[。！？!?]", text) if part.strip()]
    subtitles: List[Dict[str, Any]] = []
    cursor = 0.0
    for part in parts:
        duration = max(2.0, min(6.0, len(part) / 8.0))
        subtitles.append({"start": round(cursor, 2), "end": round(cursor + duration, 2), "text": part + "。"})
        cursor += duration
    return subtitles


def ensure_safety_notice(text: str) -> str:
    normalized = (text or "").strip()
    if SAFETY_NOTICE in normalized:
        return normalized
    if normalized.endswith("。"):
        return normalized + SAFETY_NOTICE
    return normalized + "。" + SAFETY_NOTICE


async def build_speak_response(
    scene: str,
    text: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
) -> Dict[str, Any]:
    safe_text = ensure_safety_notice(text)
    tts_result = await generate_tts(text=safe_text, voice=voice)
    audio_url = tts_result.get("audio_url")

    return {
        "scene": scene,
        "text": safe_text,
        "audio_url": audio_url,
        "avatar": {
            "closed": "/static/avatars/doctor_closed.svg",
            "open": "/static/avatars/doctor_open.svg",
            "status": "speaking" if audio_url else "text_only",
        },
        "subtitles": build_subtitles(safe_text),
        "safety_notice": SAFETY_NOTICE,
        "tts_status": tts_result.get("tts_status", "failed"),
        "message": tts_result.get("message"),
    }


async def build_digital_human_response(query: str, voice: str = "zh-CN-XiaoxiaoNeural") -> Dict[str, Any]:
    deprecated_text = (
        "数字人播报接口已调整为只播报已经生成的文本结果。"
        "请先在中医知识问答或体质辨识问卷页面生成结果后，再调用播报功能。"
    )
    result = await build_speak_response(scene="general_notice", text=deprecated_text, voice=voice)
    result["constitution"] = None
    return result
