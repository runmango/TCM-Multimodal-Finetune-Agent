<script setup lang="ts">
defineProps<{
  active: boolean;
}>();
</script>

<template>
  <div class="speaking-wave" :class="{ 'speaking-wave--active': active }" aria-hidden="true">
    <span v-for="index in 18" :key="index" />
  </div>
</template>

<style scoped>
.speaking-wave {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 36px;
  padding: 0 8px;
}

.speaking-wave span {
  width: 4px;
  height: 10px;
  background: #8fb8cc;
  border-radius: 999px;
  opacity: 0.5;
  transform-origin: center;
}

.speaking-wave--active span {
  animation: wave 0.82s ease-in-out infinite;
  background: #1f9bb4;
  opacity: 0.9;
}

.speaking-wave--active span:nth-child(2n) {
  animation-delay: 0.08s;
}

.speaking-wave--active span:nth-child(3n) {
  animation-delay: 0.16s;
}

.speaking-wave--active span:nth-child(5n) {
  animation-delay: 0.24s;
}

@keyframes wave {
  0%,
  100% {
    transform: scaleY(0.55);
  }
  50% {
    transform: scaleY(2.25);
  }
}
</style>
