from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_digital_human_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_digital_human_cors_allows_dedicated_vite_port() -> None:
    response = client.options(
        "/api/v1/digital-human/talk",
        headers={
            "Origin": "http://127.0.0.1:5175",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5175"


def test_constitution_infer_returns_qi_deficiency() -> None:
    response = client.post(
        "/api/v1/constitution/infer",
        json={"query": "乏力、气短、舌淡有齿痕", "backend": "rule"},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["constitution"] == "气虚质"
    assert "乏力" in data["reason"]
    assert "仅供健康科普参考" in data["safety_notice"]


def test_legacy_streamlit_infer_route_is_available() -> None:
    response = client.post(
        "/api/v1/infer/constitution",
        json={"query": "我最近乏力气短，自汗，舌淡有齿痕，想了解体质倾向。", "top_k": 3},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["constitution"] == "气虚质"
    assert data["evidence"]
    assert "disclaimer" in data


def test_digital_human_talk_returns_text_avatar_and_subtitles(monkeypatch) -> None:
    async def fake_generate_tts(text: str, voice: str) -> dict:
        return {
            "audio_url": None,
            "text": text,
            "tts_status": "failed",
            "message": "TTS disabled in test.",
        }

    monkeypatch.setattr("app.services.digital_human_service.generate_tts", fake_generate_tts)

    response = client.post(
        "/api/v1/digital-human/talk",
        json={"query": "乏力、气短、舌淡有齿痕", "voice": "zh-CN-XiaoxiaoNeural"},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["constitution"] == "气虚质"
    assert "体质倾向" in data["text"]
    assert "仅供健康科普参考，不替代医生诊疗。" in data["text"]
    assert data["audio_url"] is None
    assert data["avatar"]["closed"].endswith("doctor_closed.svg")
    assert data["avatar"]["status"] == "text_only"
    assert data["subtitles"]
    assert data["tts_status"] == "failed"
    assert "仅供健康科普参考" in data["safety_notice"]


def test_tts_route_handles_failed_tts(monkeypatch) -> None:
    async def fake_generate_tts(text: str, voice: str) -> dict:
        safe_text = text + " 仅供健康科普参考，不替代医生诊疗。"
        return {
            "audio_url": None,
            "text": safe_text,
            "tts_status": "failed",
            "message": "TTS generation failed in test.",
        }

    monkeypatch.setattr("app.api.routes.tts.generate_tts", fake_generate_tts)

    response = client.post(
        "/api/v1/tts/generate",
        json={"text": "体质倾向：气虚质。", "voice": "zh-CN-XiaoxiaoNeural"},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["audio_url"] is None
    assert data["tts_status"] == "failed"
    assert data["text"].endswith("不替代医生诊疗。")
