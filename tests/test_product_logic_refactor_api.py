from fastapi.testclient import TestClient

from app.api.main import app
from app.services.inference_service import SAFETY_NOTICE


client = TestClient(app)


def test_questionnaire_returns_questions_and_options() -> None:
    response = client.get("/api/v1/constitution/questionnaire")

    data = response.json()
    assert response.status_code == 200
    assert data["questions"]
    assert data["options"]
    assert {item["constitution"] for item in data["questions"]} >= {"平和质", "气虚质", "阳虚质"}
    assert data["options"][0]["label"] == "没有"


def test_questionnaire_submit_can_return_qi_deficiency() -> None:
    questionnaire = client.get("/api/v1/constitution/questionnaire").json()
    answers = []
    for question in questionnaire["questions"]:
        score = 5 if question["constitution"] == "气虚质" else 1
        answers.append({"question_id": question["id"], "score": score})

    response = client.post("/api/v1/constitution/questionnaire/submit", json={"answers": answers})

    data = response.json()
    assert response.status_code == 200
    assert data["primary_constitution"] == "气虚质"
    assert data["scores"]["气虚质"] == 100
    assert SAFETY_NOTICE in data["safety_notice"]
    assert SAFETY_NOTICE in data["result_text"]


def test_knowledge_ask_returns_answer_and_sources() -> None:
    response = client.post("/api/v1/knowledge/ask", json={"query": "气虚质有哪些表现？如何调养？", "top_k": 3})

    data = response.json()
    assert response.status_code == 200
    assert data["answer"]
    assert SAFETY_NOTICE in data["answer"]
    assert SAFETY_NOTICE in data["safety_notice"]
    assert isinstance(data["sources"], list)


def test_knowledge_ask_fallback_when_not_matched() -> None:
    response = client.post("/api/v1/knowledge/ask", json={"query": "火星经络飞船如何调养？", "top_k": 3})

    data = response.json()
    assert response.status_code == 200
    assert "未检索到足够依据" in data["answer"]
    assert data["sources"] == []
    assert SAFETY_NOTICE in data["answer"]


def test_knowledge_ask_refuses_prescription_and_diagnosis() -> None:
    response = client.post("/api/v1/knowledge/ask", json={"query": "请帮我确诊并开药，给出处方剂量。", "top_k": 3})

    data = response.json()
    assert response.status_code == 200
    assert "不能替代医生" in data["answer"]
    assert data["sources"] == []
    assert SAFETY_NOTICE in data["answer"]
