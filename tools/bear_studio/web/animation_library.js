/** Rotation-only draft motion transfer from the preserved CC0 animation pack. */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkeleton } from 'three/addons/utils/SkeletonUtils.js';
import { resetPose } from './rigging.js';

export const ANIMATION_SOURCE = Object.freeze({
  title: 'Quaternius Universal Animation Library — Standard', author: 'Quaternius',
  license: 'CC0-1.0', url: 'https://quaternius.com/packs/universalanimationlibrary.html',
  edition: 'Standard free v3 June 2026; no-root-motion GLB',
  sha256: '69591853d817488edaa8fd9bf8fc1d821eaeaf789f8627b3cd23b41c4ed67997',
});

export const RETARGET_WARNING = 'Humanoid motion transferred onto a teddy draft. Its first pose is removed to retain the bear’s rest pose. No root travel, foot planting, collision or anatomical fit is certified.';
export const SUGGESTED_CLIPS = ['Sitting_Idle_Loop', 'Sitting_Talking_Loop', 'Idle_Loop', 'Hit_Chest', 'Hit_Head', 'Walk_Loop'];

// Collapsed chain mapping includes omitted spine, neck and clavicle joints.
// Each source joint's rotation is measured relative to its mapped parent.
const MAPPING = [
  { target: 'pelvis', source: 'pelvis', parent: 'root' },
  { target: 'spine', source: 'spine_03', parent: 'pelvis' },
  { target: 'head', source: 'Head', parent: 'spine_03' },
  ...['L', 'R'].flatMap((side) => {
    const s = side.toLowerCase();
    return [
      { target: `upperarm_${side}`, source: `upperarm_${s}`, parent: 'spine_03' },
      { target: `forearm_${side}`, source: `lowerarm_${s}`, parent: `upperarm_${s}` },
      { target: `hand_${side}`, source: `hand_${s}`, parent: `lowerarm_${s}` },
      { target: `thigh_${side}`, source: `thigh_${s}`, parent: 'pelvis' },
      { target: `shin_${side}`, source: `calf_${s}`, parent: `thigh_${s}` },
      { target: `foot_${side}`, source: `foot_${s}`, parent: `calf_${s}` },
    ];
  }),
];

// The scanner exposes the spine, neck and shoulders separately; retain their motion.
const SCANNER_MAPPING = [
  { target: 'Hips', source: 'pelvis', parent: 'root' },
  { target: 'Spine', source: 'spine_01', parent: 'pelvis' },
  { target: 'Spine1', source: 'spine_02', parent: 'spine_01' },
  { target: 'Spine2', source: 'spine_03', parent: 'spine_02' },
  { target: 'Neck', source: 'neck_01', parent: 'spine_03' },
  { target: 'Head', source: 'Head', parent: 'neck_01' },
  ...[['Left', 'l'], ['Right', 'r']].flatMap(([side, s]) => [
    { target: `${side}Shoulder`, source: `clavicle_${s}`, parent: 'spine_03' },
    { target: `${side}Arm`, source: `upperarm_${s}`, parent: `clavicle_${s}` },
    { target: `${side}ForeArm`, source: `lowerarm_${s}`, parent: `upperarm_${s}` },
    { target: `${side}Hand`, source: `hand_${s}`, parent: `lowerarm_${s}` },
    { target: `${side}UpLeg`, source: `thigh_${s}`, parent: 'pelvis' },
    { target: `${side}Leg`, source: `calf_${s}`, parent: `thigh_${s}` },
    { target: `${side}Foot`, source: `foot_${s}`, parent: `calf_${s}` },
  ]),
];

const loads = new Map();
const worldQ = (object) => object.getWorldQuaternion(new THREE.Quaternion());
const sha256 = async (buffer) => [...new Uint8Array(await crypto.subtle.digest('SHA-256', buffer))].map((byte) => byte.toString(16).padStart(2, '0')).join('');

