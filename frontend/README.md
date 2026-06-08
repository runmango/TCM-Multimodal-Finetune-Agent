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

启动数据记录与分析后台：

```bash
npm run dev:admin
```

浏览器访问：

```text
http://127.0.0.1:5175
```

后台构建：

```bash
npm run build:admin
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

后台模式默认读取 `.env.admin`：

```env
VITE_ADMIN_MODE=true
VITE_API_BASE_URL=http://127.0.0.1:8010
VITE_MAIN_FRONTEND_URL=http://127.0.0.1:5173
```

开发环境已在 `vite.config.ts` 中配置 `/api` 代理到 FastAPI 后端，必要时也可以将 `VITE_API_BASE_URL` 设置为空或 `/` 来走相对路径代理。

## 页面功能

- 首页：展示四层架构、业务流程链路和医学安全声明。
- 体质辨识问卷：支持问诊量表、舌象上传、四诊结构化、九种体质转化分、知识库解释和数字人播报入口。
- 中医知识问答：调用 `POST /api/v1/knowledge/ask`，优先走向量 RAG，失败时 fallback。
- 数字人播报：调用 `POST /api/v1/digital-human/speak`，使用 Three.js Web 3D 数字人只播报已生成文本。
- 数据集与微调：调用 `POST /api/v1/dataset/build`。
- 评估报告：展示 CLI 评估报告入口。
- 数据记录与分析后台：`5175` admin 模式，查看历史记录、体质分布、四诊详情、RAG 来源和播报文本。

## 3D 模型

可选模型目录：

```text
frontend/public/models/doctor.vrm
frontend/public/models/doctor.glb
```

如果没有模型，页面会自动使用 Three.js fallback 3D 医生。模型文件请自行确认授权，`.gitignore` 已忽略 `.vrm`、`.glb`、`.gltf`。

页面会处理后端未启动、网络连接失败、404、500、字段缺失和疑似乱码提示，不会因接口异常白屏。
