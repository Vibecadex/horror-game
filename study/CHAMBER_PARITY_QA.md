# Independent chamber parity QA

The current task is to reach the chamber appearance shown in the user's [front/full-chamber target](visuals/chamber-target-front.png) and [reverse target](visuals/chamber-target-reverse.png). These are concept images, not Unreal screenshots. Both directions are authoritative for visible art direction; inferred dimensions and hidden geometry are design choices, not facts supplied by the images.

This review is separate from the completed close-combat comparison against `direction-close-best.jpg`. Earlier passing gameplay checks and the earlier finding of a reviewable room do **not** establish parity with these newly supplied chamber views. Substantial architecture, lighting and ground differences must be repaired and rendered, rather than closed by functional test counts.

The independent reviewer owns this document and `evidence/chamber-qa/`. The integrator alone runs Unreal and writes shared game assets. No reference, original asset, map or existing user game is modified by the review.

**Current final disposition:** the [consolidated independent review](../evidence/chamber-qa/final/INDEPENDENT_REVIEW.md) covers the final 114712 front/reverse views, corrected V2 ground assets, fresh chamber28 + room28 passes, all six gameplay stills and the genuine native loss-path recording. No new blocking defect was observed. Ground morphology, upper haze/direct-light balance, service visibility and exact proportions remain different; **exact chamber parity and user acceptance are still open**.

## Evidence and comparison rules

- Preserve both supplied images byte-for-byte. Front is 571×378; reverse is 475×320. Their white borders and printed captions are excluded from scene measurements. Their slightly different aspect ratios prohibit a stretched pixel overlay or a whole-image similarity score.
- Capture the actual saved chamber from a front and a reverse camera that approximate the corresponding reference. Record world position, direction, pitch, FOV, screenshot dimensions, relevant saved light/exposure settings, actor staging and any camera-only hiding in the receipt. A reverse image must show the actual opposite wall, not a mirrored front capture.
- Keep original engine PNGs ungraded and unwarped. Side-by-side display may fit each image within its own box while preserving aspect ratio. Label crops and any resizing. A special review camera is architectural evidence; it does not demonstrate the normal gameplay framing.
- Review proportions before exposure statistics. Where measurements help, annotate visible landmarks separately in each image and compare normalized relationships, not identical screen masks. Dark-pixel means cannot prove structural depth, and matching mean brightness cannot prove matched materials.
- Use front and reverse together to check a coherent room. Concept details can be inconsistent, so prioritize repeated construction/material language and plausible wall relationships over reproducing an impossible seam or duplicated prop.
- Preserve prior iteration images and failure findings. Each later review identifies exactly which saved capture it inspected and whether any defining gap remains.

## Chamber acceptance rubric

| Axis | What the targets show | Required rendered result |
| --- | --- | --- |
| Enclosure and proportions | An enclosed rectangular industrial chamber; substantial readable walls occupy roughly the upper third, with floor taking the larger share. Side walls converge into real rear corners. | Comparable front and reverse views show a coherent enclosure, believable wall height and visible floor/wall junctions. Door, pier and service proportions must not be concealed by a very distant camera, crop or black void. |
| Front focal architecture | A central broad heavy blast door, thick chamfered frame, divided leaves, central wheel, layered lower threshold and small red side indicators. | The door is recognizable at the full-room view and has visible depth: jambs, recess, threshold and layered surfaces. A flat dark rectangle with a glowing mark is insufficient. Fine stencil typography is secondary to the mass and construction. |
| Reverse wall identity | Two separated dark maintenance door bays, each with a red indicator; broad structural separation and readable vertical returns. | Both bays and the separating wall structure exist on the actual opposite wall. A low sill, open edge, copied front blast door or opaque fog curtain fails this axis. Any gameplay cutaway strategy is disclosed and tested separately. |
| Wall and service depth | Thick piers/returns, inset panels, wall staining, purposeful conduits, left electrical equipment, right pipe/tank groups, front fan and integrated perimeter grates. | The major groups can be identified at the matched views, with attachment, thickness, recess/contact shadows and coherent connections. Repeated thin boxes or unconnected floating pipes must not stand in for the target's layered construction. |
| Ground scale and integration | A connected irregular fracture network, occasional larger broken plates, fine grit and angular chips, grouped dark damp/worn areas. More clutter near margins; usable central floor remains visibly worn. | Front and reverse show several connected fracture scales and depth cues without isolated sticker-like islands. Rubble has a range of sizes and grounded side faces/contact. Wet/worn areas form broad irregular masses, while the combat lane stays clear. |
| Illumination and material readability | Cool overhead illumination reveals the chamber center and enough wall detail to read construction; local red practicals and player pool remain accents. Modest far haze separates depth. | Both directions show textured, charcoal/teal walls rather than black absence or uniform cyan wash. The main door and service groups remain readable at the saved exposure. Haze may soften distant edges but must not erase piers/doors or form a luminous horizontal bar. |
| Playable continuity | The chamber supports the existing elevated fight, grounded creatures and independently moving/aiming player. The targets do not authorize replacing gameplay with a cinematic set. | Saved ordinary gameplay retains readable subjects, light pool and telegraphs. New architecture avoids collision/movement changes and camera obstruction unless explicitly part of the implementation scope. Reuse appropriate room/input regressions, then inspect their captures: visibility traces alone do not establish visual readability. |

