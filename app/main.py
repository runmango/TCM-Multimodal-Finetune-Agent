from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


app = FastAPI(
    title="TCM Multimodal Finetune Agent",
    version="0.1.0",
    description="LangGraph powered demo for TCM dataset governance, RAG inference, and FastAPI deployment.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="TCM-Multimodal-Finetune-Agent", version="0.1.0")


@app.post("/api/v1/dataset/build", response_model=DatasetBuildResponse)
def dataset_build() -> DatasetBuildResponse:
    result = build_dataset()
    return DatasetBuildResponse(
        status=result["status"],
        summary=result["summary"],
        exports=result["exports"],
        report_path=str(REPORTS_DIR / "dataset_report.json"),
    )


@app.post("/api/v1/rag/search", response_model=RAGSearchResponse)
def rag_search(request: RAGSearchRequest) -> RAGSearchResponse:
    retriever = KeywordRetriever()
    results = retriever.search(query=request.query, top_k=request.top_k)
    return RAGSearchResponse(query=request.query, results=results)


@app.post("/api/v1/infer/constitution", response_model=ConstitutionInferResponse)
def infer_constitution(request: ConstitutionInferRequest) -> ConstitutionInferResponse:
    result = run_inference(query=request.query, top_k=request.top_k)
    return ConstitutionInferResponse(**result)
