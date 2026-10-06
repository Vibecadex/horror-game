import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as Rigging from './rigging.js';

const $ = (id) => document.getElementById(id);
const loader = new GLTFLoader();
const meshMaterials = new WeakMap();
const number = new Intl.NumberFormat();
const state = {
  bears: [], bear: null, source: null, sourceView: null, handle: null, preview: null,
  recipe: null, sourceInfo: null, tab: 'inspect', shading: 'texture', lod: 0,
  activeRigRevision: null, rigSaved: false, recipeDirty: false, metadataDirty: false, testNotesDirty: false,
  checks: null, roundtrip: null, playing: false, playTime: 0, sourceToken: 0,
  scannerUrl: null, busy: false, loading: false, deciding: false, showingSource: true, error: null, conflict: false,
  library: null, libraryModule: null,
};

const host = $('canvasHost');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x2b322c);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
host.appendChild(renderer.domElement);
renderer.domElement.setAttribute('aria-label', '3D bear model. Drag to orbit, scroll to zoom.');
renderer.domElement.setAttribute('role', 'img');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x2b322c);
const camera = new THREE.PerspectiveCamera(36, 1, 0.0005, 1000);
camera.position.set(0.22, 0.14, 0.3);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.maxPolarAngle = Math.PI * 0.88;
controls.minDistance = 0.015;
controls.maxDistance = 100;
const content = new THREE.Group();
scene.add(content);
scene.add(new THREE.HemisphereLight(0xfff1db, 0x475344, 2.0));
const keyLight = new THREE.DirectionalLight(0xffedcc, 3.4);
keyLight.position.set(3, 5, 4);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.bias = -0.0001;
keyLight.shadow.normalBias = 0.001;
scene.add(keyLight);
scene.add(keyLight.target);
const fillLight = new THREE.DirectionalLight(0xcbdada, 1.1);
fillLight.position.set(-3, 1.5, 0);
scene.add(fillLight);
const rimLight = new THREE.DirectionalLight(0xe3edcd, 2.0);
rimLight.position.set(2, 3, -4);
scene.add(rimLight);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: 0x343d31, roughness: 1, metalness: 0 }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
ground.position.y = -0.0003;
scene.add(ground);
let grid = null;
const landmarkGroup = new THREE.Group();
landmarkGroup.renderOrder = 10;
scene.add(landmarkGroup);
let cameraBounds = new THREE.Box3(new THREE.Vector3(-0.05, 0, -0.05), new THREE.Vector3(0.05, 0.1, 0.05));
let toastTimer = 0;
let previewTimer = 0;
let discardDecision = null;

function requestDiscard(message) {
  // A second action cannot reuse an approval that belongs to another target.
  if (discardDecision || state.busy || state.loading) return Promise.resolve(false);
  const previousFocus = document.activeElement;
  state.deciding = true;
  updateControls();
  $('discardMessage').textContent = message;
  return new Promise((resolve) => {
    discardDecision = { resolve, previousFocus };
    try {
      $('discardDialog').showModal();
      $('cancelDiscard').focus({ preventScroll: true });
    } catch (error) {
      finishDiscard(false);
      toast(`Unable to open the decision dialog: ${error.message}`, true);
    }
  });
}
function finishDiscard(discard) {
  const decision = discardDecision;
  if (!decision) return;
  discardDecision = null;
  state.deciding = false;
  if ($('discardDialog').open) $('discardDialog').close(discard ? 'discard' : 'cancel');
  updateControls();
  if (decision.previousFocus?.isConnected && !decision.previousFocus.disabled) decision.previousFocus.focus({ preventScroll: true });
  decision.resolve(discard);
}

