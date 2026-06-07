<script setup lang="ts">
import { computed } from "vue";
import type { DigitalHumanSubtitle } from "@/api/digitalHuman";

const props = withDefaults(
  defineProps<{
    subtitles: DigitalHumanSubtitle[];
    speaking: boolean;
    currentTime?: number;
    broadcastText?: string;
  }>(),
  {
    currentTime: 0,
    broadcastText: "",
  },
);

const activeIndex = computed(() => {
  if (!props.speaking || props.subtitles.length === 0) return -1;
  const exactIndex = props.subtitles.findIndex(
    (item) => props.currentTime >= Number(item.start) && props.currentTime < Number(item.end),
  );
  if (exactIndex >= 0) return exactIndex;
  return props.currentTime > 0 ? props.subtitles.length - 1 : 0;
});
</script>

<template>
  <section class="subtitle-panel">
    <div class="subtitle-panel__header">
      <h3>字幕</h3>
      <el-tag :type="speaking ? 'success' : 'info'" effect="light">{{ speaking ? "播报中" : "待机" }}</el-tag>
    </div>

    <ol v-if="subtitles.length" class="subtitle-panel__list">
      <li
        v-for="(item, index) in subtitles"
        :key="`${item.start}-${item.end}-${item.text}`"
        :class="{ 'subtitle-panel__item--active': index === activeIndex }"
        class="subtitle-panel__item"
      >
        <span class="subtitle-panel__time">{{ Number(item.start).toFixed(1) }}s - {{ Number(item.end).toFixed(1) }}s</span>
        <p>{{ item.text }}</p>
      </li>
    </ol>
    <el-empty v-else description="暂无字幕" />

    <div v-if="!speaking && broadcastText" class="subtitle-panel__full">
      <span>完整播报文本</span>
      <p>{{ broadcastText }}</p>
    </div>
  </section>
</template>

<style scoped>
.subtitle-panel {
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.subtitle-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.subtitle-panel__header h3 {
  margin: 0;
  color: #10466f;
}

.subtitle-panel__list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.subtitle-panel__item {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  gap: 12px;
  padding: 10px 12px;
  background: #f7fbff;
  border: 1px solid #e0edf5;
  border-radius: 8px;
}

.subtitle-panel__item--active {
  background: #eef9f5;
  border-color: #9fd4c4;
  box-shadow: 0 0 0 2px rgba(61, 168, 131, 0.08);
}

.subtitle-panel__time {
  color: #6d8494;
  font-size: 13px;
}

.subtitle-panel__item p,
.subtitle-panel__full p {
  margin: 0;
  color: #263b4a;
  line-height: 1.75;
}

.subtitle-panel__full {
  margin-top: 14px;
  padding: 12px;
  background: #eef7fb;
  border-radius: 8px;
}

.subtitle-panel__full span {
  display: block;
  margin-bottom: 6px;
  color: #10466f;
  font-weight: 700;
}

@media (max-width: 680px) {
  .subtitle-panel__item {
    grid-template-columns: 1fr;
  }
}
</style>
