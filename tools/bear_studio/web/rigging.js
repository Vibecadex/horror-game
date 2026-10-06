/**
 * Bear Studio's deliberately inspectable draft-rig workflow.
 * Source BufferGeometry and materials are never modified. A rig is not an art
 * approval: capsule-distance weights and procedural clips require inspection.
 */
import * as THREE from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const V = (p) => new THREE.Vector3(...p);
const cloneJSON = (value) => JSON.parse(JSON.stringify(value));
const DEG = Math.PI / 180;
const BONE_SPEC = [
  ['root', null, 'pelvis'], ['pelvis', 'root', 'spine'],
  ['spine', 'pelvis', 'head'], ['head', 'spine', 'head_tip'],
  ['upperarm_L', 'spine', 'forearm_L'], ['forearm_L', 'upperarm_L', 'hand_L'],
  ['hand_L', 'forearm_L', 'hand_tip_L'], ['thigh_L', 'pelvis', 'shin_L'],
  ['shin_L', 'thigh_L', 'foot_L'], ['foot_L', 'shin_L', 'foot_tip_L'],
  ['upperarm_R', 'spine', 'forearm_R'], ['forearm_R', 'upperarm_R', 'hand_R'],
  ['hand_R', 'forearm_R', 'hand_tip_R'], ['thigh_R', 'pelvis', 'shin_R'],
  ['shin_R', 'thigh_R', 'foot_R'], ['foot_R', 'shin_R', 'foot_tip_R'],
];

export const BONE_NAMES = BONE_SPEC.map(([name]) => name);
export const LANDMARK_NAMES = [...new Set(BONE_SPEC.flatMap(([name, , tip]) => [name, tip]))];
export const EDITABLE_LANDMARK_NAMES = LANDMARK_NAMES.filter((name) => name !== 'root');
export const CLIP_NAMES = ['Rest', 'Breathing', 'Arm range', 'Head turn', 'Leg deformation'];
export const RIG_WARNING = 'Heuristic draft skin: inspect limb separation, joint pinching and contact before accepting this bear.';
export const CROP_WARNING = 'Coarse crop removes whole triangles below the plane. It can cut feet and leave an open, uneven bottom; it does not reconstruct hidden surfaces.';

function ordered(value) {
  if (Array.isArray(value)) return value.map(ordered);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map((key) => [key, ordered(value[key])]));
  return value;
}

export function recipeSignature(recipe) { return JSON.stringify(ordered(recipe)); }
export function isRecipeCurrent(handle, recipe) { return !!handle && handle.recipeSignature === recipeSignature(recipe); }

function finiteNumber(value, label, min, max) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max) {
    throw new Error(`${label} must be a finite number between ${min} and ${max}.`);
  }
  return value;
}

function checkedRecipe(input) {
  const recipe = cloneJSON(input);
  if (recipe.schemaVersion !== 1) throw new Error('Unsupported rig recipe version.');
  if (!['seated', 'upright'].includes(recipe.preset)) throw new Error('Choose a seated or upright draft preset.');
  finiteNumber(recipe.lod, 'LOD', 0, 8);
  if (!Number.isInteger(recipe.lod)) throw new Error('LOD must be a whole number.');
  finiteNumber(recipe.cropFraction, 'Base crop', 0, 0.95);
  finiteNumber(recipe.yawDegrees, 'Front rotation', -360, 360);
  if (recipe.heightM !== null && recipe.heightM !== undefined) finiteNumber(recipe.heightM, 'Height in metres', 0.005, 20);
  for (const name of LANDMARK_NAMES) {
    const p = recipe.landmarks?.[name];
    if (!Array.isArray(p) || p.length !== 3) throw new Error(`Landmark ${name} needs three coordinates.`);
    p.forEach((n) => finiteNumber(n, `${name} coordinate`, -2, 2));
  }
  return recipe;
}

/** Coordinates are normalized in the original, oriented source bounds.
 * y=0 is the source base; x/z=0 is its centre; one unit is source height.
 * Crop/height changes therefore do not silently relocate the anatomy.
 */
export function presetLandmarks(preset = 'seated') {
  const seated = preset === 'seated';
  const points = seated ? {
    root: [0, 0, 0], pelvis: [0, 0.63, -0.01], spine: [0, 0.73, -0.015],
    head: [0, 0.835, 0.015], head_tip: [0, 0.96, 0.015],
    upperarm_L: [0.14, 0.775, 0], forearm_L: [0.18, 0.685, 0.045],
    hand_L: [0.145, 0.61, 0.10], hand_tip_L: [0.12, 0.585, 0.12],
    thigh_L: [0.085, 0.635, 0.01], shin_L: [0.115, 0.56, 0.11],
    foot_L: [0.135, 0.535, 0.17], foot_tip_L: [0.135, 0.545, 0.22],
  } : {
    root: [0, 0, 0], pelvis: [0, 0.43, 0], spine: [0, 0.60, 0],
    head: [0, 0.76, 0], head_tip: [0, 0.96, 0],
    upperarm_L: [0.20, 0.68, 0], forearm_L: [0.28, 0.49, 0.015],
    hand_L: [0.31, 0.32, 0.04], hand_tip_L: [0.31, 0.25, 0.045],
    thigh_L: [0.12, 0.43, 0], shin_L: [0.14, 0.25, 0],
    foot_L: [0.16, 0.075, 0.015], foot_tip_L: [0.16, 0.055, 0.14],
  };
  for (const [name, p] of Object.entries(points)) {
    if (name.endsWith('_L')) points[name.replace(/_L$/, '_R')] = [-p[0], p[1], p[2]];
  }
  return points;
}