function status(message, error = false) {
  $('activity').textContent = message;
  $('activity').classList.toggle('error', error);
  state.error = error ? message : null;
}
function toast(message, error = false) {
  $('toast').textContent = message;
  $('toast').classList.toggle('error', error);
  $('toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $('toast').hidden = true; }, error ? 7000 : 3800);
  status(message, error);
}
function showMessage(title, detail = '', loading = false) {
  const box = $('viewportMessage');
  box.replaceChildren();
  if (loading) { const ring = document.createElement('span'); ring.className = 'loading-ring'; box.append(ring); }
  const strong = document.createElement('strong'); strong.textContent = title; box.append(strong);
  if (detail) { const small = document.createElement('small'); small.textContent = detail; box.append(small); }
  box.hidden = false;
}
function hideMessage() { $('viewportMessage').hidden = true; }
async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  let body = options.body;
  if (body && typeof body === 'object' && !(body instanceof ArrayBuffer) && !(body instanceof Blob)) {
    headers['Content-Type'] = 'application/json'; body = JSON.stringify(body);
  }
  const response = await fetch(path, { ...options, headers, body });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.error || data.detail || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return data;
}
async function action(label, callback, button = null) {
  if (state.busy || state.loading || state.deciding) return;
  state.busy = true;
  updateControls();
  if (button) button.disabled = true;
  status(label);
  try { return await callback(); }
  catch (error) {
    console.error(error);
    if (error.status === 409) state.conflict = true;
    toast(`${error.message || String(error)}${error.status === 409 ? ' Refresh the catalogue to review the latest record; your unsaved inputs are still here.' : ''}`, true);
  }
  finally { state.busy = false; if (button) button.disabled = false; updateControls(); }
}
const clone = (value) => value == null ? value : JSON.parse(JSON.stringify(value));
const hasUnsavedWork = () => state.metadataDirty || state.recipeDirty || state.testNotesDirty || Boolean(state.handle && !state.rigSaved);
const pretty = (value) => String(value || '').replace(/[_-]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
const date = (value) => value ? new Date(value).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
function latestRig(bear = state.bear) { return bear?.rigs?.filter((rig) => !rig.stale && rig.sourceRevision === bear.sourceRevision).at(-1) || null; }
function selectedRig() { return state.bear?.rigs?.find((rig) => rig.revision === state.activeRigRevision) || null; }
function activeExportRig() { return selectedRig() || latestRig(); }
function reviewLabel(value) { return { unreviewed: 'Not reviewed', 'needs-work': 'Needs work', approved: 'Human approved' }[value] || 'Not reviewed'; }

function renderCatalogue() {
  const query = $('search').value.trim().toLowerCase();
  const filter = $('catalogueFilter').value;
  $('bearCount').textContent = state.bears.length;
  const bears = state.bears.filter((bear) => {
    if (query && ![bear.name, bear.role, ...(bear.tags || [])].join(' ').toLowerCase().includes(query)) return false;
    const rigged = Boolean(latestRig(bear));
    return filter === 'all' || (filter === 'rigged' && rigged) || (filter === 'unrigged' && !rigged) || bear.reviewStatus === filter;
  });
  const list = $('catalogueList');
  list.replaceChildren();
  if (!bears.length) { const p = document.createElement('p'); p.className = 'empty-state'; p.textContent = state.bears.length ? 'No bears match this view.' : 'Every character starts somewhere. Import a finished scan or a GLB.'; list.append(p); return; }
  for (const bear of bears) {
    const button = document.createElement('button');
    button.className = 'bear-card'; button.setAttribute('role', 'option'); button.setAttribute('aria-selected', String(state.bear?.id === bear.id)); button.dataset.bearId = bear.id;
    let thumb;
    if (bear.thumbnailUrl) { thumb = document.createElement('img'); thumb.src = bear.thumbnailUrl; thumb.alt = ''; thumb.className = 'bear-thumb'; }
    else { thumb = document.createElement('div'); thumb.className = 'bear-thumb bear-placeholder'; thumb.textContent = bear.name?.charAt(0).toUpperCase() || 'B'; }
    const body = document.createElement('div'); body.className = 'bear-card-content';
    const title = document.createElement('h3'); title.textContent = bear.name;
    const meta = document.createElement('span'); meta.className = 'bear-meta'; meta.textContent = `${pretty(bear.role || 'prop')} · ${bear.source?.kind === 'bundled-sample' ? 'Prebuilt sample' : 'Source r' + bear.sourceRevision}`;
    const badge = document.createElement('span'); badge.className = 'bear-status'; badge.textContent = latestRig(bear) ? `Draft rig r${latestRig(bear).revision}` : 'Awaiting rig';
    if (bear.reviewStatus === 'needs-work') badge.textContent += ' · Needs work';
    body.append(title, meta, badge); button.append(thumb, body);
    button.addEventListener('click', () => selectBear(bear.id)); list.append(button);
  }
}
async function refreshCatalogue(selectId = null) {
  if (state.deciding) return;
  const data = await api('/api/bears');
  state.bears = data.bears || [];
  renderCatalogue();
  if (selectId) return selectBear(selectId, true);
  if (state.bear) {
    const latest = state.bears.find((bear) => bear.id === state.bear.id);
    if (latest && (!state.source || latest.sourceSha256 !== state.bear.sourceSha256)) {
      if (hasUnsavedWork() && !await requestDiscard('The source changed. Loading it will discard unsaved details, rig work and test notes for this bear.')) { status('The catalogue is current. Your open source and unsaved edits are still retained.'); return; }
      state.conflict = false;
      return selectBear(latest.id, true);
    }
    if (latest) {
      const preservedEdits = state.metadataDirty || state.recipeDirty;
      upsertBear(latest); renderSourceReport();
      if (!state.metadataDirty) renderMetadata();
      state.conflict = false; updateControls();
      status(preservedEdits ? 'Loaded the latest record. Unsaved inputs remain; review them before saving.' : 'Catalogue and selected bear are up to date.');
      await loadHistory();
    }
  }
  if (!state.bear && state.bears.length) {
    const remembered = localStorage.getItem('bear-studio-selection');
    await selectBear(state.bears.some((bear) => bear.id === remembered) ? remembered : state.bears[0].id, true);
  }
}
function upsertBear(bear) {
  const index = state.bears.findIndex((item) => item.id === bear.id);
  if (index === -1) state.bears.push(bear); else state.bears[index] = bear;
  if (state.bear?.id === bear.id) state.bear = bear;
  renderCatalogue(); renderHeader(); renderHistories(); renderHandoff();
}
async function selectBear(id, force = false) {
  if (state.busy || state.deciding || (!force && state.bear?.id === id)) return;
  if (!force && hasUnsavedWork() && !await requestDiscard('Switching bears will discard unsaved details, rig work and test notes for the current bear.')) return;
  const token = ++state.sourceToken;
  state.loading = true;
  stopPlayback();
  state.metadataDirty = false; state.recipeDirty = false; state.testNotesDirty = false; state.conflict = false;
  $('testNotes').value = '';
  showMessage('Opening the bear', 'Reading its source model and saved revisions…', true);
  clearModel();
  state.recipe = null; updateControls();
  try {
    const bear = await api(`/api/bears/${encodeURIComponent(id)}`);
    if (token !== state.sourceToken) return;
    state.bear = bear;
    state.activeRigRevision = null; state.rigSaved = false; state.checks = null; state.roundtrip = null;
    localStorage.setItem('bear-studio-selection', bear.id);
    renderCatalogue(); renderHeader(); renderMetadata(); renderSourceReport(); renderHistories(); renderHandoff();
    const gltf = await loader.loadAsync(bear.modelUrl);
    if (token !== state.sourceToken) { disposeLoadedSource(gltf); return; }
    state.source = gltf;
    state.sourceInfo = Rigging.inspectSource(gltf.scene);
    state.recipe = clone(bear.draftRecipe) || Rigging.defaultRecipe(gltf.scene, { preset: 'seated', sourceSha256: bear.sourceSha256, sourceRevision: bear.sourceRevision });
    state.recipe.sourceSha256 = bear.sourceSha256; state.recipe.sourceRevision = bear.sourceRevision;
    state.lod = 0;
    renderLODChoices(); renderRecipe();
    showSourceModel(); frameModel(); hideMessage(); updateControls();
    status(`${bear.name} · original source loaded. Draft rigging and review are separate steps.`);
    loadHistory();
  } catch (error) { if (token === state.sourceToken) { showMessage('Unable to open this bear', error.message); toast(error.message, true); } }
  finally { if (token === state.sourceToken) { state.loading = false; updateControls(); } }
}

function renderHeader() {
  const bear = state.bear; if (!bear) return;
  $('assetTitle').textContent = bear.name;
  $('assetKind').textContent = pretty(bear.source?.kind || 'local import').toUpperCase();
  $('assetSubtitle').textContent = `${pretty(bear.role || 'prop')} · Source revision ${bear.sourceRevision} · ${bear.tags?.length ? bear.tags.slice(0, 3).join(' / ') : 'A character in the making'}`;
  $('assetBadge').textContent = state.handle && !state.showingSource ? 'DRAFT RIG' : bear.source?.kind === 'bundled-sample' ? 'PREBUILT SAMPLE' : 'SOURCE ASSET';
  $('statReview').textContent = reviewLabel(bear.reviewStatus);
  $('statRig').textContent = state.activeRigRevision ? `Draft r${state.activeRigRevision}` : state.handle ? 'Unsaved draft' : latestRig() ? `r${latestRig().revision} saved` : 'Source only';
}
function renderMetadata() {
  const bear = state.bear; if (!bear) return;
  $('metaName').value = bear.name || ''; $('metaTags').value = (bear.tags || []).join(', ');
  $('metaNotes').value = bear.notes || ''; $('metaReview').value = bear.reviewStatus || 'unreviewed';
  const role = bear.role || 'prop';
  if (![...$('metaRole').options].some((option) => option.value === role)) $('metaRole').add(new Option(pretty(role), role));
  $('metaRole').value = role; state.metadataDirty = false; $('metadataState').textContent = 'Saved to this studio';
}
async function saveMetadata(event) {
  event.preventDefault(); if (!state.bear) return;
  await action('Saving catalogue details…', async () => {
    const bear = await api(`/api/bears/${state.bear.id}`, { method: 'PATCH', body: {
      expectedRevision: state.bear.revision, name: $('metaName').value.trim(), tags: $('metaTags').value.split(',').map((tag) => tag.trim()).filter(Boolean),
      notes: $('metaNotes').value, role: $('metaRole').value, reviewStatus: $('metaReview').value,
    } });
    upsertBear(bear); renderMetadata(); toast('Details saved. The original model is unchanged.');
  }, $('saveMetadata'));
}
function renderChecks(hostElement, report) {
  hostElement.replaceChildren();
  const checks = Array.isArray(report) ? report : report?.checks || [];
  if (!checks.length) { const p = document.createElement('p'); p.className = 'muted'; p.textContent = 'No checks are available yet.'; hostElement.append(p); return; }
  for (const check of checks) {
    const pass = check.pass ?? check.ok ?? check.passed;
    const statusValue = check.status || (pass === true ? 'pass' : pass === false ? 'fail' : 'warn');
    const row = document.createElement('div'); row.className = `check-row ${statusValue}`;
    const icon = document.createElement('span'); icon.className = 'check-icon'; icon.textContent = statusValue === 'pass' ? '✓' : statusValue === 'fail' ? '×' : '!';
    const body = document.createElement('div'); const title = document.createElement('b'); title.textContent = check.label || check.name || pretty(check.id) || 'Check'; body.append(title);
    const detail = check.detail || check.message || (check.value != null ? typeof check.value === 'object' ? JSON.stringify(check.value) : String(check.value) : '');
    if (detail) { const p = document.createElement('p'); p.className = 'check-detail'; p.textContent = detail; body.append(p); }
    row.append(icon, body); hostElement.append(row);
  }
}
function renderSourceReport() {
  const bear = state.bear; if (!bear) return;
  const report = bear.sourceReport || {};
  $('sourceQuality').textContent = report.status === 'pass' ? 'Source checks pass' : report.status === 'warn' ? 'Source warnings' : report.status === 'fail' ? 'Source checks failed' : 'No source report';
  $('sourceQuality').className = `badge ${report.status || ''}`;
  const warnings = [];
  if (bear.source?.kind === 'bundled-sample') warnings.push('Prebuilt sample, not reconstructed here. This scan includes its supporting box; crop or clean that geometry before fitting the bear.');
  if (report.checks?.some((check) => check.status === 'warn' || check.status === 'fail')) warnings.push('Source scan issues remain visible below. A rig does not repair missing surface detail.');
  $('sourceWarning').textContent = warnings.join(' '); $('sourceWarning').hidden = !warnings.length;
  renderChecks($('sourceChecks'), report);
  const size = report.size_m || null;
  $('sourceDimensions').textContent = size ? `${(size.x * 100).toFixed(1)} × ${(size.y * 100).toFixed(1)} × ${(size.z * 100).toFixed(1)} cm` : 'See mesh measurements';
  const source = bear.source || {};
  const entries = [['Origin', pretty(source.kind)], ['Scan ID', source.scanId || 'Local GLB'], ['Revision', bear.sourceRevision], ['SHA-256', bear.sourceSha256], ['Imported', date(bear.created)], ['Filename', source.originalFilename || 'model.glb']];
  if (source.provenance && Object.keys(source.provenance).length) entries.push(['Provenance', JSON.stringify(source.provenance)]);
  const dl = $('sourceProvenance'); dl.replaceChildren();
  for (const [label, value] of entries) { const dt = document.createElement('dt'); dt.textContent = label; const dd = document.createElement('dd'); dd.textContent = String(value ?? '—'); dl.append(dt, dd); }
}
function renderLODChoices() {
  const list = $('lodSelect'); list.replaceChildren();
  const lods = [];
  state.source?.scene.traverse((node) => { const match = /^LOD(\d+)$/i.exec(node.name); if (match) lods.push(Number(match[1])); });
  const values = lods.length ? [...new Set(lods)].sort((a, b) => a - b) : [0];
  values.forEach((value) => list.add(new Option(`LOD ${value}${value === 0 ? ' · full detail' : ''}`, String(value))));
  list.value = String(state.lod);
}

function disposePreview() {
  if (!state.preview) return;
  const group = state.preview.group || state.preview;
  group.removeFromParent();
  if (typeof state.preview.dispose === 'function') state.preview.dispose();
  else group.traverse((node) => {
    if (!node.isMesh) return;
    node.geometry?.dispose();
    const materials = meshMaterials.get(node);
    const originals = Array.isArray(materials?.original) ? materials.original : [materials?.original || node.material];
    originals.forEach((material) => material?.dispose()); materials?.wire?.dispose(); materials?.clay?.dispose();
  });
  state.preview = null;
}
function releaseSourceView() {
  state.sourceView?.traverse((node) => {
    const materials = meshMaterials.get(node); materials?.wire?.dispose(); materials?.clay?.dispose();
  });
  state.sourceView?.removeFromParent(); state.sourceView = null;
}
function disposeLoadedSource(gltf) {
  const geometries = new Set(); const materials = new Set(); const textures = new Set();
  gltf?.scene?.traverse((node) => {
    if (!node.isMesh) return;
    geometries.add(node.geometry);
    (Array.isArray(node.material) ? node.material : [node.material]).forEach((material) => {
      if (!material) return; materials.add(material);
      for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
    });
  });
  geometries.forEach((geometry) => geometry.dispose()); materials.forEach((material) => material.dispose()); textures.forEach((texture) => texture.dispose());
}
function clearModel() {
  stopPlayback();
  if (state.handle) { disposeHandle(state.handle); state.handle = null; }
  disposePreview();
  releaseSourceView(); disposeLoadedSource(state.source);
  content.clear(); state.source = null; state.sourceInfo = null;
  clearLandmarks();
}
function disposeHandle(handle) {
  handle?.group.traverse((node) => { const materials = meshMaterials.get(node); materials?.wire?.dispose(); materials?.clay?.dispose(); });
  Rigging.disposeRig(handle);
}
function visibleModel() { return state.showingSource ? state.preview?.group || state.preview || state.sourceView : state.handle?.group; }
function showSourceModel(cropped = false) {
  if (!state.source) return;
  content.clear(); disposePreview();
  releaseSourceView();
  if (state.handle?.helper) state.handle.helper.visible = false;
  if (cropped && state.recipe) {
    state.preview = Rigging.previewGeometry(state.source.scene, state.recipe);
    content.add(state.preview.group || state.preview);
  } else {
    state.sourceView = state.source.scene.clone(true);
    const lodNodes = [];
    state.sourceView.traverse((node) => { if (/^LOD\d+$/i.test(node.name)) lodNodes.push(node); });
    lodNodes.forEach((node) => { node.visible = Number(node.name.replace(/LOD/i, '')) === state.lod; });
    content.add(state.sourceView);
  }
  state.showingSource = true;
  prepareMaterials(visibleModel()); applyShading();
  $('viewLabel').textContent = cropped ? 'DERIVED CROP PREVIEW' : `SOURCE MESH · LOD ${state.lod}`;
  updateStats(); renderLandmarks(); renderHeader(); updateControls();
}
function showRigModel() {
  if (!state.handle) return;
  content.clear(); disposePreview();
  content.add(state.handle.group);
  if (state.handle.helper && state.handle.helper !== state.handle.group) { content.add(state.handle.helper); state.handle.helper.visible = $('showSkeleton').checked; }
  state.showingSource = false;
  prepareMaterials(state.handle.group); applyShading();
  $('viewLabel').textContent = state.activeRigRevision ? `DRAFT RIG · REVISION ${state.activeRigRevision}` : 'DRAFT RIG · UNSAVED';
  clearLandmarks(); updateStats(); renderHeader(); updateControls();
}
function prepareMaterials(root) {
  root?.traverse((node) => {
    if (!node.isMesh) return;
    node.castShadow = true; node.receiveShadow = true; node.frustumCulled = false;
    if (!meshMaterials.has(node)) meshMaterials.set(node, { original: node.material });
  });
}
function applyShading() {
  const root = visibleModel(); if (!root) return;
  if (state.handle && !state.showingSource && $('showWeights').checked) {
    Rigging.setWeightOverlay(state.handle, $('poseBone').value || null); return;
  }
  root.traverse((node) => {
    if (!node.isMesh) return;
    const materials = meshMaterials.get(node) || { original: node.material };
    meshMaterials.set(node, materials);
    if (state.shading === 'texture') node.material = materials.original;
    else {
      const key = state.shading === 'wire' ? 'wire' : 'clay';
      materials[key] ||= new THREE.MeshStandardMaterial({ color: state.shading === 'wire' ? 0xbecdaa : 0xb6ad99, roughness: 0.83, metalness: 0, wireframe: state.shading === 'wire', side: THREE.DoubleSide });
      node.material = materials[key];
    }
  });
}
function resize() { const width = host.clientWidth || 1; const height = host.clientHeight || 1; renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix(); }
new ResizeObserver(resize).observe(host);
function modelBounds() {
  const model = visibleModel();
  if (!model) return cameraBounds;
  model.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(model);
  return bounds.isEmpty() ? cameraBounds : bounds;
}
function frameModel(direction = 'reset') {
  cameraBounds = modelBounds();
  const size = cameraBounds.getSize(new THREE.Vector3());
  const center = cameraBounds.getCenter(new THREE.Vector3());
  const radius = Math.max(size.x, size.y, size.z, 0.02);
  const verticalDistance = radius / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2));
  const distance = Math.max(verticalDistance, verticalDistance / Math.max(camera.aspect, 0.4)) * 1.5;
  controls.target.copy(center);
  const directionVector = direction === 'front' ? new THREE.Vector3(0, 0.07, 1) : direction === 'side' ? new THREE.Vector3(1, 0.07, 0) : direction === 'top' ? new THREE.Vector3(0, 1, 0.001) : new THREE.Vector3(0.85, 0.48, 1.45);
  camera.position.copy(center).addScaledVector(directionVector.normalize(), distance);
  camera.near = Math.max(radius / 1000, 0.00001); camera.far = Math.max(radius * 100, 10); camera.updateProjectionMatrix();
  controls.minDistance = radius * 0.18; controls.maxDistance = radius * 15; controls.update();
  ground.position.y = cameraBounds.min.y - radius * 0.006;
  keyLight.position.copy(center).add(new THREE.Vector3(radius * 2, radius * 4, radius * 3));
  keyLight.target.position.copy(center);
  const shadowSize = radius * 2;
  Object.assign(keyLight.shadow.camera, { left: -shadowSize, right: shadowSize, top: shadowSize, bottom: -shadowSize, near: radius * 0.01, far: radius * 20 });
  keyLight.shadow.camera.updateProjectionMatrix(); keyLight.shadow.normalBias = radius * 0.005;
  if (grid) { scene.remove(grid); grid.geometry.dispose(); grid.material.dispose(); }
  grid = new THREE.GridHelper(radius * 8, 32, 0x65735a, 0x505d46);
  grid.position.set(center.x, ground.position.y + radius * 0.0005, center.z);
  grid.material.transparent = true; grid.material.opacity = 0.28; scene.add(grid);
}
function updateStats() {
  if (!state.source) return;
  const bounds = modelBounds(); const size = bounds.getSize(new THREE.Vector3());
  $('statHeight').textContent = `${(size.y * 100).toFixed(1)} cm`;
  let triangles = 0;
  visibleModel()?.traverseVisible((node) => { if (node.isMesh && node.geometry) triangles += (node.geometry.index?.count || node.geometry.attributes.position?.count || 0) / 3; });
  $('statTriangles').textContent = number.format(Math.round(triangles));
  if (!state.bear?.sourceReport?.size_m) $('sourceDimensions').textContent = `${(size.x * 100).toFixed(1)} × ${(size.y * 100).toFixed(1)} × ${(size.z * 100).toFixed(1)} cm`;
}

