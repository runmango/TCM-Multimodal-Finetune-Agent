from fastapi import APIRouter

from app.core.paths import REPORTS_DIR
from app.graphs.inference_graph import run_inference
from app.schemas.api import (
    ConstitutionInferRequest,
    ConstitutionInferResponse,
    DatasetBuildResponse,
    HealthResponse,
    RAGSearchRequest,
    RAGSearchResponse,
)
from app.services.dataset import build_dataset
from app.services.rag import KeywordRetriever


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="TCM-Multimodal-Finetune-Agent", version="0.1.0")


@router.post("/dataset/build", response_model=DatasetBuildResponse)
def dataset_build() -> DatasetBuildResponse:
    result = build_dataset()
    return DatasetBuildResponse(
        status=result["status"],
        summary=result["summary"],
        exports=result["exports"],
        report_path=str(REPORTS_DIR / "dataset_report.json"),
    )


@router.post("/rag/search", response_model=RAGSearchResponse)
def rag_search(request: RAGSearchRequest) -> RAGSearchResponse:
    retriever = KeywordRetriever()
    results = retriever.search(query=request.query, top_k=request.top_k)
    return RAGSearchResponse(query=request.query, results=results)


@router.post("/infer/constitution", response_model=ConstitutionInferResponse)
def infer_constitution(request: ConstitutionInferRequest) -> ConstitutionInferResponse:
    result = run_inference(query=request.query, top_k=request.top_k)
    return ConstitutionInferResponse(**result)