There is no averaged parity percentage. Missing opposite-wall architecture, unreadable defining wall groups, or an obviously different ground/material scale keeps chamber parity incomplete even if every functional test passes. User acceptance remains distinct from this independent review.

## Reference observations and initial gap assessment

**Front target.** The broad rear blast door is the principal wall landmark. A fan occupies the upper right rear bay, with tanks and electrical equipment below/along the right side; left wall equipment and conduits sit above a continuous low service/drain edge. Piers, door jambs and side returns create real depth. Cool light reaches the wall and floor together. Cracked plates and larger chips are strongest toward the near floor, with dark damp/abraded patches breaking up the central surface.

**Reverse target.** Two smaller, separated door bays replace the front door as the far-wall landmarks. Their red indicators, intervening pier, left electrical bank and right elbowed pipe/tank group make the direction legible. The wall remains visibly enclosed through the haze. Floor and wall construction read as the same space from the other end.

**Current saved scene, before a matched chamber baseline.** The [prior room overview](../evidence/implementation/20261005T092659-capture_parity_delivery/03-room-overview.png), [rear-bulkhead view](../evidence/implementation/20261005T092659-capture_parity_delivery/04-rear-bulkhead.png), [side-services view](../evidence/implementation/20261005T092659-capture_parity_delivery/05-side-services.png) and [electrical view](../evidence/implementation/20261005T092659-capture_parity_delivery/06-electrical-bay.png) are engine evidence, but their cameras are not matched to these new concepts. They show architecture hidden too deeply in darkness/haze and contain no correct reverse-wall comparison. The existing low foreground cutaway does not meet the new opposite-wall target. The previous independent review also identified weaker connected/recessed cracks and overly uniform fine rubble. These are substantive new-task gaps, not merely optional finishing notes.

Recommended order: establish front/reverse framing and enclosure proportions; repair opposite-wall landmarks and layered construction; make both directions readable using the saved lighting; then tune connected floor fracture, dampness and debris scale. Recheck normal gameplay after architectural changes. Do not compensate for missing geometry by increasing fog.

## Iteration record

Initial disposition: **chamber parity not reached**. Both targets were visually inspected at their native resolution. A fresh matched front/reverse Unreal baseline is pending from the integrator; no quantitative comparison is claimed from the unmatched prior gallery.

[Annotated reference landmarks](../evidence/chamber-qa/reference-observations/reference-landmarks.png) identify the independently reviewed features without changing either original image. [Provenance and approximate bounds](../evidence/chamber-qa/reference-observations/provenance.json) record dimensions, source hashes and the aspect-preserving display method. The boxes are explanatory annotations, not segmentation truth or automatic acceptance thresholds.

### Baseline 095951

[Independent baseline review](../evidence/chamber-qa/baseline-095951/INDEPENDENT_REVIEW.md) and [front/reverse comparison](../evidence/chamber-qa/baseline-095951/comparison.png): both actual 1920×1280 engine plates were inspected and verified against their capture receipt. Main blockers are the missing reverse wall identity, veiled/underspecified front door, unreadable service groups and disconnected ground damage. Front framing is useful for the first massing pass; reverse perspective remains provisional until its wall exists. **Chamber parity remains incomplete.**

### Iteration 101028

