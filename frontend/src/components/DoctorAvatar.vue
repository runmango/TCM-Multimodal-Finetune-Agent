<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { FirstAidKit } from "@element-plus/icons-vue";

const props = withDefaults(
  defineProps<{
    speaking: boolean;
    closedAvatarUrl?: string;
    openAvatarUrl?: string;
  }>(),
  {
    closedAvatarUrl: "/static/avatars/doctor_closed.svg",
    openAvatarUrl: "/static/avatars/doctor_open.svg",
  },
);

const mouthOpen = ref(false);
const imageFailed = ref(false);
let timer: number | undefined;

const avatarUrl = computed(() => (props.speaking && mouthOpen.value ? props.openAvatarUrl : props.closedAvatarUrl));

function stopMouthTimer() {
  if (timer) {
    window.clearInterval(timer);
    timer = undefined;
  }
  mouthOpen.value = false;
}

watch(
  () => props.speaking,
  (speaking) => {
    stopMouthTimer();
    if (speaking) {
      timer = window.setInterval(() => {
        mouthOpen.value = !mouthOpen.value;
      }, 200);
    }
  },
  { immediate: true },
);

watch(
  () => [props.closedAvatarUrl, props.openAvatarUrl],
  () => {
    imageFailed.value = false;
  },
);

onBeforeUnmount(stopMouthTimer);
</script>

<template>
  <div class="doctor-avatar" :class="{ 'doctor-avatar--speaking': speaking }">
    <img
      v-if="!imageFailed"
      :key="avatarUrl"
      class="doctor-avatar__image"
      :src="avatarUrl"
      alt="中医医生数字人头像"
      @error="imageFailed = true"
    />
    <div v-else class="doctor-avatar__fallback" aria-label="医生头像占位">
      <el-icon><FirstAidKit /></el-icon>
    </div>
    <div class="doctor-avatar__pulse" />
  </div>
</template>

<style scoped>
.doctor-avatar {
  position: relative;
  display: grid;
  place-items: center;
  width: min(260px, 100%);
  aspect-ratio: 1;
  margin: 0 auto;
  background: #eef7fb;
  border: 1px solid #cbe2f1;
  border-radius: 8px;
  overflow: hidden;
}

.doctor-avatar__image {
  position: relative;
  z-index: 1;
  width: 82%;
  height: 82%;
  object-fit: contain;
}

.doctor-avatar__fallback {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 132px;
  height: 132px;
  color: #1f78b4;
  background: #ffffff;
  border: 1px solid #b9d8eb;
  border-radius: 50%;
  font-size: 58px;
}

.doctor-avatar__pulse {
  position: absolute;
  inset: 18px;
  border: 1px solid rgba(31, 120, 180, 0.2);
  border-radius: 50%;
  opacity: 0;
}

.doctor-avatar--speaking .doctor-avatar__pulse {
  animation: avatar-pulse 1.2s ease-in-out infinite;
}

@keyframes avatar-pulse {
  0% {
    transform: scale(0.92);
    opacity: 0.7;
  }
  100% {
    transform: scale(1.08);
    opacity: 0;
  }
}
</style>
