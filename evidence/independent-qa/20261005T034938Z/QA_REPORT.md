# Independent QA — original video versus Teddy Encounter

**Verdict: needs revision before sign-off.** The build captures the basic encounter concept, but three advertised keyboard bindings are invalid and the visuals do not yet reproduce the reference's composition and atmosphere.

Reviewed 5 October 2026, Africa/Johannesburg. This was a separate QA pass by the reviewing assistant, outside Astra's authoring session. No game assets were repaired or saved during QA.

[Open the visual comparison](review.html) · [Side-by-side image](comparison.png) · [Machine-readable result](qa-result.json)

## Findings, in repair order

### QA-01 · P1 · Space, Escape and F5 have invalid saved bindings

The delivered `/Game/TeddyEncounter/Input/IMC_Encounter` contains three mappings whose exported key is literally `(`. Unreal reports each key as invalid. There is no valid SpaceBar-to-dash, Escape-to-pause, or F5-to-restart mapping in that context. This contradicts the advertised controls, including the death screen's instruction to press F5. Left Shift retains a valid dash binding.

The defect originates in [build_combat.py](../../../tools/build_combat.py), line 42, and [refine_player_controls.py](../../../tools/refine_player_controls.py), line 21. Both import a key using struct-like text such as `(KeyName="SpaceBar")`. In the installed engine, FKey's text importer reads a single token and obtains `(`. A separate, read-only commandlet reproduced this and confirmed that plain `SpaceBar`, `Escape` and `F5` tokens create valid keys in memory.

**Why earlier tests passed:** injecting an Enhanced Input action bypasses the physical key mapping. My eight action-level checks also passed; the independent audit of the saved mappings exposed the missing layer of coverage. The authoring script replaces the earlier Escape/F5 key-event nodes with these Enhanced Input actions.

**Required correction:** create valid keys, remove the invalid mappings, save and reopen the asset, then test the real key-to-action route for all three controls. Validate every saved key as well as the resulting behavior. No correction was applied in this review.

Evidence: [saved keys and parser reproduction](bindings.json), [read-only audit](audit_bindings.py), [engine receipt](engine/receipt.json).

### QA-02 · P2 · Camera and subject framing feel too distant and overhead

The original's boss and player occupy more of the useful frame and have more visible side silhouette. The current build exposes a larger, flatter area of floor, reducing the encounter's immediacy. This is visible in the fresh startup capture and across the author's three staged viewpoints.

The current runtime camera was measured at a −51° pitch and 50° field of view. The original camera's exact settings cannot be recovered from this clip alone. Camera distance, angle, and subject scale should be tuned together using several comparable poses; changing one guessed angle is not sufficient.

