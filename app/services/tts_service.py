from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.paths import TTS_DIR
from app.services.inference_service import SAFETY_NOTICE


MAX_TTS_CHARS = 500


async def generate_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> Dict[str, Any]:
    """Generate TTS audio with edge-tts, returning a safe fallback on failure."""

    safe_text = ensure_safety_notice((text or "").strip())[:MAX_TTS_CHARS]
    TTS_DIR.mkdir(parents=True, exist_ok=True)
    file_name = "tts_%s_%s.mp3" % (datetime.now().strftime("%Y%m%d_%H%M%S"), uuid4().hex[:8])
    output_path = TTS_DIR / file_name
    audio_url = "/static/tts/%s" % file_name

    try:
        import edge_tts  # type: ignore

        communicate = edge_tts.Communicate(safe_text, voice)
        await communicate.save(str(output_path))
        return {"audio_url": audio_url, "text": safe_text, "tts_status": "success", "message": None}
    except ModuleNotFoundError:
        return {
            "audio_url": None,
            "text": safe_text,
            "tts_status": "failed",
            "message": "TTS 生成失败：当前后端 Python 环境未安装 edge-tts。",
        }
    except Exception:
        return {
            "audio_url": None,
            "text": safe_text,
            "tts_status": "failed",
            "message": "TTS 生成失败，请检查网络或 edge-tts 环境。",
        }


def ensure_safety_notice(text: str) -> str:
    if SAFETY_NOTICE in text:
        return text
    if text.endswith("。"):
        return text + "安全提示：" + SAFETY_NOTICE
    return text + "。安全提示：" + SAFETY_NOTICE
