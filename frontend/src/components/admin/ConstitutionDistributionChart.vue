<script setup lang="ts">
import { computed } from "vue";

import type { ConstitutionDistributionItem } from "@/types/adminRecords";

const props = defineProps<{
  items: ConstitutionDistributionItem[];
}>();

const maxCount = computed(() => Math.max(1, ...props.items.map((item) => item.count)));
const total = computed(() => props.items.reduce((sum, item) => sum + item.count, 0));
</script>

<template>
  <section class="admin-panel">
    <div class="panel-heading">
      <h2>主倾向体质分布</h2>
      <el-tag effect="light">{{ total }} 条记录</el-tag>
    </div>

    <el-empty v-if="total === 0" description="暂无记录" />
    <div v-else class="distribution-list">
      <div v-for="item in items" :key="item.name" class="distribution-row">
        <span class="distribution-name">{{ item.name }}</span>
        <div class="distribution-bar">
          <i :style="{ width: `${Math.max(4, (item.count / maxCount) * 100)}%` }" />
        </div>
        <strong>{{ item.count }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.admin-panel {
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.panel-heading h2 {
  margin: 0;
  color: #10466f;
  font-size: 20px;
}

.distribution-list {
  display: grid;
  gap: 10px;
}

.distribution-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) 42px;
  gap: 12px;
  align-items: center;
}

.distribution-name {
  color: #10466f;
  font-weight: 700;
}

.distribution-bar {
  height: 12px;
  overflow: hidden;
  background: #edf6fb;
  border-radius: 999px;
}

.distribution-bar i {
  display: block;
  height: 100%;
  background: #1f78b4;
  border-radius: inherit;
}

.distribution-row strong {
  color: #344d60;
}
</style>
