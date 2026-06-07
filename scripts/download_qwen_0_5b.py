from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
TEST_PROMPT = "请用一句话解释什么是中医体质辨识。"


@dataclass
class DownloadPlan:
    model_name: str
    hf_home: Optional[str]
    hf_endpoint: Optional[str]
    dry_run: bool


def build_download_plan(dry_run: bool = False) -> DownloadPlan:
    return DownloadPlan(
        model_name=MODEL_NAME,
        hf_home=os.getenv("HF_HOME"),
        hf_endpoint=os.getenv("HF_ENDPOINT"),
        dry_run=dry_run,
    )


def download_and_smoke_test(dry_run: bool = False) -> bool:
    plan = build_download_plan(dry_run=dry_run)
    print("model: %s" % plan.model_name)
    print("HF_HOME: %s" % (plan.hf_home or "default Hugging Face cache"))
    print("HF_ENDPOINT: %s" % (plan.hf_endpoint or "default"))

    if dry_run:
        print("[OK] dry-run only; model download skipped.")
        return True

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        print("[FAIL] transformers/torch import failed: %s" % exc)
        print("Install dependencies in the training environment before downloading.")
        return False

    try:
        tokenizer = AutoTokenizer.from_pretrained(plan.model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            plan.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        inputs = tokenizer(TEST_PROMPT, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {key: value.to(model.device) for key, value in inputs.items()}
        output_ids = model.generate(**inputs, max_new_tokens=48)
        print(tokenizer.decode(output_ids[0], skip_special_tokens=True))
        print("注意：该结果仅用于健康科普演示，不替代医生诊疗。")
        return True
    except Exception as exc:
        print("[FAIL] model download or smoke test failed: %s" % exc)
        print("Common causes: Hugging Face network access, proxy settings, disk space, or old transformers version.")
        print('Optional mirror example: $env:HF_ENDPOINT="https://hf-mirror.com"')
        return False


def main() -> int:
    return 0 if download_and_smoke_test(dry_run=False) else 1


if __name__ == "__main__":
    raise SystemExit(main())

