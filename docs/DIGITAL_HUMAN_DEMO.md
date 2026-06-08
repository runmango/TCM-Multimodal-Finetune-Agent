# Web 3D 数字人播报演示

数字人模块是应用展示层，不属于训练 Pipeline，也不参与体质判断或知识推理。当前前端已升级为 Web 3D 数字人播报：页面使用 Vue3、Three.js 和 Web Audio API 展示 3D 医生模型，并用 TTS 音频音量驱动嘴巴开合。

## 新架构

```text
体质辨识问卷 -> 打分结果 -> /api/v1/digital-human/speak -> Web 3D 数字人 + TTS + 字幕
中医知识问答 -> 知识解释 -> /api/v1/digital-human/speak -> Web 3D 数字人 + TTS + 字幕
```

旧的“输入症状 -> 数字人判断体质”链路已废弃。开放式输入只进入“中医知识问答”，体质辨识只走问卷量表。

## 主系统入口

页面位置：

```text
中医知识库与体质辨识演示系统
└── Web 3D 数字人播报 /digital-human
```

进入方式：启动主 Vue 前端后，在左侧导航点击“数字人播报”。也可以从“中医知识问答”或“体质辨识问卷”页面点击播报按钮，页面会通过 `localStorage` 把已生成文本带到 `/digital-human`。

## 后端启动

```powershell
uvicorn app.api.main:app --host 127.0.0.1 --port 8010 --reload
```

`app.main:app` 也已挂载新的应用层路由，面试演示建议统一使用 `app.api.main:app`。

健康检查：

```powershell
curl http://127.0.0.1:8010/health
curl http://127.0.0.1:8010/api/v1/health
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

端口约定：主演示前端 `frontend/` 使用 `5173`。如果看到 `5175` 或 `5176` 也能打开页面，通常是旧 Vite 进程残留，应关闭后从 `frontend/` 重新启动。

## 3D 模型

模型目录：

```text
frontend/public/models/
```

加载顺序：

```text
/models/doctor.vrm -> /models/doctor.glb -> Three.js fallback 3D 医生
```

如果没有模型文件，页面会自动显示一个由 Three.js 基础几何体构建的 3D 医生，占位模型包含白大褂、医生帽、眼睛、嘴巴和听诊器，并支持待机、思考和音量驱动嘴巴开合。

请只放入合法授权的 VRM/glTF 模型，不要提交商业模型或未知授权模型。

## API 示例

数字人播报：

```powershell
curl -X POST http://127.0.0.1:8010/api/v1/digital-human/speak `
  -H "Content-Type: application/json; charset=utf-8" `
  -d '{"scene":"knowledge_answer","text":"气虚质常见表现包括容易疲乏、气短、自汗等。","voice":"zh-CN-XiaoxiaoNeural"}'
```

响应会包含：

- `scene`：播报场景，例如 `constitution_result`、`knowledge_answer`、`general_notice`
- `text`：后端自动补齐安全提示后的文本
- `audio_url`：TTS 成功时返回 mp3 地址，失败时为 `null`
- `avatar`：闭口、开口头像和状态
- `subtitles`：按句切分的字幕
- `safety_notice`：`仅供健康科普参考，不替代医生诊疗。`

兼容接口：

```powershell
curl -X POST http://127.0.0.1:8010/api/v1/digital-human/talk `
  -H "Content-Type: application/json; charset=utf-8" `
  -d '{"query":"乏力、气短、舌淡有齿痕","voice":"zh-CN-XiaoxiaoNeural"}'
```

`/talk` 已标记为 deprecated，只返回迁移提示，不再根据症状直接判断体质。

## TTS 失败处理

TTS 使用 `edge-tts`。如果网络或依赖异常，接口不会崩溃，会返回：

```json
{
  "audio_url": null,
  "tts_status": "failed",
  "message": "TTS 生成失败，请检查网络或 edge-tts 环境。"
}
```

前端仍会显示文本、字幕和安全提示，3D 数字人保持待机或播报完成状态。

## 后续升级方向

- Live2D：用轻量 2D 角色替代 SVG 头像。
- Wav2Lip / MuseTalk：接入真实口型同步，需要 GPU 和合规视频素材。
- SadTalker：生成说话头像视频，适合离线演示。
- WebSocket：按句子流式返回字幕和播放状态。

详细实现说明见：

```text
docs/WEB3D_DIGITAL_HUMAN.md
```

## 医学安全声明

本系统仅供健康科普参考，不替代医生诊疗。系统不会提供疾病诊断、具体药方剂量或保证疗效的建议。