function renderRecipe() {
  const recipe = state.recipe; if (!recipe) return;
  $('rigPreset').value = recipe.preset || 'seated'; $('rigYaw').value = String(recipe.yawDegrees || 0);
  const sourceHeight = state.sourceInfo?.height || new THREE.Box3().setFromObject(state.source.scene).getSize(new THREE.Vector3()).y;
  $('rigHeight').value = Number(((recipe.heightM || sourceHeight * (1 - (recipe.cropFraction || 0))) * 100).toFixed(2));
  $('cropRange').value = recipe.cropFraction || 0; $('cropValue').textContent = `${Math.round((recipe.cropFraction || 0) * 100)}%`;
  const current = $('jointSelect').value; $('jointSelect').replaceChildren();
  (Rigging.EDITABLE_LANDMARK_NAMES || Object.keys(recipe.landmarks || {}).filter((name) => name !== 'root')).forEach((name) => $('jointSelect').add(new Option(pretty(name), name)));
  if (recipe.landmarks?.[current]) $('jointSelect').value = current;
  renderJoint();
}
function renderJoint() {
  const landmark = state.recipe?.landmarks?.[$('jointSelect').value];
  ['X', 'Y', 'Z'].forEach((axis, index) => { $(`joint${axis}`).value = landmark ? Number(landmark[index]).toFixed(3) : ''; });
  if (state.tab === 'rig' && state.showingSource && state.source && !state.preview) showSourceModel(true);
  renderLandmarks();
}
function clearLandmarks() {
  for (const child of [...landmarkGroup.children]) { child.geometry?.dispose(); child.material?.dispose(); landmarkGroup.remove(child); }
  $('landmarkHint').hidden = true;
}
function landmarkPosition(point) {
  if (state.preview?.landmarkPosition) return state.preview.landmarkPosition(point);
  const sourceBounds = new THREE.Box3().setFromObject(state.source.scene.getObjectByName('LOD0') || state.source.scene);
  const size = sourceBounds.getSize(new THREE.Vector3()); const center = sourceBounds.getCenter(new THREE.Vector3());
  const height = Math.max(size.y, 0.000001);
  const pointVector = new THREE.Vector3(center.x + point[0] * height, sourceBounds.min.y + point[1] * height, center.z + point[2] * height);
  return pointVector;
}
function renderLandmarks() {
  clearLandmarks();
  if (!state.source || !state.recipe || state.tab !== 'rig' || !state.showingSource || !$('showLandmarks').checked) return;
  if (!state.preview && Number(state.recipe.yawDegrees)) {
    $('landmarkHint').textContent = 'Original source view · select a joint to return to the prepared preview.';
    $('landmarkHint').hidden = false;
    return;
  }
  const height = Math.max(modelBounds().getSize(new THREE.Vector3()).y, 0.01);
  const selected = $('jointSelect').value;
  for (const [name, point] of Object.entries(state.recipe.landmarks || {})) {
    if (name === 'root') continue;
    const dot = new THREE.Mesh(new THREE.SphereGeometry(height * (name === selected ? 0.021 : 0.013), 12, 8), new THREE.MeshBasicMaterial({ color: name === selected ? 0xffcf7e : 0xe1b38a, transparent: true, opacity: name === selected ? 1 : 0.78, depthTest: false }));
    dot.position.copy(landmarkPosition(point)); dot.userData.landmarkName = name; dot.renderOrder = 20; landmarkGroup.add(dot);
  }
  $('landmarkHint').textContent = `${pretty(selected)} selected · click a marker to change joint`;
  $('landmarkHint').hidden = false;
}
function invalidateRig(message = 'Landmarks changed. Build a new draft to test these edits.') {
  stopPlayback(); state.recipeDirty = true; state.rigSaved = false; state.activeRigRevision = null; state.checks = null; state.roundtrip = null;
  if (state.handle) { disposeHandle(state.handle); state.handle = null; }
  $('rigSummary').hidden = true; $('rigState').textContent = message;
  $('testEmpty').hidden = false;
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => { try { showSourceModel(true); renderLandmarks(); } catch (error) { toast(error.message, true); showSourceModel(); } }, 100);
  updateControls();
}
function updateRecipeFromInputs() {
  if (!state.recipe) return;
  const height = Number($('rigHeight').value); if (!Number.isFinite(height) || height <= 0) return;
  state.recipe.heightM = height / 100; state.recipe.yawDegrees = Number($('rigYaw').value); state.recipe.cropFraction = Number($('cropRange').value);
  $('cropValue').textContent = `${Math.round(state.recipe.cropFraction * 100)}%`;
  invalidateRig();
}
async function saveRecipe() {
  if (!state.bear || !state.recipe) return;
  await action('Saving landmarks…', async () => {
    const bear = await api(`/api/bears/${state.bear.id}`, { method: 'PATCH', body: { expectedRevision: state.bear.revision, draftRecipe: state.recipe } });
    upsertBear(bear); state.recipeDirty = false; toast('Landmarks saved. Build a draft when the joints are in place.');
  }, $('saveRecipe'));
}
async function buildDraft() {
  if (!state.source || !state.recipe) return;
  if (state.handle && !state.rigSaved && !await requestDiscard('Rebuilding will replace this draft’s unsaved skin and added motions. Your current landmark settings will be used for the new draft.')) return;
  return action('Binding the draft skin…', async () => {
    await new Promise((resolve) => requestAnimationFrame(resolve));
    stopPlayback();
    if (state.handle) disposeHandle(state.handle);
    state.recipe.sourceRevision = state.bear.sourceRevision; state.recipe.sourceSha256 = state.bear.sourceSha256;
    state.handle = Rigging.buildRig(state.source.scene, clone(state.recipe));
    state.activeRigRevision = null; state.rigSaved = false; state.checks = Rigging.validateRig(state.handle); state.roundtrip = null;
    showRigModel(); renderMotionControls(); renderChecks($('rigChecks'), state.checks); frameModel();
    $('rigSummary').textContent = `Draft skin bound to ${state.handle.skeleton.bones.length} bones. ${number.format(state.handle.mesh.geometry.attributes.position.count)} weighted vertices. Review the pose and seams before recording a decision.`;
    $('rigSummary').hidden = false; $('rigState').textContent = 'Unsaved draft. Test its motion, then save a separate rig revision.';
    toast('Draft rig built. Try the Test tab to inspect deformation.');
  }, $('buildRig'));
}
function bytesToBase64(buffer) {
  const bytes = new Uint8Array(buffer); const size = 0x8000; let binary = '';
  for (let index = 0; index < bytes.length; index += size) binary += String.fromCharCode(...bytes.subarray(index, index + size));
  return btoa(binary);
}
async function saveRig() {
  if (!state.handle || !state.bear) return;
  const handle = state.handle;
  const recipe = clone(state.recipe);
  const bearId = state.bear.id;
  const sourceRevision = state.bear.sourceRevision;
  const sourceSha256 = state.bear.sourceSha256;
  await action('Exporting and saving a rig revision…', async () => {
    stopPlayback(); Rigging.resetPose(handle);
    Rigging.setWeightOverlay(handle, null); $('showWeights').checked = false;
    const validation = Rigging.validateRig(handle);
    const buffer = await Rigging.exportRig(handle, recipe);
    if (state.bear?.id !== bearId || state.handle !== handle || !Rigging.isRecipeCurrent(handle, state.recipe)) throw new Error('The draft changed during export. Rebuild before saving.');
    const result = await api(`/api/bears/${bearId}/rigs`, { method: 'POST', body: {
      sourceRevision, sourceSha256, recipe, validation, glbBase64: bytesToBase64(buffer),
    } });
    if (state.bear?.id !== bearId || state.handle !== handle) return;
    state.checks = validation;
    state.activeRigRevision = result.rig.revision; state.rigSaved = true; state.recipeDirty = false;
    upsertBear(result.bear);
    if (!state.metadataDirty) renderMetadata(); else $('metaReview').value = result.bear.reviewStatus;
    $('rigState').textContent = `Rig revision ${result.rig.revision} saved. The source scan remains unchanged.`;
    renderChecks($('rigChecks'), state.checks); showRigModel(); renderMotionControls(); loadHistory();
    toast(`Rig revision ${result.rig.revision} saved with its recipe and source identity.`);
  }, $('saveRig'));
}
async function openSavedRig(revision) {
  const rig = state.bear?.rigs?.find((item) => item.revision === revision); if (!rig) return;
  if (rig.stale) { toast('This rig belongs to an older source. Download it from the revision history for archival review.', true); return; }
  if (hasUnsavedWork() && !await requestDiscard('Opening this saved rig will discard unsaved details, rig work and test notes for the current bear.')) return;
  await action(`Opening saved rig revision ${revision}…`, async () => {
    const gltf = await loader.loadAsync(rig.modelUrl);
    stopPlayback();
    if (state.handle) disposeHandle(state.handle);
    state.recipe = clone(rig.recipe); state.handle = Rigging.hydrateRig(gltf, state.recipe);
    state.activeRigRevision = revision; state.rigSaved = true; state.recipeDirty = false; state.testNotesDirty = false; $('testNotes').value = '';
    if (state.metadataDirty) renderMetadata();
    state.checks = Rigging.validateRig(state.handle); state.roundtrip = null;
    renderRecipe(); showRigModel(); frameModel(); renderMotionControls(); renderChecks($('rigChecks'), state.checks); renderHistories(); renderHandoff();
    $('rigSummary').textContent = `Viewing the actual saved GLB from rig revision ${revision}, with ${state.handle.skeleton.bones.length} bones.`;
    $('rigSummary').hidden = false; $('rigState').textContent = `Saved rig revision ${revision} · draft requiring visual review.`;
    toast(`Opened saved rig r${revision}. Pose and motion controls use the exported skin.`);
  });
}

