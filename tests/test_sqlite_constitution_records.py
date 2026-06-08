from fastapi.testclient import TestClient

from app.api.main import app
from app.repositories.constitution_record_repository import get_constitution_record


client = TestClient(app)


def test_full_infer_persists_sqlite_records_and_can_be_queried() -> None:
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
            "tongue_features": {"tongue_color": "淡", "tongue_coating": "薄白", "teeth_marks": True},
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["session_id"]
    assert data["algorithm_version"] == "GB/T46939-2025"
    assert data["constitution_judgements"]["气虚质"] == "是"
    assert data["retriever_type"] in {"vector", "keyword", "fallback", "vector_unavailable"}

    stored = get_constitution_record(data["session_id"])
    assert stored is not None
    assert stored["session_id"] == data["session_id"]
    assert stored["primary_constitution"] == "气虚质"
    assert stored["four_diagnosis"]["inspection"]["tongue_color"] == "淡"
    assert stored["rag_traces"]

    detail_response = client.get(f"/api/v1/constitution/records/{data['session_id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["session_id"] == data["session_id"]
    serialized = str(detail)
    assert "姓名" not in serialized
    assert "手机号" not in serialized
    assert "身份证" not in serialized


def test_constitution_records_list_endpoint() -> None:
    response = client.get("/api/v1/constitution/records?limit=5&offset=0")

    data = response.json()
    assert response.status_code == 200
    assert "records" in data
    assert isinstance(data["records"], list)
