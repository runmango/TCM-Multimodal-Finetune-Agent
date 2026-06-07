<script setup lang="ts">
import { Connection, Refresh } from "@element-plus/icons-vue";
import { onMounted, ref, watch } from "vue";
import { checkBackend, type ApiFriendlyError, type BackendStatus } from "@/api/tcmApi";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const loading = ref(false);
const status = ref<BackendStatus | null>(null);

async function refreshStatus() {
  loading.value = true;
  status.value = await checkBackend(props.apiBaseUrl);
  loading.value = false;
}

watch(
  () => props.apiBaseUrl,
  () => {
    refreshStatus();
  },
);

onMounted(refreshStatus);

defineExpose({ refreshStatus });

function detailText(error?: ApiFriendlyError) {
  return error ? JSON.stringify(error, null, 2) : "";
}
</script>

<template>
  <section class="status-panel">
    <div class="status-panel__row">
      <el-icon><Connection /></el-icon>
      <span class="status-panel__title">后端连接状态</span>
      <el-button size="small" :icon="Refresh" :loading="loading" @click="refreshStatus">检测</el-button>
    </div>

    <el-alert
      v-if="status?.connected"
      title="后端已连接"
      type="success"
      :closable="false"
      show-icon
    />
    <el-alert
      v-else
      title="后端未连接，请先启动 FastAPI 服务"
      type="warning"
      :closable="false"
      show-icon
    />

    <p v-if="status?.endpoint" class="status-panel__endpoint">检测接口：{{ status.endpoint }}</p>
    <el-collapse v-if="status?.error" class="status-panel__detail">
      <el-collapse-item title="技术详情" name="detail">
        <pre>{{ detailText(status.error) }}</pre>
      </el-collapse-item>
    </el-collapse>
  </section>
</template>

