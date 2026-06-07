<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string;
  }>(),
  {
    text: "仅供健康科普参考，不替代医生诊疗。",
  },
);
</script>

<template>
  <el-alert class="safety-notice" :title="text" type="warning" :closable="false" show-icon />
</template>

<style scoped>
.safety-notice {
  margin: 14px 0;
  border: 1px solid #f2d59b;
  border-radius: 8px;
}
</style>
