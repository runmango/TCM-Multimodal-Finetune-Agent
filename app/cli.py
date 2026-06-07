from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from typing import Any, Dict

from app.core.paths import CONFIGS_DIR, PROCESSED_DIR, ROOT_REPORTS_DIR
from app.graphs.dataset_graph import run_dataset_build


TRAIN_MODE_CONFIG_FILES = {
    "safe": "tcm_qwen_safe_lora_sft.yaml",
    "normal": "tcm_qwen_normal_lora_sft.yaml",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TCM multimodal finetune agent CLI")
    subparsers = parser.add_subparsers(dest="command")

    dataset_parser = subparsers.add_parser("dataset", help="Dataset pipeline commands")
    dataset_subparsers = dataset_parser.add_subparsers(dest="dataset_command")
    build_parser_obj = dataset_subparsers.add_parser("build", help="Build datasets and safe demo training artifacts")
    build_parser_obj.add_argument(
        "--train-mode",
        default=None,
        choices=["safe", "normal"],
        help="Training profile used for generated configs. Defaults to normal unless TCM_TRAIN_MODE is set.",
    )

    train_parser = subparsers.add_parser("train", help="Training commands")
    train_subparsers = train_parser.add_subparsers(dest="train_command")
    real_parser = train_subparsers.add_parser("real", help="Prepare or execute real LLaMA-Factory training")
    real_parser.add_argument("--train-mode", default="safe", choices=["safe", "normal"], help="Training profile.")
    real_parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run llamafactory-cli train after all checks pass. Defaults to dry-run.",
    )

    eval_parser = subparsers.add_parser("eval", help="Evaluation commands")
    eval_subparsers = eval_parser.add_subparsers(dest="eval_command")
    eval_run_parser = eval_subparsers.add_parser("run", help="Run simulation/rule evaluation report generation")
    eval_run_parser.add_argument("--train-mode", default="normal", choices=["safe", "normal"], help="Training profile.")
    eval_run_parser.add_argument(
        "--eval-mode",
        default="simulation",
        choices=["simulation", "rule", "real"],
        help="Evaluation mode. Defaults to simulation.",
    )

    digital_parser = subparsers.add_parser("digital-human", help="Digital human demo commands")
    digital_subparsers = digital_parser.add_subparsers(dest="digital_human_command")
    digital_serve_parser = digital_subparsers.add_parser("serve", help="Show or start the digital human backend")
    digital_serve_parser.add_argument(
        "--start",
        action="store_true",
        help="Start uvicorn for app.api.main:app. Without this flag the command only prints startup commands.",
    )
    return parser


def build_real_train_plan(train_mode: str) -> Dict[str, Any]:
    config_file = CONFIGS_DIR / TRAIN_MODE_CONFIG_FILES[train_mode]
    sft_file = PROCESSED_DIR / "sft_train.jsonl"
    dataset_info = PROCESSED_DIR / "dataset_info.json"
    log_file = ROOT_REPORTS_DIR / ("real_train_%s.log" % train_mode)
    command_config = _project_relative(config_file)
    command = ["llamafactory-cli", "train", command_config]
    return {
        "train_mode": train_mode,
        "config_file": config_file,
        "sft_file": sft_file,
        "dataset_info": dataset_info,
        "log_file": log_file,
        "command": command,
        "command_text": " ".join(command),
    }


def _project_relative(path: Any) -> str:
    try:
        return path.resolve().relative_to(CONFIGS_DIR.parent.resolve()).as_posix()
    except ValueError:
        return str(path)


