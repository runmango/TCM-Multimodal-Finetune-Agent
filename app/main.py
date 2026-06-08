from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import constitution, constitution_questionnaire, digital_human, knowledge, tts, uploads
from app.core.paths import REPORTS_DIR
from app.core.paths import STATIC_DIR
from app.core.responses import UTF8JSONResponse
from app.db.init_db import init_db
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
from app.services.knowledge_qa_service import rebuild_vector_index, vector_rag_search


app = FastAPI(
    title="TCM Multimodal Finetune Agent",
    version="0.1.0",
    description="LangGraph powered demo for TCM dataset governance, RAG inference, and FastAPI deployment.",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
init_db()


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="TCM-Multimodal-Finetune-Agent", version="0.1.0")


app.include_router(constitution.router, prefix="/api/v1/constitution", tags=["constitution"])
app.include_router(
    constitution_questionnaire.router,
    prefix="/api/v1/constitution",
    tags=["constitution-questionnaire"],
)
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(tts.router, prefix="/api/v1/tts", tags=["tts"])
app.include_router(digital_human.router, prefix="/api/v1/digital-human", tags=["digital-human"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])


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
    result = vector_rag_search(query=request.query, top_k=request.top_k)
    items = [
        {
            "id": str(item.get("id") or item.get("source_id") or item.get("chunk_id") or "unknown"),
            "title": str(item.get("title") or "未命名来源"),
            "content": str(item.get("content") or item.get("answer") or ""),
            "tags": item.get("tags") if isinstance(item.get("tags"), list) else [],
            "score": float(item.get("score") or 0.0),
            "source_type": str(item.get("source_type") or "unknown"),
        }
        for item in result["results"]
    ]
    return RAGSearchResponse(
        query=request.query,
        results=items,
        retriever_type=result["retriever_type"],
        fallback_used=result["fallback_used"],
    )


@app.post("/api/v1/rag/rebuild")
def rag_rebuild() -> dict:
    return rebuild_vector_index()


@app.post("/api/v1/infer/constitution", response_model=ConstitutionInferResponse)
def infer_constitution(request: ConstitutionInferRequest) -> ConstitutionInferResponse:
    result = run_inference(query=request.query, top_k=request.top_k)
    return ConstitutionInferResponse(**result)
