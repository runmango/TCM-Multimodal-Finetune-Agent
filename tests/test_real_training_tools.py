from pathlib import Path

from app import cli
from scripts import check_train_env, download_qwen_0_5b, test_lora_inference


def test_check_train_env_importable_without_gpu():
    results = check_train_env.collect_results()

    assert results
    assert any(result.name == "Python" for result in results)


def test_download_qwen_dry_run():
    plan = download_qwen_0_5b.build_download_plan(dry_run=True)

    assert plan.model_name == "Qwen/Qwen2.5-0.5B-Instruct"
    assert plan.dry_run is True
    assert download_qwen_0_5b.download_and_smoke_test(dry_run=True) is True


def test_lora_inference_missing_adapter_is_friendly(tmp_path):
    adapter_dir = tmp_path / "missing_adapter"

    ok, message = test_lora_inference.check_adapter(adapter_dir)

    assert ok is False
    assert "先执行真实训练命令" in message


def test_cli_train_real_dry_run_does_not_execute(monkeypatch):
    executed = {"value": False}

    def fake_execute(plan):
        executed["value"] = True
        return 0

    monkeypatch.setattr(cli, "execute_real_train", fake_execute)
    monkeypatch.setattr("sys.argv", ["app.cli", "train", "real", "--train-mode", "safe"])

    cli.main()

    assert executed["value"] is False


def test_cli_train_real_execute_aborts_when_checks_fail(monkeypatch, tmp_path):
    executed = {"value": False}

    def fake_execute(plan):
        executed["value"] = True
        return 0

    def fake_plan(train_mode):
        return {
            "train_mode": train_mode,
            "config_file": tmp_path / "missing.yaml",
            "sft_file": tmp_path / "missing_sft.jsonl",
            "dataset_info": tmp_path / "missing_dataset_info.json",
            "log_file": tmp_path / "real_train_safe.log",
            "command": ["llamafactory-cli", "train", str(tmp_path / "missing.yaml")],
            "command_text": "llamafactory-cli train missing.yaml",
        }

    monkeypatch.setattr(cli, "execute_real_train", fake_execute)
    monkeypatch.setattr(cli, "build_real_train_plan", fake_plan)
    monkeypatch.setattr("sys.argv", ["app.cli", "train", "real", "--train-mode", "safe", "--execute"])

    cli.main()

    assert executed["value"] is False

