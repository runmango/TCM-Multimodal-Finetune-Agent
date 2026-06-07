# Windows 真实训练环境配置指南

本文档用于在 Windows + PowerShell + Anaconda + NVIDIA RTX 4060 Laptop GPU 8GB 环境下，准备并运行 `Qwen/Qwen2.5-0.5B-Instruct` 的 safe 模式 LoRA SFT 训练。

重要说明：本项目默认只生成配置、命令和模拟训练报告。只有你明确执行 `llamafactory-cli train ...` 或 `python -m app.cli train real --execute` 时，才会开始真实训练。

## 1. 进入项目目录

```powershell
cd D:\code5\TCM-Multimodal-Finetune-Agent
```

## 2. 创建独立 conda 环境

```powershell
conda create -n tcm-llm-train python=3.10 -y
conda activate tcm-llm-train
```

升级基础工具：

```powershell
python -m pip install --upgrade pip setuptools wheel
```

## 3. 检查显卡与驱动

```powershell
nvidia-smi
```

重点看：

- Driver Version
- CUDA Version
- GPU 名称和显存

不要盲目固定 CUDA 版本。请优先使用 PyTorch 官网安装选择器生成 Windows + pip + CUDA 的稳定安装命令：

```text
https://pytorch.org/get-started/locally/
```

示例命令如下；如果与官网当前推荐不一致，以官网为准：

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

如果官网推荐 `cu118`、`cu126` 或 `cu128`，请使用官网生成的命令。

## 4. 安装 LLaMA-Factory 与训练依赖

方案 A：pip 安装，优先尝试。

```powershell
pip install -U "llamafactory[torch,metrics]"
```

如果方案 A 失败，使用方案 B：源码安装。

```powershell
git clone https://github.com/hiyouga/LLaMA-Factory.git third_party/LLaMA-Factory
cd third_party/LLaMA-Factory
pip install -e ".[torch,metrics]"
cd D:\code5\TCM-Multimodal-Finetune-Agent
```

安装项目依赖：

```powershell
pip install -r requirements.txt
```

## 5. 运行训练环境检查

```powershell
python scripts/check_train_env.py
```

脚本会检查：

- Python 版本
- torch 是否可导入
- `torch.cuda.is_available()`
- torch CUDA version
- GPU 名称和显存
- transformers / datasets / peft / accelerate / trl
- `llamafactory-cli --help`

如果出现 `[FAIL]`，请先按脚本提示修复环境，不要直接训练。

## 6. 配置 Hugging Face 下载缓存

默认会下载到 Hugging Face cache。可选设置：

```powershell
$env:HF_HOME="D:\hf_cache"
```

如果 Hugging Face 访问不稳定，可临时使用镜像：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

不要把模型权重或 Hugging Face cache 放进项目仓库。

## 7. 下载 Qwen 0.5B 模型并做最小推理测试

```powershell
python scripts/download_qwen_0_5b.py
```

脚本会下载：

- tokenizer
- model config
- model weights

并用短问题做一次最小推理：

```text
请用一句话解释什么是中医体质辨识。
```

如果下载失败，常见原因包括：

- 网络无法访问 Hugging Face
- 需要代理或镜像
- 磁盘空间不足
- transformers 版本过低

## 8. 构建 safe 数据集与训练配置

```powershell
python -m app.cli dataset build --train-mode safe
```

检查输出文件：

```powershell
dir data\processed
dir configs
dir reports
```

必须确认存在：

```text
data/processed/sft_train.jsonl
data/processed/dataset_info.json
configs/tcm_qwen_safe_lora_sft.yaml
```

safe 配置默认适配 4060 Laptop 8GB：

- `model_name_or_path: Qwen/Qwen2.5-0.5B-Instruct`
- `cutoff_len: 1024`
- `per_device_train_batch_size: 1`
- `gradient_accumulation_steps: 8`
- `dataloader_num_workers: 0`
- `fp16: true`
- `plot_loss: true`

## 9. 启动真实训练

直接运行：

```powershell
llamafactory-cli train configs/tcm_qwen_safe_lora_sft.yaml
```

指定单卡：

```powershell
$env:CUDA_VISIBLE_DEVICES="0"
llamafactory-cli train configs/tcm_qwen_safe_lora_sft.yaml
```

建议保存日志：

```powershell
llamafactory-cli train configs/tcm_qwen_safe_lora_sft.yaml *> reports\real_train_safe.log
```

或：

```powershell
llamafactory-cli train configs/tcm_qwen_safe_lora_sft.yaml 2>&1 | Tee-Object -FilePath reports\real_train_safe.log
```

也可以使用项目 CLI。默认 dry-run，不会训练：

```powershell
python -m app.cli train real --train-mode safe
```

确认检查通过后再真实执行：

```powershell
python -m app.cli train real --train-mode safe --execute
```

该命令会把日志保存到：

```text
reports/real_train_safe.log
```

## 10. 查看训练结果

训练完成后检查：

```powershell
dir outputs\tcm_qwen_0_5b_lora
```

常见输出包括：

```text
adapter_config.json
adapter_model.safetensors
trainer_log.jsonl
training_args.bin
```

不同 LLaMA-Factory 版本文件名可能略有差异，以实际输出为准。

查看 loss：

- 控制台日志中的 `loss`
- `reports\real_train_safe.log`
- `outputs\tcm_qwen_0_5b_lora` 下的 trainer log 或 loss 图

判断训练成功：

- 命令退出码为 0
- `outputs\tcm_qwen_0_5b_lora` 生成 adapter 文件
- 日志中出现训练完成、保存 checkpoint 或 adapter 的信息

判断是否爆显存：

- 日志出现 `CUDA out of memory`
- `nvidia-smi` 显示显存占满
- 训练在第一批或保存前失败

## 11. 爆显存降级方案

优先修改 `configs/tcm_qwen_safe_lora_sft.yaml`：

```yaml
cutoff_len: 512
```

如果仍然爆显存：

```yaml
lora_rank: 4
```

继续保持：

```yaml
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
```

必要时可把：

```yaml
gradient_accumulation_steps: 16
```

## 12. 训练后 LoRA 推理测试

```powershell
python scripts/test_lora_inference.py
```

该脚本会加载：

```text
base model: Qwen/Qwen2.5-0.5B-Instruct
adapter: outputs/tcm_qwen_0_5b_lora
```

如果 adapter 不存在，会提示先执行训练命令。

所有医学相关输出仅供健康科普参考，不替代医生诊疗。

