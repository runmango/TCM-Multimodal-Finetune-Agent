<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import { DataAnalysis, DocumentChecked, FirstAidKit, InfoFilled, Search, Service } from "@element-plus/icons-vue";

import { DEFAULT_API_BASE_URL } from "@/api/tcmApi";
import AdminAnalyticsView from "@/views/AdminAnalyticsView.vue";
import DisclaimerBar from "@/components/DisclaimerBar.vue";
import StatusPanel from "@/components/StatusPanel.vue";

const route = useRoute();
const apiBaseUrl = ref(DEFAULT_API_BASE_URL);
const isAdminMode = import.meta.env.VITE_ADMIN_MODE === "true";

const activeRoute = computed(() => route.path);

const menuItems = [
  { path: "/", title: "首页", icon: InfoFilled },
  { path: "/constitution-questionnaire", title: "体质辨识问卷", icon: FirstAidKit },
  { path: "/knowledge-ask", title: "中医知识问答", icon: Search },
  { path: "/digital-human", title: "数字人播报", icon: Service },
  { path: "/dataset-build", title: "数据集与微调", icon: DocumentChecked },
  { path: "/eval-report", title: "评估报告", icon: DataAnalysis },
];
</script>

<template>
  <AdminAnalyticsView v-if="isAdminMode" />
  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand__mark">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div>
          <div class="brand__name">中医演示系统</div>
          <div class="brand__sub">知识问答 · 问卷辨识 · 数据治理</div>
        </div>
      </div>

      <el-menu :default-active="activeRoute" router class="side-menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>

      <section class="config-panel">
        <div class="section-title">后端配置</div>
        <el-input v-model="apiBaseUrl" clearable placeholder="http://127.0.0.1:8010" />
        <StatusPanel :api-base-url="apiBaseUrl" />
      </section>
    </aside>

    <main class="main-panel">
      <header class="app-header">
        <div>
          <h1>中医知识库与体质辨识演示系统</h1>
          <p>基于知识库问答、问卷量表和数字人播报的工程 Demo</p>
        </div>
      </header>

      <el-alert
        class="intro-alert"
        title="本系统为技术演示版，仅用于中医知识检索、体质倾向分析和工程能力展示，不作为临床诊断依据。"
        type="info"
        :closable="false"
        show-icon
      />

      <router-view v-slot="{ Component }">
        <component :is="Component" :api-base-url="apiBaseUrl" />
      </router-view>
    </main>

    <DisclaimerBar />
  </div>
</template>
