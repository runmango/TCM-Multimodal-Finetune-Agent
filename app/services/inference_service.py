from __future__ import annotations

from typing import Dict, List


SAFETY_NOTICE = "仅供健康科普参考，不替代医生诊疗。"

RULES = [
    ("气虚质", ["乏力", "气短", "懒言", "舌淡", "齿痕"], "建议规律作息，适度运动，避免过度劳累。"),
    ("阳虚质", ["怕冷", "手脚凉", "手脚冰凉", "腰膝酸冷"], "建议注意保暖，减少寒凉饮食，保持温和运动。"),
    ("阴虚质", ["口干", "五心烦热", "盗汗"], "建议减少熬夜和辛辣刺激，保持充足休息。"),
    ("痰湿质", ["痰多", "身重", "胸闷", "苔腻"], "建议清淡饮食，规律运动，减少油腻甜食。"),
    ("湿热质", ["口苦", "湿热", "大便黏滞", "舌红苔黄腻", "苔黄腻"], "建议饮食清淡，注意作息，减少辛辣油腻。"),
    ("气郁质", ["胸闷", "情绪低落", "叹气", "胁肋胀"], "建议保持情绪舒畅，适度运动，必要时咨询专业医生。"),
    ("血瘀质", ["瘀斑", "刺痛", "唇暗", "舌紫暗"], "建议保持适度活动，注意保暖，若疼痛明显请及时就医。"),
    ("特禀质", ["过敏", "鼻炎", "哮喘", "荨麻疹"], "建议远离明确过敏原，保持环境清洁，必要时咨询医生。"),
]


def infer_constitution(query: str, backend: str = "rule") -> Dict[str, str]:
    """Infer constitution tendency with a safe rule backend placeholder."""

    normalized = (query or "").strip()
    constitution, matched_terms, advice = _rule_infer(normalized)
    if constitution == "平和质或信息不足":
        reason = "当前信息不足以判断明显偏颇体质，暂按平和质或信息不足处理。"
        advice = "建议补充主要不适、舌象、睡眠、饮食和寒热感受后再进行体质倾向分析。"
    else:
        reason = "根据%s等表现，倾向于%s。" % ("、".join(matched_terms), constitution)

    return {
        "constitution": constitution,
        "reason": reason,
        "advice": advice,
        "safety_notice": SAFETY_NOTICE,
    }


def _rule_infer(query: str) -> tuple[str, List[str], str]:
    best_constitution = "平和质或信息不足"
    best_terms: List[str] = []
    best_advice = "建议保持规律作息、均衡饮食和适度运动。"

    for constitution, terms, advice in RULES:
        matched = [term for term in terms if term in query]
        if len(matched) > len(best_terms):
            best_constitution = constitution
            best_terms = matched
            best_advice = advice

    return best_constitution, best_terms, best_advice

