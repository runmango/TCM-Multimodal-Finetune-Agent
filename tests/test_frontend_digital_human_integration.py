from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_frontend_digital_human_route_and_menu_exist() -> None:
    router = read_text("frontend/src/router.ts")
    app = read_text("frontend/src/App.vue")

    assert "/digital-human" in router
    assert "DigitalHumanView" in router
    assert "数字人播报" in app
    assert "中医知识问答" in app
    assert "体质辨识问卷" in app


def test_frontend_digital_human_page_components_exist() -> None:
    view = read_text("frontend/src/views/DigitalHumanView.vue")

    assert "数字人播报" in view
    assert "开始播报" in view
    assert "Web 3D 中医数字人" in read_text("frontend/src/components/digital-human/AvatarStage.vue")
    assert "AvatarStage" in view
    assert "SubtitlePanel" in view
    assert "SafetyNotice" in view
    assert "speakWithDigitalHuman" in view


def test_frontend_digital_human_api_contract_exists() -> None:
    api = read_text("frontend/src/api/digitalHuman.ts")

    assert "DigitalHumanResponse" in api
    assert "/api/v1/digital-human/speak" in api
    assert "VITE_API_BASE_URL" in read_text("frontend/src/api/tcmApi.ts")
    assert "resolveBackendAssetUrl" in api


def test_frontend_audio_empty_degrades_to_text() -> None:
    view = read_text("frontend/src/views/DigitalHumanView.vue")

    assert "TTS 暂不可用，已降级为文本和字幕展示。" in view
    assert "broadcastText" in view
    assert "当前没有可播放音频，已降级为文本和字幕展示。" in view


def test_frontend_product_refactor_pages_exist() -> None:
    router = read_text("frontend/src/router.ts")
    knowledge = read_text("frontend/src/views/KnowledgeAskView.vue")
    questionnaire = read_text("frontend/src/views/ConstitutionQuestionnaireView.vue")

    assert "KnowledgeAskView" in router
    assert "ConstitutionQuestionnaireView" in router
    assert "/api/v1/knowledge/ask" in read_text("frontend/src/api/knowledge.ts")
    assert "/api/v1/constitution/questionnaire" in read_text("frontend/src/api/constitutionQuestionnaire.ts")
    assert "让数字人播报此回答" in knowledge
    assert "让数字人播报问卷结果" in questionnaire
    assert "digital_human_speak_text" in knowledge
    assert "digital_human_speak_text" in questionnaire


def test_frontend_web3d_avatar_fallback_contract_exists() -> None:
    avatar = read_text("frontend/src/components/digital-human/Web3DAvatar.vue")
    fallback = read_text("frontend/src/services/avatar/fallbackDoctorModel.ts")
    mouth_driver = read_text("frontend/src/services/avatar/audioMouthDriver.ts")
    loader = read_text("frontend/src/services/avatar/vrmLoader.ts")

    assert "THREE.WebGLRenderer" in avatar
    assert "createFallbackDoctorModel" in avatar
    assert "requestAnimationFrame" in avatar
    assert "renderer?.dispose" in avatar
    assert "mouth" in fallback
    assert "AudioContext" in mouth_driver
    assert "AnalyserNode" in mouth_driver
    assert "loadVrmModel" in loader
    assert "/models/doctor.vrm" in loader
    assert "/models/doctor.glb" in loader
