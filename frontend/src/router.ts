import { createRouter, createWebHistory } from "vue-router";

import ConstitutionQuestionnaireView from "@/views/ConstitutionQuestionnaireView.vue";
import DatasetBuildView from "@/views/DatasetBuildView.vue";
import DigitalHumanView from "@/views/DigitalHumanView.vue";
import EvalReportView from "@/views/EvalReportView.vue";
import KnowledgeAskView from "@/views/KnowledgeAskView.vue";
import SystemInfoView from "@/views/SystemInfoView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: SystemInfoView },
    { path: "/knowledge-ask", name: "knowledge-ask", component: KnowledgeAskView },
    { path: "/constitution-questionnaire", name: "constitution-questionnaire", component: ConstitutionQuestionnaireView },
    { path: "/dataset-build", name: "dataset-build", component: DatasetBuildView },
    { path: "/eval-report", name: "eval-report", component: EvalReportView },
    { path: "/digital-human", name: "digital-human", component: DigitalHumanView },
    { path: "/about", redirect: "/" },
    { path: "/constitution", redirect: "/constitution-questionnaire" },
    { path: "/rag-search", redirect: "/knowledge-ask" },
  ],
});

export default router;
