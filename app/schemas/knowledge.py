from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class KnowledgeAskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)
    backend: Literal["rule", "rag", "lora"] = "rule"


class KnowledgeSource(BaseModel):
    source_type: str
    source_id: str
    title: Optional[str] = None
    score: Optional[float] = None


class KnowledgeAskResponse(BaseModel):
    answer: str
    sources: List[KnowledgeSource]
    safety_notice: str
    retriever_type: str = "keyword"
    fallback_used: bool = False
