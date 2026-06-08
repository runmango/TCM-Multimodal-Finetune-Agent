from fastapi.testclient import TestClient

from app.api.main import app
from app.services.vector_rag import INDEX_FILE, build_vector_index


client = TestClient(app)


def test_vector_index_can_be_built() -> None:
    result = build_vector_index()

    assert result["status"] == "success"
    assert result["chunks"] > 0
    assert INDEX_FILE.exists()


def test_knowledge_ask_prefers_vector_retriever() -> None:
    build_vector_index()
    response = client.post("/api/v1/knowledge/ask", json={"query": "气虚质有哪些表现？如何调养？", "top_k": 3})

    data = response.json()
    assert response.status_code == 200
    assert data["answer"]
    assert data["sources"]
    assert data["retriever_type"] == "vector"
    assert data["fallback_used"] is False


def test_knowledge_ask_falls_back_when_vector_unavailable(monkeypatch) -> None:
    def broken_vector_search(*args, **kwargs):
        raise RuntimeError("vector backend unavailable")

    monkeypatch.setattr("app.services.knowledge_qa_service.search_vector_knowledge", broken_vector_search)
    response = client.post("/api/v1/knowledge/ask", json={"query": "气虚质有哪些表现？如何调养？", "top_k": 3})

    data = response.json()
    assert response.status_code == 200
    assert data["answer"]
    assert data["retriever_type"] == "keyword"
    assert data["fallback_used"] is True


def test_knowledge_ask_safe_fallback_when_not_matched() -> None:
    response = client.post("/api/v1/knowledge/ask", json={"query": "火星经络飞船如何调养？", "top_k": 3})

    data = response.json()
    assert response.status_code == 200
    assert "未检索到足够依据" in data["answer"]
    assert data["sources"] == []
    assert data["retriever_type"] == "fallback"
    assert data["fallback_used"] is True
    assert "不能替代医生诊断" in data["answer"]
