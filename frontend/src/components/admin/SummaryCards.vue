<script setup lang="ts">
import type { AnalyticsSummary } from "@/types/adminRecords";

defineProps<{
  summary: AnalyticsSummary;
}>();

const cards = [
  { key: "total_records", label: "总辨识次数" },
  { key: "today_records", label: "今日辨识次数" },
  { key: "tongue_upload_count", label: "舌象上传次数" },
  { key: "rag_success_count", label: "RAG 成功次数" },
  { key: "rag_fallback_count", label: "RAG fallback 次数" },
  { key: "digital_human_text_count", label: "数字人播报文本数" },
] as const;
</script>

<template>
  <div class="summary-card-grid">
    <article v-for="card in cards" :key="card.key" class="admin-summary-card">
      <span>{{ card.label }}</span>
      <strong>{{ summary[card.key] ?? 0 }}</strong>
    </article>
  </div>
</template>

<style scoped>
.summary-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
}

.admin-summary-card {
  min-height: 96px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.admin-summary-card span {
  display: block;
  margin-bottom: 10px;
  color: #6d8494;
  font-size: 13px;
}

.admin-summary-card strong {
  color: #10466f;
  font-size: 28px;
  line-height: 1.2;
}
</style>
