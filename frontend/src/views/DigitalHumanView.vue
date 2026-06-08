<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { resolveBackendAssetUrl, speakWithDigitalHuman, type DigitalHumanResponse } from "@/api/digitalHuman";
import AvatarStage from "@/components/digital-human/AvatarStage.vue";
import DigitalHumanControlPanel from "@/components/digital-human/DigitalHumanControlPanel.vue";
import SafetyNotice from "@/components/digital-human/SafetyNotice.vue";
import SubtitlePanel from "@/components/digital-human/SubtitlePanel.vue";
import type { ApiFriendlyError } from "@/api/tcmApi";
import type { AvatarStatus, DigitalHumanScene } from "@/types/digitalHuman";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const SAFETY_NOTICE = "仅供健康科普参考，不替代医生诊疗。";

const text = ref("气虚质常见表现包括容易疲乏、气短、自汗等。建议规律作息，避免过度劳累。");
const scene = ref<DigitalHumanScene>("knowledge_answer");
const voice = ref("zh-CN-XiaoxiaoNeural");
const modelUrl = ref("");
const loading = ref(false);
const speaking = ref(false);
const thinking = ref(false);
const status = ref<AvatarStatus>("idle");
const currentTime = ref(0);
const result = ref<DigitalHumanResponse | null>(null);
const error = ref<ApiFriendlyError | null>(null);
const playbackMessage = ref("");
const audioRef = ref<HTMLAudioElement | null>(null);

const broadcastText = computed(() => result.value?.text || "");
const audioUrl = computed(() => resolveBackendAssetUrl(result.value?.audio_url || "", props.apiBaseUrl));
const ttsFailed = computed(() => result.value?.tts_status === "failed" || (!audioUrl.value && Boolean(result.value)));

onMounted(() => {
  const storedText = localStorage.getItem("digital_human_speak_text");
  const storedScene = localStorage.getItem("digital_human_scene") as DigitalHumanScene | null;
  const storedVoice = localStorage.getItem("digital_human_voice");
  if (storedText) {
    text.value = storedText;
    if (storedScene && ["constitution_result", "knowledge_answer", "general_notice"].includes(storedScene)) {
      scene.value = storedScene;
    }
    if (storedVoice) {
      voice.value = storedVoice;
    }
    playbackMessage.value = "已从上一页面带入播报文本，可点击“开始播报”。";
    localStorage.removeItem("digital_human_speak_text");
    localStorage.removeItem("digital_human_scene");
    localStorage.removeItem("digital_human_voice");
  }
});

async function submit() {
  const trimmedText = text.value.trim();
  if (!trimmedText) {
    ElMessage.warning("请先输入需要播报的文本。");
    return;
  }

  loading.value = true;
  thinking.value = true;
  status.value = "thinking";
  error.value = null;
  playbackMessage.value = "";
  result.value = null;
  currentTime.value = 0;
  stopSpeaking();

  try {
    result.value = await speakWithDigitalHuman(scene.value, trimmedText, voice.value, props.apiBaseUrl);
    thinking.value = false;
    await nextTick();
    if (audioUrl.value && audioRef.value) {
      audioRef.value.currentTime = 0;
      try {
        await audioRef.value.play();
      } catch (playError) {
        playbackMessage.value = "浏览器未自动播放音频，可点击播放器手动播放。";
        status.value = "finished";
        stopSpeaking();
      }
    } else {
      status.value = "finished";
      playbackMessage.value = "当前没有可播放音频，已降级为文本和字幕展示。";
    }
  } catch (err) {
    error.value = err as ApiFriendlyError;
    thinking.value = false;
    status.value = "error";
  } finally {
    loading.value = false;
  }
}

async function replay() {
  if (audioUrl.value && audioRef.value) {
    audioRef.value.currentTime = 0;
    await audioRef.value.play().catch(() => {
      playbackMessage.value = "浏览器阻止自动播放，可点击播放器手动播放。";
    });
    return;
  }
  if (result.value?.text) {
    playbackMessage.value = "当前结果没有音频，已保留文本和字幕展示。";
  }
}

function stopPlayback() {
  if (audioRef.value) {
    audioRef.value.pause();
  }
  stopSpeaking();
  status.value = result.value ? "finished" : "idle";
}