function renderMotionControls() {
  const handle = state.handle; const boneSelect = $('poseBone'); const clipSelect = $('clipSelect');
  boneSelect.replaceChildren(); clipSelect.replaceChildren(new Option('Rest pose', ''));
  if (!handle) return;
  handle.skeleton.bones.forEach((bone) => boneSelect.add(new Option(pretty(bone.name), bone.name)));
  (handle.clips || []).forEach((clip) => clipSelect.add(new Option(pretty(clip.name), clip.name)));
  const preferred = handle.skeleton.bones.find((bone) => /arm.*l|left.*arm|upperarm_l/i.test(bone.name)); if (preferred) boneSelect.value = preferred.name;
  resetPoseInputs(); $('timeline').value = 0; $('timelineTime').textContent = '0.00 s'; $('testEmpty').hidden = true; updateControls();
}
function stopPlayback() { state.playing = false; $('playPause').textContent = '▶ Play'; }
function currentClip() { return state.handle?.clips?.find((clip) => clip.name === $('clipSelect').value); }
function resetPoseInputs() { for (const axis of ['X', 'Y', 'Z']) { $(`pose${axis}`).value = 0; $(`pose${axis}Value`).textContent = '0°'; } }
function readPoseInputs() {
  const bone = state.handle?.skeleton.bones.find((item) => item.name === $('poseBone').value);
  const rest = state.handle?.rest.find((item) => item.bone === bone);
  if (!bone || !rest) { resetPoseInputs(); return; }
  const delta = rest.quaternion.clone().invert().multiply(bone.quaternion);
  const rotation = new THREE.Euler().setFromQuaternion(delta);
  for (const axis of ['X', 'Y', 'Z']) {
    const value = Math.round(THREE.MathUtils.radToDeg(rotation[axis.toLowerCase()]));
    $(`pose${axis}`).value = value; $(`pose${axis}Value`).textContent = `${value}°`;
  }
}
function setBonePose() {
  if (!state.handle) return;
  stopPlayback(); $('clipSelect').value = ''; state.playTime = 0;
  const rotation = {};
  for (const axis of ['X', 'Y', 'Z']) { rotation[axis.toLowerCase()] = Number($(`pose${axis}`).value); $(`pose${axis}Value`).textContent = `${rotation[axis.toLowerCase()]}°`; }
  Rigging.setPose(state.handle, $('poseBone').value, rotation);
  if (state.showingSource) showRigModel();
}
function resetPose() {
  stopPlayback(); if (state.handle) Rigging.resetPose(state.handle);
  $('clipSelect').value = ''; state.playTime = 0; $('timeline').value = 0; $('timelineTime').textContent = '0.00 s'; resetPoseInputs();
}
function selectClip() {
  stopPlayback(); if (!state.handle) return;
  Rigging.resetPose(state.handle); resetPoseInputs();
  state.playTime = 0; $('timeline').value = 0; const clip = currentClip(); $('timeline').max = clip?.duration || 2; $('timelineTime').textContent = '0.00 s';
  if (clip) Rigging.sampleClip(state.handle, clip.name, 0);
  if (state.showingSource) showRigModel();
}
async function loadMotionLibrary() {
  await action('Loading the licensed motion library…', async () => {
    state.libraryModule ||= await import('./animation_library.js');
    state.library ||= await state.libraryModule.loadAnimationLibrary();
    $('libraryClip').replaceChildren();
    const preferred = state.libraryModule.SUGGESTED_CLIPS || [];
    const order = (name) => preferred.includes(name) ? preferred.indexOf(name) : preferred.length;
    const clips = [...state.library.clips].sort((a, b) => order(a.name) - order(b.name) || a.name.localeCompare(b.name));
    for (const clip of clips) {
      const option = new Option(`${pretty(clip.name)} · ${Number(clip.duration).toFixed(1)} s`, clip.name);
      if (/^A_?TPose$/i.test(clip.name)) { option.disabled = true; option.textContent += ' · reference pose'; }
      $('libraryClip').add(option);
    }
    $('loadMotionLibrary').hidden = true; $('libraryControls').hidden = false;
    $('libraryStatus').textContent = `${state.library.clips.length} source motions available. Adding a clip creates an unsaved draft; it does not approve contact or locomotion.`;
    toast(`${state.library.clips.length} Quaternius motions ready to adapt.`);
  }, $('loadMotionLibrary'));
}
async function addLibraryMotion() {
  if (!state.handle || !state.library || !state.libraryModule) return;
  await action('Adapting the selected motion to this draft…', async () => {
    stopPlayback();
    const result = state.libraryModule.addLibraryClip(state.handle, state.library, $('libraryClip').value, { strength: Number($('libraryStrength').value) });
    state.activeRigRevision = null; state.rigSaved = false; state.recipeDirty = true; state.checks = null; state.roundtrip = null;
    renderMotionControls(); $('clipSelect').value = result.clip.name; selectClip();
    if (state.showingSource) showRigModel();
    $('rigState').textContent = 'Motion added to an unsaved draft. Test it, then save a new rig revision.';
    $('libraryStatus').textContent = `${result.clip.name} added. Only motion changes are transferred; inspect shoulders, knees and floor contact.`;
    renderHeader(); renderHandoff(); toast('Motion added to the draft. Press Play to inspect it.');
  }, $('addLibraryMotion'));
}
function mergedChecks() {
  const checks = [...(state.checks?.checks || [])];
  if (state.roundtrip) checks.push(...(state.roundtrip.checks || []).map((check) => ({ ...check, id: `export_${check.id}`, label: `Exported · ${check.label}` })));
  return { checks };
}
async function runChecks() {
  if (!state.handle) return;
  return action('Checking the rig and reloading an exported copy…', async () => {
    stopPlayback(); Rigging.setWeightOverlay(state.handle, null); $('showWeights').checked = false;
    state.checks = Rigging.validateRig(state.handle);
    const roundtrip = await Rigging.roundTripRig(state.handle);
    state.roundtrip = roundtrip.validation;
    renderChecks($('rigChecks'), mergedChecks()); resetPose(); applyShading();
    const failures = mergedChecks().checks.filter((check) => check.status === 'fail' || check.pass === false || check.ok === false);
    toast(failures.length ? `${failures.length} checks need attention. Review the findings below.` : 'Rig structure, deformation and exported reload checks completed.', Boolean(failures.length));
  }, $('runChecks'));
}
async function recordTest() {
  if (!state.handle || !state.activeRigRevision) return;
  await action('Recording the rig test…', async () => {
    if (!state.checks) state.checks = Rigging.validateRig(state.handle);
    const result = await api(`/api/bears/${state.bear.id}/tests`, { method: 'POST', body: {
      rigRevision: state.activeRigRevision, suite: state.roundtrip ? 'browser-structure-deformation-roundtrip' : 'browser-structure-deformation',
      results: mergedChecks().checks, notes: $('testNotes').value,
    } });
    upsertBear(result.bear); state.testNotesDirty = false; loadHistory(); toast(`Test saved against rig r${state.activeRigRevision}. Human review remains separate.`);
  }, $('recordTest'));
}
function renderHistories() {
  const bear = state.bear; if (!bear) return;
  const rigHost = $('rigHistory'); rigHost.replaceChildren();
  if (!bear.rigs?.length) { const p = document.createElement('p'); p.className = 'muted'; p.textContent = 'No rig revisions yet.'; rigHost.append(p); }
  for (const rig of [...(bear.rigs || [])].reverse()) {
    const row = document.createElement('div'); row.className = 'history-item'; row.classList.toggle('active', state.activeRigRevision === rig.revision);
    const text = document.createElement('div'); const strong = document.createElement('b'); strong.textContent = `Rig r${rig.revision} · ${rig.stale ? 'Older source' : 'Draft'}`;
    const small = document.createElement('small'); small.textContent = `${date(rig.created)} · Source r${rig.sourceRevision}`; text.append(strong, small);
    if (rig.stale) { const link = document.createElement('a'); link.className = 'text-button'; link.href = rig.modelUrl; link.download = ''; link.textContent = 'Download'; row.append(text, link); }
    else { const button = document.createElement('button'); button.className = 'text-button'; button.textContent = 'Open'; button.addEventListener('click', () => openSavedRig(rig.revision)); row.append(text, button); }
    rigHost.append(row);
  }
  const testHost = $('testHistory'); testHost.replaceChildren();
  if (!bear.tests?.length) { const p = document.createElement('p'); p.className = 'muted'; p.textContent = 'No tests recorded yet.'; testHost.append(p); }
  for (const test of [...(bear.tests || [])].sort((a, b) => new Date(b.created) - new Date(a.created)).slice(0, 12)) {
    const row = document.createElement('div'); row.className = 'history-item';
    const text = document.createElement('div'); const strong = document.createElement('b'); strong.textContent = `Rig r${test.rigRevision} · ${test.stale ? 'Historical source' : 'Test record'}`;
    const small = document.createElement('small'); small.textContent = `${date(test.created)} · ${test.suite}`; text.append(strong, small);
    if (test.notes) { const notes = document.createElement('small'); notes.textContent = test.notes; text.append(notes); }
    row.append(text); testHost.append(row);
  }
}
async function loadHistory() {
  const id = state.bear?.id; if (!id) return;
  try {
    const result = await api(`/api/bears/${id}/history`); if (state.bear?.id !== id) return;
    const hostElement = $('historyEvents'); hostElement.replaceChildren();
    for (const event of (result.history || []).slice(0, 12)) {
      const row = document.createElement('div'); row.className = 'history-item';
      const text = document.createElement('div'); const strong = document.createElement('b'); strong.textContent = pretty(event.kind || event.action || event.event || 'Saved change');
      const small = document.createElement('small'); small.textContent = date(event.created || event.timestamp || event.at); text.append(strong, small); row.append(text); hostElement.append(row);
    }
  } catch (error) { console.warn('History unavailable', error); }
}
function linkDownload(id, url, filename) {
  const link = $(id); link.classList.toggle('disabled', !url); link.setAttribute('aria-disabled', String(!url));
  if (url) { link.href = url; link.download = filename; } else link.removeAttribute('href');
}
function renderHandoff() {
  const bear = state.bear; if (!bear) return;
  const rig = activeExportRig();
  const slug = (bear.name || 'bear').replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase();
  linkDownload('downloadOriginal', bear.modelUrl, `${slug}-source-r${bear.sourceRevision}.glb`);
  linkDownload('downloadRig', rig?.modelUrl, `${slug}-rig-r${rig?.revision}.glb`);
  linkDownload('downloadRecipe', rig?.recipeUrl, `${slug}-rig-r${rig?.revision}.json`);
  linkDownload('downloadManifest', `/api/bears/${bear.id}/manifest`, `${slug}-manifest.json`);
  $('handoffSummary').replaceChildren();
  for (const line of [bear.name, `Source r${bear.sourceRevision}${rig ? ` → Draft rig r${rig.revision}` : ' → No saved rig yet'}`, `${bear.tests?.length || 0} test records · ${reviewLabel(bear.reviewStatus)}`]) { const p = document.createElement('p'); p.textContent = line; $('handoffSummary').append(p); }
}
function handoffText() {
  const bear = state.bear; if (!bear) return '';
  const rig = activeExportRig();
  const issues = (bear.sourceReport?.checks || []).filter((check) => check.status !== 'pass').map((check) => `- ${check.label}: ${check.detail}`);
  return [
    `BEAR STUDIO HANDOFF — ${bear.name}`, `Role: ${bear.role} | Tags: ${(bear.tags || []).join(', ') || 'none'}`,
    `Source: ${bear.source.kind}, revision ${bear.sourceRevision}`, `Source SHA-256: ${bear.sourceSha256}`,
    rig ? `Draft rig: revision ${rig.revision}, SHA-256 ${rig.sha256}` : 'Draft rig: not saved',
    `Human review: ${reviewLabel(bear.reviewStatus)}`, `Test records: ${bear.tests?.filter((test) => !rig || test.rigRevision === rig.revision).length || 0} for the selected rig`,
    '', 'Source issues:', ...(issues.length ? issues : ['- No source warnings recorded.']), '', 'Notes:', bear.notes || 'No notes yet.',
    '', 'The source remains unchanged. Automatic skinning is a draft; mesh cleanup, visual approval and Unreal character integration are separate work.',
  ].join('\n');
}

