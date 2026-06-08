# TCM-Multimodal-Finetune-Agent

基于 LangGraph 编排中医多模态微调数据集治理流水线，并提供中医知识问答、体质辨识问卷、数字人播报、安全拒答、FastAPI 接口和可视化演示页面。

系统名称：

```text
中医知识库与体质辨识演示系统
```

## 目录结构

```text
.
├── app/
│   ├── agents/              # DataLoad/Clean/Schema/Quality/SFT/MM/Export 与推理 Agent
│   ├── core/                # 路径与基础配置
│   ├── graphs/              # LangGraph 数据集构建图与推理图
│   ├── schemas/             # FastAPI Pydantic schema
│   ├── services/            # dataset build 与 keyword RAG service
│   └── main.py              # FastAPI app
├── data/
│   ├── raw/                 # 中医知识库、体质辨识、多模态舌象 demo jsonl
│   ├── processed/           # 运行后生成 sft_train.jsonl、mm_sft_train.jsonl
│   └── reports/             # 运行后生成 dataset_report.json
├── finetune/
│   ├── lora_sft.yaml        # LoRA demo 配置
│   ├── qlora_sft.yaml       # QLoRA demo 配置
│   └── train_mock_log.txt   # mock 训练日志
├── tests/                   # pytest 测试
├── streamlit_app.py         # Streamlit 可视化演示界面
└── requirements.txt
```

## 快速启动

建议使用 Python 3.10+。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

构建数据集：

```bash
python -c "from app.services.dataset import build_dataset; print(build_dataset())"
```

启动 FastAPI 后端：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

启动 Streamlit 页面：

```bash
streamlit run streamlit_app.py
```

启动 Vue3 前端页面：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
Streamlit: http://localhost:8501
Vue3: http://localhost:5173
```

运行测试：

```bash
pytest -q
```

## Streamlit 演示页面（兼容版）

页面名称：

```text
中医知识库与体质辨识演示系统
```

页面副标题：

```text
基于 RAG 的中医知识检索与体质倾向分析 Demo
```

侧边栏提供：

- 后端服务地址配置，默认 `http://127.0.0.1:8010`
- `top_k` 数量选择，范围 1 到 10，默认 3
- 后端接口连通性提示
- 技术演示免责声明

主页面保留早期三个 Tab，用于兼容原始接口演示：

- 体质辨识：调用 `POST /api/v1/infer/constitution`
- 知识库检索：调用 `POST /api/v1/rag/search`
- 知识库构建：调用 `POST /api/v1/dataset/build`

如果后端未启动、接口不存在、请求超时、后端 500 或返回非 JSON，页面会展示友好提示，技术详情放在 expander 中。

## Vue3 演示页面

Vue3 前端位于 `frontend/`，使用 Vite、TypeScript、Element Plus 和 Axios。

页面包含：

- 首页 / 系统概览：展示产品边界、后端能力和安全声明。
- 中医知识问答：调用 `POST /api/v1/knowledge/ask`，自由输入只用于知识解释。
- 体质辨识问卷：调用 `GET /api/v1/constitution/questionnaire` 和 `POST /api/v1/constitution/questionnaire/submit`。
- 数据集与微调：调用 `POST /api/v1/dataset/build`，刷新 demo 数据治理产物和训练配置。
- 评估报告：展示 `reports/eval_report.json` 的 CLI 生成入口。
- 数字人播报：调用 `POST /api/v1/digital-human/speak`，用 Web 3D 数字人只播报已生成文本。

运行方式：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://localhost:5173
```

前端默认后端地址为 `http://127.0.0.1:8010`，也支持通过 `frontend/.env` 配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8010
VITE_PROXY_TARGET=http://127.0.0.1:8010
```

## 数字人播报子页面

项目在主 Vue 前端“中医知识库与体质辨识演示系统”中集成了“Web 3D 数字人播报”子页面，用于面试展示应用层闭环。它不进入训练 Pipeline，不修改 DataLoad/SFT/Train/Eval 等主链路；页面只调用 `app.api.main:app` 提供的 TTS、字幕生成和安全提示结果，前端用 Three.js 渲染 3D 医生并用 Web Audio API 驱动嘴巴开合。

后端接口：

- `GET /health`
- `GET /api/v1/constitution/questionnaire`
- `POST /api/v1/constitution/questionnaire/submit`
- `POST /api/v1/knowledge/ask`
- `POST /api/v1/tts/generate`
- `POST /api/v1/digital-human/speak`

启动应用后端：

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8010 --reload
```

