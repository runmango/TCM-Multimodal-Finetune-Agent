import json

from app.core.paths import CONFIGS_DIR, PROCESSED_DIR, REPORTS_DIR, ROOT_REPORTS_DIR
from app.agents.dataset_agents import TrainCommandAgent, TrainConfigAgent, TrainSimAgent
from app.graphs.dataset_graph import run_dataset_build


def test_dataset_build_success(monkeypatch):
    monkeypatch.delenv("TCM_TRAIN_MODE", raising=False)
    monkeypatch.delenv("TCM_BASE_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME_OR_PATH", raising=False)
    state = run_dataset_build()

    sft_path = PROCESSED_DIR / "sft_train.jsonl"
    mm_path = PROCESSED_DIR / "mm_sft_train.jsonl"
    dataset_info_path = PROCESSED_DIR / "dataset_info.json"
    config_yaml_path = CONFIGS_DIR / "tcm_qwen_normal_lora_sft.yaml"
    config_json_path = CONFIGS_DIR / "tcm_qwen_normal_lora_sft.json"
    report_path = REPORTS_DIR / "dataset_report.json"
    root_report_path = ROOT_REPORTS_DIR / "dataset_report.json"
    train_report_path = ROOT_REPORTS_DIR / "train_simulation_report.json"
    loss_csv_path = ROOT_REPORTS_DIR / "train_loss.csv"

    assert sft_path.exists()
    assert mm_path.exists()
    assert dataset_info_path.exists()
    assert config_yaml_path.exists()
    assert config_json_path.exists()
    assert report_path.exists()
    assert root_report_path.exists()
    assert train_report_path.exists()
    assert loss_csv_path.exists()
    assert state["report"]["summary"]["schema_errors"] == 0
    assert state["report"]["summary"]["sft_records"] >= 4
    assert state["report"]["summary"]["mm_sft_records"] >= 2
    assert state["dataset_registry"]["tcm_sft"]["formatting"] == "alpaca"
    assert state["train_config"]["config"]["finetuning_type"] == "lora"
    assert "llamafactory-cli train" in state["train_command"]
    assert len(state["train_simulation"]["epochs"]) == 3
    assert state["train_config"]["mode"] == "normal"
    assert state["train_config"]["base_model"] == "Qwen/Qwen2.5-1.5B-Instruct"

    with report_path.open("r", encoding="utf-8") as file_obj:
        report = json.load(file_obj)
    assert report["summary"]["valid_records"] == report["summary"]["raw_records"]
    assert "training" in report
    assert "evaluation" in report
    assert report["training"]["mode"] == "normal"
    assert report["training"]["base_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert report["training"]["config_file"].endswith("tcm_qwen_normal_lora_sft.yaml")
    assert "真实训练需要安装" in report["training"]["warning"]
    assert report["evaluation"]["eval_mode"] == "simulation"
    assert report["evaluation"]["constitution_accuracy"] == 0.78

    with dataset_info_path.open("r", encoding="utf-8") as file_obj:
        dataset_info = json.load(file_obj)
    assert dataset_info["tcm_sft"]["columns"]["prompt"] == "instruction"

    with train_report_path.open("r", encoding="utf-8") as file_obj:
        train_report = json.load(file_obj)
    assert train_report["mode"] == "simulation"
    assert train_report["status"] == "success"
    assert train_report["final_metrics"]["simulated_overfit_risk"] == "high"


def test_train_config_safe_mode(monkeypatch):
    monkeypatch.delenv("TCM_TRAIN_MODE", raising=False)
    monkeypatch.delenv("TCM_BASE_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME_OR_PATH", raising=False)
    state = {"exports": {"sft_train": str(PROCESSED_DIR / "sft_train.jsonl")}}

    state = TrainConfigAgent(train_mode="safe").run(state)

    assert state["train_config"]["mode"] == "safe"
    assert state["train_config"]["base_model"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert "safe" in state["train_config"]["yaml_path"]
    assert "0_5b" in state["train_config"]["output_dir"]
    assert state["train_config"]["config"]["cutoff_len"] == 1024
    assert state["train_config"]["metadata"]["train_mode"] == "safe"
    for unsupported_key in ("train_file", "train_mode", "hardware_hint", "notes"):
        assert unsupported_key not in state["train_config"]["config"]


def test_train_config_normal_mode(monkeypatch):
    monkeypatch.delenv("TCM_TRAIN_MODE", raising=False)
    monkeypatch.delenv("TCM_BASE_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME_OR_PATH", raising=False)
    state = {"exports": {"sft_train": str(PROCESSED_DIR / "sft_train.jsonl")}}

    state = TrainConfigAgent(train_mode="normal").run(state)

    assert state["train_config"]["mode"] == "normal"
    assert state["train_config"]["base_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert "normal" in state["train_config"]["yaml_path"]
    assert "1_5b" in state["train_config"]["output_dir"]
    assert state["train_config"]["config"]["cutoff_len"] == 1024
    assert state["train_config"]["metadata"]["train_mode"] == "normal"
    for unsupported_key in ("train_file", "train_mode", "hardware_hint", "notes"):
        assert unsupported_key not in state["train_config"]["config"]


def test_train_config_invalid_mode_fallback_safe(monkeypatch):
    monkeypatch.delenv("TCM_TRAIN_MODE", raising=False)
    monkeypatch.delenv("TCM_BASE_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME_OR_PATH", raising=False)
    state = {"exports": {"sft_train": str(PROCESSED_DIR / "sft_train.jsonl")}}

    state = TrainConfigAgent(train_mode="invalid").run(state)

    assert state["train_config"]["mode"] == "safe"
    assert state["train_config"]["base_model"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert state["warnings"]
    assert "Invalid train_mode" in state["warnings"][0]


def test_train_command_mode_specific(monkeypatch):
    monkeypatch.delenv("TCM_BASE_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME_OR_PATH", raising=False)
    safe_state = TrainConfigAgent(train_mode="safe").run({"exports": {"sft_train": str(PROCESSED_DIR / "sft_train.jsonl")}})
    safe_state = TrainCommandAgent().run(safe_state)
    normal_state = TrainConfigAgent(train_mode="normal").run({"exports": {"sft_train": str(PROCESSED_DIR / "sft_train.jsonl")}})
    normal_state = TrainCommandAgent().run(normal_state)

    assert "tcm_qwen_safe_lora_sft.yaml" in safe_state["train_commands"]["llamafactory_train"]
    assert "tcm_qwen_normal_lora_sft.yaml" in normal_state["train_commands"]["llamafactory_train"]
    assert safe_state["train_commands"]["mode"] == "safe"
    assert normal_state["train_commands"]["mode"] == "normal"


def test_train_sim_mode_specific_losses(monkeypatch):
    monkeypatch.delenv("TCM_BASE_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME_OR_PATH", raising=False)
    safe_state = TrainConfigAgent(train_mode="safe").run(
        {"exports": {"sft_train": str(PROCESSED_DIR / "sft_train.jsonl")}, "sft_records": [{"id": "1"}]}
    )
    safe_state = TrainSimAgent().run(safe_state)
    normal_state = TrainConfigAgent(train_mode="normal").run(
        {"exports": {"sft_train": str(PROCESSED_DIR / "sft_train.jsonl")}, "sft_records": [{"id": "1"}]}
    )
    normal_state = TrainSimAgent().run(normal_state)

    assert safe_state["train_simulation"]["mode"] == "simulation"
    assert normal_state["train_simulation"]["mode"] == "simulation"
    assert safe_state["train_simulation"]["train_mode"] == "safe"
    assert normal_state["train_simulation"]["train_mode"] == "normal"
    assert len(safe_state["train_simulation"]["epochs"]) == 3
    assert len(normal_state["train_simulation"]["epochs"]) == 3
    assert safe_state["train_simulation"]["epochs"][-1]["train_loss"] == 0.98
    assert normal_state["train_simulation"]["epochs"][-1]["train_loss"] == 0.86
