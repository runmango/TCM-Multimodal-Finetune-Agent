from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from app.core.paths import PROCESSED_DIR, RAW_DIR
from app.services.inference_service import SAFETY_NOTICE
from app.services.vector_rag import build_vector_index, search_vector_knowledge


KNOWN_TERMS = [
    "平和质",
    "气虚质",
    "阳虚质",
    "阴虚质",
    "痰湿质",
    "湿热质",
    "血瘀质",
    "气郁质",
    "特禀质",
    "气虚",
    "阳虚",
    "阴虚",
    "痰湿",
    "湿热",
    "血瘀",
    "气郁",
    "特禀",
    "乏力",
    "气短",
    "自汗",
    "舌淡",
    "齿痕",
    "怕冷",
    "手脚发凉",
    "口干",
    "盗汗",
    "痰多",
    "苔腻",
    "口苦",
    "小便黄",
    "刺痛",
    "过敏",
    "调养",
    "表现",
]

LOW_SIGNAL_TERMS = {"调养", "表现"}
UNSAFE_TERMS = ["开药", "处方", "确诊", "诊断", "剂量", "用量", "治疗方案", "停药"]
HEALTH_MANAGEMENT_NOTICE = "本内容为非诊疗性质，仅供健康管理参考，不能替代医生诊断。"
FALLBACK_ANSWER = "当前知识库未检索到足够依据，建议补充问题或咨询专业医生。%s%s" % (
    SAFETY_NOTICE,
    HEALTH_MANAGEMENT_NOTICE,
)
SAFETY_REFUSAL = "当前问题涉及诊断、处方、剂量或治疗决策，系统不能替代医生给出此类建议。%s%s" % (
    SAFETY_NOTICE,
    HEALTH_MANAGEMENT_NOTICE,
)

CONSTITUTION_FALLBACKS = {
    "平和质": "平和质通常表示整体状态相对协调。健康管理上建议继续保持规律作息、均衡饮食和适度运动。",
    "气虚质": "气虚质常见表现包括乏力、气短、自汗、易感冒等。调养上建议规律作息，避免过劳，可选择散步、八段锦等温和运动。",
    "阳虚质": "阳虚质常见表现包括怕冷、手脚发凉、喜热饮等。调养上建议注意保暖，减少寒凉饮食，运动循序渐进。",
    "阴虚质": "阴虚质常见表现包括口干、咽干、盗汗、手足心热等。调养上建议减少熬夜和辛辣刺激，注意休息。",
    "痰湿质": "痰湿质常见表现包括身体困重、痰多、苔腻等。调养上建议饮食清淡，减少油腻甜食，配合规律运动。",
    "湿热质": "湿热质常见表现包括口苦、口黏、小便黄、皮肤出油等。调养上建议清淡饮食，减少辛辣油腻和酒精刺激。",
    "血瘀质": "血瘀质常见表现包括面色或唇色偏暗、刺痛、舌色紫暗等。调养上建议保持适度活动和睡眠规律。",
    "气郁质": "气郁质常见表现包括情绪低落、胸胁胀满、频繁叹气等。调养上建议保持情绪舒畅，规律运动。",
    "特禀质": "特禀质常见表现包括过敏、鼻炎、皮肤敏感等。调养上建议远离明确过敏原，保持环境清洁。",
    "平和质或信息不足": "当前信息不足以判断明显偏颇体质，建议补充问卷、舌象和生活状态信息后再综合参考。",
}


def ask_knowledge(query: str, top_k: int = 3, backend: str = "rule") -> Dict[str, Any]:
    normalized = (query or "").strip()
    if _contains_unsafe_term(normalized):
        return {
            "answer": SAFETY_REFUSAL,
            "sources": [],
            "safety_notice": SAFETY_NOTICE,
            "retriever_type": "safety",
            "fallback_used": False,
        }

    vector_result = _safe_vector_search(normalized, top_k=top_k)
    matches = vector_result["matches"]
    retriever_type = vector_result["retriever_type"]
    fallback_used = vector_result["fallback_used"]
    if not matches:
        matches = search_knowledge(normalized, top_k=top_k)
        retriever_type = "keyword" if matches else retriever_type
        fallback_used = True
    if not matches:
        return {
            "answer": FALLBACK_ANSWER,
            "sources": [],
            "safety_notice": SAFETY_NOTICE,
            "retriever_type": "fallback",
            "fallback_used": True,
        }

    answer = _summarize_answer(matches[0])
    answer = _ensure_health_management_notice(_ensure_safety_notice(answer))
    sources = [_source_from_match(item) for item in matches]
    return {
        "answer": answer,
        "sources": sources,
        "safety_notice": SAFETY_NOTICE,
        "retriever_type": retriever_type,
        "fallback_used": fallback_used,
    }


