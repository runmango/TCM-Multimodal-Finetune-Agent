from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, List, Optional

from app.core.constitution_scale_items import ALGORITHM_VERSION, CONSTITUTIONS, SCALE_ITEMS
from app.schemas.constitution_questionnaire import TongueFeatures
from app.schemas.four_diagnosis import (
    AuscultationOlfactionData,
    FourDiagnosisData,
    InquiryData,
    InspectionData,
    PalpationData,
)
from app.services.constitution_scale_service import (
    SCALE_NOTICE,
    get_scale_questionnaire,
    normalize_answer_map,
    score_constitution_scale,
)
from app.services.inference_service import SAFETY_NOTICE
from app.services.knowledge_qa_service import HEALTH_MANAGEMENT_NOTICE, explain_constitution_result
from app.repositories.constitution_record_repository import save_constitution_record


OPTIONS = [
    {"label": "没有", "score": 1},
    {"label": "很少", "score": 2},
    {"label": "有时", "score": 3},
    {"label": "经常", "score": 4},
    {"label": "总是", "score": 5},
]

ADVICE = {
    "平和质": "建议继续保持规律作息、均衡饮食和适度运动。",
    "气虚质": "建议规律作息，避免过度劳累，可选择散步、八段锦等温和运动。",
    "阳虚质": "建议注意保暖，少食寒凉，运动以温和、循序渐进为主。",
    "阴虚质": "建议减少熬夜和辛辣刺激，注意补充休息，保持情绪平稳。",
    "痰湿质": "建议饮食清淡，减少油腻甜食，配合规律运动。",
    "湿热质": "建议清淡饮食，少熬夜，减少辛辣油腻和酒精刺激。",
    "血瘀质": "建议保持适度活动和睡眠规律，如疼痛明显或持续应及时就医。",
    "气郁质": "建议保持情绪舒畅，规律运动，压力持续较大时可寻求专业支持。",
    "特禀质": "建议远离明确过敏原，保持环境清洁，过敏反复或加重时咨询医生。",
    "信息不足": "建议补充问卷信息，或结合生活状态、舌象与专业评估进一步了解体质倾向。",
}


def get_questionnaire() -> Dict[str, Any]:
    return {"questions": get_scale_questionnaire(), "options": OPTIONS}


def score_questionnaire(
    answers: List[Dict[str, int]],
    tongue_image_url: Optional[str] = None,
    tongue_features: Optional[Dict[str, Any] | TongueFeatures] = None,
    top_k: int = 3,
    gender: str = "unknown",
) -> Dict[str, Any]:
    return run_full_constitution_infer(
        answers=answers,
        tongue_image_url=tongue_image_url,
        tongue_features=tongue_features,
        top_k=top_k,
        gender=gender,
    )


def run_full_constitution_infer(
    answers: List[Dict[str, int]],
    tongue_image_url: Optional[str] = None,
    tongue_features: Optional[Dict[str, Any] | TongueFeatures] = None,
    top_k: int = 3,
    gender: str = "unknown",
) -> Dict[str, Any]:
    session_id = _new_session_id()
    scale_result = score_constitution_scale(answers=answers, gender=gender)
    primary_constitution = scale_result["primary_constitution"]
    secondary_constitutions = scale_result["secondary_constitutions"]
    four_diagnosis = build_four_diagnosis_from_answers(
        answers=answers,
        tongue_image_url=tongue_image_url,
        tongue_features=tongue_features,
    )
    result_text = _build_result_text(primary_constitution, secondary_constitutions)
    query_constitution = _base_constitution_name(primary_constitution)
    rag_result = explain_constitution_result(
        primary_constitution=query_constitution,
        secondary_constitutions=secondary_constitutions,
        scores=scale_result["scores"],
        top_k=top_k,
    )
    broadcast_text = build_broadcast_text(
        primary_constitution=primary_constitution,
        secondary_constitutions=secondary_constitutions,
        four_diagnosis=four_diagnosis,
        rag_explanation=rag_result["explanation"],
    )

    payload = {
        "session_id": session_id,
        "primary_constitution": primary_constitution,
        "secondary_constitutions": secondary_constitutions,
        "scores": scale_result["scores"],
        "constitution_judgements": scale_result["constitution_judgements"],
        "algorithm_version": ALGORITHM_VERSION,
        "retriever_type": rag_result.get("retriever_type", "fallback"),
        "result_text": result_text,
        "safety_notice": _combined_safety_notice(),
        "four_diagnosis": _model_dump(four_diagnosis),
        "rag_explanation": rag_result["explanation"],
        "rag_sources": rag_result["sources"],
        "broadcast_text": broadcast_text,
    }

    save_constitution_record(
        session_id=session_id,
        payload=payload,
        four_diagnosis=payload["four_diagnosis"],
        rag_trace={
            "query": rag_result.get("query", ""),
            "top_k": top_k,
            "sources": rag_result.get("sources", []),
            "retriever_type": rag_result.get("retriever_type", "fallback"),
            "fallback_used": rag_result.get("fallback_used", True),
        },
        tongue_features=_normalize_tongue_features(tongue_features),
    )
    return payload


