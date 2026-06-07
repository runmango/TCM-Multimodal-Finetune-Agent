from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_frontend_digital_human_route_and_menu_exist() -> None:
    router = read_text("frontend/src/router.ts")
    app = read_text("frontend/src/App.vue")

    assert "/digital-human" in router
    assert "DigitalHumanView" in router
    assert "数字人演示" in app


def test_frontend_digital_human_page_components_exist() -> None:
    view = read_text("frontend/src/views/DigitalHumanView.vue")

    assert "中医体质辨识数字人演示" in view
    assert "开始辨识并播报" in view
    assert "DoctorAvatar" in view
    assert "SubtitlePanel" in view
    assert "SafetyNotice" in view
    assert "talkToDigitalHuman" in view


def test_frontend_digital_human_api_contract_exists() -> None:
    api = read_text("frontend/src/api/digitalHuman.ts")

    assert "DigitalHumanResponse" in api
    assert "/api/v1/digital-human/talk" in api
    assert "VITE_API_BASE_URL" in read_text("frontend/src/api/tcmApi.ts")
    assert "resolveBackendAssetUrl" in api


def test_frontend_audio_empty_degrades_to_text() -> None:
    view = read_text("frontend/src/views/DigitalHumanView.vue")

    assert "TTS 暂不可用，已降级为文本和字幕展示。" in view
    assert "broadcastText" in view
