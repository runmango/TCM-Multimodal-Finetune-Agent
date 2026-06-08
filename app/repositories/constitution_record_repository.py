from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db.init_db import init_db
from app.db.session import get_connection


def save_constitution_record(
    session_id: str,
    payload: Dict[str, Any],
    four_diagnosis: Dict[str, Any],
    rag_trace: Dict[str, Any],
    tongue_features: Dict[str, Any],
) -> None:
    init_db()
    created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO constitution_records (
                session_id, created_at, algorithm_version, primary_constitution,
                secondary_constitutions_json, scores_json, constitution_judgements_json,
                rag_explanation, rag_sources_json, broadcast_text, safety_disclaimer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                created_at,
                payload["algorithm_version"],
                payload["primary_constitution"],
                _to_json(payload.get("secondary_constitutions", [])),
                _to_json(payload.get("scores", {})),
                _to_json(payload.get("constitution_judgements", {})),
                payload.get("rag_explanation", ""),
                _to_json(payload.get("rag_sources", [])),
                payload.get("broadcast_text", ""),
                payload.get("safety_notice", ""),
            ),
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO four_diagnosis_records (
                session_id, created_at, inspection_json, auscultation_olfaction_json,
                inquiry_json, palpation_json, tongue_image_url, tongue_features_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                created_at,
                _to_json(four_diagnosis.get("inspection", {})),
                _to_json(four_diagnosis.get("auscultation_olfaction", {})),
                _to_json(four_diagnosis.get("inquiry", {})),
                _to_json(four_diagnosis.get("palpation", {})),
                (four_diagnosis.get("inspection") or {}).get("tongue_image_url"),
                _to_json(tongue_features),
            ),
        )
        connection.execute(
            """
            INSERT INTO rag_trace_records (
                session_id, created_at, query, top_k, sources_json, retriever_type, fallback_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                created_at,
                rag_trace.get("query", ""),
                int(rag_trace.get("top_k", 3)),
                _to_json(rag_trace.get("sources", [])),
                rag_trace.get("retriever_type", "unknown"),
                1 if rag_trace.get("fallback_used") else 0,
            ),
        )


def list_constitution_records(
    limit: int = 20,
    offset: int = 0,
    primary_constitution: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    init_db()
    safe_limit = max(1, min(int(limit), 100))
    safe_offset = max(0, int(offset))
    where_sql, params = _build_filter_clause(
        primary_constitution=primary_constitution,
        date_from=date_from,
        date_to=date_to,
    )
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT session_id, created_at, algorithm_version, primary_constitution,
                   secondary_constitutions_json, scores_json, constitution_judgements_json,
                   rag_explanation, rag_sources_json, broadcast_text, safety_disclaimer
            FROM constitution_records
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, safe_limit, safe_offset),
        ).fetchall()
    return [_record_summary_from_detail(get_constitution_record(row["session_id"]) or _constitution_row_to_dict(row)) for row in rows]


def count_constitution_records(
    primary_constitution: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> int:
    init_db()
    where_sql, params = _build_filter_clause(
        primary_constitution=primary_constitution,
        date_from=date_from,
        date_to=date_to,
    )
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT COUNT(*) AS count FROM constitution_records {where_sql}",
            params,
        ).fetchone()
    return int(row["count"] if row else 0)


def get_analytics_summary() -> Dict[str, int]:
    init_db()
    today_prefix = datetime.utcnow().date().isoformat()
    with get_connection() as connection:
        total_records = connection.execute("SELECT COUNT(*) AS count FROM constitution_records").fetchone()["count"]
        today_records = connection.execute(
            "SELECT COUNT(*) AS count FROM constitution_records WHERE created_at >= ?",
            (today_prefix,),
        ).fetchone()["count"]
        tongue_upload_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM four_diagnosis_records
            WHERE tongue_image_url IS NOT NULL AND tongue_image_url != ''
            """
        ).fetchone()["count"]
        rag_fallback_count = connection.execute(
            "SELECT COUNT(*) AS count FROM rag_trace_records WHERE fallback_used = 1"
        ).fetchone()["count"]
        rag_success_count = connection.execute(
            "SELECT COUNT(*) AS count FROM rag_trace_records WHERE fallback_used = 0"
        ).fetchone()["count"]
        digital_human_text_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM constitution_records
            WHERE broadcast_text IS NOT NULL AND broadcast_text != ''
            """
        ).fetchone()["count"]

    return {
        "total_records": int(total_records),
        "today_records": int(today_records),
        "tongue_upload_count": int(tongue_upload_count),
        "rag_success_count": int(rag_success_count),
        "rag_fallback_count": int(rag_fallback_count),
        "digital_human_text_count": int(digital_human_text_count),
    }


def get_constitution_distribution() -> Dict[str, List[Dict[str, Any]]]:
    from app.core.constitution_scale_items import CONSTITUTIONS

    init_db()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT primary_constitution, COUNT(*) AS count
            FROM constitution_records
            GROUP BY primary_constitution
            """
        ).fetchall()
    counts = {row["primary_constitution"]: int(row["count"]) for row in rows}
    distribution = [{"name": constitution, "count": counts.get(constitution, 0)} for constitution in CONSTITUTIONS]
    extra = [
        {"name": name, "count": count}
        for name, count in counts.items()
        if name not in CONSTITUTIONS
    ]
    return {"constitution_distribution": distribution + extra}


