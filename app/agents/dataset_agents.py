from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.core.paths import (
    CONFIGS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
    REPORTS_DIR,
    ROOT_REPORTS_DIR,
    ensure_output_dirs,
)
from app.utils.io import normalize_text, read_jsonl, write_json, write_jsonl


TRAIN_MODE_PROFILES: Dict[str, Dict[str, Any]] = {
    "safe": {
        "mode": "safe",
        "profile_name": "safe_low_vram_demo",
        "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
        "output_dir": OUTPUTS_DIR / "tcm_qwen_0_5b_lora",
        "yaml_name": "tcm_qwen_safe_lora_sft.yaml",
        "json_name": "tcm_qwen_safe_lora_sft.json",
        "cutoff_len": 1024,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "learning_rate": 1e-4,
        "num_train_epochs": 3,
        "logging_steps": 1,
        "save_steps": 20,
        "hardware_hint": "safe模式，模型参数0.5B",
        "losses": [1.95, 1.36, 0.98],
        "simulated_eval_score": {"high": 0.58, "medium": 0.68, "low": 0.78},
    },
    "normal": {
        "mode": "normal",
        "profile_name": "normal_8gb_gpu_demo",
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "output_dir": OUTPUTS_DIR / "tcm_qwen_1_5b_lora",
        "yaml_name": "tcm_qwen_normal_lora_sft.yaml",
        "json_name": "tcm_qwen_normal_lora_sft.json",
        "cutoff_len": 1024,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "learning_rate": 1e-4,
        "num_train_epochs": 3,
        "logging_steps": 10,
        "save_steps": 100,
        "hardware_hint": "normal模式，模型参数1.5B",
        "losses": [1.82, 1.21, 0.86],
        "simulated_eval_score": {"high": 0.62, "medium": 0.74, "low": 0.84},
    },
}


class DataLoadAgent:
    """Load all raw jsonl demo records from data/raw."""

    def __init__(self, raw_dir: Path = RAW_DIR) -> None:
        self.raw_dir = raw_dir

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        records: List[Dict[str, Any]] = []
        source_counts: Dict[str, int] = {}

        for path in sorted(self.raw_dir.glob("*.jsonl")):
            items = read_jsonl(path)
            source_counts[path.name] = len(items)
            for item in items:
                enriched = dict(item)
                enriched["_source_file"] = path.name
                records.append(enriched)

        state.update({"raw_records": records, "source_counts": source_counts})
        return state


class CleanAgent:
    """Normalize text fields and remove duplicate ids."""

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        seen_ids = set()
        cleaned: List[Dict[str, Any]] = []
        duplicate_ids: List[str] = []

        for index, record in enumerate(state.get("raw_records", []), start=1):
            item = self._clean_value(record)
            record_id = item.get("id") or "auto_%03d" % index
            item["id"] = record_id

            if record_id in seen_ids:
                duplicate_ids.append(record_id)
                continue
            seen_ids.add(record_id)
            cleaned.append(item)

        state.update(
            {
                "clean_records": cleaned,
                "clean_stats": {
                    "input_records": len(state.get("raw_records", [])),
                    "output_records": len(cleaned),
                    "duplicate_ids": duplicate_ids,
                },
            }
        )
        return state

    def _clean_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return normalize_text(value)
        if isinstance(value, list):
            return [self._clean_value(item) for item in value if item not in ("", None)]
        if isinstance(value, dict):
            return {key: self._clean_value(item) for key, item in value.items() if item is not None}
        return value


class SchemaAgent:
    """Validate the small demo schema for each record type."""

    REQUIRED_FIELDS = {
        "knowledge": ["id", "type", "title", "content"],
        "constitution_case": ["id", "type", "symptoms", "constitution", "advice"],
        "tongue_image": ["id", "type", "image", "image_description", "constitution"],
    }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        valid_records: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for record in state.get("clean_records", []):
            record_type = record.get("type")
            required = self.REQUIRED_FIELDS.get(record_type)
            if not required:
                errors.append({"id": record.get("id"), "error": "unsupported type: %s" % record_type})
                continue

            missing = [field for field in required if not record.get(field)]
            if missing:
                errors.append({"id": record.get("id"), "error": "missing fields", "fields": missing})
                continue

            valid_records.append(record)

        state.update({"valid_records": valid_records, "schema_errors": errors})
        return state


