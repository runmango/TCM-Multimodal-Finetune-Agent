from __future__ import annotations

from fastapi import APIRouter

from app.schemas.api import RAGSearchItem, RAGSearchRequest, RAGSearchResponse
from app.services.knowledge_qa_service import rebuild_vector_index, vector_rag_search


router = APIRouter()


@router.post("/rebuild")
def rebuild() -> dict:
    return rebuild_vector_index()


@router.post("/search", response_model=RAGSearchResponse)
def search(request: RAGSearchRequest) -> RAGSearchResponse:
    result = vector_rag_search(query=request.query, top_k=request.top_k)
    items = [_to_rag_item(item) for item in result["results"]]
    return RAGSearchResponse(
        query=request.query,
        results=items,
        retriever_type=result["retriever_type"],
        fallback_used=result["fallback_used"],
    )


def _to_rag_item(item: dict) -> RAGSearchItem:
    return RAGSearchItem(
        id=str(item.get("id") or item.get("source_id") or item.get("chunk_id") or "unknown"),
        title=str(item.get("title") or "未命名来源"),
        content=str(item.get("content") or item.get("answer") or ""),
        tags=item.get("tags") if isinstance(item.get("tags"), list) else [],
        score=float(item.get("score") or 0.0),
        source_type=str(item.get("source_type") or "unknown"),
    )
