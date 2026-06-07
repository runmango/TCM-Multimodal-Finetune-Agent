from __future__ import annotations

from typing import Any, Dict, List

from app.core.paths import RAW_DIR
from app.services.rag import KeywordRetriever


CONSTITUTION_PROFILES = {
    "气虚质": ["乏力", "气短", "自汗", "易感冒", "舌淡", "齿痕", "少气懒言"],
    "阳虚质": ["怕冷", "畏寒", "手脚冰凉", "腹泻", "舌淡胖", "喜热饮"],
    "阴虚质": ["口干", "盗汗", "五心烦热", "失眠", "舌红少苔", "潮热"],
    "痰湿质": ["困倦", "痰多", "胸闷", "肥胖", "苔腻", "身重"],
    "湿热质": ["口苦", "长痘", "小便黄", "苔黄腻", "烦躁", "大便黏滞"],
    "血瘀质": ["刺痛", "面色晦暗", "舌紫暗", "瘀斑", "痛经", "固定痛"],
}

SAFETY_TERMS = ["开药", "处方", "确诊", "药方", "抓药", "剂量", "诊断书", "用药方案"]


class RequestValidateAgent:
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = (state.get("query") or "").strip()
        errors: List[str] = []
        if not query:
            errors.append("query_empty")
        if len(query) > 500:
            errors.append("query_too_long")

        state.update({"query": query, "is_valid": not errors, "validation_errors": errors})
        return state


class SymptomExtractAgent:
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        symptoms = extract_symptoms(query)
        state["symptoms"] = symptoms
        return state


class RAGRetrieveAgent:
    def __init__(self, raw_dir=RAW_DIR) -> None:
        self.retriever = KeywordRetriever(raw_dir=raw_dir)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        evidence = self.retriever.search(query=state.get("query", ""), top_k=state.get("top_k", 3))
        state["evidence"] = evidence
        return state


class ConstitutionJudgeAgent:
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        symptoms = state.get("symptoms", [])
        evidence = state.get("evidence", [])
        scores = {name: 0 for name in CONSTITUTION_PROFILES}

        for constitution, terms in CONSTITUTION_PROFILES.items():
            for term in terms:
                if term in query:
                    scores[constitution] += 2
                if term in symptoms:
                    scores[constitution] += 2
            for item in evidence:
                haystack = "%s %s %s" % (item.get("title", ""), item.get("content", ""), " ".join(item.get("tags", [])))
                if constitution in haystack:
                    scores[constitution] += 1
                for term in terms:
                    if term in haystack and term in symptoms:
                        scores[constitution] += 1

        best_name = max(scores, key=scores.get)
        best_score = scores[best_name]
        constitution = best_name if best_score > 0 else "无法判断"
        confidence = min(round(best_score / 10.0, 2), 0.95) if best_score > 0 else 0.0

        state.update({"constitution": constitution, "confidence": confidence, "constitution_scores": scores})
        return state


class SafetyAgent:
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        blocked_terms = [term for term in SAFETY_TERMS if term in query]

        if state.get("validation_errors"):
            safety = {
                "status": "invalid",
                "reason": "请求内容为空或过长，请补充清晰、简短的健康描述。",
                "blocked_terms": [],
            }
        elif blocked_terms:
            safety = {
                "status": "refused",
                "reason": "请求涉及确诊、处方或具体用药决策，Demo 仅提供健康科普与体质倾向参考。",
                "blocked_terms": blocked_terms,
            }
        else:
            safety = {"status": "pass", "reason": "未发现确诊、处方或具体用药风险请求。", "blocked_terms": []}

        state["safety"] = safety
        return state


class ResponseFormatAgent:
    DISCLAIMER = "本结果仅用于健康科普和工程演示，不能替代医生面诊、诊断或处方。若症状明显或持续，请及时就医。"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        safety = state.get("safety", {})
        evidence = state.get("evidence", [])

        if safety.get("status") == "refused":
            constitution = "安全拒答"
            confidence = 0.0
            answer = "该请求涉及确诊、处方或具体用药决策，系统拒绝给出处方/确诊类结论。可以改为询问体质科普、生活方式建议或就医准备问题。"
        elif safety.get("status") == "invalid":
            constitution = "无法判断"
            confidence = 0.0
            answer = "请求信息不足，暂时无法进行体质倾向判断。"
        else:
            constitution = state.get("constitution", "无法判断")
            confidence = state.get("confidence", 0.0)
            if constitution == "无法判断":
                answer = "未提取到足够明确的体质线索，建议补充主要不适、舌象描述、睡眠、饮食和寒热感受。"
            else:
                answer = "根据症状与检索证据，体质倾向为%s。建议关注作息、饮食和运动等非药物调养，并结合专业医生意见。" % constitution

        response = {
            "constitution": constitution,
            "confidence": confidence,
            "symptoms": state.get("symptoms", []),
            "evidence": evidence,
            "safety": safety,
            "disclaimer": self.DISCLAIMER,
            "answer": answer,
        }
        state.update(response)
        state["response"] = response
        return state


def extract_symptoms(text: str) -> List[str]:
    symptoms: List[str] = []
    for terms in CONSTITUTION_PROFILES.values():
        for term in terms:
            if term in text and term not in symptoms:
                symptoms.append(term)
    return symptoms
