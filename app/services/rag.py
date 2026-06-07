from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from app.core.paths import RAW_DIR
from app.utils.io import read_jsonl


KNOWN_TERMS = [
    "气虚",
    "气虚质",
    "阳虚",
    "阳虚质",
    "阴虚",
    "阴虚质",
    "痰湿",
    "痰湿质",
    "湿热",
    "湿热质",
    "血瘀",
    "血瘀质",
    "乏力",
    "气短",
    "自汗",
    "易感冒",
    "舌淡",
    "齿痕",
    "怕冷",
    "畏寒",
    "手脚冰凉",
    "腹泻",
    "口干",
    "盗汗",
    "五心烦热",
    "失眠",
    "舌红少苔",
    "困倦",
    "痰多",
    "胸闷",
    "肥胖",
    "苔腻",
    "口苦",
    "长痘",
    "小便黄",
    "苔黄腻",
    "刺痛",
    "面色晦暗",
    "舌紫暗",
    "瘀斑",
]


class KeywordRetriever:
    """Small keyword RAG retriever, replaceable with a vector DB later."""

    def __init__(self, raw_dir: Path = RAW_DIR) -> None:
        self.raw_dir = raw_dir

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []

        top_k = max(1, min(int(top_k), 10))
        terms = self._extract_terms(query)
        documents = self._load_documents()
        scored: List[Dict[str, Any]] = []

        for doc in documents:
            score = self._score_doc(doc, query=query, terms=terms)
            if score <= 0:
                continue
            item = dict(doc)
            item["score"] = round(score, 3)
            scored.append(item)

        scored.sort(key=lambda item: (-item["score"], item["id"]))
        return scored[:top_k]

    def _load_documents(self) -> List[Dict[str, Any]]:
        documents: List[Dict[str, Any]] = []

        for item in read_jsonl(self.raw_dir / "tcm_knowledge.jsonl"):
            documents.append(
                {
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "tags": item.get("tags", []),
                    "source_type": item.get("type", "knowledge"),
                }
            )

        for item in read_jsonl(self.raw_dir / "constitution_cases.jsonl"):
            symptoms = item.get("symptoms", [])
            constitution = item.get("constitution", "")
            documents.append(
                {
                    "id": item.get("id", ""),
                    "title": "体质辨识样例：%s" % constitution,
                    "content": "症状：%s。参考建议：%s" % ("、".join(symptoms), item.get("advice", "")),
                    "tags": symptoms + [constitution],
                    "source_type": item.get("type", "constitution_case"),
                }
            )

        for item in read_jsonl(self.raw_dir / "tongue_mm_samples.jsonl"):
            symptoms = item.get("symptoms", [])
            labels = item.get("labels", [])
            constitution = item.get("constitution", "")
            documents.append(
                {
                    "id": item.get("id", ""),
                    "title": "舌象样例：%s" % constitution,
                    "content": "舌象描述：%s。伴随表现：%s" % (item.get("image_description", ""), "、".join(symptoms)),
                    "tags": labels + symptoms + [constitution],
                    "source_type": item.get("type", "tongue_image"),
                }
            )

        return documents

    def _extract_terms(self, query: str) -> List[str]:
        terms = [term for term in KNOWN_TERMS if term in query]
        return sorted(set(terms), key=len, reverse=True)

    def _score_doc(self, doc: Dict[str, Any], query: str, terms: List[str]) -> float:
        title = doc.get("title", "")
        content = doc.get("content", "")
        tags = doc.get("tags", [])
        tag_text = " ".join(tags)
        score = 0.0

        if query and query in content:
            score += 1.0

        for term in terms:
            if term in title:
                score += 3.0
            if term in tag_text:
                score += 2.0
            if term in content:
                score += 1.0

        return score

