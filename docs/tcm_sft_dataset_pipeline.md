# 开源中医 SFT 数据集处理流程

本文档说明如何将已经接入的开源中医 SFT parquet 数据集转换为本项目可用于 LLaMA-Factory smoke test 和 LoRA 训练的 Alpaca JSONL。

## 数据位置

外部数据集放在：

```text
data/external/TCM-Dataset-SFT/train/
├── 0000.parquet
├── 0001.parquet
└── 中医SFT数据集.txt
```

`data/external/` 和 `*.parquet` 已加入 `.gitignore`，不要提交到 GitHub。

## 字段说明

parquet 中已经确认存在三列：

```text
instruction
input
output
```

- `instruction`：任务说明，可能为空。
- `input`：中医相关问题。
- `output`：对应回答。

转换后的训练文件为 Alpaca 格式：

```json
{"instruction": "...", "input": "...", "output": "..."}
```

## 默认 Instruction

部分开源 SFT 样本的 `instruction` 为空。为了统一训练格式，转换脚本会补充：

```text
请回答以下中医相关问题，要求表达准确、克制，并避免替代医生诊断。
```

这样做可以减少模型学习到无任务边界的问答模式，也能强化医疗安全约束。

转换脚本默认还会做两类过滤：

- 过滤明显要求输出诊断、治疗方案、方剂和中药剂量的医案样本，避免训练模型学习“直接开方/确诊”的行为。若只是做离线数据研究，可显式添加 `--allow-clinical-plan`，但不建议用于本项目的安全演示训练。
- 过滤明显非中医主题样本，例如普通古文翻译、出处检索等。若需要保留原始混合主题，可显式添加 `--disable-tcm-keyword-filter`。

## 为什么不直接全量训练

该数据集体量较大，直接全量训练会带来：

- 首次排错成本高。
- Windows 环境更容易暴露编码、显存、路径和依赖问题。
- 训练时间长，不利于先验证数据格式、dataset_info 和 LLaMA-Factory 配置。

建议先用 1000 条做 smoke test，再扩大到 10000 条或更多。

## 检查数据集

在项目根目录运行：

```powershell
python scripts/inspect_tcm_dataset.py
```

脚本会：

- 自动读取 `data/external/TCM-Dataset-SFT/train/*.parquet`
- 输出每个 parquet 文件行数、字段名、空值统计
- 检查 `instruction/input/output`
- 统计文本长度分布
- 随机打印 5 条样本
- 将检查结果合并写入 `data/reports/dataset_report.json` 的 `external_tcm_sft_inspection` 字段

## 生成 1000 条 Smoke Test 数据

```powershell
python scripts/prepare_tcm_dataset_sft.py --max-rows 1000 --seed 42
```

输出：

```text
data/processed/sft_train.jsonl
```

如果目标文件已存在，会先备份为：

```text
data/processed/sft_train.jsonl.bak
```

同时会修正：

```text
data/processed/dataset_info.json
```

确保包含：

```json
{
  "tcm_sft": {
    "file_name": "sft_train.jsonl",
    "formatting": "alpaca",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}
```

## 生成 10000 条训练数据

smoke test 通过后，可以扩大样本：

```powershell
python scripts/prepare_tcm_dataset_sft.py --max-rows 10000 --seed 42
```

注意：当前数据集更适合作为“中医知识问答 SFT”，不是专门的九大体质辨识数据。体质辨识数据后续应单独构建，避免任务边界混淆。

## 运行 LLaMA-Factory 训练

先确认配置：

```text
configs/tcm_qwen_safe_lora_sft.yaml
```

关键字段：

```yaml
dataset_dir: data/processed
dataset: tcm_sft
```

不要在 YAML 中加入 LLaMA-Factory 不识别的自定义字段，例如：

```text
train_file
train_mode
hardware_hint
notes
```

训练命令：

```powershell
python -m app.cli train real --train-mode safe
python -m app.cli train real --train-mode safe --execute
```

训练成功后重点检查：

```text
outputs/tcm_qwen_0_5b_lora/
├── adapter_config.json
├── adapter_model.safetensors
└── trainer_state.json 或 checkpoint metadata
```

## 常见错误

### Windows GBK/UTF-8 编码错误

所有脚本均使用 `encoding="utf-8"` 写入 JSON/JSONL。PowerShell 显示中文乱码时，通常是终端显示编码问题，不代表文件损坏。

### YAML 多余字段导致 HfArgumentParser 报错

错误示例：

```text
ValueError: Some keys are not used by the HfArgumentParser:
['hardware_hint', 'notes', 'train_file', 'train_mode']
```

解决：训练 YAML 只保留 LLaMA-Factory 支持的字段；展示元信息放入报告或 JSON metadata。

### parquet 路径错误导致 files=[]

确认文件存在：

```powershell
Get-ChildItem data\external\TCM-Dataset-SFT\train\*.parquet
```

也可以显式传入目录：

```powershell
python scripts/inspect_tcm_dataset.py --dataset-dir data/external/TCM-Dataset-SFT/train
```

### 没有 eval_loss

当前训练配置没有单独验证集，因此训练日志可能只有训练 loss，没有 `eval_loss`。如需 `eval_loss`，需要额外划分验证集并在 LLaMA-Factory 配置中加入验证集设置。
