# 中医体质辨识数字人演示

数字人模块是应用展示层，不属于训练 Pipeline。训练链路中的 `DataLoadAgent`、`SFTBuildAgent`、`TrainConfigAgent`、`TrainSimAgent`、`EvalAgent` 等保持独立；数字人只调用推理服务、TTS 服务和数字人播报接口，用来展示“模型结果 -> 语音播报 -> 前端数字人交互”的闭环。

## 架构

```text
用户输入症状
 ↓
FastAPI /digital-human/talk
 ↓
规则推理 / RAG / LoRA 推理服务
 ↓
TTS 语音生成
 ↓
前端头像 + 音频 + 字幕
```

第一版不接入 MuseTalk、Wav2Lip、SadTalker 等重型视频生成框架，只做轻量播报型数字人。

## 主系统入口

页面位置：

```text
中医知识库与体质辨识演示系统
└── 数字人演示 /digital-human
```

进入方式：启动主 Vue 前端后，在左侧导航点击“数字人演示”。

## 后端启动

```powershell
uvicorn app.api.main:app --host 127.0.0.1 --port 8010 --reload
```

健康检查：

```powershell
curl http://127.0.0.1:8010/health
```

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://localhost:5173/digital-human
```

端口约定：主演示前端 `frontend/` 使用 `5173`。数字人演示是该系统的子页面，不再需要单独启动独立数字人前端。若看到 `5175` 或 `5176` 也能打开数字人页面，通常是旧 Vite 进程残留，应关闭后从 `frontend/` 重新启动。

## API 示例

体质辨识：

```powershell
curl -X POST http://127.0.0.1:8010/api/v1/constitution/infer `
  -H "Content-Type: application/json; charset=utf-8" `
  -d '{"query":"乏力、气短、舌淡有齿痕"}'
```

TTS：

```powershell
curl -X POST http://127.0.0.1:8010/api/v1/tts/generate `
  -H "Content-Type: application/json; charset=utf-8" `
  -d '{"text":"体质倾向：气虚质。安全提示：仅供健康科普参考，不替代医生诊疗。","voice":"zh-CN-XiaoxiaoNeural"}'
```

数字人总接口：

```powershell
curl -X POST http://127.0.0.1:8010/api/v1/digital-human/talk `
  -H "Content-Type: application/json; charset=utf-8" `
  -d '{"query":"乏力、气短、舌淡有齿痕","voice":"zh-CN-XiaoxiaoNeural"}'
```

## TTS 失败处理

TTS 使用 `edge-tts`。如果网络或依赖异常，接口不会崩溃，会返回：

```json
{
  "audio_url": null,
  "tts_status": "failed",
  "message": "TTS 生成失败，请检查网络或 edge-tts 环境。"
}
```

主系统数字人页面仍会显示文本、字幕和安全提示，头像保持静止状态，不影响体质辨识结果展示。

## 后续接入真实 LoRA Adapter

当前 `inference_service` 默认是规则推理。后续可以保留同一响应结构，把 backend 扩展为：

```text
rule | rag | lora
```

接入真实 LoRA 时建议：

1. 使用固定输入输出 schema，保持 `constitution/reason/advice/safety_notice` 不变。
2. 加载 `Qwen/Qwen2.5-0.5B-Instruct` 和 `outputs/tcm_qwen_0_5b_lora`。
3. 对模型输出做安全后处理，强制保留“仅供健康科普参考，不替代医生诊疗。”。
4. 禁止输出诊断、处方、剂量和保证疗效。

## 后续升级方向

- Live2D：用轻量 2D 角色替代 SVG 头像。
- Wav2Lip / MuseTalk：接入真实口型同步，但需要 GPU 和视频素材合规授权。
- SadTalker：生成说话头像视频，适合离线演示。
- WebSocket：按句子流式返回字幕和播放状态。

## 医学安全声明

本系统仅供健康科普参考，不替代医生诊疗。系统不会提供疾病诊断、具体药方剂量或保证疗效的建议。