[Independent review](../evidence/chamber-qa/iteration-101028/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-101028/comparison.png): new front pressure-door identity and the actual two-bay reverse wall are present, and the former cyan veil no longer erases the front bulkhead. Side services remain too dark, reverse beacons are weak, panel materials look speckled, and ground fracture/wear remains disconnected. Camera/proportion refinement remains necessary. **Architecture is materially improved; chamber parity is not yet reached.** The separate [floor source review](../evidence/chamber-qa/floor-source-review/INDEPENDENT_REVIEW.md) allows the new branching fields to advance to engine inspection without treating Blender previews as final evidence.

### Iteration 102310

[Independent review](../evidence/chamber-qa/iteration-102310/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-102310/comparison.png): revised cameras, readable service groups and connected floor networks are present. Wall illumination now overshoots into an even, clean appearance; the raised perimeter platform, weak reverse beacons and bright rubble filaments remain material differences. **Chamber parity remains incomplete.** The first scoped runtime audit passed 18/19 checks; the sole failure is the test camera's transient FOV restoration, with correctly operating native wall visibility. [Diagnosis and preserved failure](../evidence/chamber-qa/runtime-102211/DIAGNOSIS.md) describe the tightened harness and required rerun.

### Iteration 102903

[Independent review](../evidence/chamber-qa/iteration-102903/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-102903/comparison.png): perimeter platform dominance and reverse bright filaments are repaired; door mass/placement is closer. Regular vertical material stripes are a new visible defect, and reverse lighting/practical accents and larger floor wear remain weaker than target. **Chamber parity remains incomplete.**

### Iteration 103737

[Independent review](../evidence/chamber-qa/iteration-103737/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-103737/comparison.png): regular stripes are gone and broader ground wear/local header illumination improve the room. New reverse piers are physically hidden behind the backing and need correction. Dense fine floor mottling, sparse larger fragments, clean hot wall patches and weak reverse practicals remain visible differences at equal display width. **Chamber parity remains incomplete.**

### Iteration 104400 and audit 104516

[Visual review](../evidence/chamber-qa/iteration-104400/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-104400/comparison.png) confirm the reverse pier occlusion is repaired and the floor detail is quieter. [Independent runtime review](../evidence/chamber-qa/runtime-104516/INDEPENDENT_REVIEW.md) confirms **22/22 checks, host exit 0**, including the exact retained pilasters and attached reverse-light ownership/hiding. The planned larger slab clusters and final gameplay/room coverage remain pending. Floor fragment/erosion scale, foreground visibility and wall patina are the remaining principal art differences.

### Iteration 105217

[Independent review](../evidence/chamber-qa/iteration-105217/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-105217/comparison.png) inspect the saved larger slab addition. Defining front/reverse architecture remains coherent with no new structural defect apparent. The slabs are still subdued in the actual light; the foreground broken-plate hierarchy, reverse side-service visibility and clean wall finish remain material differences from the references. **Chamber visual parity remains incomplete.** Fresh final-scene functional coverage is separate and pending.

The [105657 full-room rerun](../evidence/chamber-qa/runtime-105657/INDEPENDENT_REVIEW.md) now passes **28/28 checks, host exit 0** after the slab import. All six original captures were independently decoded, hash-verified and visually inspected. Exact original 84-actor/21-mesh assertions are retained, with the cutaway's deliberate mesh reuse separately recorded. This precedes the final patina/foreground-light refinement and establishes geometry/playable framing, not final appearance or physical-device behavior.

### Iteration 110142

[Independent review](../evidence/chamber-qa/iteration-110142/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-110142/comparison.png) confirm improved foreground visibility and wall ageing without restoring the stripe/fog-bar defects. Ground fracture/debris morphology remains weaker than the concepts. The [reverse-service diagnosis](../evidence/chamber-qa/reverse-services-diagnosis/DIAGNOSIS.md) identifies both clipping at the architectural camera edges and insufficient local illumination. A bounded physical ground revision and service/framing trial remain under review; exact chamber parity is not accepted.

### Iteration 111910

[Independent failure review](../evidence/chamber-qa/iteration-111910/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-111910/comparison.png) record black polygonal cells in the first crust-bank engine import. This is a visible asset defect and keeps the render unaccepted. Reverse FOV70 and local service accents improve equipment visibility, but do not close the ground failure. The artist is preparing separately named V2 assets with explicit normal-orientation validation; the audit now requires the exact V2 frozen manifest/mesh names with unchanged five placement and ground-height checks. Original source and failed evidence remain preserved.

### Iteration 113224

