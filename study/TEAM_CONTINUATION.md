# Continue the chamber as a team

Private repository: https://github.com/Vibecadex/horror-game. Start with [README](../README.md), then [CHAMBER_PARITY_BRIEF.md](CHAMBER_PARITY_BRIEF.md). The saved Blueprint project is the continuation point; no regeneration is required to play/edit.

## Ownership

- **Integrator:** one owner for `TeddyBlueprint/Content/Maps/TeddyEncounter.umap` and shared Unreal packages; coordinate dependencies, save, reload and validate.
- **Environment artist:** versioned Blender/FBX/textures/manifests under `Assets/Adapted/ChamberParity/`; first task is floor erosion/transitions. Do not write shared packages concurrently.
- **Lighting artist:** bounded proposals with settings and paired native renders; integrate through the map owner.
- **Independent QA:** inspect saved output against both targets and exercise gameplay/cutaway. Passing traces do not establish visual parity.

Use branches and review before merging. Binary Unreal maps cannot be text-merged safely. Pull current main before authoring, agree scope and acquire LFS locks. Never force a teammate's lock or overwrite their asset to unblock a script.

```powershell
git switch -c chamber/floor-erosion
git lfs locks
git lfs lock TeddyBlueprint/Content/Maps/TeddyEncounter.umap
# Lock other existing packages/.blend files you will change.
# Edit, save, close Unreal and validate; add explicit reviewed paths.
git add <reviewed-files>
git commit -m "Refine chamber floor erosion"
git push -u origin chamber/floor-erosion
# Keep ownership coordinated through review/integration, then:
git lfs unlock TeddyBlueprint/Content/Maps/TeddyEncounter.umap
```

LFS may make unlocked `.uasset`, `.umap` and `.blend` files read-only. Acquire the appropriate lock. A level may save dependent/external packages: inspect all changed paths before committing.

## Validation after a chamber change

Close the running game/editor before these sequential commands. Do not run against another writer's active session. Source export needs Blender; additional motion/image tools need FFmpeg/FFprobe/Pillow. Basic launch checks use Python's standard library.

```powershell
python tools/run_encounter_test.py tools/capture_chamber_views.py
python tools/run_encounter_test.py evidence/chamber-qa/verify_chamber_runtime.py
python tools/run_encounter_test.py tools/verify_full_room.py
```

Each produces fresh `evidence/implementation/<timestamp>-<script>` receipts/host results/native output. Check the receipt and process exit. Tests intentionally pin current mesh identities/transforms: planned source replacements need independently reviewed expectation updates, not weaker checks.

Optional moving evidence:

```powershell
python tools/capture_qa_native_motion.py
```

This creates a separate QA map and uses simulated input. Inspect the movie, classify its ending, and keep physical-play/audio claims separate. Do not run full Astra setup after ordinary art edits.

Preserve the delivered run. For new work, make a new run directory and fresh asset/config/reference snapshot, then update `evidence/chamber/current-run.json` to a **checkout-relative** path. Historical `prepare_chamber_pass.py` and `chamber_preservation.py verify` assume original clipboard/workstation history; their fixed baselines are not new-checkout acceptance. `python tools/team_check.py --verify-handoff` checks initial repository Content hashes, not later intentional edits.

Review builder/checker paths now resolve from the checkout root. New deliveries need their own `delivery-inputs.json`, fresh receipts and preservation records. The current candidate is [floor recovery V4](../evidence/chamber/20261005T161155Z/FLOOR_RECOVERY_QA.md), with identities in [delivery-inputs.json](../evidence/chamber/20261005T161155Z/delivery-inputs.json). The shipped [11:47 review](../evidence/chamber/20261005T095028Z/review.html) and its movie are the historical handoff.

## Continuation prompt

Paste into the team's existing coding-agent session at the repository root:

```text
Continue the chamber environment in this checkout. Read AGENTS.md, README.md,
study/CHAMBER_PARITY_BRIEF.md, study/TEAM_CONTINUATION.md, WORK_STATUS.md,
evidence/chamber/20261005T161155Z/FLOOR_RECOVERY_QA.md and
evidence/chamber-qa/grok-20261005T163731/INDEPENDENT_REVIEW.md. The pre-Grok
evidence/chamber-qa/final/INDEPENDENT_REVIEW.md is historical. Inspect both
chamber targets and the 16:37 native views. Destination:
TeddyBlueprint/TeddyBlueprint.uproject, /Game/Maps/TeddyEncounter, Unreal 5.8.3.

Check prerequisites without installing anything, inspect Git status/LFS locks,
and establish one Unreal writer. Preserve existing changes, original art,
characters, controls and gameplay camera. Continue the saved room; never rerun
historical builders to recreate it. The visible floor is FloorRecoveryV4.
Keep it. Next visual work is bay depth, red practicals and overhead haze.
Straight floor splits and quiet chunks can be refined later without restoring
V3. Use corrected V2 sources, new versioned exports and
owned namespaces. Preserve routes and native cutaway. Show native front/reverse
and gameplay evidence after meaningful changes, with independent QA and named
gaps. Functional checks do not prove visual parity. Update the study brief and
WORK_STATUS. Hand missing-tool installation commands to the human. Do not change
Windows protection or start a second implementation session. Ask only for
information that blocks safe progress.
```

`START_ASTRA.cmd` retains its documented GPT-6 Astra / Max flow, but its project-local CLI and successful workstation receipt are not shipped. Use an existing authorized agent session and the prompt above; this handoff does not establish model availability/sign-in on teammates' machines.

## Repository scope

Included: all766 active Content files, Config/project descriptor, adapted sources, original teddy/provenance, reference copies, study, tools and retained non-cache evidence. Binary assets use LFS.

Excluded, preserved on the original workstation:

- `BossShot/`: historical native experiment, not the active game.
- Unreal/tool caches, `Saved`, `Intermediate`, `Binaries`, `Build`, `DerivedDataCache`, `.vs`.
- `.team-local/`: exact pre-repository copies, including token-bearing config. Never publish it.
- `evidence/setup`, `editor-runs`, `revisions`, `reviews`, raw `**/frames/`, logs, executables/DLLs, recovery ZIPs and `.blend1/.blend2` backups. Final sampled QA images, movies and receipts remain included.
- Local settings, environment credentials and service sign-ins.

Historical reports can reference local-only logs/backups. The current brief, study landing page, final comparison/QA and review assets must resolve after cloning. `Assets/Reference/BossShot.zip` is the small user-supplied source archive, distinct from excluded recovery ZIPs.

The tracked active INI has its Android File Server token removed and unused service/network option disabled. Original config is preserved locally. No firewall or OS protection changed; the team Content hash manifest verifies unchanged room/gameplay assets.
