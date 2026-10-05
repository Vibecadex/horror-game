# Independent visual parity review

Target: [direction-close-best.jpg](visuals/direction-close-best.jpg), selected by the user on 5 October 2026. The user requests an expert expansion of this reference and a playable scene that reaches its visual quality. The selected image is a look-development image, not a current Unreal capture. It supplies visible art direction; it cannot establish hidden room geometry, exact engine settings, moving-light behavior or physical controls.

This QA reviewer owns this document, `tools/verify_visual_parity.py`, and new evidence below `evidence/parity-review/`. The reviewer does not run Unreal or edit the map/assets. The integrator remains the sole engine writer. Original video, original teddy, starter and current licensed/adapted sources remain preserved.

## Review gates

| Gate | Required evidence | What it establishes |
| --- | --- | --- |
| 1. Honest comparison framing | A fresh 1280×720 held gameplay view with staged subjects aligned to the selected image; capture receipt identifies all staging and saved rendering settings. | Light/material/shape differences can be compared without a different architectural camera concealing them. |
| 2. Actual rendered quality | Independent full-size inspection of the seven axes below, plus close detail crops that retain the source image bounds. | The art is visibly close in the named dimensions. Numeric metrics never establish this gate alone. |
| 3. Saved runtime consistency | A fresh ordinary gameplay capture using the saved level, camera, exposure and materials, including moving/aiming, firing, evasion, enemy motion and restart. | The appearance survives ordinary use instead of existing only in a special screenshot setup. |
| 4. Readability and mechanics | Existing room edge/corner/collision suite and input/key checks appropriate to changed dependencies; inspect all edge/corner images. | New art does not hide subjects, block movement or disturb saved controls. Tests are injected-route evidence, not physical-device acceptance. |
| 5. Independent disposition | A written review states each axis as matched / materially improved with gaps / failed, with exact image links and remaining differences. | A reviewable fidelity finding distinct from implementation, test counts and owner acceptance. |

Do not substitute an architectural overview, an edited capture, an exposure-normalized image or a still of a cinematic-only alternate map for gates 1 and 3. Tiny pixel differences need not be eliminated: this target contains a particular pose and generated details that may not be physically coherent. Matching the visible relationships and quality must not weaken the playable encounter.

## Seven visual axes

| Axis | Direct observation from the selected image | Acceptance requirement |
| --- | --- | --- |
| Composition and scale | Elevated oblique camera; boss upper-left, small armed player lower-right. At 1280×720 the approximate boss body bounds are x370–534, y133–338; player including weapon x818–870, y420–504. | A deliberately matched view shows similar screen-space body proportions and separation. Suggested diagnostic tolerance is centers within 3% of frame dimensions and body width/height within 15%; pose differences are stated. No decorative camera is presented as gameplay. |
| Teal key and grounded shadow | A concentrated overhead cool key reveals the upper boss and arena center. The boss casts a strong connected shadow toward the foreground, much longer than the player's shadow. | A visible directional light relationship, contact at planted feet, substantial dark foreground boss shadow, and no bright detached blob. Shadow must remain stable through normal creature movement. |
| Far haze and dark perimeter | Far architecture dissolves into cyan/teal haze; small red fixtures survive. Corners are near black; central ground remains readable. | Depth layering and dark edges remain visible at the same exposure. No uniform cyan wash, obvious spherical fog blob, lifted grey corners, or hard room edge in the primary view. Far haze must not hide active enemies. |
| Player light and readable action | A small bright, cool-white patch lies just left of the player and separates the player from the floor. The body remains a dark armed silhouette. | The localized pool is conspicuous at gameplay size, follows the intended player/aim behavior, lights actual ground/near objects, and does not replace the body with bloom. Player, aim and attack cues remain readable centrally and at all supported edges. |
| Teddy cloth and seams | Olive/desaturated worn woven cloth, raised dark stitching across head/back, compressed folds and darker recesses. Upper surfaces show grain rather than smooth pale clay. | Cloth detail and at least one intentional seam are legible at the actual gameplay view; close crops show coherent thread scale and attachment. Body retains recognizable teddy identity and the current grounded animated silhouette. No sliding world-space pattern, plastic glare, detached stitches or unrelated mesh replacement. |
| Broken ground and rubble depth | Fractured concrete at multiple scales, embedded dark cracks, small broken chips and rubble concentrated near margins. Some chips have side faces/contact shadows. | Several sizes of irregular crack/wear, restrained color contrast, small genuine raised fragments at margins, integrated contact shadows. No giant flat sticker crack, puddle outline, repeating identical patch or obstructed clear combat route. |
| Restrained gameplay effects | Small red peripheral practicals and near-white/cyan weapon/light accents; little competing decoration. | Threat telegraphs, aim/fire feedback and health remain usable without overwhelming the intended palette. The architectural extension supports the encounter rather than becoming its brightest feature. |

