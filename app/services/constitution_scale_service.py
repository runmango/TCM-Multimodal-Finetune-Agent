from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.constitution_scale_items import (
    ALGORITHM_VERSION,
    BIAS_CONSTITUTIONS,
    CONSTITUTIONS,
    QUESTION_ID_ALIASES,
    SCALE_ITEM_BY_ID,
    SCALE_ITEMS,
    ScaleItem,
)


SCALE_NOTICE = "体质评分采用《中医体质分类与判定》转化分算法，结果仅用于体质倾向分析和健康管理参考，不能替代医生诊断。"


def get_scale_questionnaire() -> List[Dict[str, Any]]:
    question_by_id: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for item in SCALE_ITEMS:
        question_id = _answer_id(item)
        question = {
            "id": question_id,
            "text": item.text,
            "constitution": item.constitution,
            "reverse": item.reverse,
            "applies_to": item.applies_to,
        }
        if question_id not in question_by_id:
            order.append(question_id)
            question_by_id[question_id] = question
            continue
        if question_by_id[question_id]["constitution"] == "平和质" and item.constitution != "平和质":
            question_by_id[question_id] = question
    return [question_by_id[question_id] for question_id in order]


def normalize_answer_map(answers: List[Dict[str, int]]) -> Dict[str, int]:
    answer_map: Dict[str, int] = {}
    for item in answers:
        raw_question_id = str(item.get("question_id") or "").strip()
        if not raw_question_id:
            continue
        question_id = canonical_question_id(raw_question_id)
        if not _is_known_answer_id(question_id):
            continue
        try:
            score = int(item.get("score", 0))
        except (TypeError, ValueError):
            continue
        if 1 <= score <= 5:
            answer_map[question_id] = score
    return answer_map


def score_constitution_scale(answers: List[Dict[str, int]], gender: str = "unknown") -> Dict[str, Any]:
    answer_map = normalize_answer_map(answers)
    raw_scores = {constitution: 0 for constitution in CONSTITUTIONS}
    item_counts = {constitution: 0 for constitution in CONSTITUTIONS}
    answered_counts = {constitution: 0 for constitution in CONSTITUTIONS}

    for item in _applicable_items(gender):
        answer_id = _answer_id(item)
        item_counts[item.constitution] += 1
        raw_score = answer_map.get(answer_id)
        if raw_score is None:
            continue
        answered_counts[item.constitution] += 1
        raw_scores[item.constitution] += reverse_score(raw_score) if item.reverse else raw_score

    scores: Dict[str, float] = {}
    data_completeness: Dict[str, str] = {}
    for constitution in CONSTITUTIONS:
        count = answered_counts[constitution]
        if count <= 0:
            scores[constitution] = 0.0
            data_completeness[constitution] = "信息不足"
            continue
        scores[constitution] = transformation_score(raw_scores[constitution], count)
        data_completeness[constitution] = "完整" if count == item_counts[constitution] else "部分"

    judgements = judge_constitutions(scores=scores, data_completeness=data_completeness)
    primary, secondary = select_primary_and_secondary(scores=scores, judgements=judgements, data_completeness=data_completeness)

    return {
        "scores": scores,
        "raw_scores": raw_scores,
        "item_counts": item_counts,
        "answered_counts": answered_counts,
        "constitution_judgements": judgements,
        "primary_constitution": primary,
        "secondary_constitutions": secondary,
        "algorithm_version": ALGORITHM_VERSION,
        "data_completeness": data_completeness,
        "answer_map": answer_map,
    }


def transformation_score(raw_score: int, item_count: int) -> float:
    if item_count <= 0:
        return 0.0
    return round((raw_score - item_count) / (item_count * 4) * 100, 1)


def reverse_score(score: int) -> int:
    return 6 - score


def judge_constitutions(scores: Dict[str, float], data_completeness: Dict[str, str]) -> Dict[str, str]:
    judgements: Dict[str, str] = {}
    if data_completeness.get("平和质") == "信息不足":
        judgements["平和质"] = "信息不足"
    else:
        other_scores = [scores[constitution] for constitution in BIAS_CONSTITUTIONS if data_completeness.get(constitution) != "信息不足"]
        if scores["平和质"] >= 60 and other_scores and all(score < 30 for score in other_scores):
            judgements["平和质"] = "是"
        elif scores["平和质"] >= 60 and other_scores and all(score < 40 for score in other_scores):
            judgements["平和质"] = "基本是"
        else:
            judgements["平和质"] = "否"

    for constitution in BIAS_CONSTITUTIONS:
        if data_completeness.get(constitution) == "信息不足":
            judgements[constitution] = "信息不足"
            continue
        score = scores[constitution]
        if score >= 40:
            judgements[constitution] = "是"
        elif score >= 30:
            judgements[constitution] = "倾向是"
        else:
            judgements[constitution] = "否"

    return judgements


def select_primary_and_secondary(
    scores: Dict[str, float],
    judgements: Dict[str, str],
    data_completeness: Dict[str, str],
) -> tuple[str, List[str]]:
    yes_bias = [constitution for constitution in BIAS_CONSTITUTIONS if judgements.get(constitution) == "是"]
    if yes_bias:
        primary = max(yes_bias, key=lambda constitution: (scores[constitution], -CONSTITUTIONS.index(constitution)))
        secondary = [
            constitution
            for constitution in BIAS_CONSTITUTIONS
            if constitution != primary and judgements.get(constitution) in ("是", "倾向是")
        ]
        secondary.sort(key=lambda constitution: scores[constitution], reverse=True)
        return primary, secondary

    tendency_bias = [constitution for constitution in BIAS_CONSTITUTIONS if judgements.get(constitution) == "倾向是"]
    if tendency_bias:
        primary = max(tendency_bias, key=lambda constitution: (scores[constitution], -CONSTITUTIONS.index(constitution)))
        secondary = [constitution for constitution in tendency_bias if constitution != primary]
        secondary.sort(key=lambda constitution: scores[constitution], reverse=True)
        return "%s（倾向）" % primary, secondary

    has_bias_answer = any(data_completeness.get(constitution) != "信息不足" for constitution in BIAS_CONSTITUTIONS)
    if has_bias_answer and judgements.get("平和质") in ("是", "基本是"):
        return "平和质", []

    return "信息不足", []


def canonical_question_id(question_id: str) -> str:
    return QUESTION_ID_ALIASES.get(question_id, question_id)


def _is_known_answer_id(question_id: str) -> bool:
    return any(_answer_id(item) == question_id for item in SCALE_ITEMS)


def _applicable_items(gender: str) -> List[ScaleItem]:
    normalized_gender = (gender or "unknown").strip().lower()
    return [
        item
        for item in SCALE_ITEMS
        if item.applies_to is None or item.applies_to == normalized_gender
    ]


def _answer_id(item: ScaleItem) -> str:
    return item.answer_id or item.id
