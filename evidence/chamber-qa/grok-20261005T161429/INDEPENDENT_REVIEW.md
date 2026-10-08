# Independent review — V4 floor recovery

Reviewed 5 October 2026 by the separate Codex QA reviewer. Candidate: Grok's uncommitted V4 recovery over `efce679`, captured at `20261005T161429`. Grok retains sole implementation ownership. This reviewer read source/receipts and inspected images; no Unreal, Blender, implementation script or Git mutation was run. Only this report was written.

**Verdict: an improvement over V3, but not chamber parity.** Concrete grain, damp mottling and floor-to-perimeter continuity have recovered. The dominant remaining floor defect is a flat, high-contrast polygon mosaic. It needs physically legible chipped margins and coherent surface variation, not more uniform texture detail or another lighting adjustment.

## Evidence inspected

- Current native [front](../../implementation/20261005T161429-capture_chamber_views/01-chamber-front.png), [reverse](../../implementation/20261005T161429-capture_chamber_views/02-chamber-reverse.png) and [ordinary camera hold](../../implementation/20261005T161429-capture_chamber_views/03-ordinary-gameplay.png).
- User-selected [front target](../../../study/visuals/chamber-target-front.png) and [reverse target](../../../study/visuals/chamber-target-reverse.png), with the previously reviewed 13:34 V3 and 11:47 handoff images retained as comparison history.
- [Capture receipt](../../implementation/20261005T161429-capture_chamber_views/receipt.json) and [host result](../../implementation/20261005T161429-capture_chamber_views/host-result.json): passed, host exit 0. All three current PNG hashes and the capture-script hash match the records.
- All three images are native 1920×1280. Architecture poses/FOV remain the same disclosed front/reverse cameras. The held ordinary camera remains pitch −46°, FOV 54. Postprocess readback is exactly equal to the 13:34 receipt: manual exposure bias about 3.8, vignette 0.38 and bloom 0.25.

## Rendered judgment

The former smooth V3 sheet no longer dominates. The older-floor border is substantially less obvious, particularly along the near edge and the reverse-wall contact. Damp/color variation and concrete grain make the material legible again. These are useful gains to retain.

Across the front foreground, lower left and the band to the player's right, the floor now shows groups of flat dark triangles and polygons divided by thin bright/dark lines. They read as colored tessellation or inset tile patches. The same pattern remains prominent in ordinary gameplay framing, so it is not a comparison-camera artifact. Most edges do not communicate broken thickness; fragments rarely separate through small contact shadows or irregular exposed rims.

The target instead has uneven, connected cracks and plate loss, chipped aggregate margins, varied grounded fragments, damp masses crossing plate boundaries and quieter surviving areas. V4 has brought back texture variation without yet supplying that erosion structure. Do not equate the increased number of plates with reference fidelity.

Lighting and architecture remain the previously identified later gaps: weak overhead suspended haze, dark service-bay interiors, regular wall construction and inconsistent red-fixture emphasis. Keep them fixed during the next floor correction so the result can be assessed.

## Source causes and recommended correction

1. **Internal broken edges are flattened by the perimeter fade.** In `tools/make_chamber_floor_recovery.py`, `outer_segments` includes every one-owner edge, including edges around omitted cells. `edge_fade()` reduces height toward slab base over 0.7 m from all those edges. It therefore removes relief around the very erosion bites that should reveal depth. Recess faces sit at local 4.2 mm and slab bases at 5 mm; a fully faded internal rim approaches only 0.8 mm of difference. At zero fade, the inner top reaches base while the outer ring remains clamped to base + 0.4 mm, reversing the small bevel slope. Restrict the smooth edge transition to the actual outside perimeter and keep intentional low relief at internal broken margins.

2. **Per-cell material identity makes the mosaic conspicuous.** Near the erosion paths, 55% of kept cells receive `ConcreteDark`; its material factor is 0.64 versus 0.82 for `Concrete`. The categorical difference aligns exactly to the procedural cell borders. Reduce this segmentation and let coherent world-space damp/age variation cross cell boundaries. Reserve strong darkness for exposed recess/contact and sparse material change. Keep the recovered aggregate/dry-mask treatment.

3. **Use edge breakup and grounded fragments to reveal thickness.** The source now records 598 plates, 22 recess bites and 36 fragments; median plate area is 0.902 m², maximum 8.119 m², with height limited to 3.6 cm and no collision. Those counts alone cannot make the break believable. Interrupt straight split edges with localized chipped outlines, show varied exposed aggregate rims, and place fragments where material was lost. Preserve quiet zones and the original walk floor.

4. **Normal blend is not normal strength.** `normal_mix: 0.28` is a linear blend of 72% full `T_AI_Floor_Normal` and 28% diffuse-derived bump, rather than 28% total normal intensity. If a uniform hairline web or over-sharp grain reappears, add an explicit normal-strength control rather than confusing that mixture with amplitude. The current roughness is spatial again (main concrete about 0.40–0.93), which addresses a real V3 failure and should be retained.

## Source safety and validation observations

- Nominal slab winding is consistent for a counterclockwise input polygon: top points upward, reversed lower polygon downward, and the side/bevel ordering is outward. However, `Geometry.polygon()` duplicates vertices for each surface. Slab tops, side quads and bottoms are disconnected components rather than a welded shell. Recalculating normals and checking FBX dimensions/triangle counts is not proof of watertightness or final exported normal directions. Add explicit source/export normal checks before claiming those properties; no pervasive black-face failure is established by these three images.
- The floor uses a new `FloorRecoveryV4` source directory, `FloorRecovery` engine mesh namespace and new `FloorRecover` materials. V2 and V3 are hidden/preserved. The manifest's current generator hash matches. The import receipt reports the new actor at (40, 0, −5), scale Z 1, no collision, with bounds approximately X −1699 to 1688, Y −1522 to 1522 and Z −4.86 to −1.40 cm. Bounds reach the intended drainage region, but an AABB alone cannot prove exact polygon/grate clearance at every corner.
- Material creation uses the existing ownership-checked helper. Mesh import still sets `replace_existing=True` before checking an existing destination asset's ownership, and actor reuse retags a matching label before checking its current ownership. The initial destination is new, so this review does not establish an actual overwrite, but add explicit ownership checks before either reuse path to make later reruns safe.
- `tools/apply_chamber_lighting.py` changed only by excluding `ChamberRecoveryOwned` from the wall-light channel reassignment. The settings diff adds V4 material parameters/revision without changing light/fog/exposure values, and the recovery importer contains no lighting writes. Its `lighting_unchanged: true` field is a declaration rather than a before/after light snapshot; include frozen light readback with the eventual final candidate.
- The V4 checker adds exact recovery identity/transform/perimeter checks and changes the retained V3 visibility expectation to hidden. This is consistent with the declared source replacement. **At this review snapshot only the new capture receipt was complete; no new 34-check chamber or 28-check room run was present.** The earlier V3 runtime passes must not be relabeled as V4 verification.
- Fresh motion, physical-device input, audio and final package-hash binding are still outside this evidence. Do not claim them from held plates or the importer's success flag.

## Next review condition

Continue one bounded floor revision: preserve the recovered material/perimeter improvements, remove categorical mosaic contrast, and keep actual chipped relief around internal erosion rather than fading it away. Keep lights, exposure, camera and characters fixed. Then produce the same three native plates and fresh saved-world/runtime receipts. Visual parity and user acceptance remain open.
