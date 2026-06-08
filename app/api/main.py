from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import constitution, constitution_questionnaire, digital_human, knowledge, legacy, rag, tts, uploads
from app.core.paths import STATIC_DIR
from app.core.responses import UTF8JSONResponse
from app.db.init_db import init_db


app = FastAPI(
    title="TCM Digital Human Demo API",
    version="0.1.0",
    description="Lightweight digital-human style TCM constitution broadcasting demo.",
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

app.include_router(constitution.router, prefix="/api/v1/constitution", tags=["constitution"])
app.include_router(
    constitution_questionnaire.router,
    prefix="/api/v1/constitution",
    tags=["constitution-questionnaire"],
)
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(tts.router, prefix="/api/v1/tts", tags=["tts"])
app.include_router(digital_human.router, prefix="/api/v1/digital-human", tags=["digital-human"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])
app.include_router(legacy.router, prefix="/api/v1", tags=["legacy-demo"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "tcm-digital-human-demo", "version": "0.1.0"}
