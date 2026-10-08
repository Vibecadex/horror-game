# Floor morphology QA — 5 October 2026

Independent read of the native captures. This is not user acceptance.

## What changed

Visible floor actor `TE_Chamber_Morph_Main` uses `SM_ChamberFractureMorph_Main` from `Assets/Adapted/ChamberParity/FloorMorphologyV3`. No collision. Z scale 1. Location (40, 0, −5) cm. Relief stays under 3.75 cm local.

The five V2 fields, four slab groups and five crust banks are still in the level at their previous transforms and are hidden. Characters, lights, cutaway and gameplay camera were not redesigned.

Materials `M_Chamber_FloorMorph*` sample the existing floor color as a 32 m stain at 22% and use a flat tangent normal. The hidden V2 graphs were not rebuilt.

## Comparison

Before: `evidence/implementation/20261005T114712-capture_chamber_views` (front and reverse, 1920×1280, ungraded).

After: `evidence/implementation/20261005T131840-capture_chamber_views`.

- `01-chamber-front.png` — architectural front, FOV 41.5.
- `02-chamber-reverse.png` — architectural reverse, FOV 70.
- `03-ordinary-gameplay.png` — held saved director, pitch −46°, FOV 54. Not a parity plate. Not physical-device input.

Rejected intermediate: `evidence/implementation/20261005T131418-capture_chamber_views`. Wide crack faces were shaded as pure black cards. That mesh is not the saved one.

## Read of the after pair

Both directions lose the fine hairline web and the repeated dark banks. The combat floor reads as one surface, with a few larger angular plates and small grounded chips. Lanes stay open. Feet still meet the arena floor; the room trace hits `TE_ArenaFloor` at about Z −5.

The plate breaks are too sparse and too shallow next to both concepts. A rough older floor remains visible around the sheet, especially at the near and side edges. Overhead haze, direct wall wash and the small red points are unchanged.

## Checks

Chamber `20261005T131946-verify_chamber_runtime`: 31/31. Room `20261005T132018-verify_full_room`: 28/28. Passing checks do not establish visual parity.

Simulated input only. Audio, packaging and performance were not tested.