function updateControls() {
  const hasBear = Boolean(state.bear); const hasSource = Boolean(state.source); const hasRig = Boolean(state.handle);
  const blocked = state.busy || state.loading || state.deciding;
  $('metadataForm').querySelectorAll('input,select,textarea,button').forEach((element) => { element.disabled = !hasBear || blocked; });
  for (const id of ['rigPreset','rigHeight','rigYaw','cropRange','jointSelect','jointX','jointY','jointZ','resetLandmarks','mirrorLandmarks','showLandmarks','saveRecipe','buildRig']) $(id).disabled = !hasSource || blocked;
  $('saveRig').disabled = !hasRig || state.rigSaved || blocked;
  $('showSource').disabled = !hasSource || blocked || state.showingSource;
  $('testControls').disabled = !hasRig || blocked;
  $('recordTest').disabled = !hasRig || !state.activeRigRevision || blocked;
  $('testRecordHint').textContent = state.activeRigRevision ? `Records pin saved rig r${state.activeRigRevision} and its source revision.` : 'Save a rig revision before recording tests.';
  $('lodSelect').disabled = !hasSource || blocked;
  $('copyHandoff').disabled = !hasBear || blocked;
  $('saveMetadata').disabled ||= state.conflict;
  $('saveRecipe').disabled ||= state.conflict;
  $('openImport').disabled = blocked;
  document.querySelectorAll('[data-tab],[data-shading]').forEach((element) => { element.disabled = blocked; });
  $('testEmpty').hidden = hasRig;
}
function setTab(name) {
  if (state.busy || state.loading || state.deciding) return;
  state.tab = name;
  document.querySelectorAll('[data-tab]').forEach((button) => button.setAttribute('aria-selected', String(button.dataset.tab === name)));
  document.querySelectorAll('[data-panel]').forEach((panel) => { panel.hidden = panel.dataset.panel !== name; });
  if (name === 'test' && state.handle) showRigModel();
  if (name === 'rig' && state.source && !state.handle) showSourceModel(true);
  renderLandmarks();
}

