# 产品逻辑重构说明

## 重构目标

本次重构把“中医知识库与体质辨识演示系统”拆成三条清晰职责：

```text
中医知识问答 -> 知识解释 -> 数字人播报
体质辨识问卷 -> 量表打分 -> 数字人播报
数据集与微调 -> 数据治理 / 配置生成 / 模拟或真实训练入口
```

体质辨识不再使用开放式症状输入直接判断；自由文本只进入中医知识问答；数字人只负责播报已生成文本。

## 为什么体质辨识改为问卷量表

体质辨识属于结构化评估任务，直接让用户自由输入症状再输出体质，容易让系统看起来像“诊断”。问卷量表可以把输入约束为可解释的题目和分值，便于说明规则、阈值、兼夹体质和安全边界。

当前实现是演示版简化规则，不等同正式医学量表。后续可接入《中医体质分类与判定》等正式量表条目和计分规则。

## 为什么自由输入放到中医知识问答

自由输入更适合做知识解释、检索和科普问答，例如“气虚质如何调养”。当前 `POST /api/v1/knowledge/ask` 会从 `data/processed/sft_train.jsonl` 和 `data/raw/*.jsonl` 做简单关键词检索，后续可以替换为向量库 RAG、rerank 或真实 LoRA adapter 推理。

中医 SFT 数据主要服务于知识问答，不直接作为体质问卷判定依据，避免任务边界混淆。

## 为什么数字人只负责播报

数字人是展示层，不应承担体质判断或知识推理。新的 `POST /api/v1/digital-human/speak` 只接收：

```json
{
  "scene": "knowledge_answer",
  "text": "已经生成的结果文本",
  "voice": "zh-CN-XiaoxiaoNeural"
}
```

服务层负责自动补安全提示、调用 TTS、生成字幕和头像状态。旧 `/api/v1/digital-human/talk` 已废弃，只返回迁移提示。

## 新接口

- `GET /api/v1/constitution/questionnaire`
- `POST /api/v1/constitution/questionnaire/submit`
- `POST /api/v1/knowledge/ask`
- `POST /api/v1/digital-human/speak`

保留旧兼容接口：

- `POST /api/v1/infer/constitution`
- `POST /api/v1/rag/search`
- `POST /api/v1/digital-human/talk`，deprecated，不再判断体质

## 体质问卷打分规则

第一版每种体质 3 道题，共九种体质：

```text
平和质、气虚质、阳虚质、阴虚质、痰湿质、湿热质、血瘀质、气郁质、特禀质
```

每题分值 1-5：

```text
没有=1，很少=2，有时=3，经常=4，总是=5
```

每种体质得分：

```text
score_percent = actual_score / max_possible_score * 100
```

主要体质：最高分且 `>= 60` 的偏颇体质。兼夹体质：得分 `>= 50` 且不是主要体质。若无明显偏颇体质，则返回“平和质”或“平和质或信息不足”。

## 后续扩展

- 正式体质量表：替换当前简化题库和阈值规则，增加反向计分、标准转化分和边界解释。
- RAG：把关键词检索替换为 embedding 向量库、召回重排和证据归因。
- LoRA adapter：在 `knowledge_qa_service.py` 后增加 `backend=lora` 分支，加载微调 adapter 做受控生成。
- 评估报告：新增 `/api/v1/eval/report`，把 `reports/eval_report.json` 图表化展示到前端。

## 医学安全声明

所有输出必须显示：

```text
仅供健康科普参考，不替代医生诊疗。
```

系统不诊断疾病，不输出处方剂量，不承诺疗效，不建议用户停止正规治疗。严重不适或持续加重时应及时就医。
