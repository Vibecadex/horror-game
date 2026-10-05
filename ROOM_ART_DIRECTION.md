# Teddy Encounter — full chamber art direction

Prepared for the user's request to “build out the full room” with an expert team, 5 October 2026. This is the room-design recommendation; the root agent owns implementation, engine sessions and shared assets. It extends the current playable encounter without changing its controls, combat or collision envelope.

## Intended room

Build a disused industrial containment and pumping chamber: heavy concrete retaining structure, damp lower walls, corroded service steel, recessed maintenance bays, closed access doors and overhead utility runs. The arena should feel embedded in a larger facility. No functioning machinery, new interaction or new traversal route is required.

The industrial purpose is a design proposal, not a fact recoverable from the video. The inspected original frames at seconds 5, 10 and 16 establish the cool localized light, dark worn floor, restrained red edge glows and grounded subjects. They do not reveal a complete room plan. Preserve those relationships when adding architecture.

The repaired current frame has useful subject size, grounding and darkness. Its missing room character is mostly the empty periphery, simple exposed boundary and recurring slab lines. Do not brighten the whole floor to show new assets. Architecture should become legible as the player moves toward it or the existing camera widens.

## Coordinates and protected space

All dimensions below are centimetres. +X is the far/background direction; the camera sits toward −X and looks toward +X. ±Y are the two sides. Ground surface is approximately Z=0. Existing combat bounds are roughly X=−1400..1480, Y=−1500..1500.

Keep that playable footprint clear and retain existing collision tests. New solid walls, cabinets, pipes and debris must sit outside the existing inner collision faces; do not silently narrow the ring around the boss. Integrate the visual shell around existing blockers rather than duplicating competing collision surfaces. Decorative meshes should normally have no collision. Keep the existing floor collision and NavMesh behavior unchanged.

Use a separate owned `/Game/TeddyEncounter/Room` asset namespace and consistent `TE_Room_` actor labels with encounter ownership tags. Re-running the room builder must update only its explicitly owned actors/materials, not sweep away other `TE_` actors or regenerate the encounter.

## Concrete layout

| Zone | Placement and scale | Visual job |
|---|---|---|
| Far retaining wall | Inner face X≈1660; spans Y=−1750..1750; Z=0..800; thickness 100–150 | Establish a heavy enclosed room behind the fight. Give its base a dark 80cm plinth and an upper ledge. |
| Sealed service door | Far wall near Y=+180; opening about 430 wide × 550 high; shallow recessed frame | Main architectural landmark. Closed double steel leaves, restrained seams, worn lower kick plates; no luminous central signage. |
| Left service wall | Inner face Y≈−1680; X=−1350..1660; height 650–800 | Pipe/rack side. Three structural bays at unequal visible intervals; a few long horizontal runs make this side distinct. |
| Right service wall | Inner face Y≈+1680; same span/height | Electrical/service side. Recessed cabinets, cable trays, one shuttered niche; avoid mirroring the pipe side. |
| Far corners | Around (1500, ±1550), outside existing blockers; vertical service stacks | Break the square silhouette using boxed risers, elbow pipes and wall recesses. No protrusion into the playable area. |
| Foreground boundary | Around X≈−1540, spanning ±Y; visible height 40–70 | A deliberate camera cutaway: broken sill, shallow threshold, drains and short footing sections suggest the missing wall. Keep the actual existing blocker separate. |
| Side drainage | Immediately outside the inner bounds near Y≈±1560; width 35–50; dark recessed strip | Ground the walls and hide the visual join. Use a few discontinuous grates rather than another repetitive stripe across the centre. |
| Far utility strip | X≈1530..1620, behind playable limit | Low conduit curb, sparse sediment/debris and a few bolts; unifies the large wall with the floor. |
| Upper structure | Perimeter brackets and short ledges at Z≈750..950 | Suggest weight and a ceiling beyond the view. Keep the central camera-to-arena volume open. |

Suggested bay landmarks: left wall near X=−850, +100, +1100; right wall near X=−1050, +450, +1250. Use consistent structural sizes but vary the infill. Put most detail in two clusters, not at every wall metre. A cluster might contain one cabinet, one short cable loop, one wall patch and scattered sediment. Avoid rows of identical crates, barrels or bright hazard stripes.

Build bevelled or chamfered edges where highlights matter: door jamb, cabinet corner, pipe collar and wall footing. Large smooth blocks with small dark details attached still read as primitives. Prefer a small reusable mesh kit with credible thickness and layered assembly over many arbitrary boxes.

## Camera-safe construction

Retain the current −46° pitch, 48° FOV and adaptive pair framing. Its height ranges from 1700 to 5600, and it can reveal much more room during diagonal separations. Do not retune this camera simply to hide unfinished walls.

The foreground wall is the principal occlusion risk. A normal-height wall at −X sits between the camera and the fight; treat it as a cutaway in the gameplay view. Its low visible sill must still be checked against actors at X≈−1300. A complete roof slab at Z≈900–1400 would intercept camera rays and hide the entire encounter. Do not add one over the central playing area. Express the ceiling through perimeter returns, side brackets and far-wall upper structure. Avoid diagonal braces and hanging pipes crossing the centre of the screen.

