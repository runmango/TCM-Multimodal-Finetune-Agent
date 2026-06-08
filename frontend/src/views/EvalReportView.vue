<template>
  <section class="tool-surface">
    <div class="view-heading">
      <div>
        <h2>评估报告</h2>
        <p>展示训练与推理效果评估的工程入口，报告文件由 CLI 生成。</p>
      </div>
      <el-tag size="large" effect="light">Eval</el-tag>
    </div>

    <div class="summary-grid">
      <div class="summary-card accent">
        <span>默认报告</span>
        <strong>reports/eval_report.json</strong>
      </div>
      <div class="summary-card">
        <span>评估集</span>
        <strong>data/eval/tcm_eval.jsonl</strong>
      </div>
      <div class="summary-card">
        <span>演示指标</span>
        <strong>准确率 / 安全率 / 格式合规</strong>
      </div>
    </div>

    <section class="tool-surface">
      <h3>常用命令</h3>
      <pre class="json-box">python -m app.cli eval run --train-mode safe --eval-mode simulation
python -m app.cli eval run --train-mode safe --eval-mode rule</pre>
    </section>

    <el-alert
      title="当前页面只作为演示入口，后续可新增 /api/v1/eval/report 接口读取 JSON 并图表化展示。"
      type="info"
      :closable="false"
      show-icon
    />
  </section>
</template>
