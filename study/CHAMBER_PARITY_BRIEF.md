# Chamber parity — current team brief

Updated 5 October 2026 from the saved floor recovery and its independent review. [Earlier iteration notes](CHAMBER_PARITY_HISTORY_20261005.md) preserve rejected trials and superseded values.

**Objective:** reach visual parity with the two user-selected chamber concepts while preserving the playable encounter. Both defining walls are built. Floor damage, light distribution, upper haze and architectural proportions still differ materially. **Exact parity and user acceptance remain open.**

## Prerequisites and starting point

Follow the [team checkout instructions](../README.md#prerequisites-and-first-run): Windows, Unreal5.8.3, Git LFS and Python3.11+. Open `TeddyBlueprint/TeddyBlueprint.uproject`, `/Game/Maps/TeddyEncounter`. No scene regeneration or native compilation is required.

Inspect the [front target](visuals/chamber-target-front.png), [reverse target](visuals/chamber-target-reverse.png), the [current native views](../evidence/implementation/20261005T163731-capture_chamber_views/receipt.json) and the [current independent review](../evidence/chamber-qa/grok-20261005T163731/INDEPENDENT_REVIEW.md). The [pre-Grok comparison](../evidence/chamber-qa/final/comparison.png) and [pre-Grok review](../evidence/chamber-qa/final/INDEPENDENT_REVIEW.md) are the historical handoff. Assign one Unreal writer and capture the saved baseline before editing. See [TEAM_CONTINUATION.md](TEAM_CONTINUATION.md) for commands and a ready-to-run agent prompt.

The [close direction](visuals/direction-close-best.jpg) and original video establish the elevated combat atmosphere. The latest user instruction focuses on **the chamber itself**. Preserve characters, mechanics, controls and the gameplay camera. Concept labels and social-video overlays are not game UI; concepts do not supply measured dimensions or light values.

## Reference design

| Surface | Required read |
| --- | --- |
| Whole chamber | Heavy enclosed industrial room, tall worn walls around a broad combat floor, dark corners with readable depth. |
| Front | Large clipped-corner B-3 pressure bulkhead, split leaves, central wheel, deep jambs/header, red indicators, upper-right fan and services. |
| Reverse | Actual opposite wall with two separated service bays, central support, attached pipes, cabinets, drums and vessels. |
| Ground | Continuous irregular fractures, eroded plate margins, damp masses and varied angular fragments, with quiet intervals and grounded contact. |
| Atmosphere | Local teal overhead illumination and suspended haze, restrained red points, deep recesses and a moving white player pool. |

## Saved implementation

- Broad B-3 bulkhead, wheel, indicators and fan replace the earlier small X-braced appearance. Original assets remain preserved.
- Both side walls and the real two-bay reverse wall exist. Modeled piers, attached equipment and lowered perimeter drainage complete the enclosure. Native camera-dependent wall/light cutaway remains active.
- Weathered world-aligned wall materials use a new generated albedo with retained normal/roughness inputs. This is authored art, not a measured scan.
- **One recovery sheet** (`SM_ChamberFractureRecover_Main`, actor `TE_Chamber_Recover_Main`) is the visible floor. It has no collision. The V3 morphology sheet, the five V2 fields, four slab groups and five crust banks remain at their frozen transforms and are hidden. The 13:18 UTC black-card attempt and the 16:14 dark-mosaic sheet were rejected and are not the saved mesh.
- The earlier84-instance /21-mesh room extension remains. Source catalogs also contain unused variants; file presence does not establish assignment.
- Character meshes, skeleton, animation, gameplay and controls were preserved. Ordinary tracking remains pitch−46° and FOV54; architectural evidence cameras are separate.

[chamber-settings.json](chamber-settings.json), revision `chamber-12-bay-atmosphere`, holds current room values. The older `floor` object is unchanged and describes the hidden V2 graphs. `floor_morphology` describes the hidden V3 sheet. `floor_recovery` is the visible sheet: 720 cm tile, detail weight 0.28, normal mix 0.28. Lighting numbers were not edited for this floor pass. The saved fog rect is 120,000 cd at scattering 7 with diffuse 0, height-fog density is 0.010, and the combat-floor return is 14,000 cd. Exposure bias remains 3.8. These are saved implementation values, not acceptance thresholds.

## Next work in priority order

| Priority | Current difference | Task and review condition |
| --- | --- | --- |
| 1: floor depth | The V3 smooth sheet and the 16:14 dark mosaic are gone. The current sheet reads as damp cracked concrete out to the drainage. Straight splits and grounded chunks are still quieter than the concepts. | Refine erosion shape in `FloorRecoveryV4` only if a later pass still needs it. Do not restore black cards, the V3 sheet, or the hidden V2 overlays. |
| 2: light and haze | The 17:03 trial lit the bay openings, shrank the tall side bars to small points, and lowered the teal shaft to Z 1100. The bays are still shallow, and the column is still thinner than the concepts. Floor brightness rose only slightly. Exposure stayed 3.8. | Deepen the recesses only in front of the shell face. Thicken the shaft without a glowing bar or a global exposure raise. |
| 3: construction/framing | Panel divisions are more regular, wall/door/floor proportions approximate, and the upper volume is still thinner than the concepts. | Compare geometry and disclosed cameras before changing either. Strengthen architectural mass/local aging. Never hide missing construction with framing or force cutaway for a still. |

More small debris or uniform contrast will not solve continuous erosion. Do not change characters or the gameplay camera to improve the architectural comparison. Render, judge the room, then revise the narrow cause.

## Active sources and ownership

| Source | Purpose |
| --- | --- |
| [ChamberParity](../Assets/Adapted/ChamberParity/) | Editable door, wheel, bays, drums and source renders. |
| [FloorNormalsV2](../Assets/Adapted/ChamberParity/FloorNormalsV2/manifest.json) | Three corrected field mesh types, five placements. |
| [SlabsNormalsV2](../Assets/Adapted/ChamberParity/SlabsNormalsV2/manifest.json) | Sixteen closed slabs in a sparse group, four placements. |
| [CrustNormalsV2](../Assets/Adapted/ChamberParity/CrustNormalsV2/manifest.json) | Two corrected bank types, five placements. Hidden, not deleted. |
| [FloorMorphologyV3](../Assets/Adapted/ChamberParity/FloorMorphologyV3/manifest.json) | Hidden previous sheet. Kept in place. Not the visible floor. |
| [FloorRecoveryV4](../Assets/Adapted/ChamberParity/FloorRecoveryV4/manifest.json) | Visible floor sheet. One placement. Concrete normals and wet/dry roughness are applied in Unreal. |
| [WallSurface](../Assets/Adapted/ChamberParity/WallSurface/) | Albedo, prompt/provenance; retained inputs supply normal/roughness. |

Unreal assets use `/Game/TeddyEncounter/Chamber`; actor prefix `TE_Chamber_`, tags `TeddyEncounterOwned` / `ChamberOwned`. One integrator writes shared maps/packages. Source artists use separate agreed files; QA judges without changing the candidate.

V1 floor/slab/crust exports had confirmed winding/normal defects. V2 source and exported-FBX checks now pass. Retain V1 as history only. Consult `make_chamber_surface_normals_v2.py`, `make_chamber_crust_normals_v2.py` and reviewed import scripts; create new source revisions for new work. **Do not rebind old exports or rerun whole historical builders over the saved level.**

## Reproducible comparison

Native output1920×1280, no warp/grading; camera revision `chamber-03-reverse-services`:

| View | Location cm | Aim cm | FOV |
| --- | --- | --- | ---: |
| Front | `(-4050,180,2780)` | `(100,180,80)` | 41.5° |
| Reverse | `(1450,100,1450)` | `(-600,100,0)` | 70° |

Architecture capture holds characters/hides HUD, retains saved lights/materials and observes native ticks/cutaway. Label these choices. Add normal gameplay views and motion: held plates cannot establish physical input or camera continuity.

## Latest evidence and limits

| Evidence | Result |
| --- | --- |
| [Current native views](../evidence/implementation/20261005T170326-capture_chamber_views/receipt.json) | Front, reverse, and ordinary gameplay after the bay and overhead trial. Native 1920×1280. |
| [Current chamber runtime](../evidence/implementation/20261005T170523-verify_chamber_runtime/receipt.json) | **34/34**. |
| [Current room runtime](../evidence/implementation/20261005T170600-verify_full_room/receipt.json) | **28/28**. Arena-floor trace still at Z −5. |
| [Current pass note](../evidence/chamber/20261005T170149Z/BAY_ATMOSPHERE_QA.md) | Open bays, restrained side lamps, lower teal shaft. Not exact parity. |
| [Floor-recovery views](../evidence/implementation/20261005T163731-capture_chamber_views/receipt.json) | The reviewed before pair for this pass. |
| [Floor-recovery chamber runtime](../evidence/implementation/20261005T163834-verify_chamber_runtime/receipt.json) | **34/34** on the floor candidate, before this lighting pass. |
| [Floor-recovery room runtime](../evidence/implementation/20261005T163913-verify_full_room/receipt.json) | **28/28** on the floor candidate. |
| [Floor-recovery movie](../evidence/chamber/20261005T161155Z/native-motion-20261005T164043/native-motion.mp4) | 19.133s, silent, simulated input. Ends in **boss defeat**. Predates the bay and overhead trial. |
| [Floor-recovery identities](../evidence/chamber/20261005T161155Z/delivery-inputs.json) | Hashes for the reviewed floor candidate. |
| [Floor-recovery image review](../evidence/chamber-qa/grok-20261005T163731/INDEPENDENT_REVIEW.md) | Incremental floor recovery. 20 identity hashes and 62 runtime checks verified. |
| [11:47 handoff views](../evidence/implementation/20261005T114712-capture_chamber_views/receipt.json) | Historical. Not the current candidate. |
| [11:51 movie](../evidence/chamber/20261005T095028Z/native-motion-20261005T115126/native-motion.mp4) | Historical. Silent, simulated input, ends in **player loss**. |
| [Pre-Grok QA](../evidence/chamber-qa/final/INDEPENDENT_REVIEW.md) | Historical handoff review. |
| [11:47 preservation](../evidence/chamber/20261005T095028Z/final-preservation.json) | Historical. 175 owned assets through that validation. Not acceptance of the recovery sheet. |

Earlier48/48 character and12/12 saved-key checks are historical coverage. Physical-device input, matched audio, packaging and sustained performance remain unverified. The short recording is not a performance certification.

Repository preparation subsequently changes docs, portable paths and unused Android File Server config, while retaining game Content bytes. Historical preservation applies to its chamber run; the [team Content hash manifest](../evidence/team-handoff/content-sha256.json) covers this checkout. Never overwrite old receipts to suggest new verification.

## Acceptance

Both agreed views must approach the targets in enclosure/proportions, landmark depth, continuous ground damage, local wear, light, haze and services. The same saved room must preserve clear routes, native cutaway and readable normal gameplay. Deliver before/after images, fresh receipts, independent review and named remaining differences. The user's review closes visual acceptance.
