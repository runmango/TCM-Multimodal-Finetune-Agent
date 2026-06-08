<script setup lang="ts">
import { computed, ref } from "vue";
import { RefreshRight, Switch, VideoPause } from "@element-plus/icons-vue";

import Web3DAvatar from "@/components/digital-human/Web3DAvatar.vue";
import SpeakingWave from "@/components/digital-human/SpeakingWave.vue";
import type { AvatarStatus } from "@/types/digitalHuman";

const props = defineProps<{
  audioElement?: HTMLAudioElement | null;
  speaking: boolean;
  thinking: boolean;
  status: AvatarStatus;
  ttsFailed: boolean;
  modelUrl?: string;
}>();

const emit = defineEmits<{
  replay: [];
  stop: [];
}>();

const backgroundMode = ref<"clinic" | "tcm">("clinic");
const modelSource = ref<"vrm" | "gltf" | "fallback">("fallback");

const statusLabel = computed(() => {
  if (props.ttsFailed) return "TTS 失败，已降级为文本展示";
  if (props.thinking) return "正在生成";
  if (props.status === "speaking") return "正在播报";
  if (props.status === "finished") return "播报完成";
  if (props.status === "error") return "接口异常";
  return "待机";
});

function toggleBackground() {
  backgroundMode.value = backgroundMode.value === "clinic" ? "tcm" : "clinic";
}
</script>

<template>
  <section class="avatar-stage" :class="`avatar-stage--${backgroundMode}`">
    <div class="avatar-stage__topbar">
      <div>
        <span>Web 3D 中医数字人</span>
        <strong>{{ statusLabel }}</strong>
      </div>
      <el-tag :type="modelSource === 'fallback' ? 'warning' : 'success'" effect="light">
        {{ modelSource === "fallback" ? "Fallback 3D" : modelSource.toUpperCase() }}
      </el-tag>
    </div>

    <div class="avatar-stage__canvas">
      <Web3DAvatar
        :model-url="modelUrl"
        :audio-element="audioElement"
        :speaking="speaking"
        :thinking="thinking"
        :status="status"
        @model-source-change="modelSource = $event"
      />
    </div>

    <div class="avatar-stage__footer">
      <SpeakingWave :active="speaking" />
      <div class="avatar-stage__actions">
        <el-button :icon="RefreshRight" size="small" @click="emit('replay')">重新播报</el-button>
        <el-button :icon="VideoPause" size="small" @click="emit('stop')">停止播报</el-button>
        <el-button :icon="Switch" size="small" @click="toggleBackground">切换背景</el-button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.avatar-stage {
  position: relative;
  min-height: 620px;
  padding: 16px;
  overflow: hidden;
  color: #10466f;
  background:
    radial-gradient(circle at 18% 16%, rgba(89, 177, 204, 0.32), transparent 28%),
    linear-gradient(145deg, #f8fdff 0%, #e8f6fb 55%, #f9fcfb 100%);
  border: 1px solid #cfe5f0;
  border-radius: 8px;
  box-shadow: 0 14px 34px rgba(16, 70, 111, 0.12);
}

.avatar-stage--tcm {
  background:
    linear-gradient(90deg, rgba(31, 120, 180, 0.08) 1px, transparent 1px),
    linear-gradient(180deg, rgba(31, 120, 180, 0.08) 1px, transparent 1px),
    linear-gradient(145deg, #fbfdff 0%, #edf8f6 55%, #f4fbff 100%);
  background-size:
    42px 42px,
    42px 42px,
    auto;
}

.avatar-stage__topbar {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.avatar-stage__topbar span {
  display: block;
  color: #5c7282;
  font-size: 13px;
}

.avatar-stage__topbar strong {
  color: #10466f;
  font-size: 22px;
}

.avatar-stage__canvas {
  min-height: 486px;
  height: 486px;
}

.avatar-stage__footer {
  position: relative;
  z-index: 2;
  display: grid;
  gap: 10px;
  margin-top: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(207, 229, 240, 0.82);
  border-radius: 8px;
  backdrop-filter: blur(8px);
}

.avatar-stage__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
</style>
