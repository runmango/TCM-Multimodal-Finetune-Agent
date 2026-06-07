<script setup lang="ts">
import { computed, ref } from "vue";
import { Search } from "@element-plus/icons-vue";

import {
  collectReferenceItems,
  looksLikeMojibake,
  searchRag,
  type ApiFriendlyError,
  type RAGResponse,
} from "@/api/tcmApi";
import ResultCard from "@/components/ResultCard.vue";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const query = ref("乏力气短舌淡齿痕");
const topK = ref(3);
const loading = ref(false);
const result = ref<RAGResponse | null>(null);
const error = ref<ApiFriendlyError | null>(null);

const results = computed(() => collectReferenceItems(result.value));
const hasMojibake = computed(() => looksLikeMojibake(result.value));

async function submit() {
  loading.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await searchRag({ query: query.value, top_k: topK.value }, props.apiBaseUrl);
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
        <h2>知识库检索</h2>
        <p>输入关键词，检索中医知识库、体质样例和舌象多模态样例。</p>
      </div>
    </div>

    <el-form label-position="top" class="demo-form">
      <el-form-item label="检索关键词">
        <el-input v-model="query" clearable />
      </el-form-item>
      <div class="form-actions">
        <el-form-item label="top_k">
          <el-input-number v-model="topK" :min="1" :max="10" />
        </el-form-item>
        <el-button type="primary" :icon="Search" :loading="loading" @click="submit">开始检索</el-button>
      </div>
    </el-form>
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

  <section v-if="result" class="result-list">
    <div class="list-title">检索结果</div>
    <el-alert
      v-if="results.length > 0"
      :title="`检索完成，共返回 ${results.length} 条结果。`"
      type="success"
      :closable="false"
      show-icon
    />
    <ResultCard v-for="(item, index) in results" :key="`${item.id || index}`" :item="item" :index="index + 1" />
    <el-empty v-if="results.length === 0" description="未检索到相关知识条目" />
  </section>
</template>

