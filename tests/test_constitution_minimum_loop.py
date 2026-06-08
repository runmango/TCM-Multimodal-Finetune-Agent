from fastapi.testclient import TestClient

from app.api.main import app
from app.core.paths import STATIC_DIR
from app.services.knowledge_qa_service import explain_constitution_result


client = TestClient(app)


def test_full_infer_returns_minimum_loop_for_qi_deficiency() -> None:
    response = client.post(
        "/api/v1/constitution/full-infer",
        json={
            "answers": [
                {"question_id": "fatigue", "score": 5},
                {"question_id": "shortness_of_breath", "score": 5},
                {"question_id": "spontaneous_sweating", "score": 4},
                {"question_id": "easy_cold", "score": 4},
            ],
            "tongue_image_url": "/static/uploads/tongue/demo.jpg",
            "tongue_features": {
                "tongue_color": "淡",
                "tongue_coating": "薄白",
                "teeth_marks": True,
                "tongue_shape": "胖大",
            },
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["session_id"]
    assert data["algorithm_version"] == "GB/T46939-2025"
    assert data["primary_constitution"] == "气虚质"
    assert len(data["scores"]) == 9
    assert data["constitution_judgements"]["气虚质"] == "是"
    assert "secondary_constitutions" in data
    assert data["four_diagnosis"]["inspection"]["tongue_color"] == "淡"
    assert data["four_diagnosis"]["inspection"]["teeth_marks"] is True
    assert set(data["four_diagnosis"]) == {"inspection", "auscultation_olfaction", "inquiry", "palpation"}
    assert data["four_diagnosis"]["inquiry"]["fatigue"] == 5
    assert data["rag_explanation"]
    assert data["retriever_type"] in {"vector", "keyword", "fallback", "vector_unavailable"}
    assert "不能替代医生诊断" in data["rag_explanation"]
    assert data["broadcast_text"]
    assert "气虚质" in data["broadcast_text"]
    assert "不能替代医生诊断" in data["broadcast_text"]


def test_tongue_upload_saves_image_and_returns_static_url() -> None:
    response = client.post(
        "/api/v1/uploads/tongue",
        files={"file": ("tongue.png", b"\x89PNG\r\n\x1a\nminimum-loop-test", "image/png")},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["url"].startswith("/static/uploads/tongue/")
    target_path = STATIC_DIR / data["url"].replace("/static/", "")
    assert target_path.exists()
    target_path.unlink(missing_ok=True)


def test_legacy_question_ids_still_score_qi_deficiency() -> None:
    response = client.post(
        "/api/v1/constitution/questionnaire/submit",
        json={
            "answers": [
                {"question_id": "q004", "score": 5},
                {"question_id": "q005", "score": 5},
                {"question_id": "q006", "score": 5},
            ]
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["primary_constitution"] == "气虚质"


def test_rag_fallback_contains_safety_notice() -> None:
    result = explain_constitution_result("未知体质", [], {}, top_k=3)

    assert result["explanation"]
    assert result["sources"] == []
    assert "不能替代医生诊断" in result["explanation"]
    assert "非诊疗性质" in result["explanation"]
