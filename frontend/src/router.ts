import { createRouter, createWebHistory } from "vue-router";

import ConstitutionView from "@/views/ConstitutionView.vue";
import DatasetBuildView from "@/views/DatasetBuildView.vue";
import DigitalHumanView from "@/views/DigitalHumanView.vue";
import RagSearchView from "@/views/RagSearchView.vue";
import SystemInfoView from "@/views/SystemInfoView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/constitution" },
    { path: "/constitution", name: "constitution", component: ConstitutionView },
    { path: "/rag-search", name: "rag-search", component: RagSearchView },
    { path: "/dataset-build", name: "dataset-build", component: DatasetBuildView },
    { path: "/digital-human", name: "digital-human", component: DigitalHumanView },
    { path: "/about", name: "about", component: SystemInfoView },
  ],
});

export default router;
