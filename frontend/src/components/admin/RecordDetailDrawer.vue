<script setup lang="ts">
import { computed } from "vue";
import { ElMessage } from "element-plus";

import { normalizeBaseUrl } from "@/api/tcmApi";
import type { RecordDetail, RagSource } from "@/types/adminRecords";

const props = defineProps<{
  modelValue: boolean;
  detail: RecordDetail | null;
  loading: boolean;
  apiBaseUrl: string;
  mainFrontendUrl: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
}>();

const drawerVisible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit("update:modelValue", value),
});

const scoreRows = computed(() =>
  Object.entries(props.detail?.scores || {}).map(([name, score]) => ({
    name,
    score,
    judgement: props.detail?.constitution_judgements?.[name] || "信息不足",
  })),
);

const fourDiagnosisJson = computed(() => JSON.stringify(props.detail?.four_diagnosis || {}, null, 2));
const tongueImageUrl = computed(() => resolveAssetUrl(props.detail?.tongue_image_url || props.detail?.four_diagnosis?.inspection?.tongue_image_url));
const ragSources = computed(() => props.detail?.rag_sources || []);

function sectionEntries(section: Record<string, unknown> | undefined): Array<[string, unknown]> {
  return Object.entries(section || {}).filter(([, value]) => value !== null && value !== undefined && value !== "" && JSON.stringify(value) !== "{}");
}

function sourceText(source: RagSource): string {
  return String(source.text || source.title || source.section || source.source_id || "未命名来源");
}

function judgementType(judgement: string): "success" | "warning" | "info" | "danger" {
  if (judgement === "是" || judgement === "基本是") return "success";
  if (judgement === "倾向是") return "warning";
  if (judgement === "信息不足") return "info";
  return "danger";
}

async function copyBroadcastText() {
  const text = props.detail?.broadcast_text || "";
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success("播报文本已复制。");
  } catch {
    ElMessage.warning("复制失败，请手动选择文本复制。");
  }
}

function jumpToDigitalHuman() {
  const text = props.detail?.broadcast_text || "";
  if (!text) return;
  localStorage.setItem("digital_human_speak_text", text);
  localStorage.setItem("digital_human_scene", "constitution_result");
  window.location.href = `${normalizeBaseUrl(props.mainFrontendUrl)}/digital-human`;
}