The seven judgments are not averaged into a percentage. A strong floor cannot compensate for a missing player light or a smooth unstitched creature. A visible blocker in any defining feature keeps parity incomplete. User acceptance remains the user's decision.

## Initial independent assessment

Compared the selected reference at full size with the [current initial gameplay](../evidence/implementation/20261005T054732-capture_room_gallery/01-gameplay-initial.png) and [widest gameplay](../evidence/implementation/20261005T054732-capture_room_gallery/02-gameplay-wide.png). The prior [combined-room review](../evidence/full-room/20261005T050433Z/INDEPENDENT_REVIEW.md) establishes 34 functional checks and the known dim extreme-distance player; it explicitly does not establish art parity.

- The player-adjacent bright pool is absent. The initial player has a lit body, but the nearby ground does not carry the reference's clear light patch.
- The floor is significantly darker and bluer across much of the frame. The reference has brighter local turquoise midtones and more legible far haze without globally bright corners.
- The boss is pale and smoothly shaded; its surface reads as rubber/clay rather than the target's olive woven cloth and prominent stitched seams.
- A long large crack, a flat debris cluster and a large puddle-like stain appear as graphic decals. The target has smaller, distributed fractures and raised fragments with thickness/contact.
- The boss shadow is shorter and less distinctly directed toward the foreground. The target uses a long connected dark shape as a major compositional mass.
- The current boss is roughly 10–20% wider and about 40 pixels above/left of the selected composition. The player is about 40 pixels farther right and 30 pixels lower. Stage a matched comparison before fine tuning color statistics.
- At opposite corners the normal adaptive camera leaves the player extremely small/dim. A good central still must not close this issue without inspecting corner captures and motion.

## Local comparison tooling

Installed Pillow 12.2.0 and NumPy 2.4.3 are sufficient; no installer, network call, Unreal process or asset mutation is needed. The helper only writes a fresh directory beneath `evidence/parity-review/` and refuses an existing output folder. It fully decodes its output artifacts and records source hashes.

```powershell
python tools/verify_visual_parity.py --candidate "evidence/implementation/RUN/01-matched-gameplay.png" --candidate-regions "evidence/parity-review/iteration-01-regions.json" --capture-receipt "evidence/implementation/RUN/receipt.json" --capture-kind staged-gameplay --framing matched --label "Iteration 01 saved Unreal lighting" --output "evidence/parity-review/iteration-01"
```

Candidate masks use the schema `{"coordinate_size":[1280,720],"regions":{"boss_body":{"polygon":[[x,y],...]},"player_pool":{"ellipse":[x0,y0,x1,y1]},"far_haze":{"rectangle":[x0,y0,x1,y1]}}}`. Copy the reference region structure from the generated `metrics.json`, then move the candidate polygons to the actually rendered subjects after inspecting the new capture. Region labels must describe visible content; do not draw a bright pool where none exists to make a ratio look better. Boss/player body masks omit shadows; the cloth-detail region should avoid silhouettes and foreground background pixels.