High structures on the far wall can remain complete because they sit behind the targets. Side-wall components must remain outside Y±1500, including elbow pipes and cabinet doors. Use shadows and recess depth to suggest peripheral complexity, not foreground occluders or invisible collision traps.

At the widest camera settings, the outer environment must remain coherent: no raw floor edge, unsupported wall end or bright exterior void. Use dark backing surfaces and continuous low ground beyond the shell. These surfaces should remain visually subordinate and should not change play boundaries.

## Materials and surface hierarchy

Use four restrained material families:

1. **Concrete structure:** desaturated charcoal/grey with mild warm mineral variation before lighting. Roughness mostly 0.82–0.95; subdued broad staining and finer aggregate. Do not bake saturated teal into every material. Lower-wall water marks and vertical leakage should follow gravity and joints.
2. **Painted service steel:** nearly black, worn desaturated green-grey. Roughness roughly 0.55–0.8 with small chipped edges. Let exposed steel catch a narrow highlight; avoid glossy plastic panels and uniformly bright edge wear.
3. **Pipework and grates:** dark oxidised metal, roughness 0.65–0.9. Flanges, collars and elbows should communicate assembly. Rust is muted brown, not a large orange accent competing with the lights.
4. **Ground wear:** retain the repaired floor as the base. Add sparse shallow stains, sediment at wall feet, restrained patches and occasional irregular seams. No new high-contrast cellular noise, evenly repeated tiles or large wet mirror across the combat area.

Macro wear must be non-uniform: damp corners, lower-wall tide marks, cleaner swept paths near the sealed door and darker drainage margins. Keep small detail low contrast at gameplay distance. Put larger cracks/patch boundaries toward the sides; the player's silhouette and pale aiming line must remain readable over the centre.

Do not modify the original teddy, imported source art, starter assets or historical native project. The room pass is not another creature redesign.

## Lighting and haze

Preserve manual exposure +3.8 EV and current subject lighting initially; diagnose the added geometry before changing exposure. The pale teddy remains the strongest broad lit form, weapon effects the brightest brief accents, and perimeter practicals small subordinate points.

Use one dominant cool overhead pool around the encounter, with a weaker side/back contribution. Architecture should receive scraps of this light: the door jamb, a pipe shoulder, cabinet edges and the wet wall foot. Do not add a bright point light to every new bay. If a surface is unreadable, first move or angle the fixture or alter local roughness; do not raise global ambient fill.

Keep only two or three visible red practical clusters in any normal frame, around the far sides rather than the centre. Practical emissive faces should be narrow slits or small bulbs, not saturated panels. Their light radius should illuminate a nearby bracket or patch of concrete and die before reaching the combat centre. A door indicator can be dark or barely emissive.

Retain moderate low teal haze and clear nearby ground contact. Avoid making architecture disappear into uniform blue fog or filling the entire room with a luminous volume. A subtle cool shaft can indicate an unseen broken ceiling fixture, but it must not mask aiming, the attack warning or crawler silhouettes. Assess haze from the foreground and both corners, not just the starting pose.

## Recommended build and review order

1. Add the owned shell, sealed door and camera-safe cutaway; keep current light values. Render initial, far-edge and opposite-corner gameplay views. Repair occlusion before details.
2. Add two distinct service clusters, drains and structural thickness. Render again to check that the room reads without becoming busy.
3. Apply restrained material variation and surface wear, then tune local light/spill against the original three frames. Preserve the repaired floor's subtlety.
4. Run the existing camera, key-route and gameplay edge checks. Record a short input-driven orbit/movement sequence with normal HUD and a few representative clean stills.

## Acceptance for the full-room pass

- Initial gameplay still prioritizes the teddy/player/light pool. Wide and edge views reveal a coherent chamber with far access, distinct service sides, believable joins and no exposed empty-world edges.
- All twelve established conservative camera cases remain visible; new geometry does not obscure either actor, attack warning or projectiles. Review actual captures as well as projected bounds.
- No new solid prop occupies the protected movement footprint; existing wall collision, movement, evasion, aiming, defeat, pause and restart remain intact.
- Room boundaries are less regular in appearance without becoming noisy. Wall thickness, recesses, pipe fittings and grounding shadows prevent a collection-of-boxes appearance.
- Red remains restrained; haze preserves contact; surface detail supports scale without repeating conspicuously. Compare directly against original seconds 5, 10 and 16.
- Save/reopen verifies owned scene changes. Keep construction completion, runtime verification, visual fidelity and user acceptance distinct.

Reference inspection: `evidence/independent-qa/20261005T034938Z/derived/original-gameplay-05.png`, `original-gameplay-10.png`, `original-gameplay-16.png`; current baseline: `evidence/implementation/20261005T044114-verify_encounter_repair/01-initial-composition.png`. No engine session or asset mutation was performed to produce this brief.
