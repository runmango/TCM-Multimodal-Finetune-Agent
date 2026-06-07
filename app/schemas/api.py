from typing import Any, Dict, List

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class DatasetBuildResponse(BaseModel):
    status: str
    summary: Dict[str, Any]
    exports: Dict[str, str]
    report_path: str


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)


class RAGSearchItem(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    score: float
    source_type: str


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchItem]


class ConstitutionInferRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)


class SafetyResult(BaseModel):
    status: str
    reason: str
    blocked_terms: List[str] = Field(default_factory=list)


class ConstitutionInferResponse(BaseModel):
    constitution: str
    confidence: float
    symptoms: List[str] = Field(default_factory=list)
    evidence: List[RAGSearchItem] = Field(default_factory=list)
    safety: SafetyResult
    disclaimer: str
    answer: str