When candidate annotations are omitted, fixed reference-screen masks are explicitly exploratory. They must not be cited as subject-aligned measurements. A `matched` claim requires manual candidate annotations and a capture receipt. The tool records whether suggested framing tolerances are met but does not silently realign either image.

Artifacts include unchanged full-frame side-by-side images, visible region annotations, individually aspect-preserved detail crops, a fixed-threshold luminance map, JSON metrics/hashes, and a methods note. Metrics include display RGB/luma, percentiles and bright/dark area shares; separate linear luminance; local pool-to-surround, shadow-to-surround and center-to-edge ratios; and 2 px blur residuals. These are diagnosis cues. They cannot prove physical depth, thread geometry, temporal stability or artistic quality.

Do not chase old whole-image reference-video values such as "8–16% above luma 40" without remeasuring this newly selected look study. It is a different image, with a larger bright floor and player pool. Never grade-match by a global brightness adjustment that erases the dark perimeter. Full images remain unwarped and unedited; crops are labelled and cannot establish scale parity.

## Integrator capture recommendations

Use the existing frame-driven PIE gallery pattern, freeze actor movement only for the held comparison, hide HUD only for that comparison, and preserve saved lighting/post-process. Record camera position, pitch/yaw/roll, FOV, each subject transform/pose and the post-process exposure settings in the receipt. Keep the staged comparison labeled. Wait for shaders and screenshot completion; assert the held camera/actors do not drift, and fully decode the PNG. No shared assets need to be saved by the capture script.

Keep a separate ordinary-play capture without actor teleporting/freezing or capture-only light intensities. Inspect it for moving pool response, floor-normal shimmer, cloth pattern swimming, contact shadow stability, fog trails and warning visibility. Existing room visibility traces do not detect lighting contrast and do not replace the corner-image inspection. No new mirrored gameplay tests are requested by this document.

## Disposition log

Initial combined build: **parity not reached**. The seven-axis rubric and local diagnostic tooling are ready for iterative rendered review. Add each iteration's evidence and independent findings beneath this section; preserve the initial assessment as historical evidence.

### Baseline diagnostic receipt

[Baseline comparison and methods](../evidence/parity-review/baseline-054732-refined/README.md), [measurements](../evidence/parity-review/baseline-054732-refined/metrics.json), [full comparison](../evidence/parity-review/baseline-054732-refined/comparison.jpg), and [detail crops](../evidence/parity-review/baseline-054732-refined/details.png). All four output images fully decoded. The candidate hash matches its original gallery receipt. Candidate semantic regions were manually marked; the shadow mask excludes the overlapping small creature. No player-pool mask is supplied because that pool is absent in this build.

| Diagnostic | Selected look study | Before parity pass |
| --- | ---: | ---: |
| Whole-image display luma | 57.36 | 24.88 |
| Central floor display luma | 117.28 | 31.60 |
| Far-haze display luma | 78.61 | 24.32 |
| Cloth-patch display luma | 48.65 | 100.59 |
| Four corner patches display luma | 0.53 | 12.33 |
| Central floor / perimeter luma ratio | 4.90 | 1.73 |
| Boss shadow / nearby floor luma ratio | 0.20 | 0.37 |

These approximate masks substantiate the visible direction: brighten the local floor and far haze, make the corners darker, and remove the overbright smooth boss response. Raising global exposure moves important regions in the wrong direction. Reference body bounds from the drawn masks are 161×205 pixels; current boss 198×230. Player including weapon is 49×85 versus 58×94. Neither passes the suggested framing band, so this evidence remains an approximate comparison rather than a claimed matched view. Different pose and weapon direction contribute to the box differences.

### Iteration 1 — lighting/material mechanisms

