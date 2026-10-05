# Teddy Encounter working status

## Private team repository handoff — 5 October 2026

Repository: **https://github.com/Vibecadex/horror-game**, private. Existing organization collaborators have write access; no invitations or external messages were sent. Git LFS carries binary assets and supports locks for shared maps/packages/source scenes.

The current [chamber brief](study/CHAMBER_PARITY_BRIEF.md) and [visual study](study/brief/index.html) now describe the final V2 room and its remaining visual gaps. [Team continuation](study/TEAM_CONTINUATION.md) supplies prerequisites, ownership, validation commands and an agent prompt. The earlier brief and09:30 interactive study are retained as explicitly historical copies.

The full active Blueprint Content/Config, editable sources, references and retained evidence are included. Generated caches, credentials, native BossShot experiment, setup/debug outputs, raw repeated frames and recovery archives stay local; see the documented exclusions. Original external references are copied byte-for-byte into `Assets/Reference`. The tracked Android File Server token is removed and its unused service disabled; exact original config is retained under ignored `.team-local`. Portable engine overrides and checkout-relative review paths do not change game assets.

Local handoff checks pass: all766 Content hashes unchanged,98 document/review links resolve,11 launcher regression tests pass, and the play command resolves the saved encounter without launching another engine. The updated study page was rendered and visually inspected in Edge. The existing chamber/room gameplay receipts below remain the scene verification; repository preparation does not claim new physical play or visual acceptance.

**Fresh remote clone verified:** [receipt](evidence/team-handoff/remote-clone-verification.json). All1,747 LFS paths downloaded and hydrated (1,708 unique objects); LFS integrity passed, all766 game Content hashes matched,98 links resolved, six original comparison images decoded, and the launcher/QA manifest paths resolved inside the new checkout. The clone was clean after checks. The first Git connection expired during the large LFS transfer; all objects finished uploading and the branch push succeeded on retry with connection keepalive. This verification used a separate checkout on the same workstation, without starting another Unreal process or installing tools.

## Current chamber-reference pass — 5 October 2026

The current request is **chamber parity** with the supplied [front](study/visuals/chamber-target-front.png) and [reverse](study/visuals/chamber-target-reverse.png) concepts. The team is Astra art direction, a source environment artist, independent QA and one Unreal writer. The active destination remains `/Game/Maps/TeddyEncounter` in `TeddyBlueprint/TeddyBlueprint.uproject`; characters, combat graphs, controls and ordinary FOV54 are preserved.

The room now has the wide B-3 pressure bulkhead and wheel, a complete camera-aware reverse wall with two service bays, modeled piers, grounded drums/tanks/cabinets, lower perimeter drains and local architectural lights. New world-aligned weathered wall materials use a separately generated [wall albedo and provenance](Assets/Adapted/ChamberParity/WallSurface/manifest.json). Five connected shallow floor fields and four sparse slab groups remain; five broader crust banks replace the conspicuously curved old spall banks. Originals are retained, with appearance overrides or hiding where superseded.

Use **[PLAY.cmd](PLAY.cmd)** for the saved encounter or **[EDIT.cmd](EDIT.cmd)** for the editable level. The [chamber comparison](evidence/chamber/20261005T095028Z/review.html) pairs both supplied references with direct native 1920×1280 Unreal captures, includes the earlier room and a native gameplay recording. Architectural cameras are labelled; the ordinary gameplay camera remains unchanged.

| Final saved-state evidence | Result |
| --- | --- |
| `20261005T114712-capture_chamber_views` | Front and reverse 1920×1280 native images; saved materials, lights and native cutaway behavior. |
| `20261005T114820-verify_chamber_runtime` | **28/28** independent checks: exact corrected mesh identities, frozen source transforms, ownership, collision, floor height bounds, native wall/light hiding and FOV54 restoration. |
| `20261005T114928-verify_full_room` | **28/28**: retained room/spawn/boundary invariants, 36 clearance probes, four wall walks/dashes, twelve camera pairs and six decoded views. |
| `native-motion-20261005T115126` | Native 1280×720 recording, 19.1667 seconds, 572 decoded frames, about 29.84 fps; normal AI/health in an isolated QA copy, clean capture/game exits. Silent, simulated input; ends in player defeat/F5 prompt, not boss defeat. |

