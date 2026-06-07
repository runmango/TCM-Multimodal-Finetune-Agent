from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CheckResult:
    name: str
    status: str
    message: str


def check_python() -> CheckResult:
    version = sys.version.split()[0]
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 10:
        return CheckResult("Python", "OK", "Python %s" % version)
    return CheckResult("Python", "WARN", "Python %s detected; Python 3.10+ is recommended." % version)


def check_import(package: str) -> CheckResult:
    spec = importlib.util.find_spec(package)
    if spec is None:
        return CheckResult(package, "FAIL", "%s is not installed." % package)
    return CheckResult(package, "OK", "%s import is available." % package)


def check_torch() -> List[CheckResult]:
    spec = importlib.util.find_spec("torch")
    if spec is None:
        return [
            CheckResult("torch", "FAIL", "torch is not installed. Install PyTorch GPU build first."),
            CheckResult("CUDA", "FAIL", "CUDA check skipped because torch is missing."),
        ]

    import torch

    results = [CheckResult("torch", "OK", "torch version: %s" % torch.__version__)]
    cuda_available = torch.cuda.is_available()
    cuda_version = getattr(torch.version, "cuda", None)
    if not cuda_available:
        results.append(
            CheckResult(
                "CUDA",
                "FAIL",
                "torch.cuda.is_available() is False. Check NVIDIA driver, CUDA-compatible PyTorch, and GPU visibility.",
            )
        )
        results.append(CheckResult("torch CUDA", "WARN", "torch CUDA version: %s" % (cuda_version or "unknown")))
        return results

    gpu_name = torch.cuda.get_device_name(0)
    total_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    results.append(CheckResult("CUDA", "OK", "CUDA available: True; torch CUDA version: %s" % cuda_version))
    results.append(CheckResult("GPU", "OK", "%s, %.2f GB VRAM" % (gpu_name, total_memory_gb)))
    return results


def check_llamafactory_cli() -> CheckResult:
    executable = shutil.which("llamafactory-cli")
    if executable is None:
        return CheckResult(
            "llamafactory-cli",
            "FAIL",
            'llamafactory-cli not found. Try: pip install -U "llamafactory[torch,metrics]"',
        )

    try:
        completed = subprocess.run(
            [executable, "--help"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return CheckResult("llamafactory-cli", "FAIL", "Failed to run --help: %s" % exc)

    if completed.returncode == 0:
        return CheckResult("llamafactory-cli", "OK", "llamafactory-cli is available: %s" % executable)
    return CheckResult("llamafactory-cli", "WARN", "llamafactory-cli returned code %s" % completed.returncode)


def collect_results() -> List[CheckResult]:
    results = [check_python()]
    results.extend(check_torch())
    for package in ["transformers", "datasets", "peft", "accelerate", "trl"]:
        results.append(check_import(package))
    results.append(check_llamafactory_cli())
    return results


def format_result(result: CheckResult) -> str:
    return "[%s] %s - %s" % (result.status, result.name, result.message)


def has_failures(results: List[CheckResult]) -> bool:
    return any(result.status == "FAIL" for result in results)


def main() -> int:
    results = collect_results()
    for result in results:
        print(format_result(result))

    if has_failures(results):
        print()
        print("Next steps:")
        print("1. Confirm NVIDIA driver with: nvidia-smi")
        print("2. Install PyTorch from the official selector: https://pytorch.org/get-started/locally/")
        print('3. Install LLaMA-Factory: pip install -U "llamafactory[torch,metrics]"')
        print("4. Re-run: python scripts/check_train_env.py")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

