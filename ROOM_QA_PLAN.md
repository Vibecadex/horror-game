# Independent room QA

The user requested a complete room and a team of experts. This review is separate from room authoring. The room extends the worn industrial direction around the existing encounter; the reference does not establish the exact architecture of unseen walls.

## Ownership and run

The room author owns saved environment assets and the map. The QA agent owns `tools/verify_full_room.py` and this plan only. The root integrator runs the engine, maintaining one writer. The test never saves assets or changes the authored level. Runtime staging, disabled NPC movement, input simulation and held captures are explicitly recorded.

Run after the room has been saved and its authoring process has exited:

```powershell
python tools/run_encounter_test.py tools/verify_full_room.py
```

The host creates a fresh evidence directory with its invocation, host result, `receipt.json`, and six 1280 × 720 images. A successful result requires the complete checklist, not just a clean process exit. No installer or global setting change is involved.

## Mechanical checks

| Area | Evidence and acceptance |
| --- | --- |
| Saved gameplay positions | Read the saved map before staging. The player start, main teddy and three stitchling XY positions must match the established encounter. Require exactly one boss and three stitchlings. |
| Existing collision enclosure | Keep the four original combat-bound actors, locations and scales, with Pawn-blocking collision. Runtime tests must reach the original boundaries on all four sides. |
| Authored room | New actors use `TE_Room_`, `TeddyEncounterOwned` and `FullRoomOwned`. `RoomShell` identifies three tall exterior sides plus a low foreground cutaway. |
| Traversal clearance | New room mesh bounds stay outside x [−1380, 1440], y [−1460, 1460]. Floor details may enter this area only at z ≤ 3 cm with no collision. `RoomDecor` has no collision. |
| Collision geometry | First prove active PIE queries with two known floor/wall line hits and one wall capsule hit. Then sweep a slightly inset player capsule at 25 interior grid points and along six crossing routes, using the player's actual Pawn collision profile. Probe all five character spawn capsules while ignoring the characters themselves. Small capsule and floor clearance avoid treating normal ground contact as an obstruction. |
| Walk and dash limits | Simulate the saved W/S/A/D and Space mappings through PlayerController, exercising each of the four walls. Confirm each dash actually accelerates above 900 cm/s, reaches the wall and never tunnels beyond it. The right-wall lane uses x = −450 to avoid starting inside the saved stitchling. Record requested/actual starts and reject staging displacement above 5 cm. This does not claim physical keyboard testing. |
| Camera framing | Stage twelve player/boss pairs, including all four edges, corners and two opposite-corner pairs. Let the saved tracking camera settle. Project conservative full-body bounds and require them inside the established viewport safety margins. |
| Camera occlusion | Trace from the actual camera to three heights on each body in all twelve cases, ignoring character actors. Record the complete serialized HitResult for any environmental obstruction. Also record conservative room-box intersections for visual review. |
| Render evidence | Decode six held gameplay views: initial, front edge, back edge, two corners and an opposite-corner pair. Saved lighting and materials remain active. Only the pause HUD is hidden. |

The named ownership tags and interior limits are the room integrator's declared contract, received before the QA script was authored. They are not inferred from author-generated pass results.

## Independent visual review after rendering

Inspect the six new images against the upright original gameplay frames at seconds 5, 10 and 16, then inspect an ordinary-game motion recording if supplied. Keep equal aspect ratios and identify any crop. Do not brighten, retouch or fabricate captured game pixels.

- Verify the room reads as a contained industrial space: coherent wall mass, support rhythm, access points and service details. The foreground cutaway is a gameplay accommodation; an exposed floor edge or empty void is a defect.
- Check that new walls, door assemblies, pipes, consoles and debris remain secondary to the player and teddy at the actual gameplay scale. No bright decorative detail should compete with the aiming line or attack warning.
- Check player, weapon, creatures and attack-warning readability at every sampled edge/corner. Inspect potential room-box intersections in the receipt; boxes are conservative and are not exact mesh hits.
- Check the original visual relationships: cool localized light, dark perimeter, pale grounded teddy, worn readable floor, restrained red practicals and atmospheric depth. Full-room architecture is a proposed extension, not a claim to have recovered unseen reference geometry.
- Check for obvious geometry gaps, floating props, wall/floor seams, clipping, repeating modules, excessive regularity, unlit flat blocks and distracting shadow patterns.
- Report functional success, visual findings and user acceptance separately. A passing receipt cannot approve the art.

