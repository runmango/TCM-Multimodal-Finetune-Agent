<script setup lang="ts">
import { computed } from "vue";
import type { EvidenceItem } from "@/api/tcmApi";

const props = defineProps<{
  item: EvidenceItem;
  index?: number;
}>();

const title = computed(() => String(props.item.title || props.item.name || `参考知识 ${props.index || ""}`).trim());
const content = computed(() => String(props.item.content || props.item.text || props.item.answer || "暂无内容").trim());
const sourceType = computed(() => String(props.item.source_type || props.item.type || "unknown").trim());
const itemId = computed(() => String(props.item.id || props.item.source_id || "-").trim());
const tags = computed(() => {
  const rawTags = props.item.tags || props.item.labels;
  return Array.isArray(rawTags) ? rawTags.map((tag) => String(tag)).filter(Boolean) : [];
});
const scoreText = computed(() => {
  const score = props.item.score;
  if (score === undefined || score === null || score === "") return "-";
  const numeric = Number(score);
  return Number.isFinite(numeric) ? numeric.toFixed(3) : String(score);
});
</script>

<template>
  <el-card class="result-card" shadow="never">
    <template #header>
      <div class="result-card__header">
        <div class="result-card__title">{{ title }}</div>
        <el-tag type="info" effect="plain">score {{ scoreText }}</el-tag>
      </div>
    </template>

    <p class="result-card__content">{{ content }}</p>

    <div class="result-card__tags">
      <el-tag v-for="tag in tags" :key="tag" effect="light" round>{{ tag }}</el-tag>
      <el-tag v-if="tags.length === 0" type="info" effect="plain" round>无标签</el-tag>
    </div>

    <div class="result-card__meta">
      <span>source_type: <strong>{{ sourceType }}</strong></span>
      <span>ID: <strong>{{ itemId }}</strong></span>
    </div>
  </el-card>
</template>