也可以先查看启动命令：

```bash
python -m app.cli digital-human serve
```

需要直接通过 CLI 启动时：

```bash
python -m app.cli digital-human serve --start
```

启动主 Vue 前端：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://localhost:5173/digital-human
```

从主系统左侧导航点击“数字人播报”即可进入该子页面。端口约定：`frontend/` 是“中医知识库与体质辨识演示系统”，优先使用 `5173`；数字人播报不再需要单独启动独立前端。

可选 3D 模型放置位置：

```text
frontend/public/models/doctor.vrm
frontend/public/models/doctor.glb
```

如果没有模型文件，前端会自动使用 Three.js fallback 3D 医生模型。

示例请求：

```bash
curl -X POST http://127.0.0.1:8010/api/v1/digital-human/speak \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"scene":"knowledge_answer","text":"气虚质常见表现包括容易疲乏、气短、自汗等。","voice":"zh-CN-XiaoxiaoNeural"}'
```

如果 `edge-tts` 因网络或运行环境不可用，接口会返回文本、头像状态和字幕，并将 `tts_status` 标记为 `failed`，前端会降级为文本播报结果展示。旧 `/api/v1/digital-human/talk` 已标记 deprecated，不再执行“症状 -> 体质判断”。

后续可以在 `app/services/knowledge_qa_service.py` 中加入 LoRA/QLoRA adapter 推理分支；也可以把当前 Web 3D 占位医生升级为授权 VRM、Live2D、Wav2Lip、MuseTalk 或 SadTalker 一类的视频数字人方案。

## API 示例

健康检查：

```bash
curl http://127.0.0.1:8010/api/v1/health
```

构建数据集：

```bash
curl -X POST http://127.0.0.1:8010/api/v1/dataset/build
```

中医知识问答：

```bash
curl -X POST http://127.0.0.1:8010/api/v1/knowledge/ask \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"query":"气虚质有哪些表现？如何调养？","top_k":3}'
```

获取体质辨识问卷：

```bash
curl http://127.0.0.1:8010/api/v1/constitution/questionnaire
```

提交体质辨识问卷：

```bash
curl -X POST http://127.0.0.1:8010/api/v1/constitution/questionnaire/submit \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"answers":[{"question_id":"q004","score":5},{"question_id":"q005","score":5},{"question_id":"q006","score":5}]}'
```

数字人播报：

```bash
curl -X POST http://127.0.0.1:8010/api/v1/digital-human/speak \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"scene":"knowledge_answer","text":"气虚质常见表现包括容易疲乏、气短、自汗等。"}'
```

## LangGraph 流水线

数据集构建图：

```text
DataLoadAgent
  -> CleanAgent
  -> SchemaAgent
  -> QualityScoreAgent
  -> SFTBuildAgent
  -> MMBuildAgent
  -> DatasetRegistryAgent
  -> TrainConfigAgent
  -> TrainCommandAgent
  -> TrainSimAgent
  -> ExportAgent
```

推理图：

```text
RequestValidateAgent
  -> SymptomExtractAgent
  -> RAGRetrieveAgent
  -> ConstitutionJudgeAgent
  -> SafetyAgent
  -> ResponseFormatAgent
