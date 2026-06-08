import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRM, VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

export interface AvatarModelLoadResult {
  object: THREE.Object3D;
  vrm: VRM | null;
  source: "vrm" | "gltf";
}

export async function loadVrmModel(url = "/models/doctor.vrm"): Promise<AvatarModelLoadResult | null> {
  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));

  try {
    const gltf = await loader.loadAsync(url);
    const vrm = gltf.userData.vrm as VRM | undefined;
    if (!vrm) return null;

    VRMUtils.removeUnnecessaryVertices(gltf.scene);
    VRMUtils.removeUnnecessaryJoints(gltf.scene);
    vrm.scene.rotation.y = Math.PI;
    vrm.scene.position.y = -0.95;
    vrm.scene.scale.setScalar(1.05);

    return { object: vrm.scene, vrm, source: "vrm" };
  } catch (error) {
    return null;
  }
}

export async function loadGltfModel(url = "/models/doctor.glb"): Promise<AvatarModelLoadResult | null> {
  const loader = new GLTFLoader();

  try {
    const gltf = await loader.loadAsync(url);
    gltf.scene.position.y = -0.82;
    gltf.scene.scale.setScalar(1.05);
    return { object: gltf.scene, vrm: null, source: "gltf" };
  } catch (error) {
    return null;
  }
}

export async function loadAvatarModel(modelUrl?: string): Promise<AvatarModelLoadResult | null> {
  if (modelUrl) {
    const lower = modelUrl.toLowerCase();
    return lower.endsWith(".vrm") ? loadVrmModel(modelUrl) : loadGltfModel(modelUrl);
  }

  return (await loadVrmModel("/models/doctor.vrm")) || (await loadGltfModel("/models/doctor.glb"));
}