export function mirrorLandmark(recipe, name) {
  const other = name.endsWith('_L') ? name.replace(/_L$/, '_R') : name.endsWith('_R') ? name.replace(/_R$/, '_L') : null;
  if (other && recipe.landmarks[name]) {
    const p = recipe.landmarks[name];
    recipe.landmarks[other] = [-p[0], p[1], p[2]];
  }
  return other;
}

function lodOf(node, root) {
  for (let current = node; current && current !== root.parent; current = current.parent) {
    const match = /^LOD[_ -]?(\d+)(?:$|[_ .-])/i.exec(current.name);
    if (match) return Number(match[1]);
    if (current === root) break;
  }
  return null;
}

function sourceMeshes(root, lod) {
  if (!root?.isObject3D) throw new Error('Load a GLB scene before preparing a rig.');
  const meshes = [];
  root.traverse((node) => { if (node.isMesh && node.geometry?.attributes.position) meshes.push(node); });
  if (!meshes.length) throw new Error('This model has no mesh geometry.');
  const named = meshes.filter((node) => lodOf(node, root) !== null);
  const chosen = named.length ? named.filter((node) => lodOf(node, root) === lod) : meshes;
  if (!chosen.length) throw new Error(`This source has no LOD${lod}.`);
  if (chosen.some((node) => node.isSkinnedMesh)) throw new Error('This source already has skinning. Open its saved rig instead of overwriting its weights.');
  return chosen;
}

function orientedCopies(root, lod, yawDegrees) {
  root.updateWorldMatrix(true, true);
  const relative = root.matrixWorld.clone().invert();
  const yaw = new THREE.Matrix4().makeRotationY(yawDegrees * DEG);
  return sourceMeshes(root, lod).map((node) => {
    const matrix = yaw.clone().multiply(relative).multiply(node.matrixWorld);
    const geometry = node.geometry.clone().applyMatrix4(matrix);
    if (matrix.determinant() < 0) {
      // Baking a mirrored node otherwise reverses its visible face winding.
      const indices = Array.from({ length: geometry.index?.count ?? geometry.attributes.position.count }, (_, i) => geometry.index ? geometry.index.getX(i) : i);
      for (let i = 0; i + 2 < indices.length; i += 3) [indices[i + 1], indices[i + 2]] = [indices[i + 2], indices[i + 1]];
      geometry.setIndex(indices);
      const tangent = geometry.attributes.tangent;
      if (tangent) for (let i = 0; i < tangent.count; i++) tangent.setW(i, -tangent.getW(i));
    }
    geometry.deleteAttribute('skinIndex'); geometry.deleteAttribute('skinWeight');
    // A static scan morph target is not a second independently rigged surface.
    geometry.morphAttributes = {};
    return { geometry, material: node.material, name: node.name || 'BearMesh' };
  });
}

function geometryBounds(entries) {
  const box = new THREE.Box3();
  for (const { geometry } of entries) { geometry.computeBoundingBox(); box.union(geometry.boundingBox); }
  if (box.isEmpty()) throw new Error('No visible triangles remain after the crop.');
  return box;
}

const triCount = (geometry) => Math.floor((geometry.index?.count ?? geometry.attributes.position.count) / 3);
const boxJSON = (box) => ({ min: box.min.toArray(), max: box.max.toArray(), size: box.getSize(new THREE.Vector3()).toArray() });

export function inspectSource(root) {
  const meshes = [];
  root.traverse((node) => { if (node.isMesh) meshes.push(node); });
  const lods = [...new Set(meshes.map((node) => lodOf(node, root)).filter((n) => n !== null))].sort((a, b) => a - b);
  root.updateWorldMatrix(true, true);
  const box = new THREE.Box3().setFromObject(root);
  return {
    meshes: meshes.length, meshCount: meshes.length, lods: lods.length ? lods : [0],
    vertices: meshes.reduce((n, mesh) => n + (mesh.geometry.attributes.position?.count || 0), 0),
    triangles: meshes.reduce((n, mesh) => n + triCount(mesh.geometry), 0),
    skins: meshes.filter((mesh) => mesh.isSkinnedMesh).length,
    bounds: boxJSON(box), height: box.max.y - box.min.y,
  };
}

export function defaultRecipe(root, { preset = 'seated', sourceSha256 = '', sourceRevision = 1 } = {}) {
  const stats = inspectSource(root);
  return {
    schemaVersion: 1, preset, sourceSha256, sourceRevision,
    lod: stats.lods[0], heightM: null, yawDegrees: 0, cropFraction: 0,
    landmarks: presetLandmarks(preset), weighting: 'four-nearest-bone-capsules',
  };
}
export const createDefaultRecipe = defaultRecipe;

