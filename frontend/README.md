# 中医知识库与体质辨识演示系统前端

这是 `TCM-Multimodal-Finetune-Agent` 的 Vue3 可视化演示前端，使用 Vite、TypeScript、Element Plus 和 Axios 构建。

## 启动后端

在项目根目录启动 FastAPI：

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8010 --reload
```

后端健康检查：

```text
http://127.0.0.1:8010/health
```

## 启动前端

进入前端目录：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://localhost:5173
```

## 环境变量

默认 API 地址：

```text
http://127.0.0.1:8010
```

如需调整，可新建 `.env`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8010
VITE_PROXY_TARGET=http://127.0.0.1:8010
```

开发环境已在 `vite.config.ts` 中配置 `/api` 代理到 FastAPI 后端，必要时也可以将 `VITE_API_BASE_URL` 设置为空或 `/` 来走相对路径代理。

## 页面功能

- 首页：展示系统概览、产品边界和医学安全声明。
- 中医知识问答：调用 `POST /api/v1/knowledge/ask`。
- 体质辨识问卷：调用 `GET /api/v1/constitution/questionnaire` 和 `POST /api/v1/constitution/questionnaire/submit`。
- 数据集与微调：调用 `POST /api/v1/dataset/build`。
- 评估报告：展示 CLI 评估报告入口。
- 数字人播报：调用 `POST /api/v1/digital-human/speak`，使用 Three.js Web 3D 数字人只播报已生成文本。

## 3D 模型

可选模型目录：

```text
frontend/public/models/doctor.vrm
frontend/public/models/doctor.glb
```

如果没有模型，页面会自动使用 Three.js fallback 3D 医生。模型文件请自行确认授权，`.gitignore` 已忽略 `.vrm`、`.glb`、`.gltf`。

页面会处理后端未启动、网络连接失败、404、500、字段缺失和疑似乱码提示，不会因接口异常白屏。
