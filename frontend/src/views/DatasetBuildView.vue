<script setup lang="ts">
import { computed, ref } from "vue";
import { RefreshRight } from "@element-plus/icons-vue";

import { buildDataset, looksLikeMojibake, type ApiFriendlyError, type DatasetBuildResponse } from "@/api/tcmApi";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const loading = ref(false);
const result = ref<DatasetBuildResponse | null>(null);
const error = ref<ApiFriendlyError | null>(null);
const hasMojibake = computed(() => looksLikeMojibake(result.value));

async function submit() {
  loading.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await buildDataset(props.apiBaseUrl);
  } catch (err) {
    error.value = err as ApiFriendlyError;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="tool-surface">
    <div class="view-heading">
      <div>
        <h2>数据集与微调</h2>
        <p>调用后端 LangGraph 数据治理流水线，刷新 demo SFT、MM-SFT、训练配置和质量报告。</p>
      </div>
    </div>
    <el-button type="primary" size="large" :icon="RefreshRight" :loading="loading" @click="submit">
      构建 / 刷新知识库
    </el-button>
  </section>

  <el-alert v-if="error" class="page-alert" :title="error.message" type="warning" :closable="false" show-icon>
    <el-collapse class="error-detail">
      <el-collapse-item title="技术详情" name="error">
        <pre>{{ JSON.stringify(error, null, 2) }}</pre>
      </el-collapse-item>
    </el-collapse>
  </el-alert>

  <el-alert
    v-if="hasMojibake"
    class="page-alert"
    title="检测到后端返回疑似乱码，请检查知识库文件读取编码或 FastAPI 返回编码。"
    type="warning"
    :closable="false"
    show-icon
  />

  <section v-if="result" class="result-section">
    <el-alert
      :title="result.status === 'success' ? '知识库构建成功' : '知识库构建接口已返回结果'"
      :type="result.status === 'success' ? 'success' : 'info'"
      :closable="false"
      show-icon
    />

    <div v-if="result.summary" class="summary-grid">
      <div v-for="(value, key) in result.summary" :key="key" class="summary-card">
        <span>{{ key }}</span>
        <strong>{{ value }}</strong>
      </div>
    </div>

    <section class="tool-surface">
      <h3>返回信息</h3>
      <pre class="json-box">{{ JSON.stringify(result, null, 2) }}</pre>
    </section>
  </section>
</template>