def explain_constitution_result(
    primary_constitution: str,
    secondary_constitutions: List[str],
    scores: Dict[str, int],
    top_k: int = 3,
) -> Dict[str, Any]:
    query_parts = [primary_constitution, "定义", "常见表现", "调养建议", "注意事项"]
    if secondary_constitutions:
        query_parts.extend(secondary_constitutions)
        query_parts.append("兼夹体质")
    query = " ".join(query_parts)

    known_constitutions = set(CONSTITUTION_FALLBACKS) - {"平和质或信息不足"}
    vector_result = _safe_vector_search(query, top_k=top_k) if primary_constitution in known_constitutions else {
        "matches": [],
        "retriever_type": "fallback",
        "fallback_used": True,
    }
    matches = vector_result["matches"]
    retriever_type = vector_result["retriever_type"]
    fallback_used = vector_result["fallback_used"]
    if not matches and primary_constitution in known_constitutions:
        matches = search_knowledge(query, top_k=top_k)
        retriever_type = "keyword" if matches else retriever_type
        fallback_used = True
    if matches:
        explanation = _summarize_answer(matches[0])
        if secondary_constitutions:
            explanation = "%s 兼夹体质可结合%s相关表现综合参考。" % (
                explanation.rstrip("。"),
                "、".join(secondary_constitutions),
            )
        sources = [_source_from_match(item) for item in matches]
    else:
        explanation = CONSTITUTION_FALLBACKS.get(primary_constitution, CONSTITUTION_FALLBACKS["平和质或信息不足"])
        if secondary_constitutions:
            explanation = "%s 同时可关注%s倾向。" % (explanation, "、".join(secondary_constitutions))
        sources = []

    explanation = _ensure_health_management_notice(_ensure_safety_notice(explanation))
    return {
        "query": query,
        "explanation": explanation,
        "sources": sources,
        "safety_notice": SAFETY_NOTICE,
        "score_snapshot": scores,
        "retriever_type": retriever_type,
        "fallback_used": fallback_used,
    }


def rebuild_vector_index() -> Dict[str, Any]:
    return build_vector_index()


def vector_rag_search(query: str, top_k: int = 3) -> Dict[str, Any]:
    vector_result = _safe_vector_search(query, top_k=top_k)
    matches = vector_result["matches"]
    if not matches:
        matches = search_knowledge(query, top_k=top_k)
        return {
            "query": query,
            "results": matches,
            "retriever_type": "keyword" if matches else "fallback",
            "fallback_used": True,
        }
    return {
        "query": query,
        "results": matches,
        "retriever_type": vector_result["retriever_type"],
        "fallback_used": vector_result["fallback_used"],
    }