class QualityScoreAgent:
    """Attach lightweight quality scores used in the dataset report."""

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        quality_records: List[Dict[str, Any]] = []
        score_rows: List[Dict[str, Any]] = []

        for record in state.get("valid_records", []):
            score, issues = self._score(record)
            item = dict(record)
            item["quality_score"] = score
            quality_records.append(item)
            score_rows.append({"id": record["id"], "type": record["type"], "score": score, "issues": issues})

        average = round(sum(row["score"] for row in score_rows) / len(score_rows), 3) if score_rows else 0.0
        state.update(
            {
                "quality_records": quality_records,
                "quality_scores": score_rows,
                "average_quality_score": average,
            }
        )
        return state

    def _score(self, record: Dict[str, Any]) -> Tuple[float, List[str]]:
        score = 1.0
        issues: List[str] = []

        text_blob = " ".join(str(record.get(field, "")) for field in ("title", "content", "advice", "image_description"))
        if len(text_blob) < 20:
            score -= 0.25
            issues.append("text_too_short")

        if record.get("type") == "knowledge" and not record.get("tags"):
            score -= 0.1
            issues.append("missing_tags")

        if record.get("type") == "tongue_image" and not record.get("image_description"):
            score -= 0.4
            issues.append("missing_image_description")

        return max(round(score, 3), 0.0), issues


class SFTBuildAgent:
    """Build text SFT records from knowledge and constitution cases."""

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        sft_records: List[Dict[str, Any]] = []

        for record in state.get("quality_records", []):
            if record["type"] == "knowledge":
                sft_records.append(
                    {
                        "id": "sft_%s" % record["id"],
                        "instruction": "请基于中医知识回答以下问题。",
                        "input": "%s的核心辨识与调养要点是什么？" % record["title"],
                        "output": "%s：%s" % (record["title"], record["content"]),
                        "meta": {
                            "source_id": record["id"],
                            "source_type": record["type"],
                            "quality_score": record.get("quality_score", 0.0),
                        },
                    }
                )
            elif record["type"] == "constitution_case":
                symptoms = "、".join(record.get("symptoms", []))
                sft_records.append(
                    {
                        "id": "sft_%s" % record["id"],
                        "instruction": "请根据症状进行中医体质倾向辨识，并给出非诊疗性质的调养建议。",
                        "input": "症状：%s" % symptoms,
                        "output": "体质倾向：%s。参考建议：%s" % (record["constitution"], record["advice"]),
                        "meta": {
                            "source_id": record["id"],
                            "source_type": record["type"],
                            "quality_score": record.get("quality_score", 0.0),
                        },
                    }
                )

        state["sft_records"] = sft_records
        return state


class MMBuildAgent:
    """Build multimodal SFT records from tongue image examples."""

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        mm_records: List[Dict[str, Any]] = []

        for record in state.get("quality_records", []):
            if record["type"] != "tongue_image":
                continue

            symptoms = "、".join(record.get("symptoms", []))
            prompt = "请结合舌象图片与描述，判断中医体质倾向。描述：%s。伴随表现：%s。" % (
                record["image_description"],
                symptoms or "未提供",
            )
            answer = "体质倾向：%s。依据：%s。建议仅作健康科普参考。" % (
                record["constitution"],
                record["image_description"],
            )

            mm_records.append(
                {
                    "id": "mm_%s" % record["id"],
                    "image": record["image"],
                    "image_description": record["image_description"],
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image", "image": record["image"]},
                                {"type": "text", "text": prompt},
                            ],
                        },
                        {"role": "assistant", "content": answer},
                    ],
                    "meta": {
                        "source_id": record["id"],
                        "source_type": record["type"],
                        "quality_score": record.get("quality_score", 0.0),
                    },
                }
            )

        state["mm_sft_records"] = mm_records
        return state


class DatasetRegistryAgent:
    """Generate a LLaMA-Factory dataset registry for the processed SFT dataset."""

    def __init__(self, processed_dir: Path = PROCESSED_DIR) -> None:
        self.processed_dir = processed_dir

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ensure_output_dirs()
        dataset_info_path = self.processed_dir / "dataset_info.json"
        registry = {
            "tcm_sft": {
                "file_name": "sft_train.jsonl",
                "formatting": "alpaca",
                "columns": {
                    "prompt": "instruction",
                    "query": "input",
                    "response": "output",
                },
            }
        }

        write_json(dataset_info_path, registry)
        exports = dict(state.get("exports", {}))
        exports["dataset_info"] = str(dataset_info_path)
        state.update({"dataset_registry": registry, "exports": exports})
        return state


