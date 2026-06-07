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

- 体质辨识：调用 `POST /api/v1/infer/constitution`
- 知识库检索：调用 `POST /api/v1/rag/search`
- 知识库构建：调用 `POST /api/v1/dataset/build`
- 数字人演示：调用 `POST /api/v1/digital-human/talk`
- 系统说明：展示工程链路、免责声明和扩展方向

页面会处理后端未启动、网络连接失败、404、500、字段缺失和疑似乱码提示，不会因接口异常白屏。