export function loadAnimationLibrary(url = '/library/quaternius/model.glb') {
  if (!loads.has(url)) {
    const pending = (async () => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`The local animation library is unavailable (${response.status}).`);
      const bytes = await response.arrayBuffer();
      const hash = await sha256(bytes);
      if (hash !== ANIMATION_SOURCE.sha256) throw new Error('Animation-library bytes do not match the retained official source.');
      const gltf = await new GLTFLoader().parseAsync(bytes, '');
      if (!gltf.animations?.length) throw new Error('The library contains no animation clips.');
      return {
        gltf, source: { ...ANIMATION_SOURCE },
        clips: gltf.animations.map((clip) => ({ name: clip.name, duration: clip.duration, tracks: clip.tracks.length })),
      };
    })();
    loads.set(url, pending);
    pending.catch(() => loads.delete(url));
  }
  return loads.get(url);
}

function findBone(root, name) {
  let result;
  root.traverse((node) => { if (!result && node.isBone && node.name.toLowerCase() === name.toLowerCase()) result = node; });
  return result;
}

function limitedQuaternion(delta, strength, capRadians) {
  const q = delta.clone().normalize();
  if (q.w < 0) q.set(-q.x, -q.y, -q.z, -q.w);
  const angle = 2 * Math.acos(THREE.MathUtils.clamp(q.w, -1, 1));
  const amount = strength * (angle > capRadians ? capRadians / angle : 1);
  return new THREE.Quaternion().slerp(q, amount).normalize();
}

/**
 * Bakes real source animation changes at 30 fps, using the first source frame
 * as a baseline. This avoids applying a sitting pose twice to a seated scan.
 * The source model, its clips and the target bind matrices are preserved.
 */