The final corrected source sets are [FloorNormalsV2](Assets/Adapted/ChamberParity/FloorNormalsV2/manifest.json), [SlabsNormalsV2](Assets/Adapted/ChamberParity/SlabsNormalsV2/manifest.json) and [CrustNormalsV2](Assets/Adapted/ChamberParity/CrustNormalsV2/manifest.json). All source/FBX normal and closed-volume checks pass. Boundary repairs preserve positions, UVs, bounds, placement transforms and triangle counts. The V1 black-cap failure at `20261005T111910-capture_chamber_views` remains preserved as rejected evidence; `113224` first confirms its correction, and the final `114712` pair includes the corrected connected fields and sparse fragments. Current surface scripts bind retained material graphs to separate corrected mesh assets.

[Final preservation](evidence/chamber/20261005T095028Z/final-preservation.json) passed: **175 owned encounter asset files** stayed byte-identical throughout final verification, all **555 original baseline files** and original media/reference hashes remain intact, and the only preexisting asset changed by this chamber pass is `TeddyEncounter.umap`. The 49 added files include retained earlier chamber variants; this is an inventory count, not a count of assigned scene assets. Config and launcher hashes are unchanged. The 132-file before-edit archive remains at `evidence/chamber/20261005T095028Z/before-chamber.zip`. Root was the only Unreal writer; no install, security change or global Codex change was used.

The [independent final review](evidence/chamber-qa/final/INDEPENDENT_REVIEW.md), [Astra brief](study/CHAMBER_PARITY_BRIEF.md), [QA history](study/CHAMBER_PARITY_QA.md) and [saved settings](study/chamber-settings.json) separate technical verification from visual acceptance. The room's defining architecture is established. Remaining chamber differences are more localized fracture patches/fine grain, more regular wall panels, weaker overhead haze and darker service recesses. Exact visual parity and user acceptance are not established. Physical-device input, matched audio, packaging and sustained performance remain unverified. The earlier character/input evidence below is historical; those assets were preserved in this pass.

The local [review integrity check](evidence/chamber/20261005T095028Z/review-integrity.json) passes all 20 static links, eight decoded images and the inline JavaScript syntax check. Independent QA also resolved its 73 local report links. The launch helper opened the saved chamber in a responding native game window at 12:00 UTC, process71464: [launch receipt](evidence/chamber/20261005T095028Z/play-launch-receipt.json). The game is left open for the user; F5 restarts a fresh encounter. Close it before further Unreal authoring, as the shared-asset process guard remains active.

## Earlier selected-reference integration — 5 October 2026, 09:30 UTC

The selected [close reference](study/visuals/direction-close-best.jpg) has been expanded into a complete playable chamber with the requested team: Astra art direction, environment/character source authoring, independent QA and one Unreal integrator. [Visual review](evidence/parity/20261005T070301Z/review.html), [expanded concept](study/visuals/parity-expanded-reference.png), [Astra brief](study/PARITY_ART_DIRECTION.md), [active asset manifest](study/PARITY_ASSET_MANIFEST.md), [controls](ENCOUNTER.md). Use **PLAY.cmd** or **EDIT.cmd**. The saved destination is still `TeddyBlueprint/TeddyBlueprint.uproject`, `/Game/Maps/TeddyEncounter`.

The current look combines Grok's preserved texture inputs in new sibling materials, thirteen weighted crown stitches on TeddyV2, actual Cloth shading, and forty-five non-colliding damaged-floor placements. Two fracture fields now have interrupted worn plates and larger fragments. The separate `A_Teddy_DefeatGrounded` clip replaces one boss and both stitchling death routes. The original Skeleton and six clips remain preserved; source checks cover 285 floor-contact samples and eighteen original-action comparisons.

The chamber extension is integrated: **84 new non-colliding instances, 21 meshes, 6,344 unique / 38,988 placed triangles**. It replaces the appearance of 27 plain boxes while retaining their original collision/transforms and all 41 existing kit props. Reviewed source inputs were frozen and hash-checked. The full seventeen-shell/thirty-six-dressing catalogs and twenty pre-production clips are not all active. In particular, the older DefeatBreath remains unassigned.

Saved settings are [combined materials](study/parity-combined-settings.json) and [atmosphere](study/parity-atmosphere-settings.json). FOV54 and existing tracking/input are retained. The look uses a focused teal key, broad rear volumetric haze, a moving white player pool, fixed world-space foreground dampness and character-only perimeter support. The final thread material is `[0.06, 0.055, 0.045]`. QA found a rear-centre fill gap after the geometry checks; a bounded 6000 cd character-only light resolves it at three checked positions without floor or fog spill. Earlier glowing fog spheres, bright fog-bar trials and failed imports remain labelled historical evidence.