## Coverage limits and follow-up

Collision traces do not see non-colliding decoration. The actual screenshots and motion recording remain necessary, particularly for a foreground obstruction. Bounding-box intrusion tests are intentionally conservative; investigate any flagged mesh bounds before changing the geometry contract. A hollow or sparse mesh can intersect a conservative box without obstructing the rendered view.

The room test deliberately freezes/stages characters. Reuse the existing encounter key, gameplay and edge suites if the room work touches their dependencies or reveals a regression; do not claim this room suite retests combat, physical controls, audio fidelity or sustained performance. The prior repaired controls and old QA receipts are historical evidence until a relevant fresh run is performed.

API basis: installed Unreal 5.8 headers and current official documentation retrieved through the installed Context7 CLI, followed by actual runtime reflection. The reflected trace methods return the first blocking `HitResult`, otherwise `None`; positive-control hits validate that queries are active. `BreakHitResult` and the C++ hit fields are not exposed through this Python interface, so the test preserves `export_text()` rather than guessing property names. The collision-response enum is `CollisionResponseType.ECR_BLOCK`. The test writes reflected method signatures into each receipt. Reference: [Epic collision query API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UKismetSystemLibrary).

## Milestone 1 gate (GAME-017)

This gate decides whether `main` can stand as the Milestone 1 baseline. It adds to the room checks above and does not replace them. QA owns this section; the root integrator or a named person runs the engine, one process at a time.

### Preconditions

