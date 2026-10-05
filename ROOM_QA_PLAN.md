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