| Evidence | Result |
| --- | --- |
| `20261005T091420-verify_full_room` | **28/28**: original boundaries/spawns, extension ownership/bounds, 36 clearance probes, four wall walks/dashes, twelve camera pairs and six decoded views. |
| `20261005T084751-verify_parity_runtime` | **48/48**: all four V2 skins, original 17-bone Unreal hierarchy, seven clips, moving/aiming light, actual damage-triggered boss/minion deaths and grounded settled poses. |
| `20261005T080258-verify_encounter_keys` | **12/12** saved-key routes, including movement, dodge, fire, pause/resume and restart while paused. |
| `20261005T092532-capture_parity_rear_visibility` | Three saved-lighting rear-centre views; independent reviewer confirms restored head/shoulder/weapon silhouette at x1000, x1300 and x1400. |
| `20261005T092659-capture_parity_delivery` | Six decoded 1280×720 views: matched gameplay, opposite-corner gameplay and four staged architectural views. |
| `native-motion-20261005T092830` | Native 1280×720 game-window recording at 30 fps, normal AI/health in an isolated QA copy, four-second final observation hold; all frames decoded, clean exit. |

The final capture and native movie did not change any of the **126 active asset files** in their validation snapshot. All **555 original baseline files**, source video, source archive, downloaded GLB and selected reference passed fresh hash checks: [preservation receipt](evidence/parity/20261005T070301Z/final-preservation.json). The earlier snapshot is retained; [this record](evidence/parity/20261005T070301Z/rear-readability-checkpoint-change.json) explains the single map change for the visibility repair. The surface handoff, pre-room extension and pre-repair map each have preserved backups. Root remained the only Unreal writer during integration and validation.

See the [independent final review](evidence/parity-review/final/INDEPENDENT_REVIEW.md) for rendered and motion observations. Functional passes are not exact reference acceptance. Remaining visible differences include finer crown threads, less connected/varied floor wear, brighter central/lower-floor areas and the candidate's simpler anatomy/procedural motion. Physical-device play, audio matching, packaging and sustained performance are unverified. The next meaningful acceptance step is the user's play and visual review of this concrete saved result; do not rerun setup or broad historical builders to open it.

The sections below record earlier passes; their render paths and settings are historical.

Local play handoff: `PLAY.cmd`'s helper opened the saved encounter successfully in a responding native game window ([receipt](evidence/parity/20261005T070301Z/play-launch-receipt.json)). The open helper now uses the existing editor-process guard; a second play launch was refused while the first remained running. [Review integrity](evidence/parity/20261005T070301Z/review-integrity.json) passed 37 HTML references, 10 decoded images, 135 documentation links and the movie hash. The game was left open for the user; close it before further engine authoring.

## Pre-production — 5 October 2026

The study now has a pre-production set in `study/preprod/`. Index: `PREPROD.md`. Twenty new in-place clips are exported under `Assets/Adapted/AnimPreprod/` on the existing rig. The source blend was not saved back. A measured plan places 303 copies of meshes that already exist: 107 shell, 41 kit, 110 dressing, 45 floor. Four lanes stay at least 220 cm wide. The combat footprint was checked empty of shell, kit, and dressing. Concept stills that added a roof, a hall, or a fourth creature are filed as rejected. Nothing in this pass was imported. Parity is not accepted. Next for the scene writer, when the editor is free: hide the wall boxes, place the shell, then the dressing clusters, and only then consider the new clips.

## Room shell assets — 5 October 2026

The scene pass kept the editor. Shell meshes are on disk only, in `Assets/Adapted/RoomShell/`, outside the room-kit import glob. Seventeen FBX modules cover the walls, cutaway, cornice, footing, gutter, recesses, fittings, corner riser, and outer ground. `Assets/Adapted/RoomDressing/` adds 36 panel, pipe, cable, and fitting modules. The existing ten-piece kit, its wheels, TeddyV2, and the level were not edited. Four surface families sit beside the shell meshes and are not imported. See the README in each folder. Next step for the scene writer is to place the shell in place of the boxes, then dress the perimeter in clusters, without a second collision shell.

## Comfy surface pass — 5 October 2026

