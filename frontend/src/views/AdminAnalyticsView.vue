<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { Refresh } from "@element-plus/icons-vue";

import {
  getAnalyticsSummary,
  getConstitutionDistribution,
  getRecordDetail,
  getRecords,
  type RecordListParams,
} from "@/api/adminAnalytics";
import { DEFAULT_API_BASE_URL, type ApiFriendlyError } from "@/api/tcmApi";
import ConstitutionDistributionChart from "@/components/admin/ConstitutionDistributionChart.vue";
import RecordDetailDrawer from "@/components/admin/RecordDetailDrawer.vue";
import RecordTable from "@/components/admin/RecordTable.vue";
import SummaryCards from "@/components/admin/SummaryCards.vue";
import type {
  AnalyticsSummary,
  ConstitutionDistributionItem,
  RecordDetail,
  RecordSummary,
} from "@/types/adminRecords";

const MAIN_FRONTEND_URL = import.meta.env.VITE_MAIN_FRONTEND_URL || "http://127.0.0.1:5173";
const constitutions = ["平和质", "气虚质", "阳虚质", "阴虚质", "痰湿质", "湿热质", "血瘀质", "气郁质", "特禀质"];

const apiBaseUrl = ref(DEFAULT_API_BASE_URL);
const loading = ref(false);
const detailLoading = ref(false);
const drawerVisible = ref(false);
const error = ref<ApiFriendlyError | null>(null);
const summary = ref<AnalyticsSummary>(emptySummary());
const distribution = ref<ConstitutionDistributionItem[]>(constitutions.map((name) => ({ name, count: 0 })));
const records = ref<RecordSummary[]>([]);
const total = ref(0);
const detail = ref<RecordDetail | null>(null);
const filters = reactive({
  primary_constitution: "",
  date_range: [] as string[],
  limit: 20,
  offset: 0,
});

onMounted(loadDashboard);

