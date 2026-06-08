<template>
  <section class="tool-surface">
    <h2>首页 / 系统概览</h2>
    <p>
      本系统用于展示中医知识问答、体质辨识问卷、四诊结构化数据、知识库解释和数字人播报的工程闭环。
      页面为技术演示版，不提供临床诊断、处方或具体用药建议。
    </p>

    <div class="architecture-grid">
      <article class="architecture-card">
        <div class="architecture-card__index">1</div>
        <h3>采集层：中医四诊数据采集</h3>
        <p>通过问诊量表、舌象图片上传和可扩展的声音、脉象输入，将望、闻、问、切信息转化为结构化数据。</p>
        <div class="tag-row">
          <el-tag effect="plain">问诊量表</el-tag>
          <el-tag effect="plain">舌象上传</el-tag>
          <el-tag effect="plain">四诊结构化 JSON</el-tag>
        </div>
      </article>

      <article class="architecture-card">
        <div class="architecture-card__index">2</div>
        <h3>判断层：体质辨识与评分</h3>
        <p>基于问卷答案和四诊结构化数据，计算九种体质分数，输出主倾向体质和兼夹体质。</p>
        <div class="tag-row">
          <el-tag effect="plain">九种体质评分</el-tag>
          <el-tag effect="plain">主倾向体质</el-tag>
          <el-tag effect="plain">兼夹体质</el-tag>
        </div>
      </article>

      <article class="architecture-card">
        <div class="architecture-card__index">3</div>
        <h3>解释层：中医知识库问答</h3>
        <p>根据体质辨识结果调用中医知识库，解释体质含义、常见表现、调养建议和注意事项。</p>
        <div class="tag-row">
          <el-tag effect="plain">RAG 知识库</el-tag>
          <el-tag effect="plain">体质解释</el-tag>
          <el-tag effect="plain">调养建议</el-tag>
          <el-tag effect="plain">来源引用</el-tag>
        </div>
      </article>

      <article class="architecture-card">
        <div class="architecture-card__index">4</div>
        <h3>应用层：数字人播报与展示</h3>
        <p>将体质辨识结果和知识库解释文本传递给数字人模块，通过 Web3D 形象、TTS 或字幕 fallback 进行结果播报。</p>
        <div class="tag-row">
          <el-tag effect="plain">数字人播报</el-tag>
          <el-tag effect="plain">TTS</el-tag>
          <el-tag effect="plain">字幕 fallback</el-tag>
          <el-tag effect="plain">结果展示</el-tag>
        </div>
      </article>
    </div>

    <section class="flow-surface" aria-label="业务流程链路">
      <h3>业务流程链路</h3>
      <p class="flow-caption">问诊量表 → 舌象上传 → 四诊结构化 → 体质评分 → 知识库解释 → 数字人播报</p>
      <div class="flow-steps">
        <span>问诊量表</span>
        <span>舌象上传</span>
        <span>四诊结构化</span>
        <span>体质评分</span>
        <span>知识库解释</span>
        <span>数字人播报</span>
      </div>
    </section>
  </section>
</template>

<style scoped>
.architecture-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.architecture-card {
  position: relative;
  min-height: 188px;
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.architecture-card__index {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  margin-bottom: 10px;
  color: #ffffff;
  background: #1f78b4;
  border-radius: 50%;
  font-weight: 700;
}

.architecture-card h3 {
  margin: 0 0 8px;
  color: #10466f;
  font-size: 18px;
}

.architecture-card p {
  margin: 0 0 14px;
  color: #344d60;
  line-height: 1.75;
}

.flow-surface {
  margin-top: 18px;
  padding: 18px;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.flow-surface h3 {
  margin: 0 0 14px;
  color: #10466f;
}

.flow-caption {
  margin: 0 0 14px;
  color: #344d60;
  font-weight: 700;
  line-height: 1.7;
}

.flow-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.flow-steps span {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  color: #10466f;
  background: #ffffff;
  border: 1px solid #c8e0ed;
  border-radius: 8px;
  font-weight: 700;
}

.flow-steps span:not(:last-child)::after {
  content: "→";
  position: absolute;
  right: -14px;
  color: #6d8494;
}

@media (max-width: 880px) {
  .architecture-grid {
    grid-template-columns: 1fr;
  }

  .flow-steps {
    align-items: stretch;
    flex-direction: column;
  }

  .flow-steps span {
    justify-content: center;
  }

  .flow-steps span:not(:last-child)::after {
    content: "↓";
    right: auto;
    bottom: -16px;
  }
}
</style>
