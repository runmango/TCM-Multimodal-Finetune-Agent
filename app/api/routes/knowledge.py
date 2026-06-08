from fastapi import APIRouter

from app.schemas.knowledge import KnowledgeAskRequest, KnowledgeAskResponse
from app.services.knowledge_qa_service import ask_knowledge


router = APIRouter()


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask(request: KnowledgeAskRequest) -> KnowledgeAskResponse:
    result = ask_knowledge(query=request.query, top_k=request.top_k, backend=request.backend)
    return KnowledgeAskResponse(**result)
