# TCM-Multimodal-Finetune-Agent

基于 LangGraph 编排中医多模态微调数据集治理流水线，并提供中医知识问答、向量 RAG、体质辨识问卷、四诊结构化、SQLite 记录持久化、数字人播报、安全拒答、FastAPI 接口和可视化演示页面。

系统名称：

```text
中医知识库与体质辨识演示系统
```

## 目录结构

```text
.
├── app/
│   ├── agents/              # DataLoad/Clean/Schema/Quality/SFT/MM/Export 与推理 Agent
│   ├── core/                # 路径、响应、体质量表条目与基础配置
│   ├── db/                  # SQLite 连接、DDL 与初始化
│   ├── graphs/              # LangGraph 数据集构建图与推理图
│   ├── repositories/        # 体质辨识记录持久化与查询
│   ├── schemas/             # FastAPI Pydantic schema
│   ├── scripts/             # 向量索引构建脚本
│   ├── services/            # dataset build、向量 RAG、正式量表算法、数字人服务
│   └── main.py              # FastAPI app
├── data/
│   ├── raw/                 # 中医知识库、体质辨识、多模态舌象 demo jsonl
│   ├── processed/           # 运行后生成 sft_train.jsonl、mm_sft_train.jsonl
│   ├── reports/             # 运行后生成 dataset_report.json
│   ├── vector_store/        # 本地向量索引运行产物，已 gitignore
│   └── app.db               # SQLite 运行产物，已 gitignore
├── finetune/
│   ├── lora_sft.yaml        # LoRA demo 配置
│   ├── qlora_sft.yaml       # QLoRA demo 配置
├── tests/                   # pytest 测试
├── streamlit_app.py         # Streamlit 兼容演示界面
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

启动 5175 数据记录与分析后台：

```bash
cd frontend
npm run dev:admin
```

可选：预先构建向量索引：

```bash
python -m app.scripts.build_vector_index
```

浏览器访问：

```text
Streamlit: http://localhost:8501
Vue3: http://localhost:5173
分析后台: http://127.0.0.1:5175
```

运行测试：

```bash
pytest -q
```

## Vue3 演示页面

Vue3 前端位于 `frontend/`，使用 Vite、TypeScript、Element Plus 和 Axios。

页面包含：

- 首页 / 系统概览：展示采集层、判断层、解释层、应用层四层架构和业务链路。
- 体质辨识问卷：支持问诊量表、可选舌象上传、四诊结构化 JSON、正式转化分算法、SQLite 记录保存和 RAG 解释。
- 中医知识问答：调用 `POST /api/v1/knowledge/ask`，优先走本地向量检索，失败时 fallback 到关键词检索和安全兜底。
- 数字人播报：调用 `POST /api/v1/digital-human/speak`，用 Web 3D 数字人只播报已生成文本。
- 数据集与微调：调用 `POST /api/v1/dataset/build`，刷新 demo 数据治理产物和训练配置。
- 评估报告：展示 `reports/eval_report.json` 的 CLI 生成入口。

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

### 数据记录与分析后台

支持 admin 模式，运行在 `5175`，用于查看 SQLite 中的体质辨识历史记录、四诊详情、体质分布、RAG 来源和数字人播报文本。

启动方式：

```bash
cd frontend
npm run dev:admin
```

浏览器访问：

```text
http://127.0.0.1:5175
```

构建方式：

```bash
cd frontend
npm run build:admin
```

后台默认读取：

```env
VITE_API_BASE_URL=http://127.0.0.1:8010
VITE_MAIN_FRONTEND_URL=http://127.0.0.1:5173
```

后台页面仅用于技术演示、数据追踪和系统评估，不采集姓名、手机号、身份证号等个人敏感信息。

## 数字人播报子页面

项目在主 Vue 前端“中医知识库与体质辨识演示系统”中集成了“Web 3D 数字人播报”子页面，前端用 Three.js 渲染 3D 医生并用 Web Audio API 驱动嘴巴开合。

后端接口：

- `GET /health`
- `GET /api/v1/constitution/questionnaire`
- `POST /api/v1/constitution/questionnaire/submit`
- `POST /api/v1/constitution/full-infer`
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
  -d '{"answers":[{"question_id":"fatigue","score":5},{"question_id":"shortness_of_breath","score":5},{"question_id":"spontaneous_sweating","score":4},{"question_id":"easy_cold","score":4}],"tongue_features":{"tongue_color":"淡","tongue_coating":"薄白","teeth_marks":true}}'
```

完整体质辨识闭环：

```bash
curl -X POST http://127.0.0.1:8010/api/v1/constitution/full-infer \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"answers":[{"question_id":"fatigue","score":5},{"question_id":"shortness_of_breath","score":5},{"question_id":"spontaneous_sweating","score":4},{"question_id":"easy_cold","score":4}],"top_k":3}'
```

重建向量索引：

```bash
curl -X POST http://127.0.0.1:8010/api/v1/rag/rebuild
```

查看体质辨识历史记录：

```bash
curl "http://127.0.0.1:8010/api/v1/constitution/records?limit=20&offset=0"
curl http://127.0.0.1:8010/api/v1/constitution/analytics/summary
curl http://127.0.0.1:8010/api/v1/constitution/analytics/distribution
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