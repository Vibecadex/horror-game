# Bear Studio

## Prerequisites and launch

Use Python 3.11+ and a browser with WebGL 2. The source sample must be hydrated by Git LFS. Three.js 0.170.0 is loaded from jsDelivr, matching the existing scanner viewer; the browser needs access to that CDN. No npm command, package installation, Unreal editor or Blender process is required to open the studio.

Run **[BEAR_STUDIO.cmd](../BEAR_STUDIO.cmd)** from this checkout. It opens `http://127.0.0.1:8472` and starts a hidden local Python service if needed. Repeated launches reuse only a service from the same checkout and catalogue. Another service on that port produces a clear error; choose `BEAR_STUDIO.cmd --port 8473` instead.

For an interactive server that stops with Ctrl+C:

```powershell
python tools/launch_bear_studio.py --foreground
```

For automation or a health check:

```powershell
python tools/launch_bear_studio.py --no-browser
python tools/launch_bear_studio.py --status
```

The catalogue, immutable working copies, logs and local process receipt live in ignored `.team-local/bear-studio`. Back up that entire directory to preserve your local work. It is not synchronized to the private team repository automatically. The server binds loopback; phone access and multi-user hosting are separate work.

## Authoring workflow

1. **Catalogue.** Import a finished scan from the configured scanner, a self-contained `.glb`, or one bear's pack `.zip`. Versioned scanner imports verify the declared file sizes and SHA-256 hashes and retain quality reports, landmarks, capture pose and the original pack manifest. Name the bear, tag it, assign a role and retain review notes. The bundled example is explicitly a prebuilt sample.
2. **Inspect.** Review texture, clay and wireframe views, source LODs, dimensions, quality warnings and provenance. Source reconstruction quality does not become acceptable merely because the file loads.
3. **Rig.** Pick a seated or upright template, adjust normalized landmarks and symmetry, and preview an optional crop on a copy. Bind a draft skin, inspect weights, then save a real rig revision. Saving landmark settings alone does not create a rig.
4. **Test.** Inspect poses and clips with playback controls, run numerical and export/reload checks, and record findings against the saved rig revision. Changing the source or recipe requires fresh checks. Automated deformation checks cannot establish artistic quality or grounded locomotion.
5. **Handoff.** Download the original source, derived skinned GLB, recipe, validation and manifest. Keep source, rig and test identities together. Human review remains a separate decision.

The scan's support box is fused to the mesh. A horizontal crop is a coarse aid that may cut feet or leave an open surface; it is not topology cleanup. Heuristic skinning is an editable starting point. Professional weight painting, repaired topology, collision, foot contacts and final locomotion require further review and authoring.

## Included online motion library

The creator's free [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html) Standard release is retained locally with its **CC0** license and exact source hashes under `Assets/ThirdParty/QuaterniusUAL`. It contains 43 source clips, including a reference T-pose. The T-pose is excluded from motion transfer. No paid edition is required.

In **Test → Explore the motion library**, load the library, choose a clip and motion strength, then select **Add as draft motion**. Play and scrub it, inspect shoulders, seams and floor contact, and save a new rig revision before saving test findings. The handoff GLB retains the clip's source, license, hash and transfer settings. Adding a clip clears the previous saved-rig/test association.

The transfer fits humanoid rotations to 15 teddy bone chains relative to the source clip's initial pose. It limits rotation and retains the teddy's rest pose; root travel and source scaling are excluded. This is a draft animation aid. It does not plant feet, repair intersecting limbs or establish a usable walking cycle. Three clips have numerical deformation and export/reload evidence: `Sitting_Idle_Loop`, `Hit_Chest` and `Walk_Loop`. The whole library has not received visual acceptance.

The initial rig builder accepts static source meshes. Existing skinned GLBs can be catalogued and inspected; the builder refuses to overwrite their skin. Saved Bear Studio rigs can be reopened with their exact existing bones, weights and clips.

## Scope and preservation

This interface expands the fork's bear workflow; it does not replace the saved chamber, gameplay, enemy or scan source. `IMPORT_BEARS.cmd` remains the verified **static-prop** Unreal path. A studio skinned GLB is an animation handoff, not proof of a skeletal Unreal import or encounter integration.

Separately, the team's newer **21-bone rigfit exporter** now passes a [native Unreal compatibility review](TEAM_RIG_NATIVE_REVIEW.md) on a synthetic fixture, including its four test clips and basic mannequin retargets. Those results do not transfer to this Studio's 16-bone drafts or to unfinished real scans. `REVIEW_TEAM_RIG.cmd` repeats the isolated native review.

The scanner is accessed read-only. Its unfinished/failed jobs remain visible and cannot be imported. The scanner's current OpenMVS Application Control blocker is independent of using finished exports. No Windows protection, certificate trust or firewall rule is changed.

Each source and rig is copied and hashed. A changed scan, report or landmark file creates a source revision and retains older rig/test history as stale, even if the model bytes are unchanged. An older pack version cannot replace a newer one. Metadata saves use revision conflict detection. The local API refuses arbitrary filesystem paths and external GLB dependencies.

Use the scanner's per-bear **Pack** download for offline Studio imports. A ZIP can contain one pack at its root or inside one folder; combined multi-bear ZIPs remain supported by the Unreal importer, but not by Studio's single-bear picker. Live scanner identities remain scoped to the scanner address; offline packs use a separate local pack collection keyed by pack ID. Legacy scanners remain readable when the versioned endpoint is absent. An integrity error from a versioned endpoint never falls back to unchecked legacy files.

The team example now appears as **Real bear (example scan)**. Its incomplete landmarks and fused support box are retained and shown as warnings. [Remote team continuation](REMOTE_TEAM_CONTINUATION.md) records the integrated work and the remaining rig-test prerequisites.

## Team continuation

Implementation ownership: `server.py` owns catalogue/storage/API; `web/studio.js`, `index.html` and `studio.css` own the interface; `web/rigging.js` owns rig mathematics and GLB roundtrips; `web/animation_library.js` owns motion transfer and provenance. [API contract](../tools/bear_studio/API.md) documents response shapes and limits. [Side chat prompt](BEAR_STUDIO_SIDE_CHAT.md) is prepared for the user-requested ChatGPT review; consultation is recorded only if a response is actually received.

Run backend regression checks with:

```powershell
python -m unittest discover -s tools/bear_studio -p "test_*.py" -v
```

Acceptance requires browser evidence in addition to tests: inspect the real sample, edit and reload catalogue data, bind a nontrivial skin, observe non-root vertex motion, save/export/reload a rig and record findings against it. Keep implementation, automated checks, visual review and user acceptance separate.

The read-only browser regression page is `http://127.0.0.1:8472/qa.html`. It exercises a separate in-memory draft and does not update the catalogue. Current evidence: [QA report](../evidence/bear-studio/20261006T134902Z/QA_REVIEW.md) and [independent code/artifact review](../tools/bear_studio/REVIEW.md).

## Useful next work

Prioritize better source segmentation and topology repair, interactive weight painting, editable humanoid retarget maps, collision authoring, grounded gait/contact review, Unreal skeletal import with a preview scene, and shared catalogue synchronization. Each needs a concrete implementation and fresh evidence before being marked available.