function stopSpeaking() {
  speaking.value = false;
}

function handlePlay() {
  speaking.value = true;
  thinking.value = false;
  status.value = "speaking";
}

function handlePause() {
  if (!audioRef.value?.ended) {
    stopSpeaking();
  }
}

function handleEnded() {
  currentTime.value = audioRef.value?.duration || currentTime.value;
  stopSpeaking();
  status.value = "finished";
}

function handleTimeUpdate() {
  currentTime.value = audioRef.value?.currentTime || 0;
}

function clearForm() {
  text.value = "";
  result.value = null;
  error.value = null;
  playbackMessage.value = "";
  currentTime.value = 0;
  status.value = "idle";
  stopPlayback();
}
</script>

<template>
  <section class="tool-surface digital-human-view">
    <div class="view-heading">
      <div>
        <h2>数字人播报</h2>
        <p>通过 Web 3D 数字人、语音和字幕播报体质问卷结果与中医知识问答结果。</p>
      </div>
      <el-tag size="large" effect="light">Vue3 + Three.js + Web Audio</el-tag>
    </div>

    <SafetyNotice />

    <div class="digital-human-grid">
      <AvatarStage
        :audio-element="audioRef"
        :speaking="speaking"
        :thinking="thinking"
        :status="status"
        :tts-failed="ttsFailed"
        :model-url="modelUrl"
        @replay="replay"
        @stop="stopPlayback"
      />

      <div class="digital-human-side">
        <DigitalHumanControlPanel
          v-model:text="text"
          v-model:scene="scene"
          v-model:voice="voice"
          v-model:model-url="modelUrl"
          :loading="loading"
          @submit="submit"
          @clear="clearForm"
        />

        <section v-if="result || playbackMessage || error" class="digital-human-output">
          <h3>播报结果</h3>
          <el-alert v-if="error" :title="error.message" type="warning" :closable="false" show-icon>
            <el-collapse class="error-detail">
              <el-collapse-item title="技术详情" name="error">
                <pre>{{ JSON.stringify(error, null, 2) }}</pre>
              </el-collapse-item>
            </el-collapse>
          </el-alert>
          <el-alert v-if="playbackMessage" :title="playbackMessage" type="info" :closable="false" show-icon />
          <audio
            v-if="audioUrl"
            ref="audioRef"
            class="digital-human-audio"
            controls
            :src="audioUrl"
            crossorigin="anonymous"
            @play="handlePlay"
            @pause="handlePause"
            @ended="handleEnded"
            @timeupdate="handleTimeUpdate"
          />
          <el-alert
            v-if="ttsFailed"
            :title="result?.message || 'TTS 暂不可用，已降级为文本和字幕展示。'"
            type="warning"
            :closable="false"
            show-icon
          />
          <div v-if="result" class="broadcast-text">
            <span>最终播报文本</span>
            <p>{{ broadcastText }}</p>
          </div>
        </section>
      </div>
    </div>
  </section>

  <SubtitlePanel
    class="digital-human-subtitles"
    :subtitles="result?.subtitles || []"
    :speaking="speaking"
    :current-time="currentTime"
    :broadcast-text="broadcastText"
  />

  <SafetyNotice :text="result?.safety_notice || SAFETY_NOTICE" />
</template>

<style scoped>
.digital-human-view {
  overflow: hidden;
}

.digital-human-grid {
  display: grid;
  grid-template-columns: minmax(420px, 1.1fr) minmax(340px, 0.9fr);
  gap: 20px;
  align-items: start;
  margin-top: 18px;
}

.digital-human-side {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.digital-human-output {
  display: grid;
  gap: 12px;
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.digital-human-output h3 {
  margin: 0;
  color: #10466f;
}

.digital-human-audio {
  width: 100%;
}

.broadcast-text {
  padding: 14px;
  color: #263b4a;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.broadcast-text span {
  display: block;
  margin-bottom: 8px;
  color: #10466f;
  font-weight: 700;
}

.broadcast-text p {
  margin: 0;
  line-height: 1.85;
}

.digital-human-subtitles {
  margin-top: 16px;
}

@media (max-width: 1120px) {
  .digital-human-grid {
    grid-template-columns: 1fr;
  }
}
</style>
