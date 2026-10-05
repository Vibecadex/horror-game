# Independent final room and visual QA

The expanded playable room is substantially closer to the selected reference and is ready for the user's local play/review. **No critical defect was found in the final reviewed views and sampled native sequence. Exact visual parity is not achieved or accepted by this report.** Coarser stitching, more connected/recessed concrete cracking and darker lower corners remain visible differences. Test results, visual correspondence and the user's acceptance are recorded separately.

The reviewer authored separate checks, inspected rendered evidence and read the resulting receipts. Only the integrator launched Unreal or wrote shared game assets. Earlier failed/partial iterations remain preserved.

## Current evidence

| Evidence | Independent result and scope |
| --- | --- |
| [Final saved six-view gallery](six-view-gallery.jpg) | All six original 1280×720 PNGs opened and hashed against the [capture receipt](../../implementation/20261005T092659-capture_parity_delivery/receipt.json). Includes final thread color and rear character fill. [Source hashes/camera labels](gallery-provenance.json). |
| [Selected-reference comparison](comparison.jpg) | Unchanged full frames: selected look study and staged saved gameplay camera. [Detail crops](details.png), [regions](regions.jpg), [diagnostics](metrics.json). Architectural cameras do not substitute for this comparison. |
| [Fresh saved-room QA](../room-091420/INDEPENDENT_REVIEW.md) | **28/28 checks passed, host exit 0**: original 22 room checks plus six extension checks. Actual readback confirms 84 instances, 46 shell/38 dressing, 21 owned meshes, correct ownership, disabled actor/component collision and clear conservative bounds. All 12 camera cases pass; no visible-decoration box hints. |
| [Added-art runtime QA](../runtime-084751/INDEPENDENT_REVIEW.md) | **48/48 checks passed, host exit 0**: original skeleton and six clips retained, new V2 skin/seam slots, player-light attachment under movement/aim, FOV54, seven progressing clips and all actual saved grounded-death routes. Eight pose/death images inspected. This predates later material/perimeter-light changes; it is not relabeled as a new run. |
| [Rear-center visibility repair](../rear-092532/INDEPENDENT_REVIEW.md) | The issue found in the passing room sweep is resolved in independently inspected x=1000/1300/1400 poses. Head, shoulders, weapon and body outline now separate from the haze. [Before/after](../rear-092532/rear-player-before-after.png). |
| [Final native gameplay movie](../../parity/20261005T070301Z/native-motion-20261005T092830/native-motion.mp4) | 1280×720, **19.10 s / 572 frames**, matching receipt SHA-256. Decode succeeded. All 38 overview samples and 50 dense death samples inspected, including the completed collapse and settled hold. [Movie provenance](motion/review-provenance.json). |

The room checks precede the final thread-color and character-fill-only adjustments. No geometry, collision or control changes followed those checks. The final gallery/movie provide fresh rendering evidence for the later look changes. This scope distinction is retained rather than combining different receipts into a misleading single final-build test count.

## Correspondence to the selected look

The defining composition is present: an elevated oblique combat camera, large hunched teddy toward the upper left, smaller armed player toward the lower right, a connected long foreground shadow, local cool-white player pool, worn teal concrete, diffuse far haze and restrained red peripheral points. The expanded bulkhead, wall bays, supports, pipework, vents, electrical recesses and service details support this scene while leaving its center clear.

The previous rear luminous fog bar is absent in the final wide/overview views. The floor now includes actual fractured plates and raised chips rather than the earlier sparse scratch/sticker effect. The teddy reads as aged olive fabric with attached repairs; its hue correction is close to the reference's cloth color family. The player pool tracks movement/aiming in the native sequence and remains integrated with floor texture. The extreme-distance view keeps visible characters, although their small size is still a practical playtest consideration.

| Seven-axis visual disposition | Current judgment |
| --- | --- |
| Elevated combat view and subject hierarchy | Strong correspondence; saved camera is comparable, with source pose/anatomy differences. |
| Local overhead key and grounded long shadow | Present and coherent in stills/motion samples; outline differs with the creature pose. |
| Player pool and readable armed figure | Present and moving correctly in reviewed central combat; rear-center contrast repaired at three sampled positions. |
| Teal haze, dark edges and restrained red practicals | Haze shape and accents correspond; prior rear bar resolved. Lower corners remain lighter than target. |
| Worn cloth and prominent repairs | Corrected olive color, fabric response and attached seams present; weave/stitch thickness still differ. |
| Broken concrete and physical rubble | Real fractures/chips present and substantially improved; connected deep fissures and fragment-scale variation remain weaker. |
| Restrained effects and control legibility | Aim/fire, warning rings, health response and victory remain visible in automated native play. Physical-device feel and all aim directions are not established. |