async function openImport() {
  if (state.busy || state.loading || state.deciding) return;
  if (hasUnsavedWork() && !await requestDiscard('Importing another bear will leave this selection. Unsaved details, rig work and test notes will be discarded when you import.')) return;
  $('importDialog').showModal(); await refreshScans();
}
async function refreshScans() {
  $('scannerStatus').textContent = 'Checking the scanner workshop…'; $('scanList').replaceChildren();
  try {
    const result = await api('/api/scanner/scans');
    $('scannerStatus').textContent = result.available ? 'Finished scans can be copied into your catalogue.' : `Scanner unavailable. Local GLB import still works. ${result.error || ''}`;
    for (const scan of result.scans || []) {
      const row = document.createElement('div'); row.className = 'scan-card';
      const text = document.createElement('div'); const title = document.createElement('b'); title.textContent = scan.name;
      const small = document.createElement('small'); small.textContent = scan.status === 'done' ? `Finished${scan.quality ? ` · ${scan.quality === 'warn' ? 'Source warnings' : pretty(scan.quality)}` : ''}` : `${pretty(scan.status)}${scan.error ? ` · ${scan.error}` : scan.stage ? ` · ${scan.stage}` : ''}`;
      text.append(title, small); const button = document.createElement('button'); button.className = 'button compact'; button.textContent = scan.status === 'done' ? 'Import' : 'Not ready'; button.disabled = scan.status !== 'done';
      button.addEventListener('click', () => importScan(scan.id, button)); row.append(text, button); $('scanList').append(row);
    }
    if (result.available && !result.scans?.length) $('scannerStatus').textContent = 'The scanner has no scans yet. Import a local GLB to get started.';
  } catch (error) { $('scannerStatus').textContent = error.message; }
}
async function importScan(scanId, button) {
  await action('Copying the finished scan into the studio…', async () => {
    const result = await api('/api/import/scanner', { method: 'POST', body: { scanId } });
    $('importDialog').close(); state.metadataDirty = false; state.recipeDirty = false;
    // Selection runs after the current mutation releases its busy state.
    state.busy = false; await refreshCatalogue(result.bear.id);
    toast(result.imported ? 'Scan imported with its source report and identity.' : 'This exact source is already in your catalogue.');
  }, button);
}
async function importLocal(file) {
  if (!file) return;
  if (file.size > 64 * 1024 * 1024) { toast('Choose a GLB smaller than 64 MB.', true); return; }
  await action(`Importing ${file.name}…`, async () => {
    const result = await api('/api/import/local', { method: 'POST', headers: { 'Content-Type': 'model/gltf-binary', 'X-Filename': encodeURIComponent(file.name) }, body: await file.arrayBuffer() });
    $('importDialog').close(); state.metadataDirty = false; state.recipeDirty = false; state.busy = false;
    await refreshCatalogue(result.bear.id); toast(result.imported ? 'Local GLB imported. The original file is unchanged.' : 'This exact GLB is already in the catalogue.');
  });
  $('localFile').value = '';
}