/** Removes intersected triangles too; no destructive topology repair is hidden. */
function croppedGeometry(source, cutY) {
  const position = source.attributes.position;
  const index = source.index;
  const count = index?.count ?? position.count;
  const remap = new Map(), oldVertices = [], indices = [], groups = [];
  let activeMaterial = -1, groupStart = 0;
  const getIndex = (i) => index ? index.getX(i) : i;
  for (let i = 0; i + 2 < count; i += 3) {
    const old = [getIndex(i), getIndex(i + 1), getIndex(i + 2)];
    if (old.some((n) => position.getY(n) < cutY - 1e-9)) continue;
    const material = source.groups.find((g) => i >= g.start && i < g.start + g.count)?.materialIndex ?? 0;
    if (material !== activeMaterial) {
      if (activeMaterial >= 0) groups.push({ start: groupStart, count: indices.length - groupStart, materialIndex: activeMaterial });
      activeMaterial = material; groupStart = indices.length;
    }
    for (const n of old) {
      if (!remap.has(n)) { remap.set(n, oldVertices.length); oldVertices.push(n); }
      indices.push(remap.get(n));
    }
  }
  if (activeMaterial >= 0) groups.push({ start: groupStart, count: indices.length - groupStart, materialIndex: activeMaterial });
  const result = new THREE.BufferGeometry();
  for (const [name, attr] of Object.entries(source.attributes)) {
    if (name === 'skinIndex' || name === 'skinWeight') continue;
    const data = new Float32Array(oldVertices.length * attr.itemSize);
    for (let i = 0; i < oldVertices.length; i++) {
      for (let c = 0; c < attr.itemSize; c++) data[i * attr.itemSize + c] = attr.getComponent(oldVertices[i], c);
    }
    result.setAttribute(name, new THREE.BufferAttribute(data, attr.itemSize));
  }
  result.setIndex(indices);
  for (const group of groups) result.addGroup(group.start, group.count, group.materialIndex);
  if (!result.attributes.normal && oldVertices.length) result.computeVertexNormals();
  return result;
}

function clonedMaterial(material) {
  const clone = (m) => m?.clone() ?? new THREE.MeshStandardMaterial({ color: 0x998473, roughness: 0.9 });
  return Array.isArray(material) ? material.map(clone) : clone(material);
}

function prepareGeometry(root, input) {
  const recipe = checkedRecipe(input);
  const copies = orientedCopies(root, recipe.lod, recipe.yawDegrees);
  const sourceBounds = geometryBounds(copies);
  const sourceHeight = sourceBounds.max.y - sourceBounds.min.y;
  if (!Number.isFinite(sourceHeight) || sourceHeight < 1e-8) throw new Error('The source has no usable vertical extent.');
  const cutY = sourceBounds.min.y + sourceHeight * recipe.cropFraction;
  const totalTriangles = copies.reduce((n, item) => n + triCount(item.geometry), 0);
  const entries = [];
  for (const item of copies) {
    const geometry = croppedGeometry(item.geometry, cutY);
    item.geometry.dispose();
    if (triCount(geometry)) entries.push({ ...item, geometry }); else geometry.dispose();
  }
  if (!entries.length) throw new Error('The crop removes every triangle. Lower the crop before binding.');
  const retained = geometryBounds(entries);
  const keptHeight = retained.max.y - retained.min.y;
  if (keptHeight < 1e-8) throw new Error('The cropped mesh has no height.');
  const scale = recipe.heightM == null ? 1 : recipe.heightM / keptHeight;
  const centreX = (sourceBounds.max.x + sourceBounds.min.x) / 2;
  const centreZ = (sourceBounds.max.z + sourceBounds.min.z) / 2;
  for (const { geometry } of entries) {
    geometry.translate(-centreX, -retained.min.y, -centreZ).scale(scale, scale, scale);
    geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  }
  const coordinate = (p) => new THREE.Vector3(
    p[0] * sourceHeight * scale,
    (sourceBounds.min.y + p[1] * sourceHeight - retained.min.y) * scale,
    p[2] * sourceHeight * scale,
  );
  const keptTriangles = entries.reduce((n, item) => n + triCount(item.geometry), 0);
  return {
    recipe, entries, coordinate, sourceHeightM: sourceHeight, scale,
    metrics: {
      vertexCount: entries.reduce((n, item) => n + item.geometry.attributes.position.count, 0),
      triangleCount: keptTriangles, sourceTriangleCount: totalTriangles,
      removedTriangles: totalTriangles - keptTriangles, heightM: keptHeight * scale,
      bounds: boxJSON(geometryBounds(entries)), sourceBounds: boxJSON(sourceBounds),
      cropYSourceM: cutY, retainedBaseSourceM: retained.min.y,
    },
  };
}

export function previewGeometry(root, input) {
  const prepared = prepareGeometry(root, input);
  const group = new THREE.Group(); group.name = 'DerivedBearPreview';
  for (const item of prepared.entries) {
    const mesh = new THREE.Mesh(item.geometry, clonedMaterial(item.material));
    mesh.name = item.name; mesh.castShadow = true; mesh.receiveShadow = true;
    group.add(mesh);
  }
  group.userData.bearStudioPreview = true;
  return { group, metrics: prepared.metrics, recipe: prepared.recipe, landmarkPosition: prepared.coordinate };
}

