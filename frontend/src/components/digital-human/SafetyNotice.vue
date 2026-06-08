<script setup lang="ts">
import BaseSafetyNotice from "@/components/SafetyNotice.vue";

defineProps<{
  text?: string;
}>();
</script>

<template>
  <BaseSafetyNotice :text="text" />
</template>