The live log is `study/LIVE_BRIEF.md`. Flux.2 Klein 4B on a local ComfyUI server made original weave and damp scans. Those maps are on the parity cloth and floor. The stitched teddy, forty-five floor meshes, key, haze, and softened player pool stay in `/Game/Maps/TeddyEncounter`. Graphic decals and the box foot-debris are hidden. Matched plate `evidence/implementation/20261005T073350-capture_parity_look` and gallery `evidence/implementation/20261005T073442-capture_room_gallery` compiled cleanly. A movement recording reached combat and restart, then timed out waiting for its audio file, so it is not an encoded clip. Parity is not accepted. The largest gaps are the seam reading as a crack, drawn floor cracks, and a round player pool.

## Active visual parity pass — 5 October 2026

The user selected `study/visuals/direction-close-best.jpg` and explicitly requested an expert expansion plus visual parity. This selected look study is now the art target. It is substantially brighter centrally and darker in the corners than the older original-video grading notes; those earlier brightness thresholds must not be reused blindly.

Expanded concept: `study/visuals/parity-expanded-reference.png`, generated with the built-in image tool, with prompt retained beside it. Astra's production brief is `study/PARITY_ART_DIRECTION.md`; independent criteria and diagnostic tooling are `study/PARITY_QA.md` and `tools/verify_visual_parity.py`. Concept imagery is not runtime evidence.

Before-edit preservation: `evidence/parity/20261005T070301Z/before-parity.zip`, 221 files with verified hashes. All new art uses `/Game/TeddyEncounter/Parity` and `TE_Parity_`/`ParityOwned`; Grok's prior material/texture assets and the full room source remain preserved. Root is the sole engine writer. No concurrent Grok run or Unreal process was active at the start of this pass.

Current implementation: a focused teal spotlight and far local fog, a player-following white light, actual Cloth shading via material attributes, 45 placements from six original shallow damaged-concrete meshes, and a new stitched teddy skin on the existing skeleton. Eighteen weighted stitches preserve original body vertices/weights/UVs and all six clip deformations in source checks. Runtime import uses the existing animation clips. Gameplay FOV changed from 48 to 54 for the selected composition; camera tracking, inputs and spawn transforms remain intact.

First look render `20261005T070819-capture_room_gallery` overshot floor brightness and light footprint; independent QA retained that failure. `study/parity-settings.json` now records look-02, reducing/narrowing the key and player pools, correcting green bias and matching camera scale. Combined geometry/material capture `20261005T071604-capture_parity_look` is the next review. Parity is not yet accepted; the three current priorities are light-footprint balance, tactile cloth/seams, and convincing irregular ground depth. Fresh moving gameplay, corner visibility and relevant controls/animation regressions follow the visual iterations.

## Completed room and combined verification — 5 October 2026

The full industrial containment/pump chamber is built: three tall enclosing walls, a rear bulkhead, structural supports, continuous pipework, ventilation, tanks, cabinets, perimeter drains, grounded service bays and restrained warning fixtures. The central combat footprint remains clear. The user-requested team comprised Astra art direction/gallery tooling, an environment mesh artist, a separate QA reviewer and the root Unreal integrator. The room uses 126 owned actors and ten original modular meshes, with editable Blender source in `Assets/Adapted/Room`.

Run **PLAY.cmd** or **EDIT.cmd**. The [current combined review](evidence/full-room/20261005T050433Z/review.html) includes six room views, an ordinary-game recording, the original-video comparison and [independent review](evidence/full-room/20261005T050433Z/INDEPENDENT_REVIEW.md). [Build report](evidence/full-room/20261005T050433Z/ROOM_REPORT.md), [manifest](evidence/full-room/20261005T050433Z/manifest.json), [controls](ENCOUNTER.md).

The separate user-owned Grok surface pass finished before these fresh checks. Its textures, three material changes, four decals and two creature Blueprint material overrides are preserved. All 113 tracked combined assets/source/config files stayed byte-identical during verification, and the active encounter asset set stayed unchanged. The original 555 baseline files, video, source archive and teddy download remain unchanged. See [combined validation](evidence/full-room/20261005T050433Z/combined-validation.json) and [preservation](evidence/full-room/20261005T050433Z/preservation.json).

| Fresh combined run | Result |
| --- | --- |
| `20261005T054434-verify_full_room` | 22/22 checks: saved geometry/spawns, 36 clearance probes, four wall walks/dashes, twelve framing cases, 72 visibility rays, six decoded corner views. |
| `20261005T054646-verify_encounter_keys` | 12/12 saved-key checks, including dodge, firing, pause/resume and restart while paused. |
| `20261005T054732-capture_room_gallery` | Six decoded 1280×720 views at saved lighting/exposure. Gameplay and staged architectural views are labelled. |
| `native-motion-20261005T054842` | Ordinary-game window capture, normal AI/health, simulated input driver in an isolated QA map; all video frames decoded and clean exit. |

