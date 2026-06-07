from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = PROJECT_ROOT / "data" / "external" / "TCM-Dataset-SFT" / "train"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "sft_train.jsonl"
DEFAULT_DATASET_INFO_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_info.json"
DEFAULT_PREPARE_REPORT_PATH = PROJECT_ROOT / "data" / "reports" / "tcm_sft_prepare_report.json"
DEFAULT_INSTRUCTION = "请回答以下中医相关问题，要求表达准确、克制，并避免替代医生诊断。"
REQUIRED_COLUMNS = ["instruction", "input", "output"]
TCM_KEYWORDS = [
    "中医",
    "中药",
    "方剂",
    "药材",
    "本草",
    "炮制",
    "功效",
    "主治",
    "禁忌",
    "伤寒",
    "金匮",
    "黄帝内经",
    "素问",
    "灵枢",
    "针灸",
    "穴位",
    "经络",
    "脉象",
    "舌象",
    "体质",
    "气虚",
    "阳虚",
    "阴虚",
    "痰湿",
    "湿热",
    "血瘀",
    "气郁",
    "特禀",
    "五行",
    "脏腑",
    "经方",
]


def configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def require_pyarrow():
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception as exc:
        raise RuntimeError("pyarrow is required to prepare parquet data. Install it with: pip install pyarrow") from exc
    return pq


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\u0000", " ").strip()
    return " ".join(text.split())


def parquet_files(dataset_dir: Path) -> List[Path]:
    return sorted(dataset_dir.glob("*.parquet"))


def is_abnormal_text(text: str) -> bool:
    if not text:
        return True
    if "�" in text:
        return True
    if len(set(text)) <= 2 and len(text) >= 20:
        return True
    return False


def is_unsafe_clinical_plan(instruction: str, input_text: str, output_text: str) -> bool:
    joined = "\n".join([instruction, input_text, output_text])
    if "治疗方案" in instruction and ("诊断" in instruction or "患者医案" in instruction):
        return True
    if "直接给出" in instruction and ("方剂" in instruction or "中药" in instruction):
        return True
    if "方剂中药组成" in instruction or "中药组成" in instruction:
        return True
    if "病例信息" in input_text and ("方剂" in instruction or "中药" in instruction):
        return True
    treatment_question_terms = ["如何治疗", "怎么治疗", "怎样治疗", "如何医治", "怎么医治", "治法是什么", "治疗效果"]
    formula_terms = ["可用", "宜用", "方用", "煎服", "服用", "内服"]
    formula_suffixes = ["汤", "丸", "散", "膏", "丹", "方"]
    if any(term in input_text for term in treatment_question_terms) and any(term in output_text for term in formula_terms):
        if any(suffix in output_text for suffix in formula_suffixes):
            return True
    if any(term in input_text for term in treatment_question_terms) and output_text.startswith("治"):
        return True
    unsafe_markers = ["诊断:", "诊断：", "证型:", "证型：", "治疗方案:", "治疗方案：", "中药:", "中药："]
    marker_hits = sum(1 for marker in unsafe_markers if marker in joined)
    if marker_hits >= 2:
        return True
    if ("方剂:" in joined or "方剂：" in joined) and ("中药:" in joined or "中药：" in joined):
        return True
    return False


def is_tcm_related(instruction: str, input_text: str, output_text: str) -> bool:
    joined = "\n".join([instruction, input_text, output_text])
    if any(keyword in joined for keyword in TCM_KEYWORDS):
        return True
    title_like_terms = ["汤", "丸", "散", "膏", "丹"]
    return any(term in input_text[:80] for term in title_like_terms) and any(
        marker in joined for marker in ["组成", "炮制", "功效", "主治", "用法", "用量"]
    )


def normalize_record(raw: Dict[str, Any], args: argparse.Namespace) -> Tuple[Dict[str, str] | None, str]:
    raw_instruction = normalize_text(raw.get("instruction"))
    instruction = raw_instruction or DEFAULT_INSTRUCTION
    input_text = normalize_text(raw.get("input"))
    output_text = normalize_text(raw.get("output"))

    if not input_text:
        return None, "empty_input"
    if not output_text:
        return None, "empty_output"
    if len(input_text) < args.min_input_chars:
        return None, "short_input"
    if len(output_text) < args.min_output_chars:
        return None, "short_output"
    if len(input_text) > args.max_input_chars:
        return None, "long_input"
    if len(output_text) > args.max_output_chars:
        return None, "long_output"
    if is_abnormal_text(input_text) or is_abnormal_text(output_text):
        return None, "abnormal_text"
    if input_text == output_text:
        return None, "input_equals_output"
    if not args.allow_clinical_plan and is_unsafe_clinical_plan(instruction, input_text, output_text):
        return None, "unsafe_clinical_plan"
    if not args.disable_tcm_keyword_filter and not is_tcm_related(raw_instruction, input_text, output_text):
        return None, "non_tcm_topic"

    return {"instruction": instruction, "input": input_text, "output": output_text}, ""


def reservoir_sample(samples: List[Dict[str, str]], candidate: Dict[str, str], seen_valid: int, max_rows: int, rng: random.Random) -> None:
    if max_rows <= 0:
        return
    if len(samples) < max_rows:
        samples.append(candidate)
        return
    replace_index = rng.randint(0, seen_valid - 1)
    if replace_index < max_rows:
        samples[replace_index] = candidate


