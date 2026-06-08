<script setup lang="ts">
import BaseSubtitlePanel from "@/components/SubtitlePanel.vue";
import type { DigitalHumanSubtitle } from "@/api/digitalHuman";

defineProps<{
  subtitles: DigitalHumanSubtitle[];
  speaking: boolean;
  currentTime?: number;
  broadcastText?: string;
}>();
</script>

<template>
  <BaseSubtitlePanel
    :subtitles="subtitles"
    :speaking="speaking"
    :current-time="currentTime"
    :broadcast-text="broadcastText"
  />
</template>