def search_knowledge(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    query = (query or "").strip()
    if not query:
        return []

    terms = _extract_terms(query)
    documents = _load_documents()
    scored: List[Dict[str, Any]] = []

    for doc in documents:
        score = _score_document(doc, query=query, terms=terms)
        if score < 2.0:
            continue
        item = dict(doc)
        item["score"] = round(score, 3)
        scored.append(item)

    scored.sort(key=lambda item: (-item["score"], item["source_id"]))
    return scored[: max(1, min(int(top_k), 10))]


def _load_documents() -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    documents.extend(_load_sft_documents(PROCESSED_DIR / "sft_train.jsonl"))
    for raw_path in sorted(RAW_DIR.glob("*.jsonl")):
        documents.extend(_load_raw_documents(raw_path))
    return documents


def _load_sft_documents(path: Path) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    if not path.exists():
        return documents

    with path.open("r", encoding="utf-8") as file_obj:
        for index, line in enumerate(file_obj, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError:
                continue
            output = str(item.get("output") or "").strip()
            question = str(item.get("input") or item.get("instruction") or "").strip()
            if not output or not question:
                continue
            documents.append(
                {
                    "source_type": "sft",
                    "source_id": "tcm_sft_%06d" % index,
                    "title": question[:40],
                    "question": question,
                    "answer": output,
                    "tags": [],
                }
            )
    return documents


def _load_raw_documents(path: Path) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file_obj:
        for index, line in enumerate(file_obj, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError:
                continue
            content = str(
                item.get("content")
                or item.get("output")
                or item.get("image_description")
                or item.get("advice")
                or ""
            ).strip()
            title = str(item.get("title") or item.get("constitution") or path.stem).strip()
            tags = item.get("tags") or item.get("symptoms") or item.get("labels") or []
            if not content:
                continue
            documents.append(
                {
                    "source_type": str(item.get("type") or path.stem),
                    "source_id": str(item.get("id") or "%s_%06d" % (path.stem, index)),
                    "title": title,
                    "question": title,
                    "answer": content,
                    "tags": tags if isinstance(tags, list) else [str(tags)],
                }
            )
    return documents


def _extract_terms(query: str) -> List[str]:
    known_matches = [term for term in KNOWN_TERMS if term in query]
    high_signal_matches = [term for term in known_matches if term not in LOW_SIGNAL_TERMS]
    terms = list(high_signal_matches)
    if high_signal_matches:
        terms.extend(term for term in known_matches if term in LOW_SIGNAL_TERMS)
    for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", query):
        if len(token) <= 12:
            terms.append(token)
    return sorted(set(terms), key=len, reverse=True)


def _score_document(doc: Dict[str, Any], query: str, terms: List[str]) -> float:
    title = str(doc.get("title") or "")
    question = str(doc.get("question") or "")
    answer = str(doc.get("answer") or "")
    tag_text = " ".join(str(tag) for tag in doc.get("tags") or [])
    haystack = "%s %s %s %s" % (title, question, answer, tag_text)
    score = 0.0

    if query and query in haystack:
        score += 5.0

    for term in terms:
        if term in title:
            score += 4.0
        if term in question:
            score += 3.0
        if term in tag_text:
            score += 2.0
        if term in answer:
            score += 1.0

    return score


def _source_from_match(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": item["source_type"],
        "source_id": item["source_id"],
        "title": item.get("title") or None,
        "score": item.get("score"),
    }


def _safe_vector_search(query: str, top_k: int) -> Dict[str, Any]:
    if not _has_high_signal_query(query):
        return {
            "matches": [],
            "retriever_type": "vector",
            "fallback_used": True,
            "reason": "low_signal_query",
        }
    try:
        result = search_vector_knowledge(query=query, top_k=top_k, auto_build=True)
    except Exception as error:
        return {
            "matches": [],
            "retriever_type": "vector_unavailable",
            "fallback_used": True,
            "reason": str(error),
        }

    matches = [item for item in result.get("matches", []) if float(item.get("score") or 0) >= 0.12]
    return {
        "matches": matches,
        "retriever_type": result.get("retriever_type") or "vector",
        "fallback_used": bool(result.get("fallback_used")),
        "reason": result.get("reason"),
    }


def _has_high_signal_query(query: str) -> bool:
    return any(term in query for term in KNOWN_TERMS if term not in LOW_SIGNAL_TERMS)


def _summarize_answer(item: Dict[str, Any]) -> str:
    answer = str(item.get("answer") or "").strip()
    if len(answer) <= 650:
        return answer
    return answer[:650].rstrip("，。；;、 ") + "。"


def _ensure_safety_notice(text: str) -> str:
    if SAFETY_NOTICE in text:
        return text
    normalized = text.rstrip()
    if normalized.endswith("。"):
        return normalized + SAFETY_NOTICE
    return normalized + "。" + SAFETY_NOTICE


def _ensure_health_management_notice(text: str) -> str:
    if HEALTH_MANAGEMENT_NOTICE in text:
        return text
    normalized = text.rstrip()
    if normalized.endswith("。"):
        return normalized + HEALTH_MANAGEMENT_NOTICE
    return normalized + "。" + HEALTH_MANAGEMENT_NOTICE


def _contains_unsafe_term(text: str) -> bool:
    return any(term in text for term in UNSAFE_TERMS)
