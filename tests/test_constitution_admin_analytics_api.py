from fastapi.testclient import TestClient

from app.api.main import app
from app.repositories.constitution_record_repository import get_constitution_record


client = TestClient(app)


def _create_record() -> dict:
    response = client.post(
        "/api/v1/constitution/full-infer",
        json={
            "answers": [
                {"question_id": "fatigue", "score": 5},
                {"question_id": "shortness_of_breath", "score": 5},
                {"question_id": "spontaneous_sweating", "score": 4},
                {"question_id": "easy_cold", "score": 4},
            ],
            "tongue_image_url": "/static/uploads/tongue/admin-demo.png",
            "tongue_features": {"tongue_color": "淡", "tongue_coating": "薄白", "teeth_marks": True},
        },
    )
    assert response.status_code == 200
    return response.json()


def test_records_list_detail_summary_and_distribution() -> None:
    created = _create_record()

    list_response = client.get("/api/v1/constitution/records?limit=10&offset=0&primary_constitution=气虚质")
    list_data = list_response.json()
    assert list_response.status_code == 200
    assert list_data["total"] >= 1
    assert list_data["items"]
    assert list_data["records"] == list_data["items"]
    assert list_data["items"][0]["session_id"]
    assert "tongue_image_url" in list_data["items"][0]

    detail_response = client.get(f"/api/v1/constitution/records/{created['session_id']}")
    detail = detail_response.json()
    assert detail_response.status_code == 200
    assert detail["session_id"] == created["session_id"]
    assert detail["four_diagnosis"]["inspection"]["tongue_color"] == "淡"
    assert detail["scores"]["气虚质"] >= 40
    assert detail["constitution_judgements"]["气虚质"] == "是"
    assert "retriever_type" in detail
    assert "fallback_used" in detail
    assert detail["broadcast_text"]

    stored = get_constitution_record(created["session_id"])
    assert stored is not None
    assert stored["session_id"] == created["session_id"]

    summary_response = client.get("/api/v1/constitution/analytics/summary")
    summary = summary_response.json()
    assert summary_response.status_code == 200
    assert summary["total_records"] >= 1
    assert summary["tongue_upload_count"] >= 1
    assert summary["digital_human_text_count"] >= 1

    distribution_response = client.get("/api/v1/constitution/analytics/distribution")
    distribution = distribution_response.json()
    assert distribution_response.status_code == 200
    items = distribution["constitution_distribution"]
    assert len(items) >= 9
    assert any(item["name"] == "气虚质" and item["count"] >= 1 for item in items)

    serialized = str(detail)
    assert "姓名" not in serialized
    assert "手机号" not in serialized
    assert "身份证" not in serialized


def test_record_detail_not_found_returns_404() -> None:
    response = client.get("/api/v1/constitution/records/not_exists_session")

    assert response.status_code == 404


def test_records_and_analytics_return_empty_state_on_empty_database(monkeypatch, tmp_path) -> None:
    import app.db.session as session_module

    monkeypatch.setattr(session_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(session_module, "APP_DB_PATH", tmp_path / "empty.db")

    records_response = client.get("/api/v1/constitution/records?limit=10&offset=0")
    records = records_response.json()
    assert records_response.status_code == 200
    assert records["total"] == 0
    assert records["items"] == []

    summary_response = client.get("/api/v1/constitution/analytics/summary")
    summary = summary_response.json()
    assert summary_response.status_code == 200
    assert summary["total_records"] == 0
    assert summary["today_records"] == 0

    distribution_response = client.get("/api/v1/constitution/analytics/distribution")
    distribution = distribution_response.json()
    assert distribution_response.status_code == 200
    assert len(distribution["constitution_distribution"]) >= 9
    assert all(item["count"] == 0 for item in distribution["constitution_distribution"])