def get_constitution_record(session_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_connection() as connection:
        constitution_row = connection.execute(
            """
            SELECT session_id, created_at, algorithm_version, primary_constitution,
                   secondary_constitutions_json, scores_json, constitution_judgements_json,
                   rag_explanation, rag_sources_json, broadcast_text, safety_disclaimer
            FROM constitution_records
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        if constitution_row is None:
            return None
        four_row = connection.execute(
            """
            SELECT inspection_json, auscultation_olfaction_json, inquiry_json, palpation_json,
                   tongue_image_url, tongue_features_json
            FROM four_diagnosis_records
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        rag_rows = connection.execute(
            """
            SELECT query, top_k, sources_json, retriever_type, fallback_used, created_at
            FROM rag_trace_records
            WHERE session_id = ?
            ORDER BY id DESC
            """,
            (session_id,),
        ).fetchall()

    record = _constitution_row_to_dict(constitution_row)
    if four_row:
        record["four_diagnosis"] = {
            "inspection": _from_json(four_row["inspection_json"], {}),
            "auscultation_olfaction": _from_json(four_row["auscultation_olfaction_json"], {}),
            "inquiry": _from_json(four_row["inquiry_json"], {}),
            "palpation": _from_json(four_row["palpation_json"], {}),
        }
        record["tongue_features"] = _from_json(four_row["tongue_features_json"], {})
    record["rag_traces"] = [
        {
            "query": row["query"],
            "top_k": row["top_k"],
            "sources": _from_json(row["sources_json"], []),
            "retriever_type": row["retriever_type"],
            "fallback_used": bool(row["fallback_used"]),
            "created_at": row["created_at"],
        }
        for row in rag_rows
    ]
    latest_trace = record["rag_traces"][0] if record["rag_traces"] else {}
    record["retriever_type"] = latest_trace.get("retriever_type", "unknown")
    record["fallback_used"] = bool(latest_trace.get("fallback_used", False))
    inspection = (record.get("four_diagnosis") or {}).get("inspection") or {}
    record["tongue_image_url"] = inspection.get("tongue_image_url")
    return record


def _constitution_row_to_dict(row: Any) -> Dict[str, Any]:
    return {
        "session_id": row["session_id"],
        "created_at": row["created_at"],
        "algorithm_version": row["algorithm_version"],
        "primary_constitution": row["primary_constitution"],
        "secondary_constitutions": _from_json(row["secondary_constitutions_json"], []),
        "scores": _from_json(row["scores_json"], {}),
        "constitution_judgements": _from_json(row["constitution_judgements_json"], {}),
        "rag_explanation": row["rag_explanation"],
        "rag_sources": _from_json(row["rag_sources_json"], []),
        "broadcast_text": row["broadcast_text"],
        "safety_disclaimer": row["safety_disclaimer"],
    }


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _build_filter_clause(
    primary_constitution: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> tuple[str, tuple[Any, ...]]:
    clauses: List[str] = []
    params: List[Any] = []
    if primary_constitution:
        clauses.append("primary_constitution = ?")
        params.append(primary_constitution)
    if date_from:
        clauses.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("created_at <= ?")
        params.append(date_to)
    if not clauses:
        return "", tuple()
    return "WHERE " + " AND ".join(clauses), tuple(params)


def _record_summary_from_detail(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "session_id": record.get("session_id"),
        "created_at": record.get("created_at"),
        "primary_constitution": record.get("primary_constitution"),
        "secondary_constitutions": record.get("secondary_constitutions", []),
        "algorithm_version": record.get("algorithm_version"),
        "retriever_type": record.get("retriever_type", "unknown"),
        "fallback_used": bool(record.get("fallback_used", False)),
        "tongue_image_url": record.get("tongue_image_url"),
    }