export function addLibraryClip(handle, library, clipName, { strength = 0.65, maxAngleDegrees = 70 } = {}) {
  if (!Number.isFinite(strength) || strength <= 0 || strength > 1) throw new Error('Motion strength must be greater than 0 and at most 1.');
  if (!Number.isFinite(maxAngleDegrees) || maxAngleDegrees < 5 || maxAngleDegrees > 120) throw new Error('Angular cap must be between 5° and 120°.');
  const sourceClip = library.gltf.animations.find((clip) => clip.name === clipName);
  if (!sourceClip || !Number.isFinite(sourceClip.duration) || sourceClip.duration <= 0 || sourceClip.duration > 120) throw new Error('Choose a finite source clip lasting between 0 and 120 seconds.');
  const source = cloneSkeleton(library.gltf.scene);
  const sourceSkeletons = new Set(); source.traverse((node) => { if (node.isSkinnedMesh) sourceSkeletons.add(node.skeleton); });
  sourceSkeletons.forEach((skeleton) => skeleton.pose());
  source.updateMatrixWorld(true);
  const sourceMixer = new THREE.AnimationMixer(source);
  const sourceAction = sourceMixer.clipAction(sourceClip);
  sourceAction.setLoop(THREE.LoopOnce, 1); sourceAction.clampWhenFinished = true; sourceAction.play();
  sourceMixer.setTime(0); source.updateMatrixWorld(true);

  const savedPose = handle.skeleton.bones.map((bone) => ({ bone, position: bone.position.clone(), quaternion: bone.quaternion.clone(), scale: bone.scale.clone() }));
  resetPose(handle);
  const sourceFrameInverse = worldQ(source).invert();
  const targetFrameInverse = worldQ(handle.group).invert();
  try {
  const entries = handle.recipe.method === 'scanner-rigfit-v1' ? SCANNER_MAPPING : MAPPING;
  const mapping = entries.map((entry) => {
    const sourceBone = findBone(source, entry.source), sourceParent = findBone(source, entry.parent);
    const targetBone = handle.skeleton.bones.find((bone) => bone.name === entry.target);
    if (!sourceBone || !sourceParent || !targetBone) throw new Error(`The selected rigs do not provide mapped joint ${entry.source} → ${entry.target}.`);
    const baseChain = worldQ(sourceParent).invert().multiply(worldQ(sourceBone));
    const sourceBasis = sourceFrameInverse.clone().multiply(worldQ(sourceBone));
    const targetBasis = targetFrameInverse.clone().multiply(worldQ(targetBone));
    const changeBasis = targetBasis.clone().invert().multiply(sourceBasis);
    return {
      ...entry, sourceBone, sourceParent, targetBone, baseInverse: baseChain.invert(),
      changeBasis, inverseBasis: changeBasis.clone().invert(),
      restQuaternion: targetBone.quaternion.clone(), values: [], maxAngle: 0,
    };
  });
  const frameCount = Math.ceil(sourceClip.duration * 30) + 1;
  const times = Array.from({ length: frameCount }, (_, frame) => sourceClip.duration * frame / (frameCount - 1));
  let changedSamples = 0, peakAngle = 0;
    for (const time of times) {
      sourceMixer.setTime(time); source.updateMatrixWorld(true);
      for (const entry of mapping) {
        const chain = worldQ(entry.sourceParent).invert().multiply(worldQ(entry.sourceBone));
        const delta = entry.baseInverse.clone().multiply(chain);
        const converted = entry.changeBasis.clone().multiply(delta).multiply(entry.inverseBasis);
        const reduced = limitedQuaternion(converted, strength, maxAngleDegrees * Math.PI / 180);
        const result = entry.restQuaternion.clone().multiply(reduced).normalize();
        const angle = result.angleTo(entry.restQuaternion);
        if (angle > 1e-5) changedSamples++;
        entry.maxAngle = Math.max(entry.maxAngle, angle); peakAngle = Math.max(peakAngle, angle);
        // Adjacent antipodal quaternion representations need the same sign.
        const previous = entry.values.length >= 4 ? new THREE.Quaternion().fromArray(entry.values, entry.values.length - 4) : null;
        if (previous && previous.dot(result) < 0) result.set(-result.x, -result.y, -result.z, -result.w);
        entry.values.push(result.x, result.y, result.z, result.w);
      }
    }
    if (!changedSamples) throw new Error('This clip has no transferable rotational motion. Choose another clip; a static pose is not an animation test.');
    const tracks = handle.skeleton.bones.map((bone) => {
      const entry = mapping.find((item) => item.targetBone === bone);
      const values = entry?.values || times.flatMap(() => bone.quaternion.toArray());
      return new THREE.QuaternionKeyframeTrack(`${bone.name}.quaternion`, times, values);
    });
    const clip = new THREE.AnimationClip(`UAL · ${clipName}`, sourceClip.duration, tracks);
    const provenance = {
      ...library.source, sourceClip: clipName, derivedClip: clip.name, method: 'first-frame-relative-chain-rotations',
      strength, angularCapDegrees: maxAngleDegrees, frames: frameCount, sampleRate: 30,
      mappedBones: mapping.map(({ target, source: name, parent, maxAngle }) => ({ target, source: name, parent, peakDegrees: maxAngle * 180 / Math.PI })),
      includesRootTranslation: false, includesScaleTracks: false, review: 'pending', warning: RETARGET_WARNING,
    };
    const existing = handle.clips.findIndex((item) => item.name === clip.name);
    if (existing >= 0) { handle.mixer.uncacheClip(handle.clips[existing]); handle.clips.splice(existing, 1, clip); }
    else handle.clips.push(clip);
    handle.animationSources = [...(handle.animationSources || []).filter((item) => item.derivedClip !== clip.name), provenance];
    const metadata = handle.group.userData.bearStudio || {};
    handle.group.userData.bearStudio = { ...metadata, animationSources: handle.animationSources };
    if (!handle.warnings.includes(RETARGET_WARNING)) handle.warnings.push(RETARGET_WARNING);
    return {
      clip, provenance,
      report: { sourceClip: clipName, derivedClip: clip.name, mappedBones: mapping.length, frameCount, changedSamples, peakDegrees: peakAngle * 180 / Math.PI, status: 'draft', warning: RETARGET_WARNING },
    };
  } finally {
    sourceMixer.stopAllAction(); sourceMixer.uncacheRoot(source);
    savedPose.forEach(({ bone, position, quaternion, scale }) => { bone.position.copy(position); bone.quaternion.copy(quaternion); bone.scale.copy(scale); });
    handle.group.updateMatrixWorld(true); handle.skeleton.update();
    // Geometry/materials are shared with the cached official model. Do not dispose them.
  }
}
