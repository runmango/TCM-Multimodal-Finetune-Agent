from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = PROJECT_ROOT / "data" / "external" / "TCM-Dataset-SFT" / "train"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "data" / "reports" / "dataset_report.json"
REQUIRED_COLUMNS = ["instruction", "input", "output"]


def configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def require_pyarrow():
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception as exc:
        raise RuntimeError("pyarrow is required to inspect parquet files. Install it with: pip install pyarrow") from exc
    return pq


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def text_stats(lengths: List[int]) -> Dict[str, Any]:
    if not lengths:
        return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0}
    ordered = sorted(lengths)
    return {
        "count": len(lengths),
        "min": ordered[0],
        "max": ordered[-1],
        "avg": round(mean(lengths), 2),
        "p50": percentile(ordered, 0.5),
        "p95": percentile(ordered, 0.95),
    }


def percentile(ordered: List[int], ratio: float) -> int:
    if not ordered:
        return 0
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * ratio))))
    return ordered[index]


def parquet_files(dataset_dir: Path) -> List[Path]:
    return sorted(dataset_dir.glob("*.parquet"))


def reservoir_sample(samples: List[Dict[str, str]], candidate: Dict[str, str], seen: int, sample_size: int, rng: random.Random) -> None:
    if sample_size <= 0:
        return
    if len(samples) < sample_size:
        samples.append(candidate)
        return
    replace_index = rng.randint(0, seen - 1)
    if replace_index < sample_size:
        samples[replace_index] = candidate


def inspect_dataset(dataset_dir: Path, batch_size: int, sample_size: int, seed: int) -> Dict[str, Any]:
    pq = require_pyarrow()
    files = parquet_files(dataset_dir)
    if not files:
        raise FileNotFoundError("No parquet files found under: %s" % dataset_dir)

    rng = random.Random(seed)
    file_reports: List[Dict[str, Any]] = []
    total_rows = 0
    empty_counts = {column: 0 for column in REQUIRED_COLUMNS}
    input_lengths: List[int] = []
    output_lengths: List[int] = []
    samples: List[Dict[str, str]] = []
    seen_rows = 0

    for path in files:
        parquet_file = pq.ParquetFile(path)
        columns = list(parquet_file.schema.names)
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
        row_count = int(parquet_file.metadata.num_rows) if parquet_file.metadata else 0
        total_rows += row_count
        file_empty_counts = {column: 0 for column in REQUIRED_COLUMNS}

        if missing_columns:
            file_reports.append(
                {
                    "file": relative_path(path),
                    "rows": row_count,
                    "columns": columns,
                    "missing_columns": missing_columns,
                    "empty_counts": file_empty_counts,
                }
            )
            continue

        for batch in parquet_file.iter_batches(batch_size=batch_size, columns=REQUIRED_COLUMNS):
            payload = batch.to_pydict()
            row_total = len(payload["input"])
            for index in range(row_total):
                row = {column: normalize_text(payload[column][index]) for column in REQUIRED_COLUMNS}
                seen_rows += 1
                for column in REQUIRED_COLUMNS:
                    if not row[column]:
                        empty_counts[column] += 1
                        file_empty_counts[column] += 1
                input_lengths.append(len(row["input"]))
                output_lengths.append(len(row["output"]))
                reservoir_sample(samples, row, seen_rows, sample_size, rng)

        file_reports.append(
            {
                "file": relative_path(path),
                "rows": row_count,
                "columns": columns,
                "missing_columns": missing_columns,
                "empty_counts": file_empty_counts,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_dir": relative_path(dataset_dir),
        "required_columns": REQUIRED_COLUMNS,
        "files": file_reports,
        "total_rows": total_rows,
        "scanned_rows": seen_rows,
        "empty_counts": empty_counts,
        "input_length": text_stats(input_lengths),
        "output_length": text_stats(output_lengths),
        "samples": samples,
    }


def merge_report(report_path: Path, inspection: Dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    existing: Dict[str, Any] = {}
    if report_path.exists():
        try:
            existing = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing["external_tcm_sft_inspection"] = inspection
    report_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def print_report(report: Dict[str, Any]) -> None:
    print("dataset_dir: %s" % report["dataset_dir"])
    print("total_rows: %s" % report["total_rows"])
    print("scanned_rows: %s" % report["scanned_rows"])
    print("empty_counts: %s" % json.dumps(report["empty_counts"], ensure_ascii=False))
    print("input_length: %s" % json.dumps(report["input_length"], ensure_ascii=False))
    print("output_length: %s" % json.dumps(report["output_length"], ensure_ascii=False))
    print()
    for file_report in report["files"]:
        print("file: {file}, rows: {rows}, columns: {columns}".format(**file_report))
        if file_report["missing_columns"]:
            print("  missing_columns: %s" % file_report["missing_columns"])
        print("  empty_counts: %s" % json.dumps(file_report["empty_counts"], ensure_ascii=False))
    print()
    print("random_samples:")
    for index, sample in enumerate(report["samples"], start=1):
        print("[%s] instruction=%s" % (index, sample["instruction"][:120]))
        print("    input=%s" % sample["input"][:160])
        print("    output=%s" % sample["output"][:160])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect external TCM SFT parquet dataset.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR), help="Directory containing train/*.parquet files.")
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH), help="Path to merged dataset report JSON.")
    parser.add_argument("--batch-size", type=int, default=50_000, help="Parquet scan batch size.")
    parser.add_argument("--sample-size", type=int, default=5, help="Number of random samples to print and save.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sample preview.")
    return parser


def main() -> int:
    configure_stdout()
    args = build_parser().parse_args()
    report = inspect_dataset(Path(args.dataset_dir), batch_size=args.batch_size, sample_size=args.sample_size, seed=args.seed)
    merge_report(Path(args.report_path), report)
    print_report(report)
    print()
    print("report_saved_to: %s" % Path(args.report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
