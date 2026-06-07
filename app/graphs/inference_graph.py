from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, TypedDict

from app.agents.inference_agents import (
    ConstitutionJudgeAgent,
    RAGRetrieveAgent,
    RequestValidateAgent,
    ResponseFormatAgent,
    SafetyAgent,
    SymptomExtractAgent,
)
from app.core.paths import RAW_DIR
from app.graphs.compat import END, StateGraph


class InferenceState(TypedDict, total=False):
    query: str
    top_k: int
    is_valid: bool
    validation_errors: List[str]
    symptoms: List[str]
    evidence: List[Dict[str, Any]]
    constitution: str
    confidence: float
    constitution_scores: Dict[str, int]
    safety: Dict[str, Any]
    disclaimer: str
    answer: str
    response: Dict[str, Any]


def build_inference_graph(raw_dir: Path = RAW_DIR):
    graph = StateGraph(InferenceState)
    graph.add_node("RequestValidateAgent", RequestValidateAgent().run)
    graph.add_node("SymptomExtractAgent", SymptomExtractAgent().run)
    graph.add_node("RAGRetrieveAgent", RAGRetrieveAgent(raw_dir=raw_dir).run)
    graph.add_node("ConstitutionJudgeAgent", ConstitutionJudgeAgent().run)
    graph.add_node("SafetyAgent", SafetyAgent().run)
    graph.add_node("ResponseFormatAgent", ResponseFormatAgent().run)

    graph.set_entry_point("RequestValidateAgent")
    graph.add_edge("RequestValidateAgent", "SymptomExtractAgent")
    graph.add_edge("SymptomExtractAgent", "RAGRetrieveAgent")
    graph.add_edge("RAGRetrieveAgent", "ConstitutionJudgeAgent")
    graph.add_edge("ConstitutionJudgeAgent", "SafetyAgent")
    graph.add_edge("SafetyAgent", "ResponseFormatAgent")
    graph.add_edge("ResponseFormatAgent", END)
    return graph.compile()


def run_inference(query: str, top_k: int = 3, raw_dir: Path = RAW_DIR) -> Dict[str, Any]:
    graph = build_inference_graph(raw_dir=raw_dir)
    return graph.invoke({"query": query, "top_k": top_k})
