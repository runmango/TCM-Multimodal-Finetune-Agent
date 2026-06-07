from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, TypedDict

from app.agents.dataset_agents import (
    CleanAgent,
    DataLoadAgent,
    DatasetRegistryAgent,
    ExportAgent,
    MMBuildAgent,
    QualityScoreAgent,
    SFTBuildAgent,
    SchemaAgent,
    TrainCommandAgent,
    TrainConfigAgent,
    TrainSimAgent,
)
from app.agents.eval_agents import EvalAgent
from app.core.paths import PROCESSED_DIR, RAW_DIR, REPORTS_DIR
from app.graphs.compat import END, StateGraph


class DatasetState(TypedDict, total=False):
    train_mode: str
    warnings: List[str]
    raw_records: List[Dict[str, Any]]
    source_counts: Dict[str, int]
    clean_records: List[Dict[str, Any]]
    clean_stats: Dict[str, Any]
    valid_records: List[Dict[str, Any]]
    schema_errors: List[Dict[str, Any]]
    quality_records: List[Dict[str, Any]]
    quality_scores: List[Dict[str, Any]]
    average_quality_score: float
    sft_records: List[Dict[str, Any]]
    mm_sft_records: List[Dict[str, Any]]
    dataset_registry: Dict[str, Any]
    train_config: Dict[str, Any]
    train_command: str
    train_commands: Dict[str, Any]
    train_simulation: Dict[str, Any]
    eval_mode: str
    eval_report: Dict[str, Any]
    report: Dict[str, Any]
    exports: Dict[str, str]


def build_dataset_graph(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
    train_mode: str | None = None,
    eval_mode: str | None = None,
):
    graph = StateGraph(DatasetState)
    graph.add_node("DataLoadAgent", DataLoadAgent(raw_dir=raw_dir).run)
    graph.add_node("CleanAgent", CleanAgent().run)
    graph.add_node("SchemaAgent", SchemaAgent().run)
    graph.add_node("QualityScoreAgent", QualityScoreAgent().run)
    graph.add_node("SFTBuildAgent", SFTBuildAgent().run)
    graph.add_node("MMBuildAgent", MMBuildAgent().run)
    graph.add_node("DatasetRegistryAgent", DatasetRegistryAgent(processed_dir=processed_dir).run)
    graph.add_node("TrainConfigAgent", TrainConfigAgent(train_mode=train_mode or "").run)
    graph.add_node("TrainCommandAgent", TrainCommandAgent().run)
    graph.add_node("TrainSimAgent", TrainSimAgent().run)
    graph.add_node("EvalAgent", EvalAgent(eval_mode=eval_mode or "simulation").run)
    graph.add_node("ExportAgent", ExportAgent(processed_dir=processed_dir, reports_dir=reports_dir).run)

    graph.set_entry_point("DataLoadAgent")
    graph.add_edge("DataLoadAgent", "CleanAgent")
    graph.add_edge("CleanAgent", "SchemaAgent")
    graph.add_edge("SchemaAgent", "QualityScoreAgent")
    graph.add_edge("QualityScoreAgent", "SFTBuildAgent")
    graph.add_edge("SFTBuildAgent", "MMBuildAgent")
    graph.add_edge("MMBuildAgent", "DatasetRegistryAgent")
    graph.add_edge("DatasetRegistryAgent", "TrainConfigAgent")
    graph.add_edge("TrainConfigAgent", "TrainCommandAgent")
    graph.add_edge("TrainCommandAgent", "TrainSimAgent")
    graph.add_edge("TrainSimAgent", "EvalAgent")
    graph.add_edge("EvalAgent", "ExportAgent")
    graph.add_edge("ExportAgent", END)
    return graph.compile()


def run_dataset_build(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
    train_mode: str | None = None,
    eval_mode: str | None = None,
) -> Dict[str, Any]:
    graph = build_dataset_graph(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        reports_dir=reports_dir,
        train_mode=train_mode,
        eval_mode=eval_mode,
    )
    initial_state: Dict[str, Any] = {}
    if train_mode:
        initial_state["train_mode"] = train_mode
    if eval_mode:
        initial_state["eval_mode"] = eval_mode
    return graph.invoke(initial_state)