These judgments are independent observations, not seven automatic passes or an averaged parity score.

The selected image is a generated look study, not an executable scene or identical mesh/pose. The saved gameplay view is close enough for useful composition and region comparison, but remains deliberately staged. The manually marked player's height exceeds the suggested framing band by 0.29 percentage points; that false diagnostic flag remains in the receipt. Images are not warped or graded to hide differences.

| Approximate local diagnostic | Reference | Final |
| --- | ---: | ---: |
| Boss shadow / nearby floor display luma | 0.200 | 0.206 |
| Player pool / nearby floor display luma | 2.011 | 1.923 |
| Foreground fracture-patch display luma | 88.93 | 92.39 |
| Far-haze display luma | 78.61 | 73.61 |
| Central-floor display luma | 117.28 | 133.30 |
| Cloth-patch display luma | 48.65 | 73.28 |
| Four corner-patch display luma | 0.53 | 10.16 |

These masks diagnose local exposure/contrast relationships, not physical light units or artistic equivalence. Cloth masks include different surface normals, pose and stitch coverage. Matching one mean or ratio does not establish matching weave, crack depth, silhouette or atmosphere. No overall similarity percentage or numeric parity pass is assigned.

## Native movement and completed defeat

The final recording runs an isolated copy of the saved encounter, normal AI/health and a Blueprint input driver. It injects movement/fire/dodge key routes and aim actions; it does not teleport actors, edit health or freeze AI. This is native gameplay rendering under automation, not a person testing physical keyboard/gamepad input.

The reviewed sequence shows movement and dodge travel, independent aiming, enemy pursuit, visible attack rings, decreasing player/boss health bars, firing feedback and victory text. The camera retains the fight. No obvious detached stitch, exploding skin, wall obstruction, gross lighting discontinuity or repeated death restart was found in the inspected samples. The teddy completes its new collapse and holds a stable reclined/propped pose through the final seconds. Its toy-like movement and propped finish remain stylistic refinements; this is not a natural ragdoll simulation.

The complete final sequence is available in contact-sheet pages [1](motion/sequence-01.jpg), [2](motion/sequence-02.jpg), [3](motion/sequence-03.jpg), [4](motion/sequence-04.jpg), [5](motion/sequence-05.jpg), [6](motion/sequence-06.jpg), [7](motion/sequence-07.jpg). The entire final death interval is sampled at 10 fps in pages [1](motion/death-sequence-01.jpg), [2](motion/death-sequence-02.jpg), [3](motion/death-sequence-03.jpg), with [individual-frame provenance](motion/dense-death-provenance.json). The [final held frame](motion/frames-2fps/frame-038.png) was also opened at native size. Approximate sample times are disclosed. These observations are not represented as continuous 30-fps viewing; brief shimmer, frame pacing or tiny transient artifacts cannot be excluded by sampled inspection.

The movie is silent and does not establish audio correspondence. It covers central combat, while rear-position visibility is established by the separate targeted plates. It does not establish all possible inputs/aim directions or subjective play feel.

## Remaining art differences and disposition

- **Teddy surface:** repairs are finer/sparser and the cloth reads more fuzzy than the reference's coarse weave and chunky crossed stitches. Upper cloth remains brighter; source anatomy/pose and its shadow silhouette differ.
- **Ground:** current cracks are less connected and less deeply recessed than the reference. Fine rubble is denser/more uniform in places, while the reference has larger broken plates and stronger dark crevices.
- **Light distribution:** the central floor and lower corners remain brighter than the reference. The haze and local shadow/pool relationships are close, but their numeric proximity does not erase this visible distribution difference.
- **Motion finish:** the grounded collapse completes reliably in the reviewed evidence, but the propped toy pose is stylized and could be refined for weight and natural settling.

The observed fog-bar and rear-player defects have been repaired; they are historical findings, not outstanding final blockers. Within the reviewed coverage, the current room is suitable for local play/review. The evidence supports successful implementation and substantial reference alignment. **It does not support the statement “exact parity reached,” a production/performance certification, physical-device verification or user acceptance.**