[Independent review](../evidence/chamber-qa/iteration-113224/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/iteration-113224/comparison.png) confirm the Crust V2 repair closes the black-cell artifact in both engine views. The integrator reports a related defect in the active loose-slab source and is auditing the broad fields before final readback. Their prior import receipts are preserved. Final visual acceptance and current-scene runtime/native-motion evidence remain pending; do not treat the Crust-only repair as completion of all ground validation.

### Final 114712, runtime 114820/114928 and native 115126

The [final independent review](../evidence/chamber-qa/final/INDEPENDENT_REVIEW.md) and [comparison](../evidence/chamber-qa/final/comparison.png) inspect both actual saved originals after all three field meshes, the loose-slab mesh and both crust banks were rebound to separately preserved V2 exports. The missing/back-facing cap defect is no longer apparent. The defining front door, opposite service wall, side equipment and worn concrete are established, with the remaining ground/lighting differences explicitly retained.

The final chamber audit passes **28/28**, and the final full-room audit passes **28/28**, both with host exit0. Independent QA matched the detailed receipt hash, checked all 60 cutaway samples and V2 saved identities, and hash-verified/decoded/visually inspected all six gameplay PNGs. The [verification record](../evidence/chamber-qa/final/verification.json) records this coverage and the preservation receipt's scope.

The native movie was independently hash-verified and all 572 frames decoded; 39 samples with exact timestamps and five selected full-resolution frames were visually inspected. It shows active combat and ends in **player loss** with a living boss. It does not prove a new successful boss collapse or settled boss-defeat hold. The report preserves that outcome, the automated-input limitation and the lack of audio/physical-device verification. Exact visual parity is not accepted by these functional results.

## Narrow saved-chamber verification

The separate [readonly chamber harness](../evidence/chamber-qa/verify_chamber_runtime.py) is ready for the integrator to run with the existing runner:

```powershell
python tools/run_encounter_test.py evidence/chamber-qa/verify_chamber_runtime.py
```

It checks actual loaded new-geometry ownership, source identity, actor/component NoCollision state and conservative world bounds. It expects the seven static kit placements from the frozen reviewed manifest, exactly one new bulkhead body/wheel, and the 19-component cutaway, including both service-door bays and explicitly permitted reused wall/cube meshes. Floor instance count, labels and mesh identity are derived from the separately frozen floor manifest: five placements using three unique meshes, with unchanged vertical scale. Raised floor additions may occupy the combat interior only as low relief; wall/prop bounds must remain outside the existing combat guard.

The [sparse slab source review](../evidence/chamber-qa/slabs-source-review/INDEPENDENT_REVIEW.md) permits four larger-fragment groups to advance to the saved-engine inspection. Their separately frozen manifest supplies exact labels, mesh identity and placement transforms to three additional runtime checks, preserving the original five-field assertions. The later [crust source review](../evidence/chamber-qa/crust-source-review/INDEPENDENT_REVIEW.md) covers two broad connected-bank meshes in five separately frozen placements, adding three more strict identity/transform/height checks. The final chamber suite requires exact V2 identities for all three surface groups and passes 28/28 in [114820](../evidence/implementation/20261005T114820-verify_chamber_runtime/receipt.json). Neither addition broadens the original source or collision assertions.

The [104810 full-room diagnosis](../evidence/chamber-qa/runtime-104810/DIAGNOSIS.md) preserves a 25/28 failure caused by counting the new cutaway as part of the older 84-actor extension. Its bounded classification repair retains all old count, ownership and bounds thresholds and records the exact allowed mesh reuse separately. The [105657 rerun](../evidence/chamber-qa/runtime-105657/INDEPENDENT_REVIEW.md) closes that classification fault with 28/28 passing checks; its pre-crust timing remains explicit.

The runtime portion observes native cutaway ticking at ordinary startup, external front, internal reverse, both sides of the declared camera threshold and the return to the ordinary camera. It never sets visibility itself. Twelve consecutive samples per staged case record actual camera position/FOV, active component FOV, actor hidden state, environment ticking, light ownership/hiding and collision. Saved gameplay actors are held only within PIE, and no map/assets are saved. The [103051 review](../evidence/chamber-qa/runtime-103051/INDEPENDENT_REVIEW.md) closes the preserved first-run harness FOV fault. The [104516 review](../evidence/chamber-qa/runtime-104516/INDEPENDENT_REVIEW.md) passes **22/22 checks, host exit 0**, covering subsequent exact pier replacements and attached reverse light. It precedes the planned sparse slab addition. These bounded checks complement the existing room suite and do not establish visual parity.