def check_real_train_requirements(plan: Dict[str, Any], require_cuda: bool = True) -> Dict[str, Any]:
    checks = []
    for key, label in [
        ("config_file", "config file"),
        ("sft_file", "sft_train.jsonl"),
        ("dataset_info", "dataset_info.json"),
    ]:
        path = plan[key]
        exists = path.exists()
        checks.append({"name": label, "ok": exists, "status": "OK" if exists else "FAIL", "detail": str(path)})

    cli_path = shutil.which("llamafactory-cli")
    checks.append(
        {
            "name": "llamafactory-cli",
            "ok": cli_path is not None,
            "status": "OK" if cli_path else "FAIL",
            "detail": cli_path or "not found",
        }
    )

    cuda_ok = False
    cuda_detail = "torch not available"
    try:
        import torch

        cuda_ok = bool(torch.cuda.is_available())
        cuda_detail = "torch.cuda.is_available()=%s" % cuda_ok
        if cuda_ok:
            cuda_detail += ", gpu=%s" % torch.cuda.get_device_name(0)
    except Exception as exc:
        cuda_detail = "torch import/check failed: %s" % exc

    if cuda_ok:
        cuda_status = "OK"
        cuda_check_ok = True
    elif require_cuda:
        cuda_status = "FAIL"
        cuda_check_ok = False
    else:
        cuda_status = "WARN"
        cuda_check_ok = True
    checks.append({"name": "CUDA", "ok": cuda_check_ok, "status": cuda_status, "detail": cuda_detail})
    ok = all(check["ok"] for check in checks)
    return {"ok": ok, "checks": checks}


def print_real_train_plan(plan: Dict[str, Any], check_result: Dict[str, Any]) -> None:
    print("train_mode: %s" % plan["train_mode"])
    print("command: %s" % plan["command_text"])
    print("log_file: %s" % plan["log_file"])
    for check in check_result["checks"]:
        prefix = "[%s]" % check.get("status", "OK" if check["ok"] else "FAIL")
        print("%s %s - %s" % (prefix, check["name"], check["detail"]))


def execute_real_train(plan: Dict[str, Any]) -> int:
    ROOT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with plan["log_file"].open("w", encoding="utf-8") as log_obj:
        completed = subprocess.run(
            plan["command"],
            cwd=str(CONFIGS_DIR.parent),
            stdout=log_obj,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    return int(completed.returncode)


def print_digital_human_commands() -> None:
    print("backend: uvicorn app.api.main:app --host 127.0.0.1 --port 8010 --reload")
    print("frontend:")
    print("  cd frontend")
    print("  npm install")
    print("  npm run dev")
    print("browser: http://localhost:5173/digital-human")
    print("api docs: http://127.0.0.1:8010/docs")


def serve_digital_human_backend() -> int:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8010",
        "--reload",
    ]
    return int(subprocess.run(command, check=False).returncode)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "dataset" and args.dataset_command == "build":
        state: Dict[str, Any] = run_dataset_build(train_mode=args.train_mode)
        print("dataset build status: success")
        print("train_mode: %s" % state.get("train_mode"))
        print("train_command: %s" % state.get("train_command"))
        print("report: %s" % state.get("exports", {}).get("root_dataset_report"))
        return

    if args.command == "train" and args.train_command == "real":
        plan = build_real_train_plan(args.train_mode)
        check_result = check_real_train_requirements(plan, require_cuda=args.execute)
        print_real_train_plan(plan, check_result)

        if not args.execute:
            print("dry-run: no real training was started. Add --execute to run after reviewing checks.")
            return

        if not check_result["ok"]:
            print("real training aborted because one or more required checks failed.")
            return

        return_code = execute_real_train(plan)
        print("real training finished with return code: %s" % return_code)
        print("log saved to: %s" % plan["log_file"])
        return

    if args.command == "eval" and args.eval_command == "run":
        state = run_dataset_build(train_mode=args.train_mode, eval_mode=args.eval_mode)
        eval_report = state.get("eval_report", {})
        metrics = eval_report.get("metrics", {})
        print("eval status: success")
        print("train_mode: %s" % eval_report.get("train_mode"))
        print("eval_mode: %s" % eval_report.get("mode"))
        print("eval_report: %s" % state.get("exports", {}).get("eval_report"))
        print("constitution_accuracy: %s" % metrics.get("constitution_accuracy"))
        print("macro_f1: %s" % metrics.get("macro_f1"))
        print("safety_notice_rate: %s" % metrics.get("safety_notice_rate"))
        print("unsafe_advice_rate: %s" % metrics.get("unsafe_advice_rate"))
        return

    if args.command == "digital-human" and args.digital_human_command == "serve":
        print_digital_human_commands()
        if args.start:
            return_code = serve_digital_human_backend()
            print("digital human backend stopped with return code: %s" % return_code)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