Evidence: [fresh original at 5 seconds](derived/original-gameplay-05.png), [fresh game capture](engine/01-initial-composition.png), [author's staged captures](../../implementation/20261004T222718-capture_encounter/receipt.json).

### QA-03 · P2 · Lighting and atmospheric depth are not close enough

The reference concentrates cool light around the action, with haze, layered shadows, and a darker perimeter. In the build, blue light spreads more evenly across the floor and the space reads more clearly as an exposed room. The loss of localized light and atmospheric depth matters more than a global brightness adjustment.

Tune the light pool, falloff, dark perimeter, shadow breakup, and restrained haze together. Preserve visibility of the player and boss silhouette while matching the original's distribution of light.

### QA-04 · P2 · Repetition and material detail weaken the reference atmosphere

The build's floor grid and straight arena edges dominate the image. Its teddy has a smoother, simpler surface than the reference creature's irregular detail and weight. The requested teddy substitution is intentional and is **not** a defect; its material response, silhouette detail, contact shadows, and weight still need to serve the same atmosphere.

Reduce conspicuous surface repetition and improve localized wear, roughness variation, contact grounding, and teddy fabric detail. Judge these at gameplay distance, after camera and lighting are settled.

### QA-05 · P2 · The bright red warning ring changes the visual emphasis

The large, strongly saturated ring is a prominent addition compared with the reference's restrained red accents. It is particularly conspicuous in the fresh native death-screen capture. Its size, brightness, and duration should support readable attacks without taking over the composition. This observation does **not** establish a permanently stuck warning-ring bug.

Evidence: [fresh ordinary-game screenshot](native/desktop-confirmed-game-visible.png).

## What the independent checks establish

| Area | Result | Scope |
|---|---|---|
| Standstill and movement | Pass | Stationary without input; movement action moved the player about 141 units. |
| Aim independent of movement | Pass | Aim direction changed independently while moving. |
| Firing | Pass | Four new player-owned projectiles observed; boss health fell from 300 to 264. |
| Dash | Pass | Action produced acceleration and about 345 units of travel. |
| Pause and resume | Pass | Action froze world time and then resumed it. |
| Restart | Pass | Action reloaded the encounter and restored boss health to 300; player health was 100. |
| Advertised Space / Escape / F5 bindings | **Fail** | All three saved keys are invalid. |
| Asset preservation | Pass | All 68 inventoried build/configuration/editable files and the original video retained their hashes. |

These comprise eight behavior assertions in a fresh Unreal 5.8.3 play instance. They are a bounded functional check, not a complete gameplay acceptance suite. Enemy AI stayed active; no actors were teleported and no health values were edited. The world was held briefly for three fresh screenshots. The first hides the HUD; the other two include a pause overlay and are **not** used to judge lighting.

[Behavior receipt](engine/receipt.json) · [Capture validation](image-validation.json) · [Preservation receipt](preservation.json)

## Comparison method and remaining limits

- Fresh reference frames were extracted directly from the original MP4 at requested seeks of 5, 10 and 16 seconds, rotated 90° counterclockwise, then cropped to the gameplay area (700 × 384, origin 76,0 in the upright frame). No color or exposure adjustments were applied. The social/video-player overlays remain visible and are not target game UI.
- The main board shows the reference and fresh build at equal displayed widths with their aspect ratios preserved. It compares composition and atmosphere, **not identical actions at an identical simulation time**. The fresh build image is a 1280 × 720 engine capture; the play viewport reported 1014 × 550. It is not a performance benchmark.
- Previously extracted author reference frames are not pixel-identical to the fresh extractions. This is recorded in the validation receipt; no pixel-similarity score or exact frame alignment is claimed. The original MP4 hash is unchanged: `289b314d3578e76e7a8e916c31ef653c0bbea2fb97e21eea2100cb063069fdeb`.
- The source motion contact sheet and the author's gameplay sequence were inspected. The delivered movie contains approximately 9.2 unique captures per second repeated into a 30 fps container. It is insufficient for reliable judgments about fine animation smoothness, foot sliding, or frame pacing. Obtain a fresh continuous capture at the intended playback rate for that review.
- The separate native window was visible, but the desktop input harness lost foreground focus and correctly refused to send keys into another window. No keyboard or mouse input was sent by that harness. This is a QA limitation, not evidence of a game defect. Physical keyboard/mouse play and gamepad operation remain unverified.
- Exact original button assignments cannot be inferred from the video. The failed bindings above are assessed against the build's advertised controls. Audio matching was not verified in this pass. Packaging, installation on another PC, and production performance were not re-tested.

## Next acceptance pass

1. Repair and reopen the input mapping asset; verify both saved-key validity and actual Space, Escape and F5 behavior.
2. Align camera, framing, and light distribution against all three reference frames before surface polish.
3. Refine surface detail and attack effects, retaining the requested teddy monster.
4. Review a fresh continuous play capture with sound, including movement, aiming, firing, dodge, pause, death/restart, and boss defeat. Keep functional correctness and reference fidelity as separate decisions.

All evidence for this independent pass is contained in this directory. The author's delivery evidence and status documents were preserved.