function resolveAssetUrl(value: unknown): string {
  const path = String(value || "").trim();
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${normalizeBaseUrl(props.apiBaseUrl)}${path.startsWith("/") ? path : `/${path}`}`;
}
</script>

<template>
  <el-drawer v-model="drawerVisible" size="64%" title="体质辨识记录详情">
    <el-skeleton v-if="loading" :rows="8" animated />
    <el-empty v-else-if="!detail" description="暂无详情" />
    <div v-else class="detail-content">
      <section class="detail-summary">
        <div>
          <span>Session ID</span>
          <strong>{{ detail.session_id }}</strong>
        </div>
        <div>
          <span>主倾向体质</span>
          <strong>{{ detail.primary_constitution }}</strong>
        </div>
        <div>
          <span>算法版本</span>
          <strong>{{ detail.algorithm_version }}</strong>
        </div>
        <div>
          <span>RAG</span>
          <strong>{{ detail.retriever_type }} / {{ detail.fallback_used ? "fallback" : "success" }}</strong>
        </div>
      </section>

      <el-tabs>
        <el-tab-pane label="四诊详情">
          <div v-if="tongueImageUrl" class="tongue-preview">
            <img :src="tongueImageUrl" alt="舌象图片预览" />
          </div>

          <div class="four-grid">
            <section class="detail-card">
              <h3>望诊 inspection</h3>
              <el-empty v-if="sectionEntries(detail.four_diagnosis?.inspection).length === 0" description="暂无数据" />
              <p v-for="[key, value] in sectionEntries(detail.four_diagnosis?.inspection)" :key="key">
                <span>{{ key }}</span><strong>{{ value }}</strong>
              </p>
            </section>
            <section class="detail-card">
              <h3>闻诊 auscultation_olfaction</h3>
              <el-empty v-if="sectionEntries(detail.four_diagnosis?.auscultation_olfaction).length === 0" description="暂无数据" />
              <p v-for="[key, value] in sectionEntries(detail.four_diagnosis?.auscultation_olfaction)" :key="key">
                <span>{{ key }}</span><strong>{{ value }}</strong>
              </p>
            </section>
            <section class="detail-card">
              <h3>问诊 inquiry</h3>
              <el-empty v-if="sectionEntries(detail.four_diagnosis?.inquiry).length === 0" description="暂无数据" />
              <p v-for="[key, value] in sectionEntries(detail.four_diagnosis?.inquiry)" :key="key">
                <span>{{ key }}</span><strong>{{ typeof value === "object" ? JSON.stringify(value) : value }}</strong>
              </p>
            </section>
            <section class="detail-card">
              <h3>切诊 palpation</h3>
              <el-empty v-if="sectionEntries(detail.four_diagnosis?.palpation).length === 0" description="暂无数据" />
              <p v-for="[key, value] in sectionEntries(detail.four_diagnosis?.palpation)" :key="key">
                <span>{{ key }}</span><strong>{{ value }}</strong>
              </p>
            </section>
          </div>

          <h3 class="block-title">四诊 JSON 原文</h3>
          <pre class="json-box">{{ fourDiagnosisJson }}</pre>
        </el-tab-pane>

        <el-tab-pane label="体质评分">
          <el-table :data="scoreRows" border stripe>
            <el-table-column prop="name" label="体质" />
            <el-table-column prop="score" label="转化分" />
            <el-table-column label="判定">
              <template #default="{ row }">
                <el-tag :type="judgementType(row.judgement)" effect="light">{{ row.judgement }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="RAG 来源">
          <el-alert :title="detail.rag_explanation" type="info" :closable="false" show-icon />
          <div class="rag-meta">
            <el-tag effect="light">检索类型：{{ detail.retriever_type }}</el-tag>
            <el-tag :type="detail.fallback_used ? 'warning' : 'success'" effect="light">
              fallback：{{ detail.fallback_used ? "是" : "否" }}
            </el-tag>
          </div>
          <el-empty v-if="ragSources.length === 0" description="暂无引用来源，已使用安全兜底解释。" />
          <el-card v-for="source in ragSources" :key="source.chunk_id || source.source_id || sourceText(source)" class="source-card" shadow="never">
            <h3>{{ source.section || source.title || source.source || "未命名来源" }}</h3>
            <p>{{ sourceText(source) }}</p>
            <div class="source-meta">
              <span>source：{{ source.source || source.source_type || "-" }}</span>
              <span>chunk_id：{{ source.chunk_id || "-" }}</span>
              <span>score：{{ source.score ?? "-" }}</span>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="播报文本">
          <div class="broadcast-box">{{ detail.broadcast_text }}</div>
          <div class="drawer-actions">
            <el-button type="primary" plain @click="copyBroadcastText">复制播报文本</el-button>
            <el-button type="primary" @click="jumpToDigitalHuman">跳转数字人播报</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-drawer>
</template>

<style scoped>
.detail-content {
  display: grid;
  gap: 16px;
}

.detail-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.detail-summary div,
.detail-card {
  padding: 14px;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.detail-summary span {
  display: block;
  margin-bottom: 6px;
  color: #6d8494;
  font-size: 13px;
}

.detail-summary strong {
  color: #10466f;
  word-break: break-word;
}

.tongue-preview {
  margin-bottom: 14px;
}

.tongue-preview img {
  width: 100%;
  max-height: 240px;
  object-fit: contain;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.four-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-card h3,
.block-title,
.source-card h3 {
  margin: 0 0 10px;
  color: #10466f;
}

.detail-card p {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 8px;
  margin: 8px 0;
  color: #344d60;
}

.detail-card p span {
  color: #6d8494;
}

.json-box,
.broadcast-box {
  padding: 14px;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
  line-height: 1.8;
}

.rag-meta,
.source-meta,
.drawer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.source-card {
  margin-top: 12px;
  border-color: #dceaf3;
  border-radius: 8px;
}

.source-card p {
  margin: 0;
  color: #344d60;
  line-height: 1.8;
}

.source-meta {
  color: #6d8494;
  font-size: 13px;
}

@media (max-width: 860px) {
  .four-grid {
    grid-template-columns: 1fr;
  }
}
</style>
