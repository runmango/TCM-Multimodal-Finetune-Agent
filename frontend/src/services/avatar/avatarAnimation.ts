import * as THREE from "three";
import type { VRM } from "@pixiv/three-vrm";
import type { AvatarStatus } from "@/types/digitalHuman";

export function applyAvatarMotion(root: THREE.Object3D, status: AvatarStatus, elapsedSeconds: number): void {
  const head = root.userData.head as THREE.Object3D | undefined;
  const body = root.userData.body as THREE.Object3D | undefined;
  const thinkingRing = root.userData.thinkingRing as THREE.Object3D | undefined;

  const breathing = Math.sin(elapsedSeconds * 1.6) * 0.018;
  const headSway = Math.sin(elapsedSeconds * 0.72) * 0.06;
  const thinkingNod = status === "thinking" ? Math.sin(elapsedSeconds * 4.2) * 0.08 : 0;

  if (body) {
    body.scale.y = 1 + breathing;
  }
  if (head) {
    head.rotation.y = headSway;
    head.rotation.x = thinkingNod;
  }
  if (thinkingRing) {
    thinkingRing.visible = status === "thinking";
    thinkingRing.rotation.y = elapsedSeconds * 2.4;
    thinkingRing.rotation.z = Math.sin(elapsedSeconds * 2) * 0.12;
  }
}

export function applyBlink(root: THREE.Object3D, elapsedSeconds: number): void {
  const leftEye = root.userData.leftEye as THREE.Object3D | undefined;
  const rightEye = root.userData.rightEye as THREE.Object3D | undefined;
  const blinkPhase = elapsedSeconds % 4.8;
  const eyeScale = blinkPhase > 4.58 ? 0.14 : 1;
  if (leftEye) leftEye.scale.y = eyeScale;
  if (rightEye) rightEye.scale.y = eyeScale;
}

export function applyFallbackMouth(root: THREE.Object3D, mouthOpen: number): void {
  const mouth = root.userData.mouth as THREE.Object3D | undefined;
  if (!mouth) return;

  mouth.scale.y = 0.35 + mouthOpen * 2.1;
  mouth.scale.x = 1 + mouthOpen * 0.16;
}

export function applyVrmMouth(vrm: VRM | null, mouthOpen: number): void {
  const expressionManager = vrm?.expressionManager;
  if (!expressionManager) return;

  expressionManager.setValue("aa", mouthOpen);
  expressionManager.update();
}

export function disposeObject3D(object: THREE.Object3D): void {
  object.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (mesh.geometry) {
      mesh.geometry.dispose();
    }

    const material = mesh.material;
    if (Array.isArray(material)) {
      material.forEach((item) => item.dispose());
    } else if (material) {
      material.dispose();
    }
  });
}