These checks do not establish physical-device play or exact reference fidelity. At maximum separation the player remains small and dim. The new floor crack, stain and debris are more graphic and prominent than the reference wear; the teddy anatomy/motion remains simplified. Audio matching, packaged distribution and sustained performance are unverified. User acceptance remains separate.

The historical pre-room archive is `evidence/full-room/20261005T050433Z/before-room.zip`, with 158 file hashes in `baseline.json`. Do not restore it wholesale over the later Grok work. Room assets use `/Game/TeddyEncounter/Room` and `TE_Room_` actors tagged `FullRoomOwned`. `tools/build_full_room.py` is the incremental room builder; `tools/make_industrial_room.py` creates the original mesh kit. No installer, global configuration or Windows security change was used by the room team.

The camera-facing wall is a low cutaway and the central ceiling stays open for the elevated gameplay view. High walls and service fixtures stay outside the original collision footprint. New reference/layout decisions are in `ROOM_ART_DIRECTION.md`.

## AI surfaces — 5 October 2026

Original floor, plush, and decal maps are in `/Game/TeddyEncounter/Arena` as `T_AI_*`. `tools/apply_ai_surfaces.py` points `M_QA_Concrete` at the floor set (UV 9×7, albedo scale 0.20) and points `M_QA_TeddyCloth` and `M_TeddyCloth` at the existing teddy base color plus the plush normal and roughness. The materials stayed Default Lit after the script caught an enum conversion error during its Cloth attempt; this does not establish that Unreal lacks Cloth shading. Four deferred decals, `TE_AI_Decal_01` through `TE_AI_Decal_04`, are saved on the arena floor. Lights, fog, exposure, camera, combat, the teddy mesh, and `TE_Room_` actors were left as they were.

The held plates are `evidence/implementation/20261005T053842-capture_encounter/` at 1280×720. Position 1 mean RGB is (8.3, 29.0, 33.6), with 3.8% of pixels above luminance 40. The square grout grid is gone. The teddy is the same character, with seam and wear in the shading. Receipt: `evidence/implementation/ai-surfaces.json`. Two earlier captures that hour showed the engine default material, because the roughness sampler did not match the grayscale textures; those plates are not this result. Exact fidelity is still unaccepted. The remaining gap is the broad cool fill against a small light pool.

The sections below preserve the earlier independent QA repair. Their runs and asset counts describe that earlier version; the combined room evidence above is current.

## Earlier repair result

The user authorized continuing after the independent comparison. Space, Escape and F5 are now repaired and verified through saved key mappings. The visual pass tightens framing, concentrates lighting, adds peripheral haze, reduces floor repetition, adds subtle cloth detail and softens the warning ring. The scene is ready for another visual review; exact fidelity and user acceptance remain separate.

Use **PLAY.cmd** for the updated encounter, **EDIT.cmd** for the editable map, and **PLAY_BASELINE.cmd** for the preserved starter. Project: `TeddyBlueprint/TeddyBlueprint.uproject`; map: `/Game/Maps/TeddyEncounter`; engine: Unreal 5.8.3. [Historical repair review](evidence/qa-repair/20261005T042900Z/review.html), [repair report](evidence/qa-repair/20261005T042900Z/REPAIR_REPORT.md), [controls](ENCOUNTER.md).

## Repair and verification

The original independent QA found invalid `(` FKeys created by struct-style text import. Corrected `tools/build_combat.py`, `tools/refine_player_controls.py` and the saved input mapping using `tools/repair_encounter_keys.py`. Modifiers, triggers and existing device mappings were preserved. The new test routes simulated key presses through PlayerController and the saved context, closing the coverage gap in action-only tests.

| Fresh run under evidence/implementation | Result |
| --- | --- |
| `20261005T043144-verify_encounter_keys` | Preserved expected pre-repair failure: Space/Escape failed and F5 did not restart. |
| `20261005T043241-verify_encounter_keys` | 12/12 key-route checks, including pause suppression, resume and restart while paused. |
| `20261005T044114-verify_encounter_repair` | 8/8 independent action-level behavior checks, three fresh decoded captures, no teleporting/health edits/disabled AI. |
| `20261005T043927-verify_encounter_camera` | 12/12 conservative body-bounds cases at arena edges and opposite corners. |
| `20261005T044153-verify_encounter_edges` | 13/13 cursor aiming, wall collision, weapon alignment, evasion, defeat and restart checks. Cursor-aim error 0.62 degrees. |
| `20261005T044237-record_encounter` | Full encounter, boss/minion defeat, pause and restart recorded. About 12.6 unique captures/sec; use native video below for motion review. |

