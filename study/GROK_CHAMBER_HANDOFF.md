# Grok implementation handoff — continue the chamber

User instruction, 5 October 2026: **"continue keeping in mind the scene we were trying to recreate, delegate to grok from here"**.

This is an implementation continuation, not another brief/site redesign or a request for a plan alone. Continue the existing saved Unreal scene toward the supplied chamber references. Codex is transferring the next implementation pass to the existing Grok session and will not write Unreal assets concurrently.

## Prerequisites and ownership first

1. Work in `C:/Projects/to-deploy/horror-game`. Read `AGENTS.md`, `README.md`, `study/CHAMBER_PARITY_BRIEF.md`, `study/TEAM_CONTINUATION.md`, `WORK_STATUS.md` and `evidence/chamber-qa/final/INDEPENDENT_REVIEW.md`.
2. Inspect Git status, branch and LFS locks. The private repository is `https://github.com/Vibecadex/horror-game`, with the existing team authorized. The last verified game/code baseline is commit `f63f6cde397cab9f8722a79ab0167c06ecc1167b`; subsequent handoff commits are documentation. Preserve any intervening work. Create a topic branch such as `grok/chamber-parity-continuation`; do not reset, clean or force-push.
3. Use installed tools. `python tools/team_check.py --verify-handoff` verifies the initial Content bytes and prerequisites; a mismatch needs investigation, not an overwrite. Unreal5.8.3 is installed. Do not run full Astra setup or install/update packages. Hand missing-tool commands to the human. No Windows protection, certificates, firewall or global configuration changes.
4. You are the **sole Unreal integration writer for this pass**. Check for a running editor/game before authoring and coordinate if one appears. Acquire the LFS lock for `TeddyBlueprint/Content/Maps/TeddyEncounter.umap` and any existing binary source/package you will edit. One session owns shared maps/materials/Blueprints. The other open Grok terminal is not another scene writer.
5. Use this existing session: `01a10a54-69ee-7253-978b-c01aa506ee63`, title "Husk Cluster boss shot fidelity study", currently Grok4.7/xhigh. Do not start a second Codex/START_ASTRA implementation session or resume an old code snapshot.

Before engine changes, create `evidence/grok-delegation/20261005/acknowledgment.json` identifying your session, current branch/commit, intended first milestone, single-writer ownership and readiness/blockers. This acknowledges the handoff; continue the work in the same turn without waiting for another yes.

## Keep the actual scene in view

Inspect images with your image-viewing tools; do not derive the target solely from prose:

- **Original motion/camera reference:** `Assets/Reference/WhatsApp Video 2026-10-04 at 16.53.31.mp4`; upright frames in `evidence/reference-video/`, especially `upright-05.png`, `upright-10.png`, `upright-16.png`.
- **Selected close atmosphere:** `study/visuals/direction-close-best.jpg`.
- **Current chamber authority:** `study/visuals/chamber-target-front.png` and `study/visuals/chamber-target-reverse.png`. These are the latest user-selected full-room concepts. The user's latest visual scope is the chamber itself.
- **Actual starting state:** `evidence/chamber-qa/final/comparison.png`, with original native front/reverse images in `evidence/implementation/20261005T114712-capture_chamber_views/`.
- **Moving starting evidence:** `evidence/chamber/20261005T095028Z/native-motion-20261005T115126/native-motion.mp4` and its receipt. It is a silent simulated-input QA copy and ends in player loss, not boss defeat.

The intended scene is a heavy, enclosed, decayed industrial combat chamber. Dark teal overhead light and haze reveal an irregular fractured/damp concrete floor, grounded debris and attached services. The front landmark is a large clipped B-3 pressure door with split leaves, a central wheel, red markers and upper-right fan. The reverse is a real wall with two separate service bays. A small armed human and a monstrous stitched teddy share the floor, with three smaller creatures. Preserve their existing gameplay and appearance during this room pass. Do not drift into a clean sci-fi grid, isolated stage, open hall or low hero camera.

The current saved candidate establishes the architecture, but **does not reach visual parity**. The target has more connected plate erosion and varied angular rubble, stronger overhead atmospheric depth, better balanced service visibility and different room/door/floor proportions. Passing functional checks does not remove those differences.

## Continue from the saved candidate

Destination: `TeddyBlueprint/TeddyBlueprint.uproject`, `/Game/Maps/TeddyEncounter`. Runtime behavior stays in saved Blueprints; editor Python authors assets. No new native module is needed.

