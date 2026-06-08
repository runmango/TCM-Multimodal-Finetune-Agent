<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as THREE from "three";
import type { VRM } from "@pixiv/three-vrm";

import { applyAvatarMotion, applyBlink, applyFallbackMouth, applyVrmMouth, disposeObject3D } from "@/services/avatar/avatarAnimation";
import { AudioMouthDriver } from "@/services/avatar/audioMouthDriver";
import { createFallbackDoctorModel } from "@/services/avatar/fallbackDoctorModel";
import { loadAvatarModel } from "@/services/avatar/vrmLoader";
import type { AvatarStatus } from "@/types/digitalHuman";

const props = withDefaults(
  defineProps<{
    modelUrl?: string;
    audioElement?: HTMLAudioElement | null;
    speaking: boolean;
    thinking: boolean;
    status: AvatarStatus;
  }>(),
  {
    modelUrl: "",
    audioElement: null,
  },
);

const emit = defineEmits<{
  modelSourceChange: [source: "vrm" | "gltf" | "fallback"];
}>();

const containerRef = ref<HTMLDivElement | null>(null);

let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let renderer: THREE.WebGLRenderer | null = null;
let avatarRoot: THREE.Object3D | null = null;
let vrm: VRM | null = null;
let animationId = 0;
let resizeObserver: ResizeObserver | null = null;
let mouthDriver: AudioMouthDriver | null = null;
const clock = new THREE.Clock();

onMounted(async () => {
  initScene();
  await initAvatar();
  startLoop();
});

watch(
  () => props.audioElement,
  (audioElement) => {
    mouthDriver?.dispose();
    mouthDriver = null;
    if (audioElement) {
      mouthDriver = new AudioMouthDriver();
      mouthDriver.attach(audioElement);
    }
  },
  { immediate: true },
);

watch(
  () => props.speaking,
  (speaking) => {
    if (speaking) {
      void mouthDriver?.resume();
    }
  },
);

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId);
  resizeObserver?.disconnect();
  mouthDriver?.dispose();
  if (avatarRoot) disposeObject3D(avatarRoot);
  renderer?.dispose();
  renderer?.forceContextLoss();
  containerRef.value?.replaceChildren();
});

function initScene() {
  const container = containerRef.value;
  if (!container) return;

  scene = new THREE.Scene();
  scene.fog = new THREE.Fog("#e8f6fb", 5, 12);

  camera = new THREE.PerspectiveCamera(32, 1, 0.1, 50);
  camera.position.set(0, 1.2, 5.2);
  camera.lookAt(0, 0.8, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  const hemisphere = new THREE.HemisphereLight("#f6fbff", "#7db4c6", 2.2);
  scene.add(hemisphere);

  const keyLight = new THREE.DirectionalLight("#ffffff", 3.8);
  keyLight.position.set(3, 4, 5);
  keyLight.castShadow = true;
  scene.add(keyLight);

  const fillLight = new THREE.PointLight("#5bc0d6", 1.2, 8);
  fillLight.position.set(-2.6, 1.6, 2.4);
  scene.add(fillLight);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(1.52, 72),
    new THREE.MeshStandardMaterial({ color: "#dff2f8", roughness: 0.8, metalness: 0.02 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.78;
  floor.receiveShadow = true;
  scene.add(floor);

  resizeObserver = new ResizeObserver(updateSize);
  resizeObserver.observe(container);
  updateSize();
}

async function initAvatar() {
  if (!scene) return;

  const loaded = await loadAvatarModel(props.modelUrl || undefined);
  if (loaded) {
    avatarRoot = loaded.object;
    vrm = loaded.vrm;
    emit("modelSourceChange", loaded.source);
  } else {
    avatarRoot = createFallbackDoctorModel();
    vrm = null;
    emit("modelSourceChange", "fallback");
  }

  avatarRoot.traverse((child) => {
    child.castShadow = true;
  });
  scene.add(avatarRoot);
}

function startLoop() {
  const renderFrame = () => {
    animationId = requestAnimationFrame(renderFrame);
    if (!scene || !camera || !renderer) return;

    const elapsed = clock.getElapsedTime();
    const audioSpeaking = props.speaking && Boolean(props.audioElement) && !props.audioElement?.paused;
    const mouthOpen = mouthDriver?.update(audioSpeaking) || 0;
    const status = props.thinking ? "thinking" : props.status;

    if (avatarRoot) {
      applyAvatarMotion(avatarRoot, status, elapsed);
      applyBlink(avatarRoot, elapsed);
      applyFallbackMouth(avatarRoot, mouthOpen);
    }
    applyVrmMouth(vrm, mouthOpen);
    vrm?.update(clock.getDelta());
    renderer.render(scene, camera);
  };

  renderFrame();
}

function updateSize() {
  const container = containerRef.value;
  if (!container || !renderer || !camera) return;

  const width = Math.max(320, container.clientWidth);
  const height = Math.max(420, container.clientHeight);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}
</script>

<template>
  <div ref="containerRef" class="web3d-avatar" />
</template>

<style scoped>
.web3d-avatar {
  width: 100%;
  min-height: 460px;
  height: 100%;
  overflow: hidden;
  border-radius: 8px;
}

.web3d-avatar :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>