document.querySelectorAll('[data-tab]').forEach((button) => button.addEventListener('click', () => setTab(button.dataset.tab)));
document.querySelectorAll('[data-camera]').forEach((button) => button.addEventListener('click', () => frameModel(button.dataset.camera)));
document.querySelectorAll('[data-shading]').forEach((button) => button.addEventListener('click', () => {
  if (state.busy || state.loading || state.deciding) return;
  state.shading = button.dataset.shading;
  document.querySelectorAll('[data-shading]').forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
  $('showWeights').checked = false; if (state.handle) Rigging.setWeightOverlay(state.handle, null); applyShading();
}));
$('search').addEventListener('input', renderCatalogue); $('catalogueFilter').addEventListener('change', renderCatalogue);
$('refreshCatalogue').addEventListener('click', async () => {
  if (state.busy || state.loading || state.deciding) return;
  status('Refreshing the catalogue…');
  try { await refreshCatalogue(); } catch (error) { toast(error.message, true); }
});
$('metadataForm').addEventListener('submit', saveMetadata);
$('metadataForm').addEventListener('input', () => { state.metadataDirty = true; $('metadataState').textContent = 'Unsaved details'; });
$('lodSelect').addEventListener('change', () => { state.lod = Number($('lodSelect').value); showSourceModel(); frameModel(); });
$('showSource').addEventListener('click', () => { stopPlayback(); showSourceModel(); frameModel(); });
$('rigPreset').addEventListener('change', () => {
  if (!state.source) return;
  const next = Rigging.defaultRecipe(state.source.scene, { preset: $('rigPreset').value, sourceSha256: state.bear.sourceSha256, sourceRevision: state.bear.sourceRevision });
  state.recipe = next; renderRecipe(); invalidateRig('Template changed. Adjust its joints before binding a new draft.');
});
$('resetLandmarks').addEventListener('click', () => {
  if (!state.source) return;
  const defaults = Rigging.defaultRecipe(state.source.scene, { preset: state.recipe.preset, sourceSha256: state.bear.sourceSha256, sourceRevision: state.bear.sourceRevision });
  state.recipe.landmarks = defaults.landmarks; renderRecipe(); invalidateRig('Joint landmarks reset to the selected template.');
});
['rigHeight', 'rigYaw'].forEach((id) => $(id).addEventListener('change', updateRecipeFromInputs)); $('cropRange').addEventListener('input', updateRecipeFromInputs);
$('jointSelect').addEventListener('change', renderJoint); $('showLandmarks').addEventListener('change', renderLandmarks);
for (const axis of ['X', 'Y', 'Z']) $(`joint${axis}`).addEventListener('change', () => {
  const values = ['X','Y','Z'].map((item) => Number($(`joint${item}`).value));
  if (!values.every(Number.isFinite)) return;
  state.recipe.landmarks[$('jointSelect').value] = values; invalidateRig();
});
$('mirrorLandmarks').addEventListener('click', () => {
  const name = $('jointSelect').value; const landmarks = state.recipe?.landmarks; if (!landmarks?.[name]) return;
  const opposite = Rigging.mirrorLandmark(state.recipe, name);
  if (!opposite) { toast('Choose a left or right limb joint to mirror.'); return; }
  invalidateRig(`Mirrored ${pretty(name)} to ${pretty(opposite)}.`); toast(`Mirrored to ${pretty(opposite)}.`);
});
$('saveRecipe').addEventListener('click', saveRecipe); $('buildRig').addEventListener('click', buildDraft); $('saveRig').addEventListener('click', saveRig);
$('clipSelect').addEventListener('change', selectClip); $('resetPose').addEventListener('click', resetPose);
$('loadMotionLibrary').addEventListener('click', loadMotionLibrary); $('addLibraryMotion').addEventListener('click', addLibraryMotion);
$('libraryStrength').addEventListener('input', () => { $('libraryStrengthValue').textContent = `${Math.round(Number($('libraryStrength').value) * 100)}%`; });
$('playPause').addEventListener('click', () => {
  if (!state.handle) return;
  if (!currentClip() && state.handle.clips?.length) { $('clipSelect').value = state.handle.clips[0].name; selectClip(); }
  if (!currentClip()) { toast('This rig has no embedded motion clips. Use the bone controls to test it.'); return; }
  state.playing = !state.playing; $('playPause').textContent = state.playing ? 'Ⅱ Pause' : '▶ Play'; if (state.showingSource) showRigModel();
});
$('timeline').addEventListener('input', () => { stopPlayback(); state.playTime = Number($('timeline').value); const clip = currentClip(); if (clip) Rigging.sampleClip(state.handle, clip.name, state.playTime); $('timelineTime').textContent = `${state.playTime.toFixed(2)} s`; });
for (const axis of ['X','Y','Z']) $(`pose${axis}`).addEventListener('input', setBonePose);
$('poseBone').addEventListener('change', () => { stopPlayback(); readPoseInputs(); if ($('showWeights').checked && state.handle) Rigging.setWeightOverlay(state.handle, $('poseBone').value); });
$('showSkeleton').addEventListener('change', () => { if (state.handle?.helper) state.handle.helper.visible = $('showSkeleton').checked && !state.showingSource; });
$('showWeights').addEventListener('change', () => { if (!state.handle) return; Rigging.setWeightOverlay(state.handle, $('showWeights').checked ? $('poseBone').value : null); if (!$('showWeights').checked) applyShading(); });
$('runChecks').addEventListener('click', runChecks); $('recordTest').addEventListener('click', recordTest);
$('testNotes').addEventListener('input', () => { state.testNotesDirty = true; });
$('copyHandoff').addEventListener('click', () => action('Preparing the team handoff…', async () => { await navigator.clipboard.writeText(handoffText()); toast('Team handoff copied with source identity, rig revision and review notes.'); }));
$('openImport').addEventListener('click', openImport); $('closeImport').addEventListener('click', () => $('importDialog').close());
$('cancelDiscard').addEventListener('click', () => finishDiscard(false));
$('confirmDiscard').addEventListener('click', () => finishDiscard(true));
$('discardDialog').addEventListener('cancel', (event) => { event.preventDefault(); finishDiscard(false); });
$('discardDialog').addEventListener('close', () => { if (discardDecision && !$('discardDialog').open) finishDiscard(false); });
$('refreshScans').addEventListener('click', refreshScans); $('localFile').addEventListener('change', () => importLocal($('localFile').files[0]));
$('scannerLink').addEventListener('click', () => { if (state.scannerUrl) window.open(state.scannerUrl, '_blank', 'noopener,noreferrer'); else openImport(); });
$('importDialog').addEventListener('click', (event) => { if (event.target === $('importDialog')) { const rect = $('importDialog').getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) $('importDialog').close(); } });
window.addEventListener('beforeunload', (event) => { if (hasUnsavedWork()) { event.preventDefault(); event.returnValue = ''; } });
const raycaster = new THREE.Raycaster(); const pointer = new THREE.Vector2(); let pointerStart = null;
renderer.domElement.addEventListener('pointerdown', (event) => { pointerStart = [event.clientX, event.clientY]; });
renderer.domElement.addEventListener('pointerup', (event) => {
  if (!pointerStart || Math.hypot(event.clientX - pointerStart[0], event.clientY - pointerStart[1]) > 5 || !landmarkGroup.children.length) return;
  const rect = renderer.domElement.getBoundingClientRect(); pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
  raycaster.setFromCamera(pointer, camera); const hit = raycaster.intersectObjects(landmarkGroup.children)[0];
  if (hit) { $('jointSelect').value = hit.object.userData.landmarkName; renderJoint(); }
});
let previousTime = performance.now();
renderer.setAnimationLoop((now) => {
  const delta = Math.min((now - previousTime) / 1000, 0.08); previousTime = now;
  const clip = currentClip();
  if (state.playing && state.handle && clip) { state.playTime = (state.playTime + delta * Number($('playSpeed').value)) % Math.max(clip.duration, 0.01); Rigging.sampleClip(state.handle, clip.name, state.playTime); $('timeline').value = state.playTime; $('timelineTime').textContent = `${state.playTime.toFixed(2)} s`; }
  controls.update(); renderer.render(scene, camera);
});

// Read-only state plus explicit actions help independent browser QA exercise the same UI paths.
window.bearStudio = { state, Rigging, selectBear, refreshCatalogue, buildDraft, saveRig, openSavedRig, runChecks, recordTest, setTab, frameModel, handoffText };
async function boot() {
  resize(); updateControls();
  try {
    const health = await api('/api/health'); state.scannerUrl = health.scannerUrl; $('connection').textContent = 'Local studio connected';
    await refreshCatalogue();
    if (!state.bears.length) showMessage('Start your collection', 'Import a finished scanner export or a local GLB.');
  } catch (error) { $('connection').textContent = 'Studio offline'; $('connection').classList.add('offline'); showMessage('The studio could not connect', error.message); toast(error.message, true); }
}
boot();