- `main` is at a named commit that includes PR1 (#3), PR2 (#4) and PR4 (#6). Record the full SHA before the first check. A new commit on `main` restarts the gate.
- No Unreal editor, game, commandlet or implementation session is running, and the current LFS lock holder agrees to the run.
- Never save during EDIT or any B check; decline every save prompt. Never run the historical builders, and do not set `TEDDY_ALLOW_HISTORICAL_REBUILD`.
- Every receipt records the branch, SHA, start and end times and exit code. Exit 0 alone is not a pass: a pass needs the complete check count in the receipt, or the listed observation for watched checks.

### Launcher checks

The launchers write no receipt. Each check is a watched launch with a screenshot and a short note giving the SHA, time and observer. `python tools/astra_setup.py open ... --dry-run` proves only the resolved command line and map.

| Check | Run | Acceptance | Owner |
| --- | --- | --- | --- |
| L1 PLAY_BASELINE | `PLAY_BASELINE.cmd` (`/Game/Variant_TwinStick/LVL_TwinStick`, `-game`) | The template level opens and is playable; screenshot. Record which game mode and pawn LVL_TwinStick actually runs, because the global game mode is now `BP_EncounterGameMode`. Clean exit. | QA, watched |
| L2 PLAY | `PLAY.cmd` (`/Game/Maps/TeddyEncounter`, `-game`, 1600 x 900 windowed) | Opens straight into the encounter with the player, teddy and three stitchlings visible; screenshot; Esc pauses; clean exit. | QA, watched |
| L3 EDIT | `EDIT.cmd` (editor on `/Game/Maps/TeddyEncounter`) | The editor opens the map with no load errors; screenshot; closed without saving. | QA, watched |

### B checks

Engine checks run through `python tools/run_encounter_test.py <script>`. Plain-Python suites run with `PYTHONDONTWRITEBYTECODE=1`.

| Check | Run | Acceptance | Owner |
| --- | --- | --- | --- |
| B1 Keys | `tools/verify_encounter_keys.py` | 12/12. | QA |
| B2 Edges | `tools/verify_encounter_edges.py`, then `tools/verify_encounter_edges_v2.py` (new script, not yet written) | 13/13. v2 must prove evasion with the player inside the 475 cm strike radius (the old check passed at about 627 cm), slam timing 0.92 ± 0.05 s, cooldown 0.8 ± 0.05 s and i-frames of 0.26 s. | QA |
| B3 Parity | `tools/verify_parity_runtime.py` | 48/48. | QA |
| B4a Room, TeddyEncounter | `tools/verify_full_room.py` | 28/28. | QA |
| B4b Room, TeddyChamberParity | `$env:TEDDY_CHAMBER_MAP='/Game/Maps/TeddyChamberParity'`, then `tools/verify_full_room.py` | 28/28 with the 935 cm room height limit. Clear the variable afterwards. | QA |
| B4c Chamber | `evidence/chamber-qa/verify_chamber_runtime.py` | 34/34 on TeddyEncounter only. | QA |
| B5 Soft-lock matrix | `tools/verify_encounter_softlocks.py` (new script, not yet written) | From every state (idle, dashing, boss wind-up/strike, player dead, boss dead, all stitchlings dead, paused), F5 restores a playable encounter and Esc pause/resume works; no state leaves the player without input. Known PR #1 bugs, logged as failures and not waived: the boss keeps attacking a dead player; already-dead stitchlings may replay their death animation when the boss dies. **OPEN (Design/Tech):** what should F5 load? `build_combat.py` hard-codes `OpenLevel /Game/Maps/TeddyEncounter`, so F5 on TeddyChamberParity or a copied map returns to TeddyEncounter. | QA; Design/Tech for F5 |
| B6 AI pathing | `tools/verify_encounter_ai_paths.py` (new script, not yet written) | Straight-line chase, no navmesh. Within T = 10 s the boss reaches 380 cm or closes 700 cm, and each stitchling reaches 190 cm or closes 350 cm. Stuck means under 20 cm moved in any 3 s window while out of range; stuck for more than 3 s fails. Actors stay inside x [-1380, 1440], y [-1460, 1460]. The timer pauses during wind-up, strike and hit reaction. Stitchlings must not overlap. Values are Tech's proposal, pending Design. | QA; Design to confirm values |
| B7 Audio | `tools/verify_encounter_audio.py`, plus a listening pass in PLAY | The receipt passes with its checks listed. The listener confirms the slam sound against the damage tick. Known issue: the clip is offset (AttackLeft peaks at about 0.67 s against the 0.92 s timer); record it, do not pass it silently. | QA; Design listens |
| B8 Performance | Tech's `run_perf_capture_v1.py` (in progress) | Latrine (RTX 5080, Ryzen 9 9900X), 1920 x 1080 windowed, `PLAY.cmd`, `t.MaxFPS 0`, VSync off, 10-minute session. p95 frame time ≤ 8.3 ms; no frame over 33.3 ms except in the 1.5 s after each F5; reload ≤ 3 s; memory growth ≤ 10% over 10 minutes. Also record cold and warm load time and memory. Proposal, pending Producer and Luther. | Tech captures; QA reviews |
| B9 Physical input | A person on a real keyboard and mouse in `PLAY.cmd` | WASD, mouse aim, LMB, Space, Esc, F5 and Alt+F4 behave as in `ENCOUNTER.md`; notes and a short motion recording. **OPEN:** is gamepad in M1 scope? | QA |
| B10 PR2 suites | `tools/verify_team_rig_fixture.py`; `tools/verify_scanned_bears.py`; `python tools/test_bear_importer_contract.py`; from `tools/bear_studio`, `python -m unittest test_server test_bear_pack test_rigfit.RigfitTests`; `python tools/test_handoff_guards.py` | Team rig 89/89; scanned bears receipt pass (fail is reported, not retried away); importer contract 3/3; bear_studio repo-local suite 37/37 (excludes `test_rigfit.InstalledWorkerGuards`, which needs the parked bear-scanner environment); handoff guards 11/11. `verify_studio_rig` (82) joins after PR3. | QA |
| B11 Owner sign-off | Luther reviews the receipts, screenshots and motion recording | Luther accepts or rejects, as in G4. No automated pass approves art, audio or feel. | Luther |

### After M1 (journey-level, not M1 blockers)

- Save, continue and checkpoint behaviour.
- Fresh install or fresh user profile.
- Missing-asset fallback.
- Readability with audio muted.
- Teddy recognition (E01) and dream comprehension (E02).
- Scare triggers.
- Packaged build, including `MapsToCook`.
