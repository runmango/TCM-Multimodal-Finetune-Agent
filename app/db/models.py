CREATE_CONSTITUTION_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS constitution_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    primary_constitution TEXT NOT NULL,
    secondary_constitutions_json TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    constitution_judgements_json TEXT NOT NULL,
    rag_explanation TEXT NOT NULL,
    rag_sources_json TEXT NOT NULL,
    broadcast_text TEXT NOT NULL,
    safety_disclaimer TEXT NOT NULL
);
"""

CREATE_FOUR_DIAGNOSIS_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS four_diagnosis_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    inspection_json TEXT NOT NULL,
    auscultation_olfaction_json TEXT NOT NULL,
    inquiry_json TEXT NOT NULL,
    palpation_json TEXT NOT NULL,
    tongue_image_url TEXT,
    tongue_features_json TEXT NOT NULL
);
"""

CREATE_RAG_TRACE_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS rag_trace_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    query TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    sources_json TEXT NOT NULL,
    retriever_type TEXT NOT NULL,
    fallback_used INTEGER NOT NULL
);
"""

CREATE_TABLES = [
    CREATE_CONSTITUTION_RECORDS_TABLE,
    CREATE_FOUR_DIAGNOSIS_RECORDS_TABLE,
    CREATE_RAG_TRACE_RECORDS_TABLE,
]