function pointSegmentDistance(point, a, b) {
  const ab = b.clone().sub(a);
  const t = THREE.MathUtils.clamp(point.clone().sub(a).dot(ab) / Math.max(ab.lengthSq(), 1e-20), 0, 1);
  return point.distanceTo(ab.multiplyScalar(t).add(a));
}

function createSkeleton(prepared) {
  const positions = Object.fromEntries(LANDMARK_NAMES.map((name) => [name, prepared.coordinate(prepared.recipe.landmarks[name])]));
  // The root remains the derived base pivot, even when the support is cropped.
  positions.root.set(0, 0, 0);
  const bones = [], byName = {}, segments = [];
  for (const [name, parent, tip] of BONE_SPEC) {
    const length = positions[name].distanceTo(positions[tip]);
    if (!Number.isFinite(length) || length < prepared.metrics.heightM * 1e-5) throw new Error(`Bone ${name} has coincident landmarks. Move its joint or tip before binding.`);
    const bone = new THREE.Bone(); bone.name = name;
    bone.position.copy(positions[name]);
    if (parent) { bone.position.sub(positions[parent]); byName[parent].add(bone); }
    bones.push(bone); byName[name] = bone;
    segments.push({ name, head: positions[name].toArray(), tail: positions[tip].toArray(), length });
  }
  return { bones, byName, segments, positions };
}

function skinGeometry(geometry, rig, height, preserveSupport) {
  const position = geometry.attributes.position;
  const indices = new Uint16Array(position.count * 4);
  const weights = new Float32Array(position.count * 4);
  const capsules = rig.segments.map((segment, index) => ({ ...segment, index, a: V(segment.head), b: V(segment.tail) }));
  const p = new THREE.Vector3();
  // The support beneath the seated pelvis stays rigid at root; it never
  // masquerades as a calf. Cropping can remove it, but is the user's choice.
  const footFloor = Math.min(rig.positions.foot_L.y, rig.positions.foot_R.y);
  const supportCeiling = preserveSupport ? Math.max(0, footFloor - height * 0.04) : 0;
  for (let vertex = 0; vertex < position.count; vertex++) {
    p.fromBufferAttribute(position, vertex);
    if (p.y < supportCeiling) { indices[vertex * 4] = 0; weights[vertex * 4] = 1; continue; }
    const side = p.x < 0 ? '_R' : '_L';
    const ranked = capsules.filter((capsule) => capsule.index !== 0 && (!/_[LR]$/.test(capsule.name) || capsule.name.endsWith(side)))
      .map((capsule) => ({ index: capsule.index, distance: pointSegmentDistance(p, capsule.a, capsule.b) }))
      .sort((a, b) => a.distance - b.distance).slice(0, 4);
    const raw = ranked.map((item) => 1 / Math.pow(Math.max(item.distance, height * 0.025), 4));
    const total = raw.reduce((sum, value) => sum + value, 0);
    ranked.forEach((item, slot) => { indices[vertex * 4 + slot] = item.index; weights[vertex * 4 + slot] = raw[slot] / total; });
  }
  geometry.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(indices, 4));
  geometry.setAttribute('skinWeight', new THREE.Float32BufferAttribute(weights, 4));
}

function makeClips(bones) {
  return CLIP_NAMES.map((name) => {
    const duration = name === 'Rest' ? 1 : 4;
    const frameCount = name === 'Rest' ? 2 : 121;
    const times = Array.from({ length: frameCount }, (_, frame) => duration * frame / (frameCount - 1));
    const tracks = [];
    for (const bone of bones) {
      const values = [];
      for (const time of times) {
        const phase = Math.PI * 2 * time / duration;
        const e = new THREE.Euler();
        if (name === 'Breathing') {
          if (bone.name === 'spine') e.x = 0.035 * Math.sin(phase);
          if (bone.name === 'head') e.z = 0.025 * Math.sin(phase);
        } else if (name === 'Arm range') {
          const wave = 0.5 - 0.5 * Math.cos(phase);
          if (/^upperarm_/.test(bone.name)) { e.x = -0.55 * wave; e.z = (bone.name.endsWith('_L') ? 1 : -1) * 0.24 * wave; }
          if (/^forearm_/.test(bone.name)) e.x = -0.28 * wave;
        } else if (name === 'Head turn' && bone.name === 'head') e.y = 0.5 * Math.sin(phase);
        else if (name === 'Leg deformation') {
          const wave = Math.sin(phase + (bone.name.endsWith('_L') ? 0 : Math.PI));
          if (/^thigh_/.test(bone.name)) e.x = 0.22 * wave;
          if (/^shin_/.test(bone.name)) e.x = -0.32 * Math.max(0, wave);
          if (/^foot_/.test(bone.name)) e.x = -0.10 * wave;
        }
        const q = new THREE.Quaternion().setFromEuler(e); values.push(q.x, q.y, q.z, q.w);
      }
      tracks.push(new THREE.QuaternionKeyframeTrack(`${bone.name}.quaternion`, times, values));
    }
    return new THREE.AnimationClip(name, duration, tracks);
  });
}