[Independent review](../evidence/parity-review/iteration-01-070819/INDEPENDENT_REVIEW.md), [comparison](../evidence/parity-review/iteration-01-070819/comparison.jpg), and [diagnostics](../evidence/parity-review/iteration-01-070819/README.md). Actual player pool and long grounded shadows are now present; olive cloth hue is closer. The key is too broad/bright, corners are lifted, the pool is oversized and aimed below the player, and the boss shadow extends too far toward the lower left. Far haze brightness is already close to target. The pool's core brightness is also close, so shrinking the footprint is preferable to blindly reducing peak intensity. Floor/stitch geometry and a matched aiming view are still pending. **Parity remains incomplete.**

### Iteration 2 — comparable framing and first physical detail

[Independent review](../evidence/parity-review/iteration-02-071701/INDEPENDENT_REVIEW.md), [comparison](../evidence/parity-review/iteration-02-071701/comparison.jpg), [detail crops](../evidence/parity-review/iteration-02-071701/details.png), and [diagnostics](../evidence/parity-review/iteration-02-071701/README.md). FOV54 and transient aim staging now produce a useful comparable composition. Player and pool brightness are close, central floor is substantially closer, large decals are gone, and a seam plus small physical fragments are visible. Remaining defining gaps are dark far haze/missing red points, lifted lower corners, smooth olive cloth with a thin seam rather than readable weave/cross-stitches, broad cloudy concrete with sparse scratch-like cracks and tiny pebble clusters, and very hard cast shadows. The player pool needs surface integration rather than another large intensity change. **Parity remains incomplete.**

### Added-art runtime suite prepared

`tools/verify_parity_runtime.py` supplements the existing room22/key12 checks. It was authored without launching Unreal and has parsed successfully; runtime results are still pending. Only the integrator may run it after confirming the shared project has no external editor/writer:

```powershell
python tools/run_encounter_test.py tools/verify_parity_runtime.py
```

The saved audit checks45 `ParityFloorDecor` actors and their actual `NoCollision` profiles, disabled component collision and disabled actor collision. It checks `SK_TeddyParityV2` on the existing boss and three minions, original skeleton identity, original six clip identities, seam/thread material slots and saved FOV54. A brief transient input fixture verifies that the saved spotlight follows player movement and two aim directions while its owner, attachment parent, relative offset and relative yaw stay stable. Artist-adjustable intensity, cone angles and offsets are not hardcoded.

The six original clips—Idle, Walk, Crawl, Attack, Hit and Defeat—then naturally advance on the new saved skin. Each records three distinct animation-time/bone snapshots and one fully decoded held1280×720 image. All16 bone names, socket positions, animation asset identity, component render bounds, foot-bone heights, camera and exposure are recorded. The script does not save assets, launch another process or edit gameplay graphs. It explicitly stages/freeze NPC actors and restores/holds the player's initial position for clip inspection.

These are supplementary structural/runtime checks, not an automatic skin approval. Render bounds are conservative culling bounds; bones are not stitched vertices. Independent inspection of all six actual poses is still required to detect floating stitches, stretched geometry, missing sections and visible ground penetration. Moving-light appearance and ordinary gameplay also require the final native recording. The reviewer has not run the engine while Grok is an active shared-project owner.

### Combined V2 candidate and first runtime run

[Combined visual review](../evidence/parity-review/combined-074707/INDEPENDENT_REVIEW.md), [comparison](../evidence/parity-review/combined-074707/comparison.jpg), and [six-pose/harness review](../evidence/parity-review/poses-074830/INDEPENDENT_REVIEW.md). Cloth texture, crown stitching, larger/more physical chips, softer boss shadow and integrated player pool are clear improvements. Far haze is still much darker than target, lower corners remain lifted, upper cloth is warm/bright, and connected large concrete fracture remains weak. **Parity remains incomplete.**