def build_four_diagnosis_from_answers(
    answers: List[Dict[str, int]],
    tongue_image_url: Optional[str] = None,
    tongue_features: Optional[Dict[str, Any] | TongueFeatures] = None,
) -> FourDiagnosisData:
    answer_map = normalize_answer_map(answers)
    tongue_data = _normalize_tongue_features(tongue_features)

    inspection = InspectionData(
        tongue_image_url=tongue_image_url,
        tongue_color=tongue_data.get("tongue_color"),
        tongue_coating=tongue_data.get("tongue_coating"),
        teeth_marks=tongue_data.get("teeth_marks"),
        tongue_shape=tongue_data.get("tongue_shape"),
    )

    inquiry_values: Dict[str, Any] = {"raw_answers": answer_map}
    for item in SCALE_ITEMS:
        answer_id = item.answer_id or item.id
        if not item.inquiry_field or answer_id not in answer_map:
            continue
        current_value = inquiry_values.get(item.inquiry_field)
        score = answer_map[answer_id]
        inquiry_values[item.inquiry_field] = max(int(current_value or 0), score)

    inquiry = InquiryData(**inquiry_values)
    return FourDiagnosisData(
        inspection=inspection,
        auscultation_olfaction=AuscultationOlfactionData(),
        inquiry=inquiry,
        palpation=PalpationData(),
    )


def build_broadcast_text(
    primary_constitution: str,
    secondary_constitutions: List[str],
    four_diagnosis: FourDiagnosisData | Dict[str, Any],
    rag_explanation: str,
) -> str:
    four_diagnosis_data = four_diagnosis if isinstance(four_diagnosis, FourDiagnosisData) else FourDiagnosisData(**four_diagnosis)
    tongue_summary = _build_tongue_summary(four_diagnosis_data.inspection)
    if primary_constitution == "信息不足":
        tendency = "当前问卷信息不足，暂不能形成稳定体质倾向"
    elif secondary_constitutions:
        tendency = "当前更偏向%s，同时存在%s倾向" % (primary_constitution, "、".join(secondary_constitutions))
    else:
        tendency = "当前更偏向%s" % primary_constitution

    text = "根据你的问诊量表%s，%s。%s" % (tongue_summary, tendency, rag_explanation)
    return _ensure_full_safety_notice(text)


def _build_result_text(primary_constitution: str, secondary_constitutions: List[str]) -> str:
    base = _base_constitution_name(primary_constitution)
    if primary_constitution == "信息不足":
        text = "根据本次问卷结果，当前信息不足，暂不能形成稳定体质倾向。%s" % ADVICE["信息不足"]
    elif secondary_constitutions:
        text = "根据正式转化分算法，您的主要体质倾向为%s，兼有%s倾向。%s" % (
            primary_constitution,
            "、".join(secondary_constitutions),
            ADVICE.get(base, ADVICE["信息不足"]),
        )
    else:
        text = "根据正式转化分算法，您的主要体质倾向为%s。%s" % (
            primary_constitution,
            ADVICE.get(base, ADVICE["信息不足"]),
        )
    return _ensure_full_safety_notice("%s%s" % (SCALE_NOTICE, text))


def _build_tongue_summary(inspection: InspectionData) -> str:
    parts: List[str] = []
    if inspection.tongue_image_url:
        parts.append("已上传舌象图片")
    if inspection.tongue_color:
        parts.append("舌质%s" % inspection.tongue_color)
    if inspection.tongue_coating:
        parts.append("舌苔%s" % inspection.tongue_coating)
    if inspection.teeth_marks is not None:
        parts.append("有齿痕" if inspection.teeth_marks else "无明显齿痕")
    if inspection.tongue_shape:
        parts.append("舌形%s" % inspection.tongue_shape)
    if not parts:
        return ""
    return "和舌象信息（%s）" % "、".join(parts)


def _normalize_tongue_features(tongue_features: Optional[Dict[str, Any] | TongueFeatures]) -> Dict[str, Any]:
    if tongue_features is None:
        return {}
    if isinstance(tongue_features, dict):
        return dict(tongue_features)
    return _model_dump(tongue_features)


def _base_constitution_name(primary_constitution: str) -> str:
    return primary_constitution.replace("（倾向）", "")


def _combined_safety_notice() -> str:
    return "%s%s" % (SAFETY_NOTICE, HEALTH_MANAGEMENT_NOTICE)


def _ensure_full_safety_notice(text: str) -> str:
    normalized = text.rstrip()
    if SAFETY_NOTICE not in normalized:
        normalized = normalized + ("" if normalized.endswith("。") else "。") + SAFETY_NOTICE
    if HEALTH_MANAGEMENT_NOTICE not in normalized:
        normalized = normalized + HEALTH_MANAGEMENT_NOTICE
    return normalized


def _new_session_id() -> str:
    return "%s_%s" % (datetime.now().strftime("%Y%m%d%H%M%S"), uuid4().hex[:8])


def _model_dump(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