function makeHandle(group, meshes, recipe, metrics, clips, segments = []) {
  const mesh = meshes[0], skeleton = mesh.skeleton;
  const helper = new THREE.SkeletonHelper(group); helper.name = 'DraftRigSkeletonOverlay';
  helper.material.depthTest = false; helper.renderOrder = 20;
  const handle = {
    group, mesh, meshes, skeleton, helper, clips, recipe: cloneJSON(recipe), metrics,
    segments, boneNames: skeleton.bones.map((bone) => bone.name),
    recipeSignature: recipeSignature(recipe), mixer: new THREE.AnimationMixer(group),
    status: 'draft', review: 'pending', warnings: [RIG_WARNING],
    originalMaterials: meshes.map((item) => item.material), weightMaterials: [],
  };
  handle.rest = skeleton.bones.map((bone) => ({ bone, position: bone.position.clone(), quaternion: bone.quaternion.clone(), scale: bone.scale.clone() }));
  if (recipe.cropFraction > 0) handle.warnings.push(CROP_WARNING, 'The source collision hull is stale after cropping; no replacement collision has been generated.');
  if (recipe.preset === 'seated') handle.warnings.push('Seated / support preset: landmarks are suggestions. Leg deformation is not a walking or planted-foot test.');
  meshes.forEach((item) => { item.frustumCulled = false; item.castShadow = true; item.receiveShadow = true; });
  return handle;
}

export function buildRig(root, input) {
  const prepared = prepareGeometry(root, input);
  const rig = createSkeleton(prepared);
  const group = new THREE.Group(); group.name = 'BearStudioDraftRig'; group.add(rig.bones[0]);
  const skeleton = new THREE.Skeleton(rig.bones);
  const meshes = [];
  for (const item of prepared.entries) {
    skinGeometry(item.geometry, rig, prepared.metrics.heightM, prepared.recipe.preset === 'seated');
    const mesh = new THREE.SkinnedMesh(item.geometry, clonedMaterial(item.material));
    mesh.name = `BearSkin_${meshes.length}`; group.add(mesh); meshes.push(mesh);
  }
  group.updateMatrixWorld(true); skeleton.calculateInverses();
  for (const mesh of meshes) { mesh.bind(skeleton); mesh.normalizeSkinWeights(); }
  const clips = makeClips(rig.bones);
  const metrics = { ...prepared.metrics, boneCount: skeleton.bones.length };
  group.userData.bearStudio = {
    schemaVersion: 1, status: 'draft', method: 'manual-landmarks-proximity-skin',
    sourceSha256: prepared.recipe.sourceSha256, sourceRevision: prepared.recipe.sourceRevision,
    recipe: prepared.recipe, metrics, segments: rig.segments, warnings: [RIG_WARNING, ...(prepared.recipe.cropFraction ? [CROP_WARNING] : [])],
  };
  const handle = makeHandle(group, meshes, prepared.recipe, metrics, clips, rig.segments);
  handle.landmarkPosition = prepared.coordinate;
  return handle;
}
export const createRig = buildRig;

/** Uses the exact saved skin and animation, never regenerating its weights. */
export function hydrateRig(gltf, recipe = null) {
  const group = gltf.scene || gltf;
  const meshes = []; group.traverse((node) => { if (node.isSkinnedMesh) meshes.push(node); });
  if (!meshes.length) throw new Error('This saved GLB contains no skinned mesh.');
  group.updateMatrixWorld(true);
  // Export restores rest pose. Recover it from inverse bind transforms too,
  // so opening a posed document cannot turn a test pose into a new bind pose.
  [...new Set(meshes.map((mesh) => mesh.skeleton))].forEach((skeleton) => skeleton.pose());
  group.updateMatrixWorld(true);
  let metadata = group.userData?.bearStudio;
  if (!metadata) group.traverse((node) => { if (!metadata && node.userData?.bearStudio) metadata = node.userData.bearStudio; });
  const chosenRecipe = recipe || metadata?.recipe;
  if (!chosenRecipe) throw new Error('Saved rig is missing its source-linked recipe.');
  const box = new THREE.Box3().setFromObject(group);
  const metrics = {
    ...metadata?.metrics, boneCount: meshes[0].skeleton.bones.length,
    vertexCount: meshes.reduce((n, mesh) => n + mesh.geometry.attributes.position.count, 0),
    triangleCount: meshes.reduce((n, mesh) => n + triCount(mesh.geometry), 0),
    heightM: box.max.y - box.min.y, bounds: boxJSON(box),
  };
  group.userData.bearStudio = { ...metadata, recipe: cloneJSON(chosenRecipe) };
  const handle = makeHandle(group, meshes, chosenRecipe, metrics, gltf.animations || [], metadata?.segments || []);
  handle.animationSources = cloneJSON(metadata?.animationSources || []);
  for (const provenance of handle.animationSources) if (provenance.warning && !handle.warnings.includes(provenance.warning)) handle.warnings.push(provenance.warning);
  return handle;
}