class TrainConfigAgent:
    """Generate safe demo LoRA/QLoRA-ready fine-tuning configuration files."""

    DEFAULT_MODE = "normal"

    def __init__(self, train_mode: str = "normal", configs_dir: Path = CONFIGS_DIR) -> None:
        self.train_mode = train_mode
        self.configs_dir = configs_dir

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ensure_output_dirs()
        self.configs_dir.mkdir(parents=True, exist_ok=True)

        mode = self._resolve_mode(state)
        profile = TRAIN_MODE_PROFILES[mode]
        output_dir = Path(profile["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        sft_path = self._resolve_train_file(state)
        yaml_path = self.configs_dir / str(profile["yaml_name"])
        json_path = self.configs_dir / str(profile["json_name"])
        base_model = self._resolve_base_model(profile=profile, json_path=json_path)
        config = {
            "stage": "sft",
            "do_train": True,
            "model_name_or_path": base_model,
            "trust_remote_code": True,
            "dataset": "tcm_sft",
            "dataset_dir": relative_path(PROCESSED_DIR),
            "template": "qwen",
            "finetuning_type": "lora",
            "lora_rank": 8,
            "lora_alpha": 16,
            "lora_dropout": 0.05,
            "lora_target": "all",
            "output_dir": relative_path(output_dir),
            "num_train_epochs": profile["num_train_epochs"],
            "per_device_train_batch_size": profile["per_device_train_batch_size"],
            "gradient_accumulation_steps": profile["gradient_accumulation_steps"],
            "learning_rate": profile["learning_rate"],
            "cutoff_len": profile["cutoff_len"],
            "max_samples": 1000,
            "preprocessing_num_workers": 4,
            "dataloader_num_workers": 0,
            "overwrite_output_dir": True,
            "save_only_model": False,
            "plot_loss": True,
            "fp16": True,
            "lr_scheduler_type": "cosine",
            "warmup_ratio": 0.1,
            "logging_steps": profile["logging_steps"],
            "save_steps": profile["save_steps"],
            "report_to": "none",
        }
        metadata = {
            "train_mode": mode,
            "profile_name": profile["profile_name"],
            "train_file": relative_path(sft_path),
            "hardware_hint": profile["hardware_hint"],
            "notes": "Safe demo config only. Use LLaMA-Factory/MS-SWIFT/Transformers+PEFT for real training.",
        }

        self._write_yaml(yaml_path, config)
        write_json(json_path, config)

        exports = dict(state.get("exports", {}))
        exports.update(
            {
                "train_config_yaml": str(yaml_path),
                "train_config_json": str(json_path),
                "adapter_output_dir": str(output_dir),
            }
        )
        state.update(
            {
                "train_mode": mode,
                "train_config": {
                    "mode": mode,
                    "profile_name": profile["profile_name"],
                    "base_model": base_model,
                    "config": config,
                    "metadata": metadata,
                    "yaml_path": str(yaml_path),
                    "json_path": str(json_path),
                    "output_dir": str(output_dir),
                    "hardware_hint": profile["hardware_hint"],
                },
                "exports": exports,
            }
        )
        return state

    def _resolve_mode(self, state: Dict[str, Any]) -> str:
        candidates = [
            self.train_mode,
            os.getenv("TCM_TRAIN_MODE"),
            state.get("train_mode"),
            self.DEFAULT_MODE,
        ]
        for candidate in candidates:
            if candidate is None:
                continue
            mode = str(candidate).strip().lower()
            if not mode:
                continue
            if mode in TRAIN_MODE_PROFILES:
                return mode
            warnings = list(state.get("warnings", []))
            warnings.append("Invalid train_mode '%s', fallback to safe." % candidate)
            state["warnings"] = warnings
            return "safe"
        return self.DEFAULT_MODE

    def _resolve_train_file(self, state: Dict[str, Any]) -> Path:
        exports = state.get("exports", {})
        train_file = exports.get("sft_train") or exports.get("train_file")
        return Path(train_file) if train_file else PROCESSED_DIR / "sft_train.jsonl"

    def _resolve_base_model(self, profile: Dict[str, Any], json_path: Path) -> str:
        env_model = os.getenv("TCM_BASE_MODEL") or os.getenv("MODEL_NAME_OR_PATH")
        if env_model:
            return env_model

        if json_path.exists():
            try:
                import json

                with json_path.open("r", encoding="utf-8") as file_obj:
                    payload = json.load(file_obj)
                model = payload.get("model_name_or_path")
                if model:
                    return str(model)
            except Exception:
                pass

        return str(profile["base_model"])

    def _write_yaml(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import yaml  # type: ignore

            with path.open("w", encoding="utf-8") as file_obj:
                yaml.safe_dump(payload, file_obj, allow_unicode=True, sort_keys=False)
        except Exception:
            with path.open("w", encoding="utf-8") as file_obj:
                file_obj.write(simple_yaml_dump(payload))


class TrainCommandAgent:
    """Generate fine-tuning commands without running real training."""

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        train_config = state.get("train_config", {})
        mode = train_config.get("mode") or state.get("train_mode") or TrainConfigAgent.DEFAULT_MODE
        profile = TRAIN_MODE_PROFILES.get(str(mode), TRAIN_MODE_PROFILES["safe"])
        yaml_path = train_config.get("yaml_path") or str(CONFIGS_DIR / str(profile["yaml_name"]))
        output_dir = train_config.get("output_dir") or str(profile["output_dir"])
        command = "llamafactory-cli train %s" % relative_path(Path(yaml_path))
        dry_run_note = (
            "当前命令仅用于演示，不会自动执行。真实训练需要确认 GPU 显存、CUDA/PyTorch 环境、"
            "模型权重下载、训练框架安装和数据合规性。"
        )
        train_commands = {
            "mode": str(mode),
            "llamafactory_train": command,
            "dry_run_note": dry_run_note,
            "output_dir": output_dir,
            "adapter_dir": output_dir,
            "hardware_hint": train_config.get("hardware_hint") or profile["hardware_hint"],
        }

        state.update({"train_command": command, "train_commands": train_commands})
        return state


class TrainSimAgent:
    """Simulate a LoRA training run and export clearly labeled simulation reports."""

    def __init__(self, reports_dir: Path = ROOT_REPORTS_DIR) -> None:
        self.reports_dir = reports_dir

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ensure_output_dirs()
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        train_config = state.get("train_config", {})
        config = train_config.get("config", {})
        train_mode = str(train_config.get("mode") or state.get("train_mode") or TrainConfigAgent.DEFAULT_MODE)
        profile = TRAIN_MODE_PROFILES.get(train_mode, TRAIN_MODE_PROFILES["safe"])
        total_samples = len(state.get("sft_records", []))
        base_model = train_config.get("base_model") or config.get("model_name_or_path") or profile["base_model"]
        output_dir = train_config.get("output_dir") or config.get("output_dir") or str(profile["output_dir"])
        epochs = [{"epoch": index, "train_loss": loss} for index, loss in enumerate(profile["losses"], start=1)]
        overfit_risk = self._risk_level(total_samples)
        simulation = {
            "mode": "simulation",
            "train_mode": train_mode,
            "profile_name": profile["profile_name"],
            "status": "success",
            "total_samples": total_samples,
            "trainable_method": "LoRA",
            "base_model": base_model,
            "hardware_hint": train_config.get("hardware_hint") or profile["hardware_hint"],
            "output_dir": output_dir,
            "epochs": epochs,
            "final_metrics": {
                "final_train_loss": epochs[-1]["train_loss"],
                "simulated_eval_score": self._eval_score(total_samples, profile),
                "simulated_overfit_risk": overfit_risk,
            },
            "note": "This is a simulation report for demo only. It does not represent real model training.",
        }

        report_path = self.reports_dir / "train_simulation_report.json"
        loss_path = self.reports_dir / "train_loss.csv"
        write_json(report_path, simulation)
        self._write_loss_csv(loss_path, epochs)

        exports = dict(state.get("exports", {}))
        exports.update({"train_simulation_report": str(report_path), "train_loss_csv": str(loss_path)})
        state.update({"train_simulation": simulation, "exports": exports})
        return state

    def _risk_level(self, total_samples: int) -> str:
        if total_samples < 20:
            return "high"
        if total_samples < 100:
            return "medium"
        return "low"

    def _eval_score(self, total_samples: int, profile: Dict[str, Any]) -> float:
        scores = profile["simulated_eval_score"]
        if total_samples < 20:
            return scores["high"]
        if total_samples < 100:
            return scores["medium"]
        return scores["low"]

    def _write_loss_csv(self, path: Path, epochs: List[Dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=["epoch", "train_loss"])
            writer.writeheader()
            writer.writerows(epochs)


class ExportAgent:
    """Persist processed datasets and a compact dataset governance report."""

    def __init__(self, processed_dir: Path = PROCESSED_DIR, reports_dir: Path = REPORTS_DIR) -> None:
        self.processed_dir = processed_dir
        self.reports_dir = reports_dir

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ensure_output_dirs()
        sft_path = self.processed_dir / "sft_train.jsonl"
        mm_path = self.processed_dir / "mm_sft_train.jsonl"
        report_path = self.reports_dir / "dataset_report.json"
        root_report_path = ROOT_REPORTS_DIR / "dataset_report.json"

        write_jsonl(sft_path, state.get("sft_records", []))
        write_jsonl(mm_path, state.get("mm_sft_records", []))
        exports = dict(state.get("exports", {}))
        exports.update(
            {
                "sft_train": str(sft_path),
                "mm_sft_train": str(mm_path),
            }
        )

        training = self._build_training_report(state, exports)

        report = {
            "build_time": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "raw_records": len(state.get("raw_records", [])),
                "clean_records": len(state.get("clean_records", [])),
                "valid_records": len(state.get("valid_records", [])),
                "schema_errors": len(state.get("schema_errors", [])),
                "sft_records": len(state.get("sft_records", [])),
                "mm_sft_records": len(state.get("mm_sft_records", [])),
                "average_quality_score": state.get("average_quality_score", 0.0),
            },
            "source_counts": state.get("source_counts", {}),
            "clean_stats": state.get("clean_stats", {}),
            "schema_errors": state.get("schema_errors", []),
            "quality": state.get("quality_scores", []),
            "training": training,
            "evaluation": self._build_evaluation_report(state),
            "exports": exports,
        }
        write_json(report_path, report)
        write_json(root_report_path, report)

        state.update(
            {
                "report": report,
                "exports": {**exports, "dataset_report": str(report_path), "root_dataset_report": str(root_report_path)},
            }
        )
        return state

    def _build_training_report(self, state: Dict[str, Any], exports: Dict[str, str]) -> Dict[str, Any]:
        train_config = state.get("train_config", {})
        config = train_config.get("config", {})
        train_commands = state.get("train_commands", {})
        return {
            "mode": train_config.get("mode"),
            "profile_name": train_config.get("profile_name"),
            "hardware_hint": train_config.get("hardware_hint"),
            "base_model": train_config.get("base_model") or config.get("model_name_or_path"),
            "finetuning_type": config.get("finetuning_type", "lora"),
            "train_file": exports.get("sft_train"),
            "config_file": train_config.get("yaml_path") or exports.get("train_config_yaml"),
            "train_command": state.get("train_command") or train_commands.get("llamafactory_train"),
            "output_dir": train_config.get("output_dir") or train_commands.get("output_dir"),
            "simulation_report": exports.get("train_simulation_report"),
            "warning": (
                "当前 Demo 部署环境支持两种模式，safe 模式使用 0.5B 模型，normal 模式使用 1.5B 模型。"
                "真实训练需要安装 LLaMA-Factory/MS-SWIFT/Transformers+PEFT，并准备可用 GPU 环境。"
            ),
        }

    def _build_evaluation_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        eval_report = state.get("eval_report")
        if not eval_report:
            return {"status": "skipped"}
        metrics = eval_report.get("metrics", {})
        return {
            "eval_report": state.get("exports", {}).get("eval_report"),
            "eval_mode": eval_report.get("mode"),
            "eval_set_size": eval_report.get("eval_set_size"),
            "constitution_accuracy": metrics.get("constitution_accuracy"),
            "macro_f1": metrics.get("macro_f1"),
            "safety_notice_rate": metrics.get("safety_notice_rate"),
            "unsafe_advice_rate": metrics.get("unsafe_advice_rate"),
            "hallucination_rate": metrics.get("hallucination_rate"),
        }


def simple_yaml_dump(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    for key, value in payload.items():
        lines.append("%s: %s" % (key, _yaml_scalar(value)))
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    text = str(value)
    if text == "" or any(char in text for char in [":", "#", "{", "}", "[", "]", ","]):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)
