<template>
  <section class="tool-surface">
    <h2>系统说明</h2>
    <p>
      本系统用于展示中医多模态微调数据治理、关键词 RAG 检索、体质倾向分析和接口部署能力。
      页面是技术演示版，不提供临床诊断、处方或具体用药建议。
    </p>

    <div class="info-grid">
      <div>
        <h3>后端能力</h3>
        <ul>
          <li>FastAPI 暴露健康检查、知识库构建、RAG 检索和体质辨识接口。</li>
          <li>数字人播报接口组合体质规则判断、TTS 和字幕结果，不进入训练 Pipeline。</li>
          <li>LangGraph 编排数据集治理与推理 Agent。</li>
          <li>规则安全策略拒绝“确诊、处方、开药”等高风险请求。</li>
        </ul>
      </div>
      <div>
        <h3>前端能力</h3>
        <ul>
          <li>Vue3 + Vite + TypeScript + Element Plus。</li>
          <li>统一 Axios API 封装与异常提示。</li>
          <li>卡片化展示证据、标签、分数和来源类型。</li>
          <li>新增“数字人演示”子页面，以头像、音频和字幕展示体质辨识结果。</li>
        </ul>
      </div>
    </div>
  </section>
</template>
