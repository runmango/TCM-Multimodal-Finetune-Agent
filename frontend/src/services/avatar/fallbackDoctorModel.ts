import * as THREE from "three";

const skin = new THREE.MeshStandardMaterial({ color: "#f2c8a7", roughness: 0.76 });
const whiteCoat = new THREE.MeshStandardMaterial({ color: "#f7fbff", roughness: 0.6, metalness: 0.02 });
const teal = new THREE.MeshStandardMaterial({ color: "#1f9bb4", roughness: 0.58 });
const dark = new THREE.MeshStandardMaterial({ color: "#1f3343", roughness: 0.7 });
const mouthMaterial = new THREE.MeshStandardMaterial({ color: "#bd4a58", roughness: 0.5 });
const accent = new THREE.MeshStandardMaterial({ color: "#55b8cf", roughness: 0.48 });

export function createFallbackDoctorModel(): THREE.Group {
  const group = new THREE.Group();
  group.name = "fallback-tcm-doctor";

  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.78, 1.62, 32), whiteCoat);
  body.position.y = 0.12;
  group.add(body);

  const shirt = new THREE.Mesh(new THREE.BoxGeometry(0.48, 1.24, 0.08), teal);
  shirt.position.set(0, 0.12, 0.59);
  group.add(shirt);

  const leftArm = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 1.16, 18), whiteCoat);
  leftArm.position.set(-0.78, 0.08, 0.02);
  leftArm.rotation.z = -0.16;
  group.add(leftArm);

  const rightArm = leftArm.clone();
  rightArm.position.x = 0.78;
  rightArm.rotation.z = 0.16;
  group.add(rightArm);

  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.2, 0.22, 20), skin);
  neck.position.y = 1.0;
  group.add(neck);

  const headGroup = new THREE.Group();
  headGroup.position.y = 1.5;
  group.add(headGroup);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.43, 36, 28), skin);
  head.scale.set(0.95, 1.08, 0.9);
  headGroup.add(head);

  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.45, 32, 12, 0, Math.PI * 2, 0, Math.PI / 2), whiteCoat);
  cap.position.y = 0.32;
  cap.scale.set(1.06, 0.52, 1.02);
  headGroup.add(cap);

  const capBand = new THREE.Mesh(new THREE.TorusGeometry(0.37, 0.018, 8, 48), accent);
  capBand.position.set(0, 0.29, 0.01);
  capBand.rotation.x = Math.PI / 2;
  headGroup.add(capBand);

  const leftEye = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 12), dark);
  leftEye.position.set(-0.15, 0.06, 0.37);
  headGroup.add(leftEye);

  const rightEye = leftEye.clone();
  rightEye.position.x = 0.15;
  headGroup.add(rightEye);

  const mouth = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.035, 0.026), mouthMaterial);
  mouth.position.set(0, -0.16, 0.39);
  headGroup.add(mouth);

  const stethoscope = new THREE.Mesh(new THREE.TorusGeometry(0.27, 0.012, 10, 64, Math.PI * 1.24), dark);
  stethoscope.position.set(0, 0.66, 0.61);
  stethoscope.rotation.set(Math.PI / 2, 0, Math.PI * 0.88);
  group.add(stethoscope);

  const pendant = new THREE.Mesh(new THREE.SphereGeometry(0.045, 18, 12), accent);
  pendant.position.set(0.24, 0.34, 0.66);
  group.add(pendant);

  const thinkingRing = new THREE.Mesh(new THREE.TorusGeometry(0.72, 0.012, 8, 80), accent);
  thinkingRing.position.y = 1.55;
  thinkingRing.rotation.x = Math.PI / 2;
  thinkingRing.visible = false;
  group.add(thinkingRing);

  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.92, 0.98, 0.08, 44), new THREE.MeshStandardMaterial({ color: "#d9eefb" }));
  base.position.y = -0.74;
  group.add(base);

  group.userData.body = body;
  group.userData.head = headGroup;
  group.userData.leftEye = leftEye;
  group.userData.rightEye = rightEye;
  group.userData.mouth = mouth;
  group.userData.thinkingRing = thinkingRing;
  group.position.y = -0.08;

  return group;
}
