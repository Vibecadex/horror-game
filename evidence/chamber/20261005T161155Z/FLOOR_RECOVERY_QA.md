# Floor recovery V4 — current candidate

Recorded 5 October 2026. Grok session `01a10a54-69ee-7253-978b-c01aa506ee63` is the sole Unreal writer. Parent commit `efce679`. This note is the current candidate. It does not replace the historical 11:47 handoff or the 11:51 movie.

## What changed

`TE_Chamber_Recover_Main` is the visible floor. The mesh is `SM_ChamberFractureRecover_Main` at (40, 0, −5), scale Z 1, no collision. Source is `Assets/Adapted/ChamberParity/FloorRecoveryV4`. The sheet has 595 plates, median area 0.744 m², 22 bites, 39 fragments, 65,622 triangles, and local relief at most 3.6 cm. It reaches the drainage lip.

V3 `TE_Chamber_Morph_Main` stays in place and is hidden. The 14 V2 floor, slab, and crust actors stay hidden and unmoved. `TE_ArenaFloor` remains the collision floor. A walk trace in the room audit hits it at Z −5. Exposure bias stays 3.8. The gameplay camera stays pitch −46° and FOV 54. The cutaway Blueprint is unchanged from `efce679`.

The 16:14 capture was an intermediate: flat dark triangular caps. Those caps are gone. Perimeter fade applies only to the chamber boundary. Internal bites keep a chipped lip. Bevel and side triangles are tested with normalized normals against the local edge outward `(dy, -dx)`, including both triangles of each quad. Degenerate means a cross-product shorter than 1e-8. The export does not weld, recalculate, or flip normals afterward. The manifest records 0 authored faults and 0 repairs. The FBX round-trip counts downward faces only when every vertex is above 1 cm. That count does not cover quiet caps below 1 cm or side orientation. Those are in the authored test. This is not a watertightness claim.

## Current evidence

| Evidence | Result |
| --- | --- |
| [Native views](../../implementation/20261005T163731-capture_chamber_views/receipt.json) | Front, reverse, and ordinary gameplay. 1920×1280. Exposure 3.8. Passed. |
| [Chamber audit](../../implementation/20261005T163834-verify_chamber_runtime/receipt.json) | **34/34**. Three recovery checks were added. V3 is required to be hidden. Earlier checks were not weakened. |
| [Room audit](../../implementation/20261005T163913-verify_full_room/receipt.json) | **28/28**. Spawns and combat bounds unchanged. |
| [Native motion](native-motion-20261005T164043/native-motion.mp4) | 19.133 s, 1280×720, 573 frames. Silent. Simulated input in an isolated QA copy. Ends in **boss defeat** (`THE STITCHES GIVE WAY` / `THE UNRAVELLED`, F5 prompt). The player is still standing. |
| [Identities](delivery-inputs.json) | Map, mesh, materials, settings, and capture hashes for this candidate. |

`native-game-audio.wav` sits beside the movie and was not auditioned. Do not treat it as an audio match.

Independent image review: [16:37 recovery](../../chamber-qa/grok-20261005T163731/INDEPENDENT_REVIEW.md). It checks the native views, both runtime receipts, the boss-defeat movie, and all 20 delivery hashes. The 16:14 mosaic review remains [historical](../../chamber-qa/grok-20261005T161429/INDEPENDENT_REVIEW.md). The V3 sheet review remains [historical](../../chamber-qa/grok-20261005T133413/INDEPENDENT_REVIEW.md).

## Still open

The floor reads as damp cracked concrete in both directions and in gameplay. Straight split lines still cross quieter areas. Grounded chunks and chipped rims are still quieter than the two concepts. Overhead haze, dark service bays, regular wall courses, and the tall red side fixtures were held fixed for this comparison. Exact visual parity and user acceptance are open. Physical-device input is not claimed.

Next work is bay depth, red practicals, and overhead atmosphere, using the same cameras. A later erosion refinement can still deepen chips without returning the dark mosaic or the V3 sheet.
