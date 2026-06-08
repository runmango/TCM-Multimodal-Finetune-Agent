# Web 3D 中医数字人播报

## 定位

Web 3D 数字人是“中医知识库与体质辨识演示系统”的应用展示层，不属于微调训练链路。它不做体质判断，不做知识推理，只把已经生成的体质问卷结果、中医知识问答结果或手动输入的健康科普文本，通过 3D 虚拟医生、TTS 音频和字幕进行播报。

```text
体质辨识问卷 -> 结果文本 -> Web 3D 数字人播报
中医知识问答 -> 知识解释 -> Web 3D 数字人播报
手动输入文本 -> Web 3D 数字人播报
```

所有医学内容必须包含：

```text
仅供健康科普参考，不替代医生诊疗。
```

## 为什么使用 Vue3 + Three.js

- Vue3 负责页面状态、表单、路由和 API 调用。
- Three.js 负责浏览器端 3D 场景、灯光、相机、模型和动画。
- Web Audio API 负责读取 TTS 音频音量，用音量驱动嘴巴开合。
- `@pixiv/three-vrm` 预留 VRM 模型加载能力，便于后续替换高质量授权数字人。

第一版不使用 Unity、Unreal、MuseTalk、Wav2Lip、SadTalker 等重型方案，优先保证面试演示稳定。

## 前端目录

当前项目实际前端目录是：

```text
frontend/
```

主要新增文件：

```text
frontend/src/components/digital-human/Web3DAvatar.vue
frontend/src/components/digital-human/AvatarStage.vue
frontend/src/components/digital-human/SpeakingWave.vue
frontend/src/components/digital-human/DigitalHumanControlPanel.vue
frontend/src/services/avatar/vrmLoader.ts
frontend/src/services/avatar/audioMouthDriver.ts
frontend/src/services/avatar/avatarAnimation.ts
frontend/src/services/avatar/fallbackDoctorModel.ts
frontend/src/types/digitalHuman.ts
frontend/public/models/README.md
```

## 模型放置

可自行放入合法授权模型：

```text
frontend/public/models/doctor.vrm
frontend/public/models/doctor.glb
```

加载顺序：

1. 优先加载 `/models/doctor.vrm`
2. 如果失败，加载 `/models/doctor.glb`
3. 如果都不存在，自动使用 Three.js 几何体生成 fallback 3D 医生

不要提交商业模型、未知授权模型或大型二进制模型。`.gitignore` 已忽略：

```text
frontend/public/models/*.vrm
frontend/public/models/*.glb
frontend/public/models/*.gltf
```

## Fallback 效果

没有 VRM/GLB 时，前端会自动创建一个简化 3D 医生：

- 球体头部
- 白色医生帽
- 白大褂和蓝绿色内衬
- 眼睛、嘴巴、听诊器
- 待机呼吸、眨眼、轻微头部摆动
- 思考状态的旋转提示环
- 播报时根据音频音量驱动嘴巴开合

该模型不引用外部版权资源。

## 启动后端

```powershell
uvicorn app.api.main:app --host 127.0.0.1 --port 8010 --reload
```

数字人播报接口：

```http
POST /api/v1/digital-human/speak
```

## 启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问：

```text
http://localhost:5173/digital-human
```

## 播报体质问卷结果

在“体质辨识问卷”页面提交问卷后，点击“让数字人播报问卷结果”。前端会写入：

```typescript
localStorage.setItem("digital_human_speak_text", result.result_text)
localStorage.setItem("digital_human_scene", "constitution_result")
```

随后跳转到 `/digital-human`，数字人页面自动填充文本，等待用户点击“开始播报”。

## 播报知识问答结果

在“中医知识问答”页面生成回答后，点击“让数字人播报此回答”。前端会写入：

```typescript
localStorage.setItem("digital_human_speak_text", answer.answer)
localStorage.setItem("digital_human_scene", "knowledge_answer")
```

随后跳转到 `/digital-human`。

## TTS 失败降级

如果 `edge-tts` 不可用、网络失败或后端未返回 `audio_url`，页面不会崩溃：

- 3D 数字人保持待机/完成状态
- 仍显示后端返回文本
- 仍显示字幕
- 显示 “TTS 暂不可用，已降级为文本和字幕展示。”

## 测试

```powershell
cd frontend
npm run build
```

后端回归：

```powershell
python -m pytest -q
```

## 后续升级

- 替换高质量授权 VRM 模型
- 接入 Live2D
- 接入 MuseTalk 或 Wav2Lip 做更精确口型同步
- 用 WebRTC 做实时数字人互动
- 增加 `/api/v1/eval/report`，把评估报告图表化

## 面试解释

数字人模块是系统的应用展示层，不属于微调训练链路。主系统负责中医数据集整理、SFT 构建、LoRA 微调配置、训练评估、知识问答和体质问卷；Web 3D 数字人页面负责把体质问卷结果或知识问答结果通过 3D 虚拟医生、TTS 语音和字幕进行播报。第一版使用 Three.js 和 Web Audio API 实现网页端 3D 数字人和音量驱动口型，不依赖重型视频生成模型，保证演示稳定。后续如果有更高要求，可以替换为高质量 VRM 模型、Live2D 或 MuseTalk 实时口型同步方案。