```

仓库包含一个轻量 LangGraph 兼容层：安装 `langgraph` 时使用真实 `StateGraph`；未安装时可用同样接口跑通本地测试，便于面试现场快速演示。

## 演示流程

1. 启动 FastAPI 后端：`uvicorn app.api.main:app --host 127.0.0.1 --port 8010 --reload`
2. 启动 Vue3 前端：`cd frontend && npm run dev`
3. 打开“中医知识问答”，输入“气虚质有哪些表现？如何调养？”，展示知识解释和来源。
4. 点击“让数字人播报此回答”，确认数字人只播报已生成文本。
5. 打开“体质辨识问卷”，填写量表并提交，展示主要体质、兼夹体质和九种体质得分。
6. 点击“让数字人播报问卷结果”，展示 TTS、字幕和头像状态。
7. 打开“数据集与微调”，演示 LangGraph 数据治理与训练配置产物。
8. 运行 `pytest -q`，证明关键链路可回归。

## 微调扩展

当前只生成训练数据和配置样例，不执行真实训练。后续可以：

当前数据集构建接口会自动生成 safe demo 微调产物：

- `data/processed/dataset_info.json`：LLaMA-Factory 数据集注册文件。
- `configs/tcm_qwen_safe_lora_sft.yaml`：safe 模式 Qwen 0.5B LoRA SFT 配置。
- `configs/tcm_qwen_safe_lora_sft.json`：safe 模式 JSON 配置。
- `configs/tcm_qwen_normal_lora_sft.yaml`：normal 模式 Qwen 1.5B LoRA SFT 配置。
- `configs/tcm_qwen_normal_lora_sft.json`：normal 模式 JSON 配置。
- `reports/train_simulation_report.json`：模拟训练报告，明确标注 `mode=simulation`。
- `reports/train_loss.csv`：模拟 3 个 epoch 的 loss 下降曲线。
- `reports/dataset_report.json`：包含数据质量和 training 字段的综合报告。

默认训练模式为 `normal`，适合 RTX 4060 Laptop 8GB 等消费级 GPU 演示；`safe` 模式使用 0.5B 模型，优先保证低显存和首次跑通。

命令行构建 normal 模式：

```bash
python -m app.cli dataset build --train-mode normal
```

命令行构建 safe 模式：

```bash
python -m app.cli dataset build --train-mode safe
```

也可以通过环境变量切换：

```bash
TCM_TRAIN_MODE=safe python -m app.cli dataset build
```

生成的训练命令只展示、不自动执行：

```bash
llamafactory-cli train configs/tcm_qwen_normal_lora_sft.yaml
```

这条命令用于展示后续可接入 LLaMA-Factory 的方式；真实训练需要自行准备 GPU、模型权重、训练框架和数据合规审核。

### 真实训练准备

Windows + RTX 4060 Laptop 8GB 环境的真实训练准备流程见：

```text
docs/REAL_TRAINING_SETUP_WINDOWS.md
```

常用命令：

```bash
python scripts/check_train_env.py
python scripts/download_qwen_0_5b.py
python -m app.cli train real --train-mode safe
python -m app.cli train real --train-mode safe --execute
python scripts/test_lora_inference.py
```

`train real` 默认是 dry-run，只打印检查结果和训练命令；只有加 `--execute` 才会尝试真实调用 LLaMA-Factory。

### 模型评估报告

项目会生成标准化评估报告：

```text
reports/eval_report.json
```

评估命令：

```bash
python -m app.cli eval run --train-mode safe --eval-mode simulation
python -m app.cli eval run --train-mode normal --eval-mode simulation
python -m app.cli eval run --train-mode safe --eval-mode rule
```

默认评估集位于：

```text
data/eval/tcm_eval.jsonl
```

如果 `data/eval/model_outputs.jsonl` 存在，`rule` 模式会基于模型输出计算体质识别准确率、格式合规率、安全提示率、不安全建议率和幻觉率。`real` 模式预留真实加载模型与 LoRA adapter 的接口，但默认不执行真实推理。

报告中的 `compare_to_previous` 会自动与上一轮 `reports/eval_report.json` 对比，用于说明这一轮微调是否在 accuracy、macro-F1、安全和幻觉风险上更好。所有指标默认仅用于工程演示，不代表真实临床效果。

- 将 `data/processed/sft_train.jsonl` 注册到 LLaMA Factory dataset 配置。
- 将 `data/processed/mm_sft_train.jsonl` 转换为目标多模态模型格式。
- 使用 `finetune/lora_sft.yaml` 或 `finetune/qlora_sft.yaml` 作为 LoRA/QLoRA 起点。
- 用 PEFT、Transformers、bitsandbytes 接入真实训练与 adapter 导出。

## 局限性

- RAG 当前是关键词检索，不包含 embedding、rerank 或向量库。
- 体质判断是规则打分，不是医学模型，也不构成诊断。
- 舌象图片使用占位路径，Demo 只治理 `image_description` 和元数据。
- Streamlit 页面用于演示，不包含登录、权限、审计和生产级前端工程。
- 安全策略是关键词级别，生产系统需要更完整的医疗安全分类器、审计和人工兜底。