def prepare_records(args: argparse.Namespace) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    pq = require_pyarrow()
    files = parquet_files(Path(args.dataset_dir))
    if not files:
        raise FileNotFoundError("No parquet files found under: %s" % args.dataset_dir)

    rng = random.Random(args.seed)
    selected: List[Dict[str, str]] = []
    raw_rows = 0
    valid_rows = 0
    filtered_counts: Dict[str, int] = {}

    for path in files:
        parquet_file = pq.ParquetFile(path)
        columns = list(parquet_file.schema.names)
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing_columns:
            raise ValueError("%s missing required columns: %s" % (path, missing_columns))

        for batch in parquet_file.iter_batches(batch_size=args.batch_size, columns=REQUIRED_COLUMNS):
            payload = batch.to_pydict()
            row_total = len(payload["input"])
            for index in range(row_total):
                raw_rows += 1
                raw = {column: payload[column][index] for column in REQUIRED_COLUMNS}
                record, reason = normalize_record(raw, args)
                if record is None:
                    filtered_counts[reason] = filtered_counts.get(reason, 0) + 1
                    continue
                valid_rows += 1
                reservoir_sample(selected, record, valid_rows, args.max_rows, rng)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_dir": relative_path(Path(args.dataset_dir)),
        "max_rows": args.max_rows,
        "seed": args.seed,
        "raw_rows": raw_rows,
        "valid_rows": valid_rows,
        "kept_rows": len(selected),
        "filtered_rows": sum(filtered_counts.values()),
        "filtered_counts": filtered_counts,
    }
    return selected, metadata


def backup_existing(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup_path)
    return backup_path


def write_jsonl(path: Path, records: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file_obj:
        for record in records:
            file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")


def update_dataset_info(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
    payload["tcm_sft"] = {
        "file_name": "sft_train.jsonl",
        "formatting": "alpaca",
        "columns": {
            "prompt": "instruction",
            "query": "input",
            "response": "output",
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_prepare_report(path: Path, metadata: Dict[str, Any], output_path: Path, backup_path: Path | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(metadata)
    payload["output_path"] = relative_path(output_path)
    payload["backup_path"] = relative_path(backup_path) if backup_path else None
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relative_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def print_summary(records: List[Dict[str, str]], metadata: Dict[str, Any], output_path: Path, backup_path: Path | None) -> None:
    print("raw_rows: %s" % metadata["raw_rows"])
    print("valid_rows: %s" % metadata["valid_rows"])
    print("kept_rows: %s" % metadata["kept_rows"])
    print("filtered_rows: %s" % metadata["filtered_rows"])
    print("filtered_counts: %s" % json.dumps(metadata["filtered_counts"], ensure_ascii=False))
    if backup_path:
        print("backup_path: %s" % backup_path)
    print("output_path: %s" % output_path)
    print()
    print("preview:")
    for index, record in enumerate(records[:3], start=1):
        print("[%s] instruction=%s" % (index, record["instruction"][:120]))
        print("    input=%s" % record["input"][:160])
        print("    output=%s" % record["output"][:160])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare external TCM SFT parquet dataset as Alpaca JSONL.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR), help="Directory containing train/*.parquet files.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Output Alpaca JSONL path.")
    parser.add_argument("--dataset-info", default=str(DEFAULT_DATASET_INFO_PATH), help="LLaMA-Factory dataset_info.json path.")
    parser.add_argument("--prepare-report", default=str(DEFAULT_PREPARE_REPORT_PATH), help="Preparation report JSON path.")
    parser.add_argument("--max-rows", type=int, default=1000, help="Maximum sampled rows to write.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reservoir sampling.")
    parser.add_argument("--batch-size", type=int, default=50_000, help="Parquet scan batch size.")
    parser.add_argument("--min-input-chars", type=int, default=4, help="Filter inputs shorter than this length.")
    parser.add_argument("--min-output-chars", type=int, default=10, help="Filter outputs shorter than this length.")
    parser.add_argument("--max-input-chars", type=int, default=2000, help="Filter overly long inputs.")
    parser.add_argument("--max-output-chars", type=int, default=6000, help="Filter overly long outputs.")
    parser.add_argument(
        "--allow-clinical-plan",
        action="store_true",
        help="Keep samples that ask for diagnosis/prescription plans. Defaults to filtering them for safety.",
    )
    parser.add_argument(
        "--disable-tcm-keyword-filter",
        action="store_true",
        help="Keep non-TCM topics. Defaults to filtering obvious ancient-text/general-domain samples.",
    )
    return parser


def main() -> int:
    configure_stdout()
    args = build_parser().parse_args()
    if args.max_rows <= 0:
        raise ValueError("--max-rows must be positive.")

    output_path = Path(args.output)
    records, metadata = prepare_records(args)
    backup_path = backup_existing(output_path)
    write_jsonl(output_path, records)
    update_dataset_info(Path(args.dataset_info))
    write_prepare_report(Path(args.prepare_report), metadata, output_path, backup_path)
    print_summary(records, metadata, output_path, backup_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
