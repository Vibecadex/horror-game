# Run the corrected horror encounter implementation

> **Written for the original workstation's Astra run** (START_ASTRA.cmd, 4-5 October 2026), with its paths and tools. On a team checkout it is background: start at [README.md](README.md) and [study/TEAM_CONTINUATION.md](study/TEAM_CONTINUATION.md), and continue the saved project rather than rebuilding it.

This is the implementation request submitted by START_ASTRA.cmd. The task is to carry the reference-based encounter through a reviewable playable result, not to write another plan.

## First, use the prepared prerequisites

Read `MASTER_PROMPT.md`, `REFERENCE_BRIEF.md`, `WORK_STATUS.md`, `SETUP_STATUS.md`, `tools/BLUEPRINT_WORKFLOW.md` and `tools/project-settings.json`. Use `TeddyBlueprint/TeddyBlueprint.uproject` in Unreal 5.8.3 and check the latest setup receipt. This prepared Blueprint route needs no new native module or signing certificate; Windows protection stays enabled. Inspect the upright reference frames at seconds 5, 10 and 16; open the motion sheets if timing or behavior is uncertain. Treat the original phone/social UI as outside the game target.

Preserve the Twin Stick starter, the separate native BossArena experiment and the source originals. Reuse the prepared Blueprint authoring, capture and import tools. The downloaded teddy is a starting candidate; its lack of rigging/animation is part of the implementation work, not an installation problem.

Run saved Unreal Python scripts with `python tools/astra_setup.py editor-script <project-local-script.py>` (add `--render` when rendering is needed). Author and compile Blueprint graphs using the built-in 5.8 API; native `build_editor.ps1` belongs to the preserved experiment. For real frame/tick-driven tests use the full editor with `-ExecutePythonScript`, `EditorPythonScripting.set_keep_python_script_alive(True)` and a bounded callback, as demonstrated in `tools/verify_blueprint_runtime.py`. The helper's commandlet mode alone does not tick a game. Reuse `unreal_local_arguments()` and `tool_environment()` for every engine process.

## First milestone: make the evidence trustworthy

Read the confirmed findings in [the visual tooling review](C:/Projects/to-deploy/horror-game/evidence/reviews/grok-heavy-20261004/REVIEW_SUMMARY.md). Its recommendations have not been implemented. Close the relevant gaps with a bounded, isolated starter test before treating new captures as visual acceptance:

- Require a fresh capture inside its run directory, correct dimensions, PNG integrity/CRC checks and a full pixel decode. Prove completion before reporting success or quitting. Record the loaded map, engine build, camera and rendering settings. Hold a known camera/pawn state across a static capture, or prove a frame-identity method. Neither request-time nor file-completion-time transforms establish the exact rendered frame. The editor screenshot task API requires a local gameplay-view proof before replacing the current capture path.
- Use separate no-input and action phases. Verify movement in the mapped direction, wrapped yaw toward the mapped aim, and new player-attributable projectiles. Explicitly test dash or report it uncovered. Template enemy presence proves only the starter. Keep input checks separate from visual comparison.
- Record loading/warmup conditions and use the actual gameplay rendering settings. Preserve intentional manual exposure if selected; do not enable or disable exposure, shadows or other effects merely to make a diff pass. Crop/mask reference overlays using `evidence/reference-video/inspection.json`; the recorded post-rotation crop is `[76, 0, 700, 384]`, and text still obscures some gameplay.

Save the targeted proof and remaining limitations in WORK_STATUS.md, then proceed with the encounter. Do not expand this into a new testing framework or repeated full setup runs. A complete image or a similarity score alone does not prove fidelity, and a self-reviewed image does not establish user acceptance.

## Build, render, compare, improve

Begin with a separate `/Game/Maps/TeddyEncounter` level. Establish elevated combat framing, grounded human/monster proportions, worn readable floor, localized cool light, dark peripheral atmosphere and restrained red accents. Use the actual teddy model in the composition. Capture three comparable player positions and inspect them yourself.

Judge the teddy in that view. Refine the geometry/materials and prepare a rig and animations if viable; otherwise obtain a better licensed free model and record why it is a better fit. Preserve originals and provenance. Do not let the first available asset dictate a weaker visual target.

Continue to independent movement and mouse aiming, firing, an evasive move, pause and restart. Then complete a bounded encounter with animated boss motion, a telegraphed attack, damage, reactions, defeat and a few surrounding threats. Follow the proposed controls in the master prompt; do not describe them as exact bindings recovered from the video.

Use one integration owner for shared Unreal assets. Delegate only if requested by the user or applicable instructions, with non-conflicting ownership. Show intermediate results when useful while continuing authorized corrections; do not request permission for each build or material adjustment.

After meaningful changes, run the scene, capture its actual output and identify the three largest remaining discrepancies against the reference. Resolve the most consequential issue before adding minor polish. Do not replace the requested outcome with another primitive-only checkpoint.

## Prove completion

Update verification for the new controls and encounter rather than citing the baseline camera-trigger tests. Exercise normal input paths, collision, aiming while moving, firing, damage, evasion, defeat, pause and repeated restart. Save and reopen the level. Inspect animation contact and exposure in rendered output; measure runtime performance at the recorded resolution.

After ordinary art edits, run the affected scene/capture checks. Do not recursively launch START_ASTRA.cmd or repeat `python tools/astra_setup.py verify` as routine validation; the full validator launches a separate bounded Astra request. CHECK_SETUP.cmd is the non-inference prerequisite check. Revisit full setup only for an actual environment failure or change requiring it, after ending this implementation session.

Audition the source gameplay audio before claiming an audio match; otherwise label sound design as proposed original work. Record physical-device input verification separately from injected actions. Record visual review and user acceptance separately; only explicit user feedback establishes the latter. Preserve the historical setup receipt as setup evidence.

At each meaningful milestone and before an interruption, update `WORK_STATUS.md` with the current objective, exact files/level paths, commands and results, capture/run IDs, the three largest remaining discrepancies, failed approaches worth avoiding, active asset ownership and the next concrete action. On resume, verify the referenced artifacts and continue that action. Keep progress updates brief, show useful captures, and avoid repeating completed setup or broad tests without new evidence.

Deliver a playable launch path, editable source/assets, controls, provenance, comparison stills and a short actual gameplay recording. Distinguish implementation, runtime verification, visual comparison and user acceptance. Continue through repairable issues until the requested encounter is complete; report any genuinely external blocker with the completed work and exact remaining action.
