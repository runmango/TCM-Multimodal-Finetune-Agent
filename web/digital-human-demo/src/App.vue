<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { staticUrl, talk, type TalkResponse } from "./api";

const query = ref("乏力、气短、舌淡有齿痕");
const loading = ref(false);
const result = ref<TalkResponse | null>(null);
const error = ref("");
const speaking = ref(false);
const mouthOpen = ref(false);
const audioRef = ref<HTMLAudioElement | null>(null);
let timer: number | undefined;
const defaultAvatar = {
  closed: "/static/avatars/doctor_closed.svg",
  open: "/static/avatars/doctor_open.svg",
};

const avatarUrl = computed(() => {
  const avatar = result.value?.avatar || defaultAvatar;
  const avatarPath = speaking.value && mouthOpen.value ? avatar.open : avatar.closed;
  return staticUrl(avatarPath);
});

async function submit() {
  loading.value = true;
  error.value = "";
  result.value = null;
  stopSpeaking();
  try {
    result.value = await talk(query.value);
    await nextTick();
    if (result.value.audio_url && audioRef.value) {
      await audioRef.value.play();
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "请求失败，请检查后端服务。";
  } finally {
    loading.value = false;
  }
}

function startSpeaking() {
  speaking.value = true;
  timer = window.setInterval(() => {
    mouthOpen.value = !mouthOpen.value;
  }, 200);
}

function stopSpeaking() {
  speaking.value = false;
  mouthOpen.value = false;
  if (timer) {
    window.clearInterval(timer);
    timer = undefined;
  }
}
</script>

<template>
  <main class="page">
    <section class="hero">
      <div>
        <h1>中医体质辨识数字人演示系统</h1>
        <p>输入症状，生成体质倾向、播报语音、字幕和轻量数字人交互。</p>
      </div>
      <span>仅供健康科普参考，不替代医生诊疗。</span>
    </section>

    <section class="workspace">
      <div class="control-panel">
        <label for="query">症状描述</label>
        <textarea id="query" v-model="query" rows="6" maxlength="500" />
        <button :disabled="loading" @click="submit">{{ loading ? "生成中..." : "开始辨识" }}</button>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div class="avatar-panel">
        <div class="avatar-frame">
          <img :src="avatarUrl" alt="doctor avatar" />
        </div>
        <div class="status" :class="{ active: speaking }">{{ speaking ? "说话中" : "待机" }}</div>
      </div>
    </section>

    <section v-if="result" class="result-card">
      <div class="summary">
        <span>体质倾向</span>
        <strong>{{ result.constitution }}</strong>
      </div>
      <p class="broadcast">{{ result.text }}</p>
      <p v-if="result.tts_status === 'failed'" class="warning">{{ result.message }}</p>
      <audio
        v-if="result.audio_url"
        ref="audioRef"
        controls
        :src="staticUrl(result.audio_url)"
        @play="startSpeaking"
        @pause="stopSpeaking"
        @ended="stopSpeaking"
      />
      <div class="subtitles">
        <h2>字幕</h2>
        <div v-for="item in result.subtitles" :key="`${item.start}-${item.text}`" class="subtitle">
          <span>{{ item.start }}s - {{ item.end }}s</span>
          <p>{{ item.text }}</p>
        </div>
      </div>
      <div class="safety">{{ result.safety_notice }}</div>
    </section>
  </main>
</template>
