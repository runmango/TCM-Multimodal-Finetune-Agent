# 3D 数字人模型目录

将合法授权的模型文件放在此目录：

```text
frontend/public/models/doctor.vrm
frontend/public/models/doctor.glb
```

加载顺序：

1. 优先加载 `/models/doctor.vrm`
2. 如果 VRM 不存在或加载失败，尝试 `/models/doctor.glb`
3. 如果都不可用，前端自动使用 Three.js 几何体创建的 fallback 3D 医生模型

请不要提交商业模型、未知授权模型或大型二进制模型文件。`.gitignore` 已忽略 `.vrm`、`.glb`、`.gltf` 文件。