All six first runtime pose images were inspected. Their six failures were an exact bone-list harness error: Unreal contains the original `TeddyRig` import wrapper plus16 authored bones, rather than16 total. Actual motion, clip identity and finite data were present in every clip. The corrected test explicitly verifies the imported17-name hierarchy against original-mesh parent links. It also drains the first resumed game tick before the next short animation, avoiding the observed0.4s initial jump. Original failure evidence is preserved; fresh corrected results are pending. No detached seam/mesh explosion was apparent in inspected poses, but the rolled Defeat pose and partly detached-looking shadow still need a grounded-collapse check in motion. Static culling bounds cannot clear that concern.

### Grounded-collapse verification extension

The integrator imported a separate `/Game/TeddyEncounter/Parity/Animation/A_Teddy_DefeatGrounded` clip on the original skeleton, with the original six clips retained. The extended runtime harness now inspects saved Blueprint graphs and requires exactly one boss and two stitchling `NewAnimToPlay` bindings to the grounded clip, with no obsolete original-Defeat binding in either gameplay Blueprint. It still loads, audits and plays all six original clips; the new grounded clip is a seventh pose capture.

After these deliberately selected poses, a distinct runtime section exercises the actual saved death events. It applies lethal damage to one stitchling while the boss is alive, then applies lethal damage to the boss and enables the two surviving stitchlings' actor ticks to exercise their boss-death cascade. It never sets Health, State or graph pins, and never selects animation directly during this death-route section. It checks resulting health/state, disabled collision, actual animation identity and progressing playback; waits for all four deaths to reach the grounded clip's end; records final bone/bounds data; and saves an eighth image of the actual death-route result. Injected damage does not establish weapon-hit delivery, so the planned ordinary-input movie remains separate evidence.

This extension was authored and parsed without launching Unreal. Actual runtime results and the new settled poses remain pending. The earlier source-Defeat and failed harness receipts stay preserved for comparison; the original animation is not overwritten or relabeled as fixed.

### Fresh extended runtime result and FloorV3 candidate

[Extended runtime review](../evidence/parity-review/runtime-084751/INDEPENDENT_REVIEW.md): **48/48 passed, host exit0**, with all eight actual images independently opened. Original six clips and skeleton are preserved; new grounded clip and all three changed saved death-binding routes execute. Direct stitchling damage, boss damage and the two surviving stitchlings' boss-death cascade all reach the correct grounded clip/end state. The new held collapse is visibly lower/more connected than original Defeat; no obvious detached stitching or skin explosion is present. Temporal settling remains for ordinary-motion review.

[FloorV3/atmosphere review](../evidence/parity-review/candidate-084605/INDEPENDENT_REVIEW.md): the close view now combines all major visual ingredients and is the strongest reviewed candidate. Fixed foreground wear mean improves100.23→89.63 against target88.93; detail and contrast improve but remain lower than target. Preserve V3. Remaining defining problems are an obvious luminous rear fog bar in wider views, overbright close haze/corners, small/faint player at extreme separation, and cloth/seam stylistic differences. **Full-room visual parity remains incomplete despite passing runtime checks.**

### Rear-haze and extreme-player refinement — interim

[Independent interim review](../evidence/parity-review/candidate-085410/INTERIM_REVIEW.md) and [current comparable plate](../evidence/parity-review/candidate-085410/comparison.jpg): the previous rear fog bar is absent in both wide/overview views, and the extreme-distance player now has visible head, torso and limbs. Close haze moves106.53→67.26 against target78.61; corners17.02→9.54 against0.53. Preserve the diffuse haze shape and V3 floor. Shadow/floor ratio matches0.200, while pool/surround remains close at1.935 versus2.011. Cloth is still warmer/brighter with finer stitching, connected floor cracks are less pronounced, and ordinary-motion legibility remains unreviewed. **Final visual disposition stays open until the optional room extension and normal-input movie are reviewed; resolved historical fog-bar findings must not be carried forward as current defects.**

### Expanded delivery gallery and fresh room audit prepared