function update(handle) {
  handle.group.updateMatrixWorld(true);
  for (const skeleton of new Set(handle.meshes.map((mesh) => mesh.skeleton))) skeleton.update();
  handle.helper.updateMatrixWorld(true);
}

export function resetPose(handle) {
  handle.mixer.stopAllAction();
  for (const item of handle.rest) { item.bone.position.copy(item.position); item.bone.quaternion.copy(item.quaternion); item.bone.scale.copy(item.scale); }
  update(handle);
}

export function setPose(handle, boneName, rotationDegrees) {
  handle.mixer.stopAllAction();
  const bone = handle.skeleton.bones.find((item) => item.name === boneName);
  if (!bone) throw new Error(`This rig has no bone named ${boneName}.`);
  const degrees = ['x', 'y', 'z'].map((axis) => finiteNumber(rotationDegrees[axis] ?? 0, `${axis} rotation`, -180, 180));
  const rest = handle.rest.find((item) => item.bone === bone);
  bone.quaternion.copy(rest.quaternion).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(...degrees.map((value) => value * DEG))));
  update(handle);
}

export function sampleClip(handle, name, timeSeconds = 0) {
  if (!Number.isFinite(timeSeconds)) throw new Error('Animation time must be finite.');
  const clip = handle.clips.find((item) => item.name === name);
  if (!clip) throw new Error(`No saved clip named ${name}.`);
  resetPose(handle);
  const action = handle.mixer.clipAction(clip);
  action.reset().setLoop(THREE.LoopOnce, 1); action.clampWhenFinished = true; action.play();
  // setTime also resets mixer time and thus remains deterministic under scrubbing.
  handle.mixer.setTime(THREE.MathUtils.clamp(timeSeconds, 0, clip.duration));
  update(handle);
  return clip.duration;
}

export function setWeightOverlay(handle, boneName = null) {
  handle.weightMaterials.forEach((material) => material.dispose()); handle.weightMaterials = [];
  if (!boneName) {
    handle.meshes.forEach((mesh, index) => {
      mesh.material = handle.originalMaterials[index];
      if (mesh._bearStudioOriginalColorSaved) {
        if (mesh._bearStudioOriginalColor) mesh.geometry.setAttribute('color', mesh._bearStudioOriginalColor);
        else mesh.geometry.deleteAttribute('color');
      }
    });
    return;
  }
  const boneIndex = handle.skeleton.bones.findIndex((bone) => bone.name === boneName);
  if (boneIndex < 0) throw new Error(`No bone ${boneName} to inspect.`);
  for (const mesh of handle.meshes) {
    const geometry = mesh.geometry, joints = geometry.attributes.skinIndex, weights = geometry.attributes.skinWeight;
    const colors = new Float32Array(joints.count * 3);
    for (let vertex = 0; vertex < joints.count; vertex++) {
      let weight = 0;
      for (let slot = 0; slot < 4; slot++) if (joints.getComponent(vertex, slot) === boneIndex) weight += weights.getComponent(vertex, slot);
      colors[vertex * 3] = 0.05 + weight * 0.95;
      colors[vertex * 3 + 1] = 0.10 + Math.sin(Math.PI * weight) * 0.70;
      colors[vertex * 3 + 2] = 0.85 * (1 - weight);
    }
    // Keep the source colour attribute intact for GLB export.
    if (!mesh._bearStudioOriginalColorSaved) {
      mesh._bearStudioOriginalColorSaved = true;
      mesh._bearStudioOriginalColor = geometry.getAttribute('color') || null;
    }
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const material = new THREE.MeshBasicMaterial({ vertexColors: true });
    mesh.material = material; handle.weightMaterials.push(material);
  }
}

function snapshotPose(handle) { return handle.skeleton.bones.map((bone) => ({ bone, p: bone.position.clone(), q: bone.quaternion.clone(), s: bone.scale.clone() })); }
function restorePose(handle, snapshot) { handle.mixer.stopAllAction(); snapshot.forEach(({ bone, p, q, s }) => { bone.position.copy(p); bone.quaternion.copy(q); bone.scale.copy(s); }); update(handle); }

