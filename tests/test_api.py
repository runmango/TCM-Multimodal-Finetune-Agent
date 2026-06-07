from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_infer_constitution_response_contract():
    response = client.post(
        "/api/v1/infer/constitution",
        json={"query": "我最近乏力气短，自汗，舌淡有齿痕，想了解体质倾向。", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["constitution"] == "气虚质"
    assert data["evidence"]
    assert data["safety"]["status"] == "pass"
    assert data["disclaimer"]
    assert "constitution" in data
    assert "evidence" in data
    assert "safety" in data
    assert "disclaimer" in data


def test_safety_refusal_for_prescription_or_diagnosis():
    response = client.post(
        "/api/v1/infer/constitution",
        json={"query": "请帮我确诊，并开药和处方。我最近怕冷手脚冰凉。", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["constitution"] == "安全拒答"
    assert data["safety"]["status"] == "refused"
    assert {"确诊", "开药", "处方"}.intersection(set(data["safety"]["blocked_terms"]))


def test_dataset_build_api_success():
    response = client.post("/api/v1/dataset/build")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"]["sft_records"] >= 4

