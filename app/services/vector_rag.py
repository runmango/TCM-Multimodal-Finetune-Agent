from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from app.core.paths import PROCESSED_DIR, RAW_DIR, VECTOR_STORE_DIR
from app.services.embedding_service import cosine_similarity, embed_text


INDEX_FILE = VECTOR_STORE_DIR / "chunks.jsonl"
CHUNK_SIZE = 320
CHUNK_OVERLAP = 60


def build_vector_index() -> Dict[str, Any]:
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    documents = load_knowledge_documents()
    chunks: List[Dict[str, Any]] = []

    for document in documents:
        for chunk_index, chunk_text in enumerate(chunk_text_by_length(document["text"])):
            chunk_id = "%s_%04d" % (document["source_id"], chunk_index + 1)
            metadata = {
                "source": document["source"],
                "section": document["title"],
                "chunk_id": chunk_id,
                "text": chunk_text,
                "source_type": document["source_type"],
                "source_id": document["source_id"],
                "title": document["title"],
                "tags": document.get("tags", []),
            }
            chunks.append({"metadata": metadata, "embedding": embed_text(chunk_text)})

    with INDEX_FILE.open("w", encoding="utf-8") as file_obj:
        for chunk in chunks:
            file_obj.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    return {
        "status": "success",
        "retriever_type": "vector",
        "index_path": str(INDEX_FILE),
        "documents": len(documents),
        "chunks": len(chunks),
    }


def search_vector_knowledge(query: str, top_k: int = 3, auto_build: bool = True) -> Dict[str, Any]:
    normalized = (query or "").strip()
    if not normalized:
        return {"matches": [], "retriever_type": "vector", "fallback_used": True, "reason": "empty_query"}

    if not INDEX_FILE.exists() and auto_build:
        build_vector_index()
    if not INDEX_FILE.exists():
        return {"matches": [], "retriever_type": "vector", "fallback_used": True, "reason": "index_missing"}

    query_embedding = embed_text(normalized)
    matches: List[Dict[str, Any]] = []
    with INDEX_FILE.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError:
                continue
            metadata = item.get("metadata") or {}
            score = cosine_similarity(query_embedding, item.get("embedding") or [])
            if score <= 0:
                continue
            matches.append(_match_from_metadata(metadata=metadata, score=score))

    matches.sort(key=lambda item: (-item["score"], item["source_id"]))
    return {
        "matches": matches[: max(1, min(int(top_k), 10))],
        "retriever_type": "vector",
        "fallback_used": False,
        "reason": None,
    }


def load_knowledge_documents() -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    documents.extend(_load_sft_documents(PROCESSED_DIR / "sft_train.jsonl"))
    for raw_path in sorted(RAW_DIR.glob("*.jsonl")):
        documents.extend(_load_raw_documents(raw_path))
    return documents


def chunk_text_by_length(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: List[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunks.append(normalized[start:end])
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def _load_sft_documents(path: Path) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    if not path.exists():
        return documents

    with path.open("r", encoding="utf-8") as file_obj:
        for index, line in enumerate(file_obj, start=1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            question = str(item.get("input") or item.get("instruction") or "").strip()
            answer = str(item.get("output") or "").strip()
            if not question or not answer:
                continue
            source_id = "tcm_sft_%06d" % index
            documents.append(
                {
                    "source": path.name,
                    "source_type": "sft",
                    "source_id": source_id,
                    "title": question[:60],
                    "text": "%s\n%s" % (question, answer),
                    "tags": [],
                }
            )
    return documents


def _load_raw_documents(path: Path) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file_obj:
        for index, line in enumerate(file_obj, start=1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = str(item.get("content") or item.get("output") or item.get("image_description") or item.get("advice") or "").strip()
            title = str(item.get("title") or item.get("constitution") or path.stem).strip()
            tags = item.get("tags") or item.get("symptoms") or item.get("labels") or []
            if not content:
                continue
            documents.append(
                {
                    "source": path.name,
                    "source_type": str(item.get("type") or path.stem),
                    "source_id": str(item.get("id") or "%s_%06d" % (path.stem, index)),
                    "title": title,
                    "text": "%s\n%s" % (title, content),
                    "tags": tags if isinstance(tags, list) else [str(tags)],
                }
            )
    return documents


def _match_from_metadata(metadata: Dict[str, Any], score: float) -> Dict[str, Any]:
    return {
        "source_type": metadata.get("source_type") or "vector_chunk",
        "source_id": metadata.get("source_id") or metadata.get("chunk_id") or "unknown",
        "title": metadata.get("title") or metadata.get("section") or "未命名来源",
        "answer": metadata.get("text") or "",
        "content": metadata.get("text") or "",
        "tags": metadata.get("tags") or [],
        "score": round(float(score), 4),
        "chunk_id": metadata.get("chunk_id"),
        "source": metadata.get("source"),
        "section": metadata.get("section"),
    }
