<script setup lang="ts">
import type { RecordSummary } from "@/types/adminRecords";

defineProps<{
  records: RecordSummary[];
  loading: boolean;
}>();

const emit = defineEmits<{
  view: [sessionId: string];
}>();
</script>

<template>
  <section class="admin-panel">
    <div class="panel-heading">
      <h2>历史体质辨识记录</h2>
      <el-tag effect="light">{{ records.length }} 条</el-tag>
    </div>

    <el-table :data="records" :loading="loading" border stripe empty-text="暂无记录">
      <el-table-column prop="created_at" label="时间" min-width="170" />
      <el-table-column prop="session_id" label="Session ID" min-width="180" />
      <el-table-column prop="primary_constitution" label="主倾向体质" width="130" />
      <el-table-column label="兼夹体质" min-width="150">
        <template #default="{ row }">
          {{ row.secondary_constitutions?.length ? row.secondary_constitutions.join("、") : "无" }}
        </template>
      </el-table-column>
      <el-table-column prop="algorithm_version" label="算法版本" min-width="150" />
      <el-table-column prop="retriever_type" label="RAG 类型" width="110" />
      <el-table-column label="fallback" width="100">
        <template #default="{ row }">
          <el-tag :type="row.fallback_used ? 'warning' : 'success'" effect="plain">
            {{ row.fallback_used ? "是" : "否" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="舌象" width="90">
        <template #default="{ row }">
          <el-tag :type="row.tongue_image_url ? 'success' : 'info'" effect="plain">
            {{ row.tongue_image_url ? "已上传" : "无" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="emit('view', row.session_id)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>
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
</style>
