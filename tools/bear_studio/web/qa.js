import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as THREE from 'three';
import * as rigging from './rigging.js';
import { loadAnimationLibrary, addLibraryClip } from './animation_library.js';

const output = document.querySelector('#result');
let report = null, artifact = null;
function download(name, blob) {
  const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = name;
  link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}
document.querySelector('#download').onclick = () => download('bear-studio-rig-regression.json', new Blob([JSON.stringify(report, null, 2)], {type:'application/json'}));
document.querySelector('#glb').onclick = () => download('bear-studio-tested-draft.glb', new Blob([artifact], {type:'model/gltf-binary'}));
document.querySelector('#run').onclick = async () => {
  const button = document.querySelector('#run'); button.disabled = true;
  report = {date:new Date().toISOString(),threeRevision:THREE.REVISION,checks:[],cases:[],passed:false};
  const check = (name, passed, detail) => {report.checks.push({name,passed,detail}); if (!passed) throw new Error(name + ': ' + detail);};
  try {
    output.textContent = 'Loading the actual source…';
    const {bears} = await (await fetch('/api/bears')).json();
    const bear = bears.find(item => item.source.kind === 'bundled-sample') || bears[0];
    if (!bear) throw new Error('No source available. Import a GLB in the studio first.');
    report.source = {id:bear.id,sha256:bear.sourceSha256,revision:bear.sourceRevision};
    const source = await new GLTFLoader().loadAsync(bear.modelUrl);
    const original = [];
    source.scene.traverse(node => {if (node.isMesh) original.push({node,position:new Float32Array(node.geometry.attributes.position.array),skin:node.geometry.getAttribute('skinWeight'),material:node.material});});
    for (const crop of [0,0.52]) {
      output.textContent = 'Testing real skin, deformation and GLB reload; crop ' + crop;
      const recipe = rigging.defaultRecipe(source.scene,{sourceSha256:bear.sourceSha256,sourceRevision:bear.sourceRevision});
      recipe.cropFraction = crop;
      const rig = rigging.buildRig(source.scene, recipe);
      try {
        check('Actual skinned mesh at crop ' + crop, rig.mesh.isSkinnedMesh && rig.skeleton.bones.length === 16, 'Real Bone/Skeleton with 16 joints');
        const numerical = rigging.validateRig(rig);
        check('Draft structure and deformation at crop ' + crop, numerical.passed, numerical.checks.filter(c => c.status === 'fail'));
        const skin = rig.mesh.geometry.attributes.skinWeight;
        const saved = skin.getX(0); skin.setX(0,0);
        const invalid = rigging.validateRig(rig);
        skin.setX(0,saved);
        check('Corrupt weights detected at crop ' + crop, !invalid.passed, 'Intentionally changed one influence; restored afterward');
        skin.setX(0,NaN); const nanValidation=rigging.validateRig(rig); skin.setX(0,saved);
        check('Nonfinite weights fail cleanly',!nanValidation.passed,'No validator crash or false pass');
        const joints=rig.mesh.geometry.attributes.skinIndex, originalJoint=joints.getX(0);
        joints.setX(0,65000); const badJointValidation=rigging.validateRig(rig); joints.setX(0,originalJoint);
        check('Invalid joint indices fail cleanly',!badJointValidation.passed,'No validator crash or false pass');
        rigging.setWeightOverlay(rig, 'head');
        rig.group.visible=false;
        const roundtrip = await rigging.roundTripRig(rig, recipe);
        rig.group.visible=true;
        check('Hidden viewport state still exports complete rig',roundtrip.validation.passed,'Export includes the owned rig while source view is shown');
        check('Exported skin reloads and deforms at crop ' + crop, roundtrip.validation.passed, roundtrip.validation.metrics);
        const reloaded = await new GLTFLoader().parseAsync(roundtrip.glb,'');
        const hydrated = rigging.hydrateRig(reloaded, recipe);
        check('Weight visualization not baked into export', !hydrated.mesh.geometry.getAttribute('color'), 'Temporary weight colours stripped from delivered GLB');
        rigging.disposeRig(hydrated,{textures:true});
        const changed = structuredClone(recipe); changed.landmarks.head[0] += 0.01;
        let rejected = false; try {await rigging.exportRig(rig,changed);} catch {rejected = true;}
        check('Changed landmarks require rebind', rejected, 'Stale recipe export refused');
        if (crop === 0.52) {
          output.textContent = 'Testing licensed animation transfer, exported clips and provenance…';
          const library = await loadAnimationLibrary();
          check('Official animation pack hash and inventory', library.clips.length === 43, library.source);
          report.motion = [];
          for (const name of ['Sitting_Idle_Loop','Hit_Chest','Walk_Loop']) {
            const transfer = addLibraryClip(rig,library,name);
            const positions = rig.mesh.geometry.attributes.position;
            const samples = Array.from({length:Math.ceil(positions.count/32)},(_,n)=>n*32).filter(n=>n<positions.count);
            const at = time => {rigging.sampleClip(rig,transfer.clip.name,time); return samples.map(n=>rig.mesh.applyBoneTransform(n,new THREE.Vector3().fromBufferAttribute(positions,n)));};
            const before = at(0); let peak=0,moved=0;
            for(const fraction of [0.2,0.45,0.7]) at(transfer.clip.duration*fraction).forEach((p,n)=>{const d=p.distanceTo(before[n]);peak=Math.max(peak,d);if(d>1e-7)moved++;});
            check('Imported motion actually deforms: '+name, moved>0 && Number.isFinite(peak), {movedSamples:moved,peakMetres:peak,...transfer.report});
            report.motion.push(transfer.report);
          }
          const motionRoundtrip = await rigging.roundTripRig(rig,recipe);
          const loadedMotion = rigging.hydrateRig(await new GLTFLoader().parseAsync(motionRoundtrip.glb,''),recipe);
          check('Online motions and provenance survive export/reload',motionRoundtrip.validation.passed && loadedMotion.clips.length === 8 && loadedMotion.animationSources?.length === 3,{clips:loadedMotion.clips.map(c=>c.name),sourceCount:loadedMotion.animationSources?.length});
          rigging.disposeRig(loadedMotion,{textures:true});
          artifact=motionRoundtrip.glb; report.motionValidation=motionRoundtrip.validation;
        }
        const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',roundtrip.glb)),b=>b.toString(16).padStart(2,'0')).join('');
        report.cases.push({crop,sha256:hash,bytes:roundtrip.glb.byteLength,validation:roundtrip.validation});
        if (!artifact) artifact = roundtrip.glb;
      } finally {rigging.disposeRig(rig);}
    }
    check('Original geometry and materials unchanged', original.every(({node,position,skin,material}) => node.material === material && node.geometry.getAttribute('skinWeight') === skin && position.every((v,i)=>Object.is(v,node.geometry.attributes.position.array[i]))), 'All source position values and skin/material references preserved');
    report.passed = true;
  } catch (error) {report.error = error.stack || String(error);}
  output.textContent = JSON.stringify(report,null,2); button.disabled = false;
  document.querySelector('#download').disabled = false;
  document.querySelector('#glb').disabled = !artifact;
};
