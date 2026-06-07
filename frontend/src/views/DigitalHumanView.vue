<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { DataAnalysis } from "@element-plus/icons-vue";

import {
  resolveBackendAssetUrl,
  talkToDigitalHuman,
  type DigitalHumanResponse,
} from "@/api/digitalHuman";
import type { ApiFriendlyError } from "@/api/tcmApi";
import DoctorAvatar from "@/components/DoctorAvatar.vue";
import SafetyNotice from "@/components/SafetyNotice.vue";
import SubtitlePanel from "@/components/SubtitlePanel.vue";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const SAFETY_NOTICE = "仅供健康科普参考，不替代医生诊疗。";

const query = ref("乏力、气短、舌淡有齿痕");
const voice = ref("zh-CN-XiaoxiaoNeural");
const loading = ref(false);
const speaking = ref(false);
const currentTime = ref(0);
const result = ref<DigitalHumanResponse | null>(null);
const error = ref<ApiFriendlyError | null>(null);
const playbackMessage = ref("");
const audioRef = ref<HTMLAudioElement | null>(null);

const broadcastText = computed(() => {
  const text = result.value?.text || "";
  if (!text) return "";
  return text.includes(SAFETY_NOTICE) ? text : `${text} 安全提示：${SAFETY_NOTICE}`;
});

const closedAvatarUrl = computed(() =>
  resolveBackendAssetUrl(result.value?.avatar?.closed || "/static/avatars/doctor_closed.svg", props.apiBaseUrl),
);
const openAvatarUrl = computed(() =>
  resolveBackendAssetUrl(result.value?.avatar?.open || "/static/avatars/doctor_open.svg", props.apiBaseUrl),
);
const audioUrl = computed(() => resolveBackendAssetUrl(result.value?.audio_url || "", props.apiBaseUrl));
const ttsFailed = computed(() => result.value?.tts_status === "failed" || (!audioUrl.value && Boolean(result.value)));

function stopSpeaking() {
  speaking.value = false;
}

async function submit() {
  loading.value = true;
  error.value = null;
  playbackMessage.value = "";
  result.value = null;
  currentTime.value = 0;
  stopSpeaking();

  try {
    result.value = await talkToDigitalHuman(query.value, voice.value, props.apiBaseUrl);
    await nextTick();
    if (audioUrl.value && audioRef.value) {
      try {
        await audioRef.value.play();
      } catch (playError) {
        playbackMessage.value = "浏览器未自动播放音频，可点击播放器手动播放。";
        stopSpeaking();
      }
    }
  } catch (err) {
    error.value = err as ApiFriendlyError;
  } finally {
    loading.value = false;
  }
}

function handleTimeUpdate() {
  currentTime.value = audioRef.value?.currentTime || 0;
}

function handleEnded() {
  currentTime.value = audioRef.value?.duration || currentTime.value;
  stopSpeaking();
}
</script>

<template>
  <section class="tool-surface digital-human-view">
    <div class="view-heading">
      <div>
        <h2>中医体质辨识数字人演示</h2>
        <p>通过数字人头像、语音播报和字幕展示中医体质辨识结果。</p>
      </div>
      <el-tag size="large" effect="light">应用展示层</el-tag>
    </div>

    <SafetyNotice />

    <div class="digital-human-layout">
      <section class="digital-human-input">
        <h3>症状输入</h3>
        <el-form label-position="top">
          <el-form-item label="症状描述">
            <el-input v-model="query" type="textarea" :rows="7" maxlength="500" show-word-limit />
          </el-form-item>
          <el-form-item label="播报音色">
            <el-input v-model="voice" placeholder="zh-CN-XiaoxiaoNeural" />
          </el-form-item>
          <el-button type="primary" :icon="DataAnalysis" :loading="loading" @click="submit">
            开始辨识并播报
          </el-button>
        </el-form>
      </section>

      <section class="digital-human-stage">
        <DoctorAvatar
          :speaking="speaking"
          :closed-avatar-url="closedAvatarUrl"
          :open-avatar-url="openAvatarUrl"
        />
        <div class="digital-human-status">
          <span>当前状态</span>
          <strong>{{ speaking ? "播报中" : result ? "已生成" : "待输入" }}</strong>
        </div>
        <audio
          v-if="audioUrl"
          ref="audioRef"
          class="digital-human-audio"
          controls
          :src="audioUrl"
          @play="speaking = true"
          @pause="stopSpeaking"
          @ended="handleEnded"
          @timeupdate="handleTimeUpdate"
        />
        <el-alert
          v-if="ttsFailed"
          class="digital-human-alert"
          :title="result?.message || 'TTS 暂不可用，已降级为文本和字幕展示。'"
          type="warning"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="playbackMessage"
          class="digital-human-alert"
          :title="playbackMessage"
          type="info"
          :closable="false"
          show-icon
        />
      </section>

      <section class="digital-human-result">
        <h3>体质辨识结果</h3>
        <div v-if="result" class="digital-human-result__body">
          <div class="summary-card accent">
            <span>体质倾向</span>
            <strong>{{ result.constitution }}</strong>
          </div>
          <div class="digital-human-broadcast">
            <span>播报文本</span>
            <p>{{ broadcastText }}</p>
          </div>
        </div>
        <el-empty v-else description="提交症状后展示体质倾向和播报文本" />
      </section>
    </div>
  </section>

  <el-alert v-if="error" class="page-alert" :title="error.message" type="warning" :closable="false" show-icon>
    <el-collapse class="error-detail">
      <el-collapse-item title="技术详情" name="error">
        <pre>{{ JSON.stringify(error, null, 2) }}</pre>
      </el-collapse-item>
    </el-collapse>
  </el-alert>

  <SubtitlePanel
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

.digital-human-layout {
  display: grid;
  grid-template-columns: minmax(260px, 0.95fr) minmax(240px, 0.8fr) minmax(300px, 1.05fr);
  gap: 18px;
  margin-top: 18px;
}

.digital-human-input,
.digital-human-stage,
.digital-human-result {
  min-width: 0;
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.digital-human-input h3,
.digital-human-result h3 {
  margin: 0 0 14px;
  color: #10466f;
}

.digital-human-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  background: #f7fbff;
}

.digital-human-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  color: #5c7282;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.digital-human-status strong {
  color: #10466f;
}

.digital-human-audio {
  width: 100%;
}

.digital-human-alert {
  width: 100%;
}

.digital-human-result__body {
  display: grid;
  gap: 14px;
}

.digital-human-broadcast {
  padding: 14px;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.digital-human-broadcast span {
  display: block;
  margin-bottom: 8px;
  color: #10466f;
  font-weight: 700;
}

.digital-human-broadcast p {
  margin: 0;
  color: #263b4a;
  line-height: 1.85;
}

@media (max-width: 1120px) {
  .digital-human-layout {
    grid-template-columns: 1fr;
  }
}
</style>
