from __future__ import annotations

from pathlib import Path
from typing import Tuple


BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER_DIR = Path("outputs/tcm_qwen_0_5b_lora")
PROMPT = "症状：乏力、气短、舌淡有齿痕，请判断中医体质倾向，并给出非诊疗建议。"
DISCLAIMER = "注意：该结果仅用于健康科普演示，不替代医生诊疗。"


def check_adapter(adapter_dir: Path = ADAPTER_DIR) -> Tuple[bool, str]:
    if not adapter_dir.exists():
        return False, "adapter 目录不存在，请先执行真实训练命令：llamafactory-cli train configs/tcm_qwen_safe_lora_sft.yaml"
    expected_files = ["adapter_config.json", "adapter_model.safetensors"]
    existing = [name for name in expected_files if (adapter_dir / name).exists()]
    if not existing:
        return False, "未找到 adapter 文件，请确认训练是否完成，或检查 LLaMA-Factory 实际输出文件名。"
    return True, "adapter looks available."


def run_lora_inference(adapter_dir: Path = ADAPTER_DIR) -> bool:
    ok, message = check_adapter(adapter_dir)
    if not ok:
        print("[WARN] %s" % message)
        return False

    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        print("[FAIL] transformers/peft/torch import failed: %s" % exc)
        return False

    try:
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        model = PeftModel.from_pretrained(model, str(adapter_dir))
        inputs = tokenizer(PROMPT, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {key: value.to(model.device) for key, value in inputs.items()}
        output_ids = model.generate(**inputs, max_new_tokens=120)
        print(tokenizer.decode(output_ids[0], skip_special_tokens=True))
        print(DISCLAIMER)
        return True
    except Exception as exc:
        print("[FAIL] LoRA inference failed: %s" % exc)
        return False


def main() -> int:
    return 0 if run_lora_inference() else 1


if __name__ == "__main__":
    raise SystemExit(main())