All these final runs have successful host receipts and clean exits. Methods differ: key simulation, action injection, cursor placement, and staged edge cases are explicitly identified in each receipt. Physical keyboard/mouse/gamepad play is not claimed.

The fresh ordinary-game capture is `evidence/qa-repair/20261005T042900Z/native-motion-044641/native-motion.mp4`: 1280 x 720, 17.1 seconds, 512 decoded frames, about 30 fps. It captures only the owned game-window client area. Its separate QA map copies the current encounter and adds a normal-input driver; gameplay, AI, health and animation are unchanged. No OS input events were sent. The native audio master is nonzero; a separate stereo preview is available. The movie is silent and no audio synchronization or reference match is claimed.

## Settings and limits recorded during the earlier repair

Camera pitch −46°, FOV 48, height=clamp(max(1.8*abs(deltaX),1.0*abs(deltaY))+850,1700,5600), backoffset=−cot46°*height. Existing midpoint, foreground bias, Z 160 target and interpolation 5 remain. Saved manual exposure +3.8 EV, Lumen and virtual shadows retained.

`tools/refine_qa_visuals.py` makes three new owned `M_QA_*` materials, retaining original materials/textures. Broad fill is reduced; key/rim/fill lights are more localized. Fog density .035 and warning material changes are visual only; attack timing/radius/collision are preserved. An over-bright procedural-floor trial and an overly plain trial were rejected before the retained worn-floor blend.

Largest remaining differences: simpler teddy anatomy, procedural creature motion, and regular arena boundaries/some floor seams. Exact atmospheric fidelity still needs visual feedback. The look study is in [study/BOSS_SCENE_STUDY.md](study/BOSS_SCENE_STUDY.md), [study/VISUAL_FIDELITY.md](study/VISUAL_FIDELITY.md), and [study/AI_FIDELITY.md](study/AI_FIDELITY.md). Boards and direction frames are in `study/visuals/`. Those notes do not change the repair above. Audio matching, physical controls, packaged delivery and sustained performance remain unverified; no old performance number is presented as current.

## Preservation and ownership

Root desktop Codex integrated and independently checked the repair; the requested Astra agent drafted and advised on visual/camera settings without concurrent engine writes. No editor or native game process is left running at handoff. No new Codex CLI session, installer, global setting change or Windows protection change was used.

Pre-repair 142-file backup: `evidence/qa-repair/20261005T042900Z/before-repair.zip`, verified in `baseline.json`. All 555 original baseline files, source video, source ZIP and original teddy are unchanged. Only five existing encounter assets changed; three new owned materials and isolated QA capture assets were added. Adapted source files remain unchanged. A concurrent AGENTS.md context-guidance addition was preserved. Original independent QA and delivery evidence remain intact.

The current repair manifest is `evidence/qa-repair/20261005T042900Z/manifest.json`; the older `evidence/delivery/manifest.json` describes the preserved pre-repair delivery. Ownership remains `TeddyEncounter.Owner=encounter-20261004`; use one writer for the map/assets.

## Continuation notes

- Use the combined full-room review and its fresh native movie for feedback. Further visual refinement should target a concrete remaining discrepancy and retain these receipts. Coordinate with the user-owned Grok session before shared asset writes; do not rerun broad builders over its surface work.
- Run an authoring script with `python tools/astra_setup.py editor-script tools/<script>.py --render`; run a relevant test with `python tools/run_encounter_test.py tools/<test>.py`. Do not rerun broad historical builders over the final scene or repeat the full Astra setup probe for routine edits.
- Unreal 5.8 material input display names can differ from C++ fields. Noise's position uses its reflected world-position name; single unnamed sockets accept an empty input name. The refinement helper now resolves these through MaterialEditingLibrary.
- Repeated PNG screenshot capture remains too slow for a smooth gameplay recording. The scoped native-window capture route is in `tools/capture_qa_native_motion.py` and `tools/author_qa_native_motion.py`; it does not alter the playable level or send global input.
- Reuse installed tools and cached Context7. Hand installation/update commands to the user. Keep Windows protection and global Codex settings unchanged.

Earlier status documents are preserved in the pre-repair archive and `evidence/revisions/`. The historical native BossShot DLL restriction and low-angle BossArena are not the active Blueprint target.
