# Teddy Encounter — QA repair result

**The broken controls are fixed, and the scene has been refined against the original.** Fresh saved-build checks pass. The new comparison is ready for visual review; exact reference fidelity and user acceptance are not claimed.

5 October 2026, South Africa time. Continue playing through [PLAY.cmd](../../../PLAY.cmd), or open [the comparison and videos](review.html).

## Changes and evidence

| QA finding | Repair | Result |
|---|---|---|
| QA-01: invalid Space, Escape, F5 mappings | Replaced the invalid `(` keys with real key names; corrected both original authoring scripts. Existing mappings, modifiers and triggers were retained. | **Fixed.** A test through the saved key mappings failed before repair and passed 12/12 after reopening. |
| QA-02: distant, overhead framing | Camera −51° → −46°, FOV50 → 48, tighter close framing with separation-aware widening. Existing tracking and smoothing retained. | Improved in fresh images; all 12 conservative camera edge cases pass. |
| QA-03: flat light and weak atmosphere | Lower broad fill, localized key/rim light, stronger low haze, dark perimeter. Exposure remains the saved manual setting. | Inspected in fresh captures and ordinary-game output. |
| QA-04: repetitive floor and smooth teddy | Reduced and varied texture repeats, blended procedural wear, softened floor normals; added subtle cloth normal/roughness detail. Original textures and earlier materials retained. | Surface repetition and coarse weave reduced. The teddy's simpler anatomy remains a limitation. |
| QA-05: dominant red ring | Dimmer, desaturated warning material. The actual attack radius, timing and collision were preserved. | Warning remains visible in native footage with less visual dominance. |

The first material trial was too bright and blotchy; the second lost too much floor detail. The retained version balances worn detail with quieter seams. These iterations are preserved in the numbered authoring receipts. The previous QA report and delivery are unchanged.

## Fresh verification

| Verification | Result | Receipt |
|---|---|---|
| Saved key routing, including pause suppression and repeated restart | 12/12 | [Key test](../../implementation/20261005T043241-verify_encounter_keys/receipt.json) |
| Independent behavior regression and three fresh captures | 8/8 | [Independent run](../../implementation/20261005T044114-verify_encounter_repair/receipt.json) |
| Player/boss visibility at arena edges and opposite corners | 12/12 | [Camera checks](../../implementation/20261005T043927-verify_encounter_camera/receipt.json) |
| Mouse aim, wall collision, rifle alignment, evasion, defeat and restart | 13/13 | [Combat checks](../../implementation/20261005T044153-verify_encounter_edges/receipt.json) |
| Native game movie | 1280 × 720, 17.1 seconds, 512 decoded frames, approximately 30 fps | [Capture receipt](native-motion-044641/receipt.json) |
| Native game audio | Nonzero game-master recording, peak 0.1965 linear | [Motion/audio validation](native-motion-044641/motion-validation.json) |
| Original source and starter preservation | All 555 baseline files plus source video, source ZIP and original teddy unchanged | [Preservation](preservation.json) |

The key test uses simulated key events routed through `PlayerController::InputKey`, the saved mapping context and runtime Blueprints. It does not inject those gameplay actions directly. Its [pre-repair run](../../implementation/20261005T043144-verify_encounter_keys/receipt.json) reproduced failed Space/Escape behavior and a failed F5 restart. That failure is preserved.

The independent eight-check run uses action injection and does not duplicate the key-route claim. The camera check uses staged positions. The combat check uses action injection, cursor positioning and staged positions, with one explicitly labelled damage call during invulnerability. Their receipts retain these distinctions. Relevant engine processes exited cleanly.

## Visual and motion review

![Original, before repair and repaired scene](comparison-original-before-after.png)

The main still compares equal image widths with aspect ratios preserved. The original is the 5-second gameplay crop, rotated from the unchanged phone recording. Its social-player overlays remain visible. The before/after engine stills use the same startup player pose and a naturally approaching boss at about 2.46 seconds; the original depicts a different action moment. No color adjustment or numerical fidelity score was applied to these images.

The [native movie](native-motion-044641/native-motion.mp4) captures the actual game window, with its client rectangle held topmost for capture. It uses an isolated copy of the level and an added test driver: movement/fire/dodge use key events and aim uses a continuous action. The original gameplay, enemy AI, health and animation are unchanged. There are no staging teleports, health edits or AI freezes. The sequence shows movement, aiming, a dodge, firing, warning/strike motion and boss defeat. No OS keyboard/mouse events were sent.

All 512 video frames decoded; every consecutive decoded frame changed in the 256 × 144 motion check. This supports a continuous motion recording, not a performance benchmark or an exact engine-frame identity claim. The [contact sheet](native-motion-contact-sheet.png) samples once per second; the final grid slot is empty. Motion remains procedurally animated and simpler than the source.

The movie is silent. [Native game audio](native-game-audio-stereo.mp3) is a separate stereo downmix of the actual game-master capture; it was not dubbed onto the movie and synchronization is not claimed. Audio matching to the original remains unverified. The [original gameplay excerpt](original-gameplay.mp4) preserves source audio for comparison.

An additional [full encounter recording](../../implementation/20261005T044237-record_encounter/TeddyEncounter-gameplay.mp4) includes boss/minion defeat, pause and restart. Its screenshot-based method achieved only about 12.6 unique captures per second despite requesting 30, so it is retained as behavioral evidence rather than the primary animation review. Its silent audio track was omitted.

## Preservation and continuation

The verified pre-repair archive contains 142 files: [backup manifest](baseline.json), `before-repair.zip`. Only five existing gameplay assets changed: the encounter map, camera Blueprint, boss/minion material references, and input mapping. Three new owned materials were added. Original references, adapted texture/mesh/audio sources, starter and native BossShot experiment were preserved. A concurrent addition to `AGENTS.md` was retained, not rolled back.

The incremental repair scripts are [repair_encounter_keys.py](../../../tools/repair_encounter_keys.py) and [refine_qa_visuals.py](../../../tools/refine_qa_visuals.py). The original key-authoring scripts also contain the corrected parser call, so rebuilding them will not recreate the invalid keys. No installers, Windows protection changes or global Codex changes were used.

Remaining review limits: physical keyboard/mouse and gamepad play, exact audio match, packaged delivery and sustained performance. The teddy anatomy, procedural motion and regular arena boundaries still differ from the source. The next visual decision should use this repaired build and its fresh evidence, not the previous delivery images.