async function loadDashboard() {
  loading.value = true;
  error.value = null;
  try {
    const [summaryData, distributionData, recordData] = await Promise.all([
      getAnalyticsSummary(apiBaseUrl.value).catch(() => emptySummary()),
      getConstitutionDistribution(apiBaseUrl.value).catch(() => ({ constitution_distribution: distribution.value })),
      getRecords(buildRecordParams(), apiBaseUrl.value),
    ]);
    summary.value = summaryData;
    distribution.value = normalizeDistribution(distributionData.constitution_distribution);
    records.value = recordData.items || recordData.records || [];
    total.value = recordData.total || records.value.length;
  } catch (err) {
    error.value = err as ApiFriendlyError;
    summary.value = emptySummary();
    records.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

async function openDetail(sessionId: string) {
  detailLoading.value = true;
  drawerVisible.value = true;
  detail.value = null;
  error.value = null;
  try {
    detail.value = await getRecordDetail(sessionId, apiBaseUrl.value);
  } catch (err) {
    error.value = err as ApiFriendlyError;
  } finally {
    detailLoading.value = false;
  }
}

function buildRecordParams(): RecordListParams {
  return {
    limit: filters.limit,
    offset: filters.offset,
    primary_constitution: filters.primary_constitution || undefined,
    date_from: filters.date_range?.[0],
    date_to: filters.date_range?.[1],
  };
}

function normalizeDistribution(items: ConstitutionDistributionItem[]): ConstitutionDistributionItem[] {
  const counts = new Map(items.map((item) => [item.name, item.count]));
  return constitutions.map((name) => ({ name, count: counts.get(name) || 0 }));
}

function emptySummary(): AnalyticsSummary {
  return {
    total_records: 0,
    today_records: 0,
    tongue_upload_count: 0,
    rag_success_count: 0,
    rag_fallback_count: 0,
    digital_human_text_count: 0,
  };
}
</script>

<template>
  <div class="admin-page">
    <header class="admin-header">
      <div>
        <h1>中医体质辨识数据记录与分析后台</h1>
        <p>用于查看体质辨识历史记录、四诊结构化数据、知识库来源和数字人播报文本。</p>
      </div>
    </header>

    <el-alert
      class="admin-alert"
      title="本后台仅用于技术演示、数据追踪和系统评估，不作为临床诊断依据。"
      type="info"
      :closable="false"
      show-icon
    />

    <section class="admin-toolbar">
      <el-form label-position="top" class="filter-form">
        <el-form-item label="后端服务地址">
          <el-input v-model="apiBaseUrl" clearable placeholder="http://127.0.0.1:8010" />
        </el-form-item>
        <el-form-item label="主倾向体质筛选">
          <el-select v-model="filters.primary_constitution" clearable placeholder="全部体质">
            <el-option v-for="name in constitutions" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围筛选">
          <el-date-picker
            v-model="filters.date_range"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item label=" ">
          <el-button type="primary" :icon="Refresh" :loading="loading" @click="loadDashboard">刷新</el-button>
        </el-form-item>
      </el-form>
    </section>

    <el-alert v-if="error" class="admin-alert" :title="error.message" type="warning" :closable="false" show-icon>
      <el-collapse class="error-detail">
        <el-collapse-item title="技术详情" name="detail">
          <pre>{{ JSON.stringify(error, null, 2) }}</pre>
        </el-collapse-item>
      </el-collapse>
    </el-alert>

    <SummaryCards :summary="summary" />

    <div class="analytics-grid">
      <ConstitutionDistributionChart :items="distribution" />
      <section class="admin-panel">
        <div class="panel-heading">
          <h2>数据追踪说明</h2>
        </div>
        <ul>
          <li>历史记录来自 SQLite 表 `constitution_records` 与 `four_diagnosis_records`。</li>
          <li>RAG 来源和 fallback 状态来自 `rag_trace_records`。</li>
          <li>本后台不采集姓名、手机号、身份证号等个人敏感信息。</li>
        </ul>
      </section>
    </div>

    <RecordTable :records="records" :loading="loading" @view="openDetail" />

    <div class="pagination-row">
      <span>共 {{ total }} 条</span>
      <el-pagination
        layout="prev, pager, next"
        :total="total"
        :page-size="filters.limit"
        :current-page="Math.floor(filters.offset / filters.limit) + 1"
        @current-change="(page: number) => { filters.offset = (page - 1) * filters.limit; loadDashboard(); }"
      />
    </div>

    <RecordDetailDrawer
      v-model="drawerVisible"
      :detail="detail"
      :loading="detailLoading"
      :api-base-url="apiBaseUrl"
      :main-frontend-url="MAIN_FRONTEND_URL"
    />
  </div>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  padding: 24px;
  color: #1f3343;
  background: #f5f9fc;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  margin-bottom: 16px;
  padding: 22px 24px;
  color: #ffffff;
  background: #1f78b4;
  border-radius: 8px;
}

.admin-header h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.25;
}

.admin-header p {
  margin: 8px 0 0;
  color: #d9eefb;
}

.admin-alert,
.admin-toolbar,
.analytics-grid,
.pagination-row {
  margin-bottom: 16px;
}

.admin-toolbar,
.admin-panel {
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.filter-form {
  display: grid;
  grid-template-columns: minmax(220px, 1.2fr) minmax(180px, 0.8fr) minmax(280px, 1fr) auto;
  gap: 14px;
  align-items: end;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.analytics-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.8fr);
  gap: 16px;
  margin-top: 16px;
}

.panel-heading {
  margin-bottom: 12px;
}

.panel-heading h2 {
  margin: 0;
  color: #10466f;
  font-size: 20px;
}

.admin-panel ul {
  margin: 0;
  padding-left: 18px;
  color: #344d60;
  line-height: 1.9;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  align-items: center;
  margin-top: 14px;
  color: #5c7282;
}

.error-detail pre {
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 980px) {
  .admin-header,
  .pagination-row {
    align-items: stretch;
    flex-direction: column;
  }

  .filter-form,
  .analytics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