export function validateRig(handle) {
  const snapshot = snapshotPose(handle), checks = [], metrics = { ...handle.metrics };
  const add = (id, label, passed, detail, value) => checks.push({ id, label, status: passed ? 'pass' : 'fail', detail, ...(value !== undefined ? { value } : {}) });
  const p = new THREE.Vector3(), skinned = new THREE.Vector3();
  let maxWeightError = 0, invalidWeights = 0, invalidIndices = 0, nonfiniteVertices = 0, weightedVertices = 0, maxRestError = 0;
  const influenceCounts = new Array(handle.skeleton.bones.length).fill(0);
  try {
    resetPose(handle);
    for (const mesh of handle.meshes) {
      const { position, skinIndex, skinWeight } = mesh.geometry.attributes;
      if (!skinIndex || !skinWeight || skinIndex.count !== position.count || skinWeight.count !== position.count) {
        add('skin_attributes', 'Every vertex has skin weights', false, 'Missing or mismatched skin attributes.');
        return { schemaVersion: 1, kind: 'rig-structural', passed: false, status: 'failed', review: 'pending', checks, metrics, warnings: handle.warnings };
      }
      for (let vertex = 0; vertex < position.count; vertex++) {
        let sum = 0, safe = true;
        for (let slot = 0; slot < 4; slot++) {
          const joint = skinIndex.getComponent(vertex, slot), weight = skinWeight.getComponent(vertex, slot);
          if (!Number.isInteger(joint) || joint < 0 || joint >= mesh.skeleton.bones.length) { invalidIndices++; safe = false; }
          if (!Number.isFinite(weight) || weight < 0 || weight > 1.000001) { invalidWeights++; safe = false; }
          if (weight > 0.001 && joint >= 0 && joint < influenceCounts.length) influenceCounts[joint]++;
          sum += weight;
        }
        if (sum > 0.999) weightedVertices++;
        maxWeightError = Math.max(maxWeightError, Math.abs(sum - 1));
        p.fromBufferAttribute(position, vertex);
        if (![p.x, p.y, p.z].every(Number.isFinite)) { nonfiniteVertices++; safe = false; }
        if (safe) {
          mesh.applyBoneTransform(vertex, skinned.copy(p));
          maxRestError = Math.max(maxRestError, p.distanceTo(skinned));
        } else maxRestError = Infinity;
      }
    }
    const finiteMatrices = handle.skeleton.bones.every((bone) => bone.matrixWorld.elements.every(Number.isFinite)) && handle.skeleton.boneInverses.every((matrix) => matrix.elements.every(Number.isFinite));
    add('finite_geometry', 'Finite geometry and skeleton', !nonfiniteVertices && finiteMatrices, `${nonfiniteVertices} non-finite vertices; skeleton transforms inspected.`);
    add('joint_indices', 'Valid joint references', invalidIndices === 0, `${invalidIndices} invalid joint indices.`, invalidIndices);
    add('weights', 'Normalized four-influence weights', invalidWeights === 0 && maxWeightError < 1e-4 && weightedVertices === metrics.vertexCount, `Maximum sum error ${maxWeightError.toExponential(2)}.`, maxWeightError);
    const zeroBones = handle.segments.filter((segment) => !Number.isFinite(segment.length) || segment.length < metrics.heightM * 1e-5);
    const collapsedLinks = handle.skeleton.bones.filter((bone) => bone.parent?.isBone && bone.position.length() < metrics.heightM * 1e-5);
    add('bone_lengths', 'Nonzero authored bone lengths', zeroBones.length === 0 && collapsedLinks.length === 0 && handle.skeleton.bones.length > 1, `${handle.segments.length} authored segments and ${handle.skeleton.bones.length} saved joints inspected.`);
    add('rest_pose', 'Rest pose reconstructs the mesh', Number.isFinite(maxRestError) && maxRestError < Math.max(1e-6, metrics.heightM * 1e-4), `Maximum rest error ${maxRestError.toExponential(2)} m.`, maxRestError);
    if (invalidWeights || invalidIndices || nonfiniteVertices || !finiteMatrices) {
      return { schemaVersion: 1, kind: 'rig-structural', passed: false, status: 'failed', review: 'pending', checks, metrics: { ...metrics, invalidWeights, invalidIndices, nonfiniteVertices }, warnings: [...handle.warnings] };
    }

    const bestJoint = influenceCounts.map((count, index) => ({ count, index })).filter((item) => handle.skeleton.bones[item.index].parent?.isBone).sort((a, b) => b.count - a.count)[0];
    let moved = 0, maxDeformation = 0;
    if (bestJoint?.count) {
      setPose(handle, handle.skeleton.bones[bestJoint.index].name, { z: 14 });
      for (const mesh of handle.meshes) {
        const position = mesh.geometry.attributes.position;
        for (let vertex = 0; vertex < position.count; vertex++) {
          p.fromBufferAttribute(position, vertex); mesh.applyBoneTransform(vertex, skinned.copy(p));
          const delta = skinned.distanceTo(p);
          if (delta > metrics.heightM * 1e-6) moved++;
          maxDeformation = Math.max(maxDeformation, delta);
        }
      }
    }
    add('non_root_deformation', 'A non-root joint deforms actual vertices', moved > 0 && Number.isFinite(maxDeformation), `${moved} vertices moved; max ${maxDeformation.toFixed(6)} m. Whole-object motion is excluded.`, moved);

    let badSamples = 0, sampledPositions = 0, minimumY = Infinity;
    for (const clip of handle.clips) for (const fraction of [0, 0.25, 0.5, 0.75, 1]) {
      sampleClip(handle, clip.name, clip.duration * fraction);
      for (const mesh of handle.meshes) {
        const position = mesh.geometry.attributes.position;
        for (let vertex = 0; vertex < position.count; vertex += Math.max(1, Math.floor(position.count / 128))) {
          p.fromBufferAttribute(position, vertex); mesh.applyBoneTransform(vertex, skinned.copy(p)); sampledPositions++;
          if (![skinned.x, skinned.y, skinned.z].every(Number.isFinite)) badSamples++;
          minimumY = Math.min(minimumY, skinned.y);
        }
      }
    }
    add('clips_present', 'Saved skeletal test clips', handle.clips.length > 0, `${handle.clips.length} clips.`, handle.clips.length);
    add('finite_playback', 'Finite sampled animation deformation', sampledPositions > 0 && badSamples === 0, `${sampledPositions} sampled vertex positions; ${badSamples} invalid.`, sampledPositions);
    checks.push({ id: 'visual_review', label: 'Deformation and contact need visual review', status: 'warn', detail: RIG_WARNING });
    if (minimumY < -metrics.heightM * 0.02) checks.push({ id: 'floor_contact', label: 'Some test poses cross the ground', status: 'warn', detail: `Lowest sampled vertex ${minimumY.toFixed(4)} m; this is not a planted-foot locomotion rig.` });
    if (handle.recipe.cropFraction > 0) checks.push({ id: 'crop_surface', label: 'Cropped underside needs inspection', status: 'warn', detail: CROP_WARNING });
    Object.assign(metrics, { weightedVertices, maxWeightError, maxRestErrorM: maxRestError, nonRootMovedVertices: moved, maxDeformationM: maxDeformation, sampledPositions, minimumSampledY: minimumY });
    const passed = checks.every((check) => check.status !== 'fail');
    return { schemaVersion: 1, kind: 'rig-structural', passed, status: passed ? 'passed' : 'failed', review: 'pending', checks, metrics, warnings: [...handle.warnings] };
  } finally { restorePose(handle, snapshot); }
}

