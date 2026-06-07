<script setup lang="ts">
import { computed, ref } from "vue";
import { DataAnalysis } from "@element-plus/icons-vue";

import {
  asList,
  collectReferenceItems,
  inferConstitution,
  looksLikeMojibake,
  pickText,
  type ApiFriendlyError,
  type InferenceResponse,
} from "@/api/tcmApi";
import ResultCard from "@/components/ResultCard.vue";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const query = ref("我最近乏力气短，自汗，舌淡有齿痕，想了解体质倾向。");
const topK = ref(3);
const loading = ref(false);
const result = ref<InferenceResponse | null>(null);
const error = ref<ApiFriendlyError | null>(null);

const constitution = computed(() =>
  pickText(result.value, ["constitution", "result", "type", "constitution_type", "label"], "未返回"),
);
const analysis = computed(() => pickText(result.value, ["answer", "analysis", "conclusion"], "后端未返回分析结论。"));
const safety = computed(() => (result.value?.safety || {}) as Record<string, unknown>);
const symptoms = computed(() => asList<string>(result.value?.symptoms || result.value?.matched_symptoms));
const references = computed(() => collectReferenceItems(result.value));
const hasMojibake = computed(() => looksLikeMojibake(result.value));

async function submit() {
  loading.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await inferConstitution({ query: query.value, top_k: topK.value }, props.apiBaseUrl);
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
        <h2>体质辨识</h2>
        <p>输入症状、舌象或体质相关描述，系统将结合规则判断与 RAG 证据返回体质倾向。</p>
      </div>
    </div>

    <el-form label-position="top" class="demo-form">
      <el-form-item label="症状描述">
        <el-input v-model="query" type="textarea" :rows="5" maxlength="500" show-word-limit />
      </el-form-item>
      <div class="form-actions">
        <el-form-item label="top_k">
          <el-input-number v-model="topK" :min="1" :max="10" />
        </el-form-item>
        <el-button type="primary" :icon="DataAnalysis" :loading="loading" @click="submit">开始体质辨识</el-button>
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

  <section v-if="result" class="result-section">
    <div class="summary-grid">
      <div class="summary-card accent">
        <span>体质倾向</span>
        <strong>{{ constitution }}</strong>
      </div>
      <div class="summary-card">
        <span>置信度</span>
        <strong>{{ pickText(result, ["confidence"], "-") }}</strong>
      </div>
      <div class="summary-card">
        <span>安全状态</span>
        <strong>{{ pickText(safety, ["status"], "unknown") }}</strong>
      </div>
    </div>

    <section class="tool-surface">
      <h3>分析结论</h3>
      <el-alert
        :title="analysis"
        :type="pickText(safety, ['status']) === 'refused' ? 'warning' : 'success'"
        :closable="false"
        show-icon
      />

      <h3>匹配依据</h3>
      <div class="tag-row">
        <el-tag v-for="symptom in symptoms" :key="symptom" effect="light">{{ symptom }}</el-tag>
        <el-tag v-if="symptoms.length === 0" type="info" effect="plain">未返回明确症状匹配</el-tag>
      </div>
    </section>

    <section class="result-list">
      <div class="list-title">参考知识</div>
      <ResultCard v-for="(item, index) in references" :key="`${item.id || index}`" :item="item" :index="index + 1" />
      <el-empty v-if="references.length === 0" description="暂无参考知识返回" />
    </section>
  </section>
</template>

