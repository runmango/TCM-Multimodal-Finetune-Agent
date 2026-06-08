<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { ChatDotRound, Service } from "@element-plus/icons-vue";

import { askKnowledge, type KnowledgeAskResponse } from "@/api/knowledge";
import type { ApiFriendlyError } from "@/api/tcmApi";
import SafetyNotice from "@/components/SafetyNotice.vue";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const SAFETY_NOTICE = "仅供健康科普参考，不替代医生诊疗。";
const router = useRouter();

const query = ref("气虚质有哪些表现？如何调养？");
const topK = ref(3);
const voice = ref("zh-CN-XiaoxiaoNeural");
const loading = ref(false);
const result = ref<KnowledgeAskResponse | null>(null);
const error = ref<ApiFriendlyError | null>(null);

const sourceCount = computed(() => result.value?.sources?.length || 0);

async function submit() {
  loading.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await askKnowledge(query.value, topK.value, props.apiBaseUrl);
  } catch (err) {
    error.value = err as ApiFriendlyError;
  } finally {
    loading.value = false;
  }
}

async function speakAnswer() {
  if (!result.value?.answer) return;
  const speakText = result.value.answer.includes(result.value.safety_notice)
    ? result.value.answer
    : `${result.value.answer}${result.value.safety_notice}`;
  localStorage.setItem("digital_human_speak_text", speakText);
  localStorage.setItem("digital_human_scene", "knowledge_answer");
  void router.push("/digital-human");
}

</script>

<template>
  <section class="tool-surface">
    <div class="view-heading">
      <div>
        <h2>中医知识问答</h2>
        <p>开放式输入只用于知识解释和健康科普，不直接进行体质判定。</p>
      </div>
      <el-tag size="large" effect="light">Knowledge QA</el-tag>
    </div>

    <el-form label-position="top" class="demo-form">
      <el-form-item label="中医相关问题">
        <el-input v-model="query" type="textarea" :rows="5" maxlength="500" show-word-limit />
      </el-form-item>
      <div class="form-actions">
        <el-form-item label="top_k">
          <el-input-number v-model="topK" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="播报音色">
          <el-input v-model="voice" class="voice-input" />
        </el-form-item>
        <el-button type="primary" :icon="ChatDotRound" :loading="loading" @click="submit">开始问答</el-button>
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

  <section v-if="result" class="result-section">
    <div class="summary-grid">
      <div class="summary-card accent">
        <span>问答状态</span>
        <strong>已生成</strong>
      </div>
      <div class="summary-card">
        <span>来源数量</span>
        <strong>{{ sourceCount }}</strong>
      </div>
      <div class="summary-card">
        <span>安全提示</span>
        <strong>已附加</strong>
      </div>
    </div>

    <section class="tool-surface">
      <h3>回答</h3>
      <el-alert :title="result.answer" type="success" :closable="false" show-icon />
      <div class="question-actions">
        <el-button type="primary" plain :icon="Service" @click="speakAnswer">
          让数字人播报此回答
        </el-button>
      </div>
    </section>

    <section class="result-list">
      <div class="list-title">参考来源</div>
      <el-card v-for="source in result.sources" :key="source.source_id" class="result-card" shadow="never">
        <div class="result-card__header">
          <div class="result-card__title">{{ source.title || "未命名来源" }}</div>
          <el-tag effect="light">{{ source.source_type }}</el-tag>
        </div>
        <div class="result-card__meta">
          <span>ID：{{ source.source_id }}</span>
          <span>score：{{ source.score ?? "-" }}</span>
        </div>
      </el-card>
      <el-empty v-if="result.sources.length === 0" description="未命中本地知识来源，已返回安全兜底回答" />
    </section>
  </section>

  <SafetyNotice :text="result?.safety_notice || SAFETY_NOTICE" />
</template>

<style scoped>
.voice-input {
  width: 240px;
}

.question-actions {
  margin-top: 14px;
}

</style>