export async function exportRig(handle, currentRecipe = handle.recipe) {
  if (!isRecipeCurrent(handle, currentRecipe)) throw new Error('The recipe changed after binding. Rebind and rerun tests before saving this rig.');
  const validation = validateRig(handle);
  if (!validation.passed) throw new Error('The draft failed structural checks. Correct the failing checks before exporting.');
  const snapshot = snapshotPose(handle);
  const materials = handle.meshes.map((mesh) => mesh.material);
  const colors = handle.meshes.map((mesh) => mesh.geometry.getAttribute('color'));
  try {
    resetPose(handle);
    handle.meshes.forEach((mesh, index) => {
      mesh.material = handle.originalMaterials[index];
      if (mesh._bearStudioOriginalColorSaved) {
        if (mesh._bearStudioOriginalColor) mesh.geometry.setAttribute('color', mesh._bearStudioOriginalColor);
        else mesh.geometry.deleteAttribute('color');
      }
    });
    // The original/derived comparison toggle is a viewing preference, not a
    // content filter. The owned rig group contains no viewport helpers.
    const data = await new GLTFExporter().parseAsync(handle.group, { binary: true, animations: handle.clips, trs: true, onlyVisible: false });
    if (!(data instanceof ArrayBuffer)) throw new Error('Exporter did not return a binary GLB.');
    return data;
  } finally {
    handle.meshes.forEach((mesh, index) => {
      mesh.material = materials[index];
      if (colors[index]) mesh.geometry.setAttribute('color', colors[index]); else mesh.geometry.deleteAttribute('color');
    });
    restorePose(handle, snapshot);
  }
}
export const exportDraft = exportRig;

/** Export/reload proves the delivered GLB, not just the in-memory preview. */
export async function roundTripRig(handle, currentRecipe = handle.recipe) {
  const glb = await exportRig(handle, currentRecipe);
  const parsed = await new GLTFLoader().parseAsync(glb, '');
  const reloaded = hydrateRig(parsed, handle.recipe);
  try {
    const validation = validateRig(reloaded);
    const same = reloaded.skeleton.bones.length === handle.skeleton.bones.length && reloaded.clips.length === handle.clips.length && reloaded.metrics.vertexCount === handle.metrics.vertexCount;
    validation.checks.push({ id: 'glb_roundtrip', label: 'Exported GLB reloads with skin and clips', status: same ? 'pass' : 'fail', detail: `${reloaded.skeleton.bones.length} joints, ${reloaded.metrics.vertexCount} vertices, ${reloaded.clips.length} clips; reloaded deformation tested.` });
    validation.passed = validation.passed && same; validation.status = validation.passed ? 'passed' : 'failed';
    validation.kind = 'rig-glb-roundtrip'; validation.metrics.exportBytes = glb.byteLength;
    return { glb, validation, report: validation };
  } finally { disposeRig(reloaded, { textures: true }); }
}

export function disposeRig(handle, { textures = false } = {}) {
  if (!handle) return;
  handle.mixer?.stopAllAction(); handle.mixer?.uncacheRoot(handle.group);
  handle.helper?.geometry.dispose(); handle.helper?.material.dispose();
  const materials = new Set([...(handle.originalMaterials || []).flat(), ...(handle.weightMaterials || [])]);
  (handle.meshes || []).forEach((mesh) => mesh.geometry.dispose());
  for (const skeleton of new Set((handle.meshes || []).map((mesh) => mesh.skeleton))) skeleton.dispose();
  for (const material of materials) {
    if (textures) for (const value of Object.values(material)) if (value?.isTexture) value.dispose();
    material.dispose();
  }
  handle.group.removeFromParent(); handle.helper?.removeFromParent();
}