The complete project has766 Content files. The room has the B-3 assembly, complete reverse two-bay wall, services, piers, low drainage and native camera-dependent cutaway. Current ground uses five connected fields, four sparse slab groups and five crust-bank placements;43 of45 earlier floor actors are hidden with originals preserved. Corrected source sets are:

- `Assets/Adapted/ChamberParity/FloorNormalsV2/manifest.json`
- `Assets/Adapted/ChamberParity/SlabsNormalsV2/manifest.json`
- `Assets/Adapted/ChamberParity/CrustNormalsV2/manifest.json`

The V1 exports had known cap/winding faults; their V2 repairs are complete. Do not reopen that repaired defect by reimporting old sources. Preserve originals and create new versioned exports for further changes. Current room settings: `study/chamber-settings.json`, revision `chamber-08-crust`. Historical study notes and pre-production bans/values do not override the updated chamber brief.

The original Grok surface inputs and prior cloth/floor material work are preserved. Do not roll back the subsequent combined room, V2 normals or final lighting simply to restore your older session state. Read the current files first.

## First milestone, then the next pass

**First: floor morphology.** Build broader connected erosion with a varied plate-size hierarchy and sparse angular fragments; remove the read of isolated crack patches over fine grain. Work on visible shape, transitions and material scale together. Keep quiet floor, grounded contacts, no-collision dressing and clear combat lanes. More uniformly scattered tiny debris is not the solution.

Freeze the starting Content and source hashes into a fresh run directory, take the native before pair, implement one coherent floor change, save/reload, then capture the after pair plus normal gameplay. Provide an independent visual assessment. If the first change does not visibly improve both directions, correct its cause before adding more decoration.

**Next: local lighting/haze.** Restore overhead mist glow and readable cabinet/pipe/tank contours, calm the direct wall-wash and even bright near-floor read, and balance the small red points. Keep dark recesses. Do not globally raise exposure, bake lighting into textures or replace haze with a glowing sphere/bar. Reassess architectural mass/proportions after floor/light improvements; change real causes rather than hiding them with a camera.

Preserve the player's independent movement/aiming/firing, dodge, pause/restart, creature behavior, health and animation. Ordinary gameplay stays at pitch−46°/FOV54 with its existing tracking. No creature redesign, new phase, weapon, ceiling or unrelated expansion is requested.

## Evidence and completion

Use disclosed architectural cameras from `tools/capture_chamber_views.py`: front `(-4050,180,2780)` toward `(100,180,80)`, FOV41.5; reverse `(1450,100,1450)` toward `(-600,100,0)`, FOV70. Native1920×1280 originals, no crop/warp/grade to imply parity. Hold/HUD choices must remain labelled, and native cutaway must remain enabled. Add ordinary gameplay views and moving evidence.

After a substantial scene change, with the editor/game closed, run sequentially:

```powershell
python tools/run_encounter_test.py tools/capture_chamber_views.py
python tools/run_encounter_test.py evidence/chamber-qa/verify_chamber_runtime.py
python tools/run_encounter_test.py tools/verify_full_room.py
```

Current chamber and room suites passed28/28 each. Intentional new mesh identities require reviewed expectation changes, not weakened tests. Earlier48/48 character and12/12 key results are historical, not fresh coverage. For additional native motion use the documented `tools/capture_qa_native_motion.py` workflow in its isolated QA copy. Keep simulated input, physical play, audio matching, packaging and performance claims distinct.

Keep a fresh checkout-relative run pointer, preserve the delivered run, and snapshot the current state rather than relying on original clipboard paths or555-file historical configuration equality. Repository preparation deliberately sanitized the unused Android File Server settings. Its original INI is retained under ignored `.team-local`; do not publish credentials or that folder.

You may use source-only art/lighting help and a separate QA reviewer, with non-conflicting ownership. Keep yourself as the only engine writer. The user has authorized ordinary reversible work without repeated yes prompts; purchases, paid generation, public publishing and unrelated changes are outside that authority.

Continue until there is a concrete improved saved room, native comparison and truthful QA report—not just a proposed plan. Update `WORK_STATUS.md` and the current study brief with exact new assets, receipts and remaining differences. Commit scoped work on your topic branch and push it to the existing private origin for team review; do not merge or claim user acceptance on the team's behalf. Leave play/edit instructions and explicit next gaps. Exact visual acceptance remains the user's decision.
