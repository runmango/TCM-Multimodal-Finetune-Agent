from typing import Any, Dict

from app.graphs.dataset_graph import run_dataset_build


def build_dataset() -> Dict[str, Any]:
    state = run_dataset_build()
    report = state.get("report", {})
    return {
        "status": "success" if report.get("summary", {}).get("schema_errors", 0) == 0 else "warning",
        "summary": report.get("summary", {}),
        "exports": state.get("exports", {}),
    }