[Independent six-view review](../evidence/parity-review/delivery-090957/INDEPENDENT_REVIEW.md), [gallery](../evidence/parity-review/delivery-090957/six-view-gallery.jpg), and [selected-reference comparison](../evidence/parity-review/delivery-090957/comparison.jpg): all six actual 1280×720 images opened and hashed against their capture receipt. The 84-instance perimeter extension supports the same unobstructed close composition; no new critical still-image defect is apparent. Corrected cloth hue is now close to the reference after matching patch luminance. Preserve this color direction and diffuse rear haze. Finer stitching, weaker connected/recessed cracking, brighter upper cloth/central floor and lighter lower corners remain secondary fidelity differences. Exact parity is not claimed.

At the integrator's request, `verify_full_room.py` now retains the existing 22 checks and adds six independent saved-extension checks. It audits 84 instances/46 shell/38 dressing, explicit tags/unique labels and owned namespace, 21 unique meshes, disabled actor/all primitive-component collision with actual `NoCollision` profiles, finite world bounds at or below 700 cm, and no bound intrusion into the combat rectangle. Actual saved component bounds are used, not importer-plan coordinates. Extension components participate in conservative camera-box hints; concealed components are excluded only from these visual hints. Source parsed successfully. Fresh engine results and ordinary-motion review remain pending.

### Fresh room result, rear visibility repair and first native recording

[Fresh room QA](../evidence/parity-review/room-091420/INDEPENDENT_REVIEW.md) passes **28/28 checks, host exit 0**, retaining all original room checks and passing all six new saved-extension checks. All 12 camera cases have clear traces and no visible-decoration box hints. Independently opening all six actual case images exposed a separate rear-center contrast issue despite the geometry pass.

The subsequent [rear visibility repair review](../evidence/parity-review/rear-092532/INDEPENDENT_REVIEW.md) confirms readable player head/shoulders/weapon/body at x=1000,1300,1400 without an obvious added bright floor patch. Its [unaltered before/after evidence](../evidence/parity-review/rear-092532/rear-player-before-after.png) preserves the original defect and repaired result. The specific still-image concern is resolved for those sampled positions; do not describe every aim direction or physical input as verified.

[First native motion review](../evidence/parity-review/motion-092128/INDEPENDENT_REVIEW.md): the 16.57 s native game recording has 496 frames and matches its receipt hash. Inspection covers 33 unaltered 2-fps samples plus 18 attack/25 death samples at 10 fps. Normal central combat, moving pool, readable warnings, decreasing health bars and victory text are present, without an obvious skin/stitch explosion or camera obstruction. Automated input in an isolated encounter copy is explicitly disclosed. The silent clip predates the rear repair and ends before a full settled-death hold; both limitations remain explicit while the final movie/gallery are pending.

### Consolidated final evidence

[Final independent report](../evidence/parity-review/final/INDEPENDENT_REVIEW.md), [final reference comparison](../evidence/parity-review/final/comparison.jpg), [final six-view gallery](../evidence/parity-review/final/six-view-gallery.jpg), and [final native movie](../evidence/parity/20261005T070301Z/native-motion-20261005T092830/native-motion.mp4) are now reviewed. All six final PNGs match their capture hashes. The final 19.10 s / 572-frame native movie matches its receipt hash and includes the full collapse plus settled hold. Review covers all 38 overview samples and 50 dense death samples, with native-size end-state inspection and explicit sampling/automation limits.

No critical defect was found in the final reviewed views and sampled sequence. The rear fog-bar and rear-player contrast findings are resolved in their documented coverage. Fresh room checks pass 28/28; the earlier added-art/death-route checks pass 48/48, with their differing build scope preserved. The room is suitable for the user's local play/review. Remaining art differences are finer stitching/fuzzier cloth, weaker connected/recessed concrete cracks, brighter upper cloth/central floor/lower corners, source mesh/pose differences and a stylized propped defeat. **Exact visual parity and user acceptance remain unclaimed.**
