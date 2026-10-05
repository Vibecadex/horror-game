# Selected-reference parity: production art direction

5 October 2026. The user's selected visual target is [direction-close-best.jpg](visuals/direction-close-best.jpg). The asset inventory for the four-panel expansion is [FULL_ASSET_LIST.md](FULL_ASSET_LIST.md). This is an art-direction image, not a runtime capture. Its selection supersedes the darker numerical targets in `VISUAL_FIDELITY.md` and `AI_FIDELITY.md`. The original video continues to inform moving combat; the selected image determines this lighting/material pass.

**Latest review, 09:14 UTC:** the broader room-case suite exposes a real rear-centre player-readability gap in case03 that the six delivery plates did not cover. A local character-only fill is warranted before claiming room-wide visual readability; passing collision/framing checks do not resolve it. Preserve the matched crown colour, floorwear12, source shape/falloff2, camera, key, pool and FloorV3. The fog-shape defects remain resolved, but upper haze, grouped wear and seam profile retain reference differences. The proposed local repair and its explicit visual check are recorded at the end; moving evidence and user acceptance remain separate gates.

Inspected against the actual saved-game gallery: [initial gameplay](../evidence/implementation/20261005T054732-capture_room_gallery/01-gameplay-initial.png), [wide gameplay](../evidence/implementation/20261005T054732-capture_room_gallery/02-gameplay-wide.png), and [architectural overview](../evidence/implementation/20261005T054732-capture_room_gallery/03-architecture-overview.png). Current state and source anchors were checked in `WORK_STATUS.md`, `ROOM_ART_DIRECTION.md`, the adapted asset manifests, and the authoring scripts. No Unreal session or asset edit was performed for this brief. The integration owner controls shared assets.

## What must read first

A heavy stitched plush creature stands in a dirty pool of overhead teal light. Its black contact shadow gives it weight. A small armed human is readable because of a tight, almost-white light on the ground beside/in front of them. The floor carries fracture, dampness and debris at believable scales. The upper room dissolves into teal haze and black structure, punctuated by tiny red practicals.

The current shot already has useful diagonal blocking and grounded subjects. Its largest failures are a dim, nearly uniform floor; no distinct player pool; a pale stone-like teddy; and enormous graphic crack/stain shapes. Fix those before adding architecture or adjusting the camera. Current wide shots expose bright regular wall trim and a miniature stage-like perimeter; the completed extension must retain its existing room logic while allowing darkness and haze to break that outline.

## Observed image versus proposed extension

| Directly visible in the selected image | Full-room production decision, inferred rather than recovered |
| --- | --- |
| Boss upper-left, player lower-right, small threats near the periphery. Elevated oblique camera. | Preserve adaptive pair framing and circulating gameplay. Maintain similar subject scale at comparable separation; do not lock the game to this pose. |
| Teal light is strongest through the upper-middle floor and falls away toward the borders. Upper haze is clearly brighter than black corners. | One dominant stationary overhead source governs the chamber. Weak service pools support traversal at the edges without becoming a second evenly lit arena. |
| Boss crown is dirty olive/taupe fabric; a dark seam and individual stitches cross it. Deep torso/limb shadows remain. | Use the existing teddy, skeleton and clips. Extend a restrained sewn construction language over other visible surfaces without inventing a new monster. |
| Floor has irregular fine cracks, worn pale areas, darker damp patches, and raised fragments with shadows. | Dry abrasion through travelled central ground; damp margins at drains; broken concrete concentrated around wall feet and two asymmetric damaged bays. |
| Red marks are tiny and distant; architecture is only partially legible. | Retain the current industrial containment/pump room, bulkhead and service kit. Its function is an established design extension, not something proven by this image. |
| A white ground hotspot sits near the player's weapon-facing side; player is mostly a dark silhouette. | Attach a short downward-forward light to the player's aim. Its footprint travels and rotates smoothly with aim; no full-character white fill. The still alone cannot prove the original light's attachment. |
| Strong dark cast shadows extend toward the lower part of the picture. | Preserve world-space shadow direction and contact as actors move. Do not paint a fixed shadow or light into a texture to reproduce the still. |

## Value, colour and light masks

Treat this as four spatial masks: **lit action ground**, **upper haze**, **dark perimeter**, **small player hotspot**. Their locations and relationships matter more than an image-wide score. Build them with the saved game's lighting/materials; a post-process vignette cannot substitute for room depth.

Fresh measurements from the two 1280×720 images use encoded RGB and `Y = .2126R + .7152G + .0722B`; they are image diagnostics, not physical light units. Pixel coordinates below are fixed comparison rectangles for the matching initial view. They must be reselected on moving/wide views to represent the same kind of surface, not copied onto unrelated pixels.

| Region `(x0,y0)-(x1,y1)` | Selected median Y | Current median Y | Interpretation |
| --- | ---: | ---: | --- |
| Lit floor between subjects `(550,250)-(735,400)` | 147.6 | 35.1 | Central ground needs a large increase in local illumination/material readability. |
| Foreground worn ground `(430,570)-(700,650)` | 73.5 | 35.0 | Foreground receives less light than centre, with visible abrasion. |
| Upper haze `(470,25)-(760,115)` | 111.7 | 25.6 | Depth must carry a luminous teal veil beyond the action. |
| Upper-left corner `(0,0)-(100,80)` | 0.0 | 19.8 | Brighten the action while darkening this peripheral wash. |
| Upper-right corner `(1180,0)-(1280,80)` | 0.0 | 7.1 | Keep the corner dark and the upper silhouette incomplete. |
| White pool `(746,433)-(811,494)` | 226.2 | 27.9 | A compact neutral hotspot is missing. |

Selected mean RGB is **35.8/63.2/62.7**; current is **8.3/28.9/33.6**. Selected pixels above Y40 cover **58.91%**, current **3.97%**. The old study's 8–16% bright-area band is for a different reference and must not be used to pass this selection. Do not increase exposure until those means match: that would lift the wrong regions. The reference's teal is also less blue than the current cyan wash.

Suggested review bands for a comparable initial frame: centre ground Y110–165, foreground worn ground Y50–95, upper haze Y80–130, unlit upper corner medians below Y8, player hotspot core Y190–245 with a small clipped core acceptable. These broad bands are **necessary directional diagnostics, never sufficient acceptance**. Subjects, shadows, texture and spatial transitions must also match visually. No geometry/light placement may be distorted merely to score inside a rectangle.

Lighting recipe:

1. Keep manual exposure fixed initially. Concentrate the dominant cool key over the upper/middle action ground and make its floor footprint broader and substantially brighter. Retain a sufficiently compact source for an identifiable boss cast shadow. Read the crown and limb edges without whitening the entire body.
2. Reduce broad `TE_Rim`, `TE_PlayerFill`, `TE_FaceFill` and `TE_AmbientFill` influence where they flatten the perimeter. The names do not imply their current settings are correct. The room's four `TE_Room_CornerBounce_*` sources must support edge visibility without filling the initial image uniformly.
3. Use near-neutral or only faintly cool light for the player hotspot, clearly distinct from the teal field. Keep a soft outer roll-off and a small bright centre. At the initial view its visible footprint is approximately one player-height across, offset a little toward the aimed ground. Avoid a circular white aura centred exactly on the capsule or a long theatrical searchlight cone.
4. Tune actual fog scattering and placement to create upper depth. Keep the near floor and foot contacts clear. Far forms lose local contrast gradually: the distant small creature can remain a silhouette while walls recede. Reject a uniform turquoise screen veil, thick ground smoke hiding telegraphs, and obvious spherical fog boundaries.
5. Keep visible red practicals pin-sized: a few pixels wide at 1280×720, with brief local bloom and no large red floor/wall pool. Existing fixtures remain plausible sources. Their exact count in the still is less important than their subordinate area and placement.

## Concrete, wear and physical debris

The reference's floor operates at three scales: broad irregular worn/damp regions, intermediate branching fractures and spalls, and fine aggregate. No one mark should read first as a logo or painted graphic.

- Keep `T_AI_Floor_Color/Normal/Roughness` and `M_QA_Concrete` as available inputs. The current base-colour scale is 0.20, UV 9×7 over the full slab, and roughness is compressed into 0.78–0.96 (`tools/apply_ai_surfaces.py`). Diagnose those in the new light before replacing the whole material. The almost uniformly rough floor currently suppresses the subtle wet/dry response.
- Make dry concrete predominantly rough (starting range 0.75–0.95), with sparse irregular damp areas nearer 0.40–0.65. These are working material ranges, not image-derived measurements. No mirror puddle, metallic concrete, glowing crack or bright white fracture edge. A damp patch is normally darker in base colour; its limited highlight should move with the view/light.
- Reduce/replace the currently conspicuous zigzag crack, lobed stain and flat debris decals. Existing `TE_AI_Decal_01..04` can be reduced, faded and repositioned individually; preserve their source maps. A stain edge must fragment into the base floor. Fractures branch and taper rather than remaining constant-width strips several metres long.
- Use physically small cracks: most ground fissures should be hairline to a few centimetres wide, with occasional wider spalls; do not enlarge every crack to force visibility. At gameplay resolution detail should integrate into worn concrete, with only selected branches visible.
- Add actual low rubble meshes where a raised fragment is visible: varied broken slabs/stone chips about 8–35cm across and 1–7cm high, with a few perimeter pieces 40–70cm across. The dominant chips need irregular silhouettes, bevel/edge variation and contact shadows. Flat painted debris cannot supply that cue.
- Arrange 5–7 unequal clusters along side/far margins, plus two sparse inward spill trails. Dense material stays outside movement bounds; any tiny visual fragments inside are non-colliding. Keep several player-width lanes through the action area. Avoid uniform random confetti or a continuous ring of equal cubes.
- Ground the clusters in the room: broken bits beneath a chipped footing, sediment around a drain, dust caught against a service-bay step. Use `SM_RoomFloorGrate`, existing wall foundations and the room's concrete/oxide families as anchors. Current `TE_Room_FootDebris_*` boxes can be replaced with shaped fragments under the integration owner's control.

## Plush, seams and stitch scale

Keep `Assets/Adapted/Teddy/Teddy_Encounter.blend`, its sixteen-bone rig, six clips and source UV identity. The desired improvement is a sewn, worn textile response with real surface construction. Changing the shading-model name alone will not achieve it.

The existing `Teddy_BaseColor.png` already carries brown/taupe variation. The current material desaturates it by 0.5 and multiplies it by 1.30–1.65, while the strong normal uses UV7.5×6.2. Rebalance this to dirty olive-brown/taupe under teal light, with the underside and seams darker. Stop the pale cyan stone read before adding more noise. Keep the minions darker than the large boss; all should remain recognisable as the same material family.

Add one clear, irregular crown/back-of-head seam where the selected frame has its main sewing feature. It should read as two compressed fabric lips and separate dark thread bridges. A continuous painted black stripe is insufficient; stitching needs relief, tiny shadows and attachment to the deforming surface.

Suggested authoring scale for the current 4.6m boss: thread diameter **1–2cm**, thread crossing length **10–16cm**, stitch interval **8–14cm**, seam lip depth/height **1–3cm**. Use roughly 8–14 visible bridges along the main head seam, varying their angle and tension. These are deliberate monster-toy construction proposals, not recoverable real-world dimensions. At the gameplay crop, target an irregular sequence of around 1–2px thread widths and several-pixel gaps; tune without creating staples as thick as the player's limbs. A secondary seam around an ear or shoulder can support construction but should not compete with the crown.

Pile/weave lives at a much smaller scale: roughly **2–6mm** fine fibre response and **1–2cm** matted clumps. Most individual fibres will be subpixel at gameplay distance; they should combine into soft grazing highlights and broken shading, not sharp stones, giant grooves or sparkling noise. Roughness stays predominantly high. Cloth fuzz is useful if the installed reflected API supports it, but visual response is the acceptance condition. The previous Default Lit fallback was an authoring issue, not proof Cloth is unavailable.

If geometry is added, keep it under the owned adaptation and skin it to the existing skeleton. Head stitches follow the head; shoulder construction follows local deformation. Inspect walk, attack and defeat for detached threads, z-fighting, seam intersections, stretched fabric and loss of foot contact. Preserve original downloads and adapted backups.

## Camera, perimeter and continuous play

Use current −46° pitch / 48° FOV as the first comparison camera; the current diagonal is close enough to isolate art changes. The selected boss is centred near (35%,31%) and player near (66%,65%). Its visible body is approximately 2–3 times the player's screen height, excluding the cast shadow. Treat these as approximate initial-shot checks, not permanent screen positions. Current subjects appear modestly larger; consider a small framing adjustment only after light/material parity is established and recheck all extreme separations.

Retain the existing chamber outside the combat envelope: +X far bulkhead, ±Y service walls, low −X cutaway, open central overhead camera path. The extension uses the completed room kit, not another room rebuild. Let two service clusters emerge when approached; the rest remain partially concealed. Cut the continuous bright pilaster/cornice outline seen in wide images with uneven light and haze. Keep believable wall thickness, footing and dark backing so no empty-world edge appears.

A stationary room key gives geography; the small player pool carries readability through darker areas. Edge support lighting can be dim and local. Do not tether the entire overhead pool or haze to the player merely to keep a still-like spotlight composition. Preserve aiming guide, shot effects and attack warning legibility; make telegraphs restrained without hiding them or changing attack timing/damage.

Moving review must show: walking and dodging across the pool boundary; aiming 180° so the local hotspot rotates; boss crossing light and turning; one attack; player in two side bays; maximum player/boss separation; a return to the original area. Watch for fog popping, light trails, roughness shimmer, texture swimming, sudden exposure shifts, crushed player silhouettes, shadows breaking contact and stitch deformation. The full room must hold up in these transitions, not only six curated camera poses.

## Ordered integration and visual gates

| Priority | Existing source/asset anchor | Concrete gate before advancing |
| --- | --- | --- |
| 1. Establish light/value structure and player pool | `TE_Key`, other `TE_*` lights, `TE_LowMist`, `TE_Room_*` lights; `BP_EncounterPlayer` | Matching initial capture visibly separates bright action ground, dark border, upper haze, black boss shadow and small neutral player pool. Central light can rise while upper corners darken. |
| 2. Remove graphic floor marks and establish multi-scale wear | `M_QA_Concrete`, `T_AI_Floor_*`, `TE_AI_Decal_01..04` | Floor reads as worn concrete at full frame and in a 100% crop. No zigzag ribbon, lobed logo-like stain, tile grid or obvious repeating bright patch. |
| 3. Establish plush identity and real crown sewing | `M_QA_TeddyCloth`, `M_TeddyCloth`, adapted teddy source and rig | Viewer can identify cloth plus separate stitches without zooming beyond 100%; belly remains dark, crown is not pale stone. Same result holds during a turn/attack. |
| 4. Extend wear into real debris and room depth | `/Game/TeddyEncounter/Room`, room kit, foundations/grates/service bays | Three matching gameplay positions have plausible grounded wear and subordinate room structure. No collision loss, repeated cube scatter or bright stage-box outline. |
| 5. Validate continuity and save/reopen | Existing capture/runtime tools; owned encounter map | Fresh initial, two edge and wide captures plus a normal-game movement clip retain the look. Affected input/camera/animation checks pass after saved reload. |

Review the **three largest remaining discrepancies** after each substantial pass. A histogram match, successful material compile, static pose, or passing gameplay checks cannot close the art gate. Compare equal-sized target/runtime frames and the actual gameplay recording, inspect subject/floor crops at 100%, and state unresolved differences plainly. Rendered fidelity, functional evidence, and explicit user acceptance remain separate.

## First integrated render review — 07:08 UTC

Reviewed [look-01 initial gameplay](../evidence/implementation/20261005T070819-capture_room_gallery/01-gameplay-initial.png) against the selected close image. This pass contains lighting/material changes and the player light; new sewing/floor geometry was not yet integrated. The [expanded concept](visuals/parity-expanded-reference.png) usefully describes room continuity and material construction, while the original close remains the primary grading target.

The cast shadow and local player light now establish the right structure, but the dominant pool covers nearly the entire floor and is too bright. Measured central floor Y195 versus selected Y148, foreground Y148 versus Y74, and right-side ground `(930,470)-(1080,560)` Y168 versus Y53. Upper haze is already near the target at Y118 versus Y112. Its colour is too green: median RGB65/134/118 versus63/125/124. The upper-left corner remains lifted at Y26 versus0. The player hotspot core is already correctly bright at about Y230; its footprint is roughly twice the desired width.

Recommended **next trial**, not a claim of verified settings:

- Key 350,000→about130,000cd; inner/outer cones28°/49°→22°/40°. Shift aim target X−300→about+100, Y0, to keep the dominant light between subjects and reduce foreground spill. Intensity reduction alone cannot recover the target distribution.
- Move key lateral position Y240→0–80. The current boss shadow is displaced too far left; the reference points mostly downward with a slight left component. Hold source height for this trial; if the shadow remains too long after framing correction, raise Z1400→about1600 rather than flattening it with fill.
- Trial key colour `(0.50,0.94,1.0)`, far-fog emissive `(0.009,0.040,0.040)`, and fog albedo around `(0.42,0.76,0.76)` to reduce the green bias. Leave fog densities initially unchanged. Its upper brightness already works; dimming or thickening all fog would solve the wrong problem.
- Keep player-light intensity initially. Narrow outer cone39°→24–27°, inner24°→14–16°, so the player stays a silhouette beside a small ground pool. The gallery player currently aims toward the foreground, which explains the pool below them; inspect the staged aim-toward-boss capture before changing attachment position. Do not reposition the light to a fixed screen coordinate.
- FOV48°→54° is a reasonable small composition correction now: it should reduce current subject sizes and move their centres closer to the selected initial frame. Keep pitch/tracking unchanged and check the saved-game extreme separations later.

The next capture must show that localisation darkens the foreground/borders while keeping upper haze and player hotspot readable. Fabric still needs the actual seam geometry and floor still needs the planned wear/debris; do not interpret their absence in this intermediate pass as a reason to raise light again.

## Second integrated render review — 07:17 UTC

Reviewed [look-02 matched gameplay](../evidence/implementation/20261005T071701-capture_parity_look/01-matched-gameplay.png), with FOV54, aim staged toward the boss, physical floor dressing and new crown sewing. Character scale/composition, dominant ground shadow and player pool are materially closer. Keep this camera. Neither the new geometry nor this review establishes final visual parity.

| Matching region | Selected median Y | Look-02 median Y | Remaining issue |
| --- | ---: | ---: | --- |
| Central floor | 147.6 | 108.4 | Local lit action ground still needs brighter worn regions. |
| Foreground worn ground | 73.5 | 64.7 | Mean is close, but target spatial standard deviation21.8 versus7.6: current surface is smooth/cloudy. |
| Upper haze | 111.7 | 49.6 | Far depth is much too dark; top centre ends in a dark band. |
| Upper-left / upper-right corners | 0 / 0 | 0.1 / 0 | Correct: retain these dark corners. |
| Player hotspot | 226.2 | 226.1 | Correct core value and near-correct footprint. |
| Crown `(428,155)-(477,194)` | 82.4 | 43.2 | Fabric/sewing visibility is suppressed. Pose/detail differences make this an indicative comparison. |
| Right-side floor | 52.5 | 54.3 | Already close: avoid lifting this edge globally. |
| Bottom strip `(520,675)-(755,719)` | 46.7 | 63.5 | Light should fall off more before the near boundary. |

Look-02 bright area above Y40 is56.8%, close to the selected58.9%, yet haze, central floor and surface structure still differ. This is an explicit example of why an image-wide threshold cannot pass the shot.

Priority corrections for the next trial:

1. **Recover upper depth separately from floor brightness.** Leave camera, key aim/cones and global fog density in place. Try key130k→175–190kcd and local far-fog emission from `(0.009,0.040,0.040)` to roughly `(0.018,0.075,0.075)`, checking the volume's actual bounds cover top-centre behind the boss. These are working trials; the final settings are whichever reproduce the visible mask. The upper veil needs to brighten without fogging the near feet, right floor or black corners. If the volume does not reach the required region, move/reshape it before adding density. Target a continuous upper teal glow with gradual lateral loss, not an obvious emissive fog ball. Current central colour74/117/122 is slightly bluer than selected112/157/156; a small blue reduction can follow the luminance correction rather than changing saturation blindly.
2. **Add the missing intermediate floor structure.** Current concrete reads as fine cloudy noise with isolated thin line drawings and pin-sized grit. Preserve the base maps, but add irregular abrasion/damp masks at approximately50–150cm scale with stronger colour variation and corresponding roughness. Keep broad dry worn patches near the inter-subject floor and foreground; include sparse darker damp patches with broken edges. Move a `SM_ParityFractureField_A` instance into the foreground-centre where its actual lifted lips and patch variation can read. Do not simply add more uniform hairlines or high-frequency normal noise. The new geometry must integrate into the substrate rather than remain isolated dark outlines on smooth paint.
3. **Make physical chips readable at the right scale.** Current imported aggregate values0.09–0.14 are much darker than the lit floor, so most chips read as black specks. Bring their top-face value nearer the adjacent concrete, preserving dark side/contact faces. Add a few30–60cm fragments among the smaller pieces, and bring selected edge clusters slightly inward along side margins so they appear in the matched camera. Do not scale every cluster uniformly or blanket the centre. Reference wear contains both flat spalls and raised fragments; distinguish those silhouettes.
4. **Lift crown visibility before remaking the seam.** After the modest key increase, trial cloth base scale0.36→0.48–0.52 if needed. Retain the dark underside and dirty olive/taupe palette; avoid reverting to the pale cyan body. The visible crown currently reads smooth and the sewing reads mainly as a thin ink line. Review at100% for separate crossing bridges, seam relief and fabric breakup after the light lift. The selected seam traverses the crown; the current pose shows a longer diagonal/vertical line, so inspect attachment/orientation in model space if lighting alone cannot reveal the intended crossing construction. Do not enlarge all threads to compensate for a dark surface.

Secondary adjustments only after those comparisons:

- Source radius30→about65–80cm can soften the current razor-edged cast shadow while retaining black ground contact. Its end reaches abouty500 versus selectedy478; moving keyX900→about800 can shorten it without changing camera. Re-evaluate illumination after moving the source rather than stacking unmeasured intensity changes.
- Player hotspot now has the right value and size but a broad flat white centre. First let the improved floor introduce texture, then try inner cone15°→about9° with outer26° retained if the disc-like plateau persists. Keep the light tied to aim and inspect motion.
- No tiny red practicals or convincing side-wall hints appear in this held frame. Once haze works, place or adjust two plausible existing housing/fixture accents so a few pixels show at the far upper sides. Keep local spill weak and preserve dark wall tops. This should reveal the room's depth, not draw a bright rectangular border.

Next art gate: brighter upper haze and central abrasion, legible crown cloth/sewing, and physical side/foreground fragments must appear **together**, while the near-right ground, corners and player hotspot retain their present useful values. Follow the held plate with edge and moving views before calling the room coherent.

## Third integrated render review — 07:28 UTC

Reviewed [look-03 matched gameplay](../evidence/implementation/20261005T072829-capture_parity_look/01-matched-gameplay.png). FOV54, key165kcd/source radius70, detailed diffuse with aligned runtime bump, revised floor placements and cloth scale0.48 improve the result. Keep camera and key intensity for the next focused pass.

Fresh diagnostics: central floor Y116.5 versus target147.6; foreground73.8 versus73.5; upper haze57.9 versus111.7; right floor48.5 versus52.5; crown62.2 versus82.4; player pool210.9 versus226.2. Both upper corners remain black. Player-pool texture now varies naturally instead of forming a flat white disc, and the softer boss shadow has better weight. Floor contrast improved, but its grain is now spread too uniformly; the scene risks reading as granular gravel rather than worn concrete with distinct abrasion patches.

The upper haze remains the largest gap. Doubling emission in the same volume moved its measured value only from49.6 to57.9, so repeated intensity changes alone are a poor next step. The integrator's focused trial moves far fog from `(1050,-200,370)` / scale `(2.6,2.2,1.5)` to `(1400,0,650)` / scale `(2.4,3,2)`, with emission `(0.045,0.20,0.20)`. Judge whether it actually intersects the upper viewing rays, recedes the far crawler and fills the space behind the crown. Stop increasing it if it becomes a flat glowing slab or washes the near contacts. The original close wants illuminated depth with variation, not a turquoise upper-screen card.

The proposed floor adjustment—70% detailed colour with30% of the earlier soft colour, plus bump strength2.8→1.8—is a sensible reduction of the uniform grit. Preserve hairline fractures, larger spalls and physical fragment silhouettes. The remaining central-floor brightness should come from a few broader worn islands between the subjects, with irregular edges and consistent roughness, while the already-correct foreground/right edge stay near their present values. Do not raise all ground albedo or global exposure.

Cloth should retain the existing0.48 base scale through the corrected crown-seam import. The proposed small UV-anchored colour grain and blue tint increase0.60→0.76 can restore textile breakup and dirty taupe instead of olive mud. Inspect it at100% and in motion: fine grain must not sparkle or crawl. The new crossing seam should provide the main readable construction cue; further brightening or oversized normal response cannot replace it.

Small warning posts near the upper and side margins are an inferred room extension. Use dark grounded housings, lens widths around2–5px in the matched1280 frame and weak local spill. Their purpose is sparse depth punctuation. Keep the lights out of the movement collision path and avoid large red pools or a continuous row. Existing far-wall fixtures atX1615 are outside this camera and cannot establish the selected composition by remaining invisible.

Focused next comparison: upper haze, corrected crown sewing and calmer floor grain. If those settle, proceed to the wide/edge/moving review instead of continuing to tune the held image indefinitely. Detailed fidelity gaps still need to be stated; this iteration is progress, not final parity or user acceptance.

## Read-only comparison of the concurrent surface pass — 07:33 UTC

Compared [07:33 matched gameplay](../evidence/implementation/20261005T073350-capture_parity_look/01-matched-gameplay.png), [our look-03](../evidence/implementation/20261005T072829-capture_parity_look/01-matched-gameplay.png) and the selected close. The integration owner reported an external Grok writer had changed shared materials/player lighting and paused engine writes pending ownership selection. This review changes no shared settings, material or asset. The corrected crown-seamV2 is ready but was not imported in either compared image.

### Recommended combined result

Use Grok's cloth weave/roughness and damp/dry floor mask as retained source inputs, together with our camera, key/cast-shadow balance, physical floor geometry and player-light placement. Combine deliberately in one owned material pass after the writer is selected; do not rerun either broad script over the other as an integration strategy.

| Element | What the fresh pictures show | Best combined choice |
| --- | --- | --- |
| Concrete brightness | Grok central floor Y139.9 is closer to target147.6 than our116.5. Its foreground88.1 is too bright versus target73.5; ours73.8 was close. | Keep its broad tonal/dampness contribution locally, with restrained foreground response. Preserve black corners and the existing key165k/source70. |
| Concrete structure | Grok central standard deviation9.7 is flatter than target18.4 and our17.9. Its surface looks smooth with repeated blot-like stains; our look-03 is too uniformly gritty. | Start from Grok's calmer base and blend back roughly25–35% of our detailed concrete at restrained bump. Keep broken slabs and raised fragments. Use common world-space coordinates so colour, cracks, normal and damp masks agree. Avoid combining two unrelated tiling scales into drifting wear. |
| Wet/dry response | `T_Comfy_Floor_Dry` explicitly distinguishes damp and dry material regions; its roughness mapping spans0.42–0.93. | Retain that control and correlated damp darkening. Break the repeated stain silhouettes with the broader abrasion pattern; do not turn every patch into a high-contrast dark spot. |
| Cloth | Grok crown medianY96.8 versus target82.4; our62.2 was too dim. The newer weave is useful and the warmer neutral colour is closer than olive mud. | Retain `T_Comfy_Cloth_Weave/Normal/Roughness`, Cloth shading and separate darker minion material. Trial its base multiplier1.05→about0.80–0.88, then inspect the corrected seamV2. Preserve our rig, animation and new seam geometry. |
| Player pool | Our hotspot's bright-pixel centroid is(777.8,468.8), almost identical to selected(779.2,467.1). Grok's moves to(729.9,445.7), about50px left and21px up from target. | Restore our attachment transform/cones as the starting placement; retain texture-breaking floor response. Grok's lower/longer spotlight is displaced too far ahead for the selected shot. |
| Pool area | In the same comparison window, pixels aboveY180 occupy target6149, ours4438 and Grok10329. Our spot is slightly small/dim; Grok's is broad and elongated. | Use our location(105,0,170), pitch−80°, outer26°/inner15° as the controlled baseline. After merging floor, consider only a10–15% intensity increase over16000 if the hotspot remains dim. Do not compensate by widening to48°. |
| Far haze | Grok upper hazeY60.0, our57.9, selected111.7. Both remain dark and miss the luminous depth. | Retain the planned independent far-volume placement/coverage investigation. Neither surface pass fixes this. |

The pool measurements use thresholdY180 inside `(650,390)-(835,535)` only, excluding most character geometry; they describe placement/extent in these comparable held frames and are not a general acceptance score. Source parameters were read from `tools/apply_comfy_surfaces.py` and `Assets/Adapted/Parity/Surfaces/provenance.json`; the current mutable settings file is not treated as proof of which graph produced an earlier render.

The new texture provenance records local ComfyUI generation and preserves its source files. Keep both source sets. Cloth weave quality, roughness stability, point-light shadows and the eventual combined material still need an actual moving-game review; neither still establishes temporal behaviour. The best end state is a single integrated look with the chosen strengths, not a wholesale restoration of either competing material pass.

## Combined look-05 and fog diagnosis — 07:51 UTC

Reviewed the [saved combined look-05](../evidence/implementation/20261005T074707-capture_parity_look/01-matched-gameplay.png) with corrected cross-crown seamV2, Comfy weave, restored player pool and35% detailed floor /65% AI base plus dampness. Also reviewed all three [transient fog tests](../evidence/implementation/20261005T075109-diagnose_parity_fog/): luminance05,20 and60. The test script changes emissive fog in PIE only; those three images are diagnostic, not saved-scene acceptance evidence.

The integration owner verified the renderer was enabled and identified the earlier weak result: fog emissive is luminance, and0.2 was too small under the saved exposure. They also verified the volume uses its **maximum scale uniformly**. Earlier nonuniform scale suggestions in this note must therefore not be read as working ellipsoid dimensions; placement, a true uniform radius, and actual rendered coverage govern the next change.

| Diagnostic emission multiplier, RGB ratio0.225:1:1 | Upper haze medianY | Upper-left corner medianY | Visual result |
| --- | ---: | ---: | --- |
| 5 | 61.6 | 3.1 | Perimeter stays dark, but upper depth remains far too dim. |
| 20 | 87.5 | 18.3 | Usable conservative brightness; starts spilling into the left border. |
| 60 | 135.4 | 49.1 | Too bright/flat and clearly washes the left edge. |
| Selected close | 111.7 | 0.0 | Luminous upper-centre wedge with black outer corners. |

**Choose interpolated multiplier35, RGB `(7.875,35,35)`, for the next saved proof**, with the actual uniform radius reduced from3 to roughly2.4–2.5 and, if the viewed footprint is still left-biased, a small worldY+100–200 recentering. These are a combined coverage/value trial, not measured final settings. Preserve haze behind the crown and around the far crawler, retain clear feet, and reject a glowing sphere boundary or upper-screen slab. Choose tested20 as the conservative fallback if the coverage cannot be corrected; do not use60 simply to satisfy the upper rectangle. No global exposure or stronger vignette is needed to conceal the spill.

Near floor, player hotspot and boss contact remain almost unchanged across the sweep. The primary failure at60 is peripheral coverage and flat upper brightness, not disappearance of near contacts. The boss shadow remains extremely dark; its precise black level is less consequential than the now-correct weight/contact and should not trigger another broad fill-light pass.

### Seven-axis review of the combined result

| Axis | Evidence and current judgment | Remaining focused action |
| --- | --- | --- |
| Composition | FOV54, relative scale and diagonal placement are close to the selected frame. | Hold camera/initial scale; verify wide/edge cases. |
| Key and ground shadow | Key165k/source70 produces a grounded dominant silhouette with softer edges. | Hold the key while fixing fog/material structure. Do not chase small pose-dependent shadow-length differences. |
| Upper haze and dark perimeter | Cause is now identified; tested values bracket the required brightness. | Save/render multiplier35 with tighter coverage and check the upper-left border. |
| Player pool/readability | Saved medianY225.9 versus selected226.2, with restored near-matching placement. | Hold placement/intensity; verify it rotates/travels smoothly during normal play. |
| Woven cloth and seams | CrownY82.9 versus82.4; Comfy weave and seamV2 give the intended construction direction. | Hold brightness. Check thread attachment, weave stability and cloth deformation in turn/attack/defeat. |
| Fractured floor and rubble depth | Central floorY138.3 versus147.6 is reasonably close. ForegroundY87.9/standard deviation10.3 versus selected73.5/21.8 is too even and clean between small details. | Move a broken-slab field into lower-centre-left, approximately screenx400–650/y520–680; add one or two irregular darker damp/abrasion boundaries. Preserve clear movement lanes. Do not increase all micro-noise or global floor brightness. |
| Restrained practicals/gameplay effects | Small red posts are present but very dim; aiming line and player pool remain readable in the held frame. | After fog is saved, modestly raise lens emission only if still unreadable; keep red spill weak. Inspect warning, muzzle/impact effects and aiming during the moving encounter. |

The remaining floor change should create larger broken worn areas that the eye can group, not add more tiny detail. It is a concrete discrepancy against the selected ground structure, not a reason to keep changing the camera or already-matched light pool. Finish the focused fog/floor work, then use wide, edge and moving gameplay evidence to decide which axes are actually met. Static art-direction progress, temporal continuity, functional checks and user acceptance remain separate.

## Saved look-06 review — 07:57 UTC

Reviewed [saved look-06](../evidence/implementation/20261005T075756-capture_parity_look/01-matched-gameplay.png): fog multiplier35, actual uniform radius2.45, Y150 centre adjustment, more visible red lenses, foreground fracture-field placement and stronger dampness. The change preserves black upper corners and makes the room direction clearer. **The defining atmosphere and floor axes are not yet at parity.**

Upper haze now measuresY86.1 versus selected111.7, RGB29/101/103 versus63/125/124. The tighter coverage solved the left-corner problem, but also lowered the useful upper-centre contribution. Hold that radius/centre and trial multiplier55–60, while making the emissive ratio less saturated: red fraction approximately0.32–0.38, green1, blue around0.97. This is a focused value/colour trial; confirm the new saved frame rather than assuming the earlier radius3 test60 predicts it. Preserve contact, black corners and the far crawler's gradual loss of contrast. Do not widen the volume again or use global exposure to compensate.

Foreground floor isY83.5/standard deviation10.5 versus selected73.5/21.8; near-right floorY52.4 nearly equals target52.5. The visible Field_A patch has reached the needed foreground region, but its closed straight-sided cells, consistent narrow dark boundaries and nearly uniform top faces read as a polygon diagram. Extra light or additional tiny noise will not turn that structure into the selected broken concrete.

Keep the field placement and repair its construction: interrupt approximately25–35% of boundary segments; add restrained edge subdivision/jitter; chip selected corners; vary neighbouring plate values approximately±15–20% so a few pale abraded plates read while others merge into the substrate. Add sparse detached20–40cm fragments along the torn outer margin. Avoid making every cell an equally complete dark outline, lifting every plate or scattering additional rubble across the clear fight lane. These percentages are working authoring guides; the acceptance cue is irregular eroded continuity, not achievement of a deletion count.

The current cyan impression includes insufficient neutral/red contribution, not simply too little green. For the floor, use a slightly more desaturated warm-neutral albedo or small red lift/blue reduction while keeping the key fixed; do not introduce a green colour wash. Camera, key, player pool and cloth remain fixed for this final material/atmosphere correction. PoolY223.1 versus226.2 and crownY81.3 versus82.4 do not justify another brightness pass.

Continue the full-room edge suite, fresh gallery and moving encounter in parallel with non-conflicting animation repair. The unchanged framing/readability axes still require moving evidence, while the explicitly unresolved floor/fog differences must remain visible in any completion assessment.

## FloorV3 and physical fog review — 08:31 UTC

The separate [FloorV3 export](../Assets/Adapted/Parity/FloorV3/README.md), authored by [make_parity_fracture_v3.py](../tools/make_parity_fracture_v3.py), is now integrated by the shared-asset owner. Its interrupted, jittered and chipped boundaries, restrained plate-value groups and sparse detached fragments reduce the earlier polygon-diagram appearance. The FBX roundtrip preserved dimensions, triangles, UVs and five slots; all 13 pre-existing Floor-kit files retained their hashes. This verifies the adapted export, not final scene fidelity.

Reviewed [08:25 matched gameplay](../evidence/implementation/20261005T082552-capture_parity_room/01-matched-gameplay.png) and [wide gameplay](../evidence/implementation/20261005T082552-capture_parity_room/02-gameplay-wide.png). Three emissive local fog spheres form detached glowing bags when the camera widens. A prior single sphere formed a dome above the rear wall. These are explicit full-room failures, regardless of a useful close-frame upper brightness. Stop tuning the emissive sphere approach; the previous radius/luminance recommendations above are superseded by this evidence.

The [08:31 matched gameplay](../evidence/implementation/20261005T083129-capture_parity_room/01-matched-gameplay.png), [wide view](../evidence/implementation/20261005T083129-capture_parity_room/02-gameplay-wide.png) and [room overview](../evidence/implementation/20261005T083129-capture_parity_room/03-room-overview.png) replace the spheres with physically lit volumetric height fog. The room no longer contains detached luminous objects. The close view instead shows a pale narrow column at top centre; the far creature and ground shadow gain too much veil. The wide views lose almost all upper fog, consistent with the fog frustum ending before the far room. That distance explanation is a source-supported diagnosis awaiting the next runtime trial, not established solely by these stills.

| Same close-frame region | Selected median Y | 08:31 median Y | Practical implication |
| --- | ---: | ---: | --- |
| Upper centre `(470,25)-(760,115)` | 111.7 | 152.7 | Centre is too bright. |
| Upper-left interior `(250,30)-(380,120)` | 71.2 | 11.2 | Useful glow is much too narrow. |
| Upper-right interior `(835,30)-(970,120)` | 53.6 | 6.8 | Broaden depth within the room; preserve the extreme black corner. |
| Central action floor | 147.6 | 141.6 | Do not increase the main key. |
| Foreground worn floor | 73.5 | 84.3 | Avoid more near-floor veil. |
| Bottom strip | 46.7 | 68.4 | Restore near falloff while correcting far haze. |

FloorV3 should remain fixed through this atmosphere correction. Target wear still has stronger coherent abrasion and damp boundaries: foreground standard deviation21.8 versus10.7 and centre18.4 versus9.6. Those statistics corroborate the visible smoother current ground but are not a request to add uniform noise. V3 solves the most obvious geometric construction error; another geometry rewrite is lower priority than obtaining stable atmosphere. Any later wear adjustment should be restrained and local, after the fog stops changing surface contrast.

### Controlled next trial and current-source basis

Use the existing height fog with local emission disabled. Restore density0.017, height falloff0.15 and extinction scale1; the tested0.035/0.65/3 changes near attenuation too strongly even when a light contributes no direct surface illumination. Set volumetric view distance around12000cm for the widest gameplay camera; the rear floor is approximately8900cm from that camera. Review sampling quality after changing distance rather than raising grid settings pre-emptively.

Place the stationary fog spotlight inside the rear chamber, near `(1050,150,610)`, aimed down and toward the far floor near `(1450,150,50)`, with approximately20/48-degree cones and1800cm attenuation. The integrator's next100kcd/VSI6 is a test, not an accepted exposure. Adjust that light's volumetric scattering before changing global density again. Keep diffuse scale0, specular scale0, indirect intensity0, lighting channel0 and volumetric shadowing enabled. A zero direct-surface response does not prevent the atmosphere from attenuating or veiling surfaces; inspect contacts in the actual render.

Installed UE5.8 source was checked in `LightComponent.h`, `LightSceneInfo.cpp`, `VolumetricFog.usf` and `ExponentialHeightFogComponent.h`: fog injection uses the light colour and volumetric scattering intensity separately from direct diffuse/specular scales; light eligibility does not reject a light just because those scales are zero. Retaining channel0 also keeps the ordinary room surfaces eligible for the light's shadowing. The [official volumetric-fog documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine) confirms camera-relative view distance, local-light scattering/shadow controls and the sampling tradeoff with a longer view range. Use low scattering anisotropy for a plume viewed partly from the side, and keep player/muzzle scattering0 to avoid temporal light trails.

Only after the broad glow works, consider subtle low-frequency variation through a grayscale light-function texture. Installed `VolumetricFog.usf` samples the light-function atlas; the [current Light Function documentation](https://dev.epicgames.com/documentation/unreal-engine/using-light-functions-in-unreal-engine) supports volumetric fog and restricts atlas-eligible materials from world-position/depth sampling. Begin with unmodified texture UVs and low contrast. Do not introduce a new particle/noise system to conceal an unresolved beam footprint.

The atmosphere gate is visual and spatial: a broad muted teal glow behind the boss and far crawler, diminishing smoothly into black outer corners; clear near feet and a dark dominant contact shadow; no spherical outline, cone-shaped luminous prop or glow beyond the chamber; the same world-space haze remains plausible in close, wide and side views. An upper-centre number alone cannot pass this gate. Finish with moving evidence before assessing overall parity.

## Broad-source fog trial — 08:34 UTC

Reviewed the [VSI6 close](../evidence/implementation/20261005T083411-diagnose_parity_scattering/01-close-vsi-06.png), [VSI40 close](../evidence/implementation/20261005T083411-diagnose_parity_scattering/03-close-vsi-40.png) and [VSI40 wide](../evidence/implementation/20261005T083411-diagnose_parity_scattering/06-wide-vsi-40.png). The far-facing spotlight suggested above is insufficient: increasing scattering exposes a concentrated glowing patch near the rear wall, with little useful glow in either upper wing. The longer fog view range restores that patch in the wide view, confirming the need to retain12000cm, but its footprint remains wrong. Do not continue scalar sweeps of this placement.

The next controlled trial should change the source area: a **Movable RectLight fixed in world space**, approximately1800cm wide and250cm high at `(1400,150,530)`, facing `(700,150,100)`. Use explicit Candelas units,100kcd/VSI20 as a diagnostic starting pair, attenuation around1800cm, direct diffuse/specular/indirect0, channel0 and volumetric shadows. Keep height-fog density0.017/falloff0.15/extinction1/distance12000. Open the barn doors fully (angle88 degrees, minimum length), with source texture and light function empty for this first coverage check. The projected emitting rectangle must remain entirely below the685cm rear wall; placing a300cm-high tilted rectangle atZ600 would put its top around723cm and risk recreating the exterior glow.

This is supported specifically by the **installed volumetric implementation**, not an assumption that every RectLight path is a true area light. `RectLightSceneProxy.cpp:49–65` normalizes colour by half the rectangle area and passes half-width/half-height as SourceRadius/SourceLength. `RectLight.ush:602–618` uses those dimensions to construct the rectangle. `VolumetricFog.usf:481–493` and1097–1109 then integrate that rectangle, while other local lights use capsule integration. Thus the volume can receive a broad area contribution without collapsing this source to a point. The [Rect Light documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/rectangular-area-lights-in-unreal-engine) documents dimensions, one-sided orientation and area-normalized intensity; its general Movable-light surface description must not be substituted for the separately checked fog shader.

Judge the first rectangle result by footprint before brightness. It should light a continuous upper interior, retain softly darker corners and remain within the chamber in the wide shot. If its coverage succeeds, one intensity correction is preferable to changes in global fog density, floor maps or camera. If it exposes a visible flat luminous bar, reduce/redirect the actual light contribution; do not hide that bar by another vignette or an emissive sphere.

## Rectangular-light selection and remaining visual gate — 08:39 UTC

Reviewed [Rect8 close](../evidence/implementation/20261005T083904-diagnose_parity_scattering/01-close-vsi-08.png), [Rect25 close](../evidence/implementation/20261005T083904-diagnose_parity_scattering/02-close-vsi-25.png), [Rect75 close](../evidence/implementation/20261005T083904-diagnose_parity_scattering/03-close-vsi-75.png), plus the [8 wide](../evidence/implementation/20261005T083904-diagnose_parity_scattering/04-wide-vsi-08.png) and [25 wide](../evidence/implementation/20261005T083904-diagnose_parity_scattering/05-wide-vsi-25.png) views. Actual tested source:150kcd,1800×300cm at `(1300,150,650)`, pointing straight down. This orientation puts the entire emitting plane atZ650, below the wall; the earlier warning about a tilted emitter extending above the wall does not apply to this tested transform.

| Region, median Y | Selected | Rect8 | Rect25 | Rect75 |
| --- | ---: | ---: | ---: | ---: |
| Upper centre | 111.7 | 87.2 | 160.7 | 217.5 |
| Upper-left interior | 71.2 | 56.9 | 124.0 | 196.7 |
| Upper-right interior | 53.6 | 61.4 | 133.9 | 204.5 |
| Extreme upper-left corner | 0.0 | 11.4 | 40.8 | 99.0 |
| Central floor | 147.6 | 135.1 | 144.4 | 166.0 |
| Foreground worn floor | 73.5 | 85.4 | 86.4 | 88.9 |
| Bottom strip | 46.7 | 70.2 | 70.2 | 71.0 |

**Choose Rect8 as the tested base.** Its muted green-teal hue is useful, and the wide view reads as low overhead mist contained in the room. At25 the upper interior becomes a conspicuous luminous bar;75 washes out depth and contacts. Increasing intensity alone cannot fix Rect8's left/right imbalance.

The integrator's narrower source shifted toward image-left is justified: trial width1400/depth500, centre `(1250,-100,650)`, straight down, VSI14 with150kcd retained. Its area grows540000→700000cm², so raw intensity is distributed over more area; the trial aims to lift centre/left while reducing the bright right wing and corner spill. Do not jump to18 before reviewing14. The source's current colour should remain fixed through this change; the higher contribution already raises its red component naturally. Keep height fog and all surface lighting fixed.

V3 now reads as connected worn concrete, with broken boundaries and detached pieces instead of closed polygon outlines. Preserve its topology. The remaining floor gap is material/value structure: foreground variation is11.1 versus target21.8, with a brighter baseline, while the bottom strip stays too pale across all three fog trials. A fog adjustment cannot remove this nearly invariant discrepancy. If a final material correction is undertaken, use local dark damp boundaries and grouped worn plate values with restrained near-floor darkening; protect the already-matching right floor and player pool. Do not add uniform grit, another global contrast pass or another fracture rewrite.

Final visual gate: inspect the saved close, widest separation, opposite-room/edge view and a moving encounter. Require broad upper depth, subdued corners, grounded near shadows, stable sewn cloth, a travelling player pool and no luminous geometry outside the room. Static composition, pool placement and improved physical floor construction are close; the stronger target floor wear and temporal continuity remain explicit limitations until new evidence demonstrates them. User acceptance is separate from this technical art review.

## Saved close versus full-room fog slab — 08:46 UTC

The [saved close](../evidence/implementation/20261005T084605-capture_parity_room/01-matched-gameplay.png) combines atmosphere11 (1400×500cm source, VSI14) and floorwear12. It is the strongest complete close so far. The [wide](../evidence/implementation/20261005T084605-capture_parity_room/02-gameplay-wide.png) and [overview](../evidence/implementation/20261005T084605-capture_parity_room/03-room-overview.png), however, expose a bright horizontal slab beneath the rear wall. The lack of an exterior dome is progress, but the visible lighting shape still fails atmospheric continuity. The player body also needs the integrator's independent perimeter-readability check.

Floorwear12 improves foreground medianY75.9 versus target73.5, bottom54.3 versus46.7 and right floor51.5 versus52.5. Preserve it. Foreground spatial variation11.5 versus target21.8 remains a material-fidelity limitation, with target abrasion/dampness more strongly grouped. This is now secondary to the obvious fog slab; no further fracture rewrite or broad floor-brightness change is justified.

The current haze has brightness available for redistribution: centre medianY138.8 versus111.7, left interior113.5 versus71.2 and right interior72.5 versus53.6. Trial a1200×1200cm source at `(900,-100,650)`, straight down, retaining150kcd/VSI14. Its area increases from700000 to1440000cm²; **do not compensate by doubling intensity**. The front of the source reachesX300, so guard the boss/central ground shadow against new veil. Review close and wide together before any scalar correction.

A physical fallback is the height-density profile. Installed `SceneCore.cpp:405` scales the authored height falloff by1/1000; `VolumetricFog.usf:169` applies an exponential base2 decay with height. The present falloff0.15 leaves density atZ650 approximately93.5% of the floor density: the emitter sits in almost full-density mist. If the larger source still reveals a ceiling plane, trial falloff1.5–2.0 while retaining floor density/extinction. That makes the650cm-to-floor density ratio about51%–41%, potentially shifting the brightest scattering below the emitter. This is a source-derived candidate, not a rendered result; do not change it simultaneously with the first broad-source trial or compensate with higher global density.

A softened source texture is a later fallback. Current Context7 documentation exposes `RectLightComponent.SetSourceTexture`; installed `VolumetricFog.cpp:183–190` shows `r.VolumetricFog.RectLightTexture` is disabled by default, and the shader only samples the source texture when that path is enabled. A source-profile texture therefore needs a deliberately verified renderer setting as well as the texture; simply assigning a gradient is insufficient. Prefer the already-supported source geometry and height profile first. Keep the final solution fixed in world space and assess it from all gameplay camera positions.

## Atmosphere13 and final static art gate — 08:54 UTC

Reviewed the saved [matched close](../evidence/implementation/20261005T085410-capture_parity_room/01-matched-gameplay.png), [widest gameplay](../evidence/implementation/20261005T085410-capture_parity_room/02-gameplay-wide.png) and [angled overview](../evidence/implementation/20261005T085410-capture_parity_room/03-room-overview.png). The deep square source plus height falloff2 removes the visible luminous bar/dome. Haze now reads as depth inside the chamber. The front character-only fills also reveal the peripheral player's body beside its travelling-pool position. This is the best full-room combination reviewed; preserve its geometry and density profile.

| Close-frame region | Target median Y | Atmosphere13 median Y |
| --- | ---: | ---: |
| Central action floor | 147.6 | 143.8 |
| Upper haze | 111.7 | 90.3 |
| Upper-left interior | 71.2 | 74.2 |
| Upper-right interior | 53.6 | 36.3 |
| Extreme upper-left / upper-right corners | 0 / 0 | 12.2 / 0 |
| Foreground worn floor | 73.5 | 77.8 |
| Right floor | 52.5 | 53.3 |
| Player hotspot | 226.2 | 223.9 |

The former slab region also changes coherently between the prior and current saved views: wide rectangle `(520,145)-(755,225)` falls from medianY162.0 to46.8; overview rectangle `(400,180)-(610,270)` falls170.7→62.9. Middle-floor regions remain around132→138. These are same-camera before/after diagnostics, not reference targets for the inferred room. Together with direct visual inspection, they show removal of concentrated upper glow rather than global scene darkening.

If making one last scalar correction, test **VSI14→17 only**, then inspect the same three views. Do not pursue the upper-centre target number with a larger increase: the left interior already matches and its extreme corner has modest spill. Keep14 if17 reveals the source plane again or weakens contacts. No new colour shift, volume, camera compensation, source texture or geometry change is justified by these frames.

| Art axis | Final static judgment | Visible residual / evidence limit |
| --- | --- | --- |
| Composition and scale | Close to selected diagonal staging and elevated framing. | Reference pose differs; adaptive movement/framing needs motion evidence. |
| Key light and grounded shadow | Close: dominant plush weight, directional cast silhouette and clear contacts. | Some pose-dependent shadow-shape/black-level differences remain; hold key. |
| Haze and dark perimeter | Full-room shape continuity now works in the three reviewed views. | Upper centre/right are dimmer than target; small left-corner spill. Optional VSI17 is a bounded trial. |
| Player pool and readability | Close-frame pool value/placement works; peripheral body is visible in wide view. | Smooth travel/aim rotation and clarity during combat must be checked in motion. |
| Woven plush and sewing | Fabric and actual cross-crown construction provide the intended sewn-creature cue. | Current crown is warmer/browner than selected; deformation and weave stability are not proven by stills. |
| Broken floor and debris | V3 construction and latest mean values are close enough to preserve. | Target retains stronger grouped abrasion/dampness and larger-looking edge fragments; current foreground variation11.6 versus21.8 remains visible. |
| Practicals and gameplay effects | Sparse red practicals read without lighting the whole perimeter. | These staged frames do not verify warning/muzzle/impact effects, combat readability or defeat motion. |

**Gate opinion:** no critical geometry defect remains in this comparison; continue final runtime/motion verification with the current visual foundation. Static fidelity is substantially closer across all seven axes, but remaining material and atmospheric differences should be reported accurately. A reviewed implementation, passing runtime checks and the user's acceptance are distinct conclusions; none can be inferred from these three stills alone.

### Bounded crown-colour remediation after the 08:54 review

Compared approximately corresponding lit fabric patches on the target and current head, using a coordinate-grid crop for inspection only. The seam paths and head normals differ, so the same screen rectangle is not an adequate material comparison. The front-crown patches avoid the dark stitch line; an additional diffuse-head mask selects65<Y<115 to compare colour at nearly equal displayed luminance.

| Surface comparison | Target median RGB / Y | Current median RGB / Y |
| --- | --- | --- |
| Front crown: target `(427,173)-(449,189)`; current `(441,160)-(463,176)` | 78 /86 /72.5; Y83.4 | 100 /95 /70; Y94.4 |
| Upper crown: target `(468,154)-(482,166)`; current `(466,149)-(480,161)` | 121 /129 /107.5; Y125.6 | 129 /121.5 /92; Y121.0 |
| Diffuse-head mask,65<Y<115 | 82 /91 /78; Y87.5 | 89 /89 /68; Y87.9 |

For the equal-luminance diffuse masks, median per-pixel RGB/Y is target `(0.937,1.032,0.869)` versus current `(1.039,1.013,0.766)`. The consistent discrepancy is excessive red and deficient blue, not insufficient green brightness. The mask polygon follows the visible head surface and excludes the ear/background; it contains1683 target and2139 current qualifying pixels. These are approximate surface-aligned diagnostics, not recovered physical albedo.

Current material settings supplied by the integrator are tint `(1,0.94,0.80)`, base0.84 and desaturation0.12. The proposed `(0.94,1.03,0.83)` plus a lower base would mildly reduce red but barely raise blue. A more targeted bounded trial is **tint `(0.86,1.00,1.05)`, base0.82, desaturation0.12 unchanged**. Inspect the same surface regions after rendering, keeping the grey-olive textile distinct from the teal lighting and preserving the dark underside. This is an estimated corrective trial through a nonlinear Cloth/lighting/tone-mapping path, not a claim that tint ratios map directly to final pixel ratios. Retain the existing material assets/texture inputs; no new geometry or shader model is required.

## Six-view delivery candidate — 09:09 UTC

Independently reviewed all six saved plates: [matched gameplay](../evidence/implementation/20261005T090957-capture_parity_delivery/01-matched-gameplay.png), [widest gameplay](../evidence/implementation/20261005T090957-capture_parity_delivery/02-gameplay-wide.png), [overview](../evidence/implementation/20261005T090957-capture_parity_delivery/03-room-overview.png), [rear bulkhead](../evidence/implementation/20261005T090957-capture_parity_delivery/04-rear-bulkhead.png), [side services](../evidence/implementation/20261005T090957-capture_parity_delivery/05-side-services.png) and [electrical bay](../evidence/implementation/20261005T090957-capture_parity_delivery/06-electrical-bay.png). The integrator reports the reviewed84 wall/dressing actors are now included, with kit and collision retained. These pictures establish visible integration only; they do not independently test that collision claim.

The crown-colour trial succeeds. Using the same diffuse-head polygons and65<Y<115 filter, target median RGB/Y is82/91/78 atY87.5; the new image is81/91/77 atY87.9. Median per-pixel RGB/Y ratios are target `(0.937,1.032,0.869)` and current `(0.938,1.032,0.871)`. The former brown/yellow bias has been corrected without dimming the crown. Preserve tint `(0.86,1.00,1.05)`, base0.82 and the existing Cloth construction.

Gameplay and overview retain grounded shadows, the small player pool, a visible peripheral player body and room-confined haze without the previous bar/dome. The rear architectural camera is immersed in strong far mist, so the bulkhead is heavily veiled but still legible; side-service and electrical-bay views retain plausible dark perimeter structure and sparse red practicals. No critical material, clipping or luminous-volume defect is apparent in these six plates. This does not replace a moving review.

Current close diagnostics: upper hazeY92.5 versus target111.7; left interior75.4 versus71.2; right interior37.3 versus53.6; central floor144.2 versus147.6; foreground77.8 versus73.5; player pool224.0 versus226.2. The selected image still has stronger upper-middle/right depth and richer grouped floor wear; the current foreground standard deviation11.4 remains lower than21.8. These are residual fidelity differences, not reasons to reopen the successfully matched cloth or change the camera.

The seam remains finer than the selected construction. In a magnified surface comparison, the target has a wider gathered black valley and thicker crossing bridges; the current crown shows a narrow stitched line. A single bounded thread-material correction is reasonable: change `M_Parity_ThreadV2` base colour from `(0.12,0.105,0.075)` to approximately **`(0.06,0.055,0.045)`**, leaving the dark seam material unchanged. This can reduce pale-tan lacing while keeping individual bridges readable. Avoid near-black thread that merges every bridge into the valley. Material colour cannot reproduce missing seam width/profile, so do not report that residual as fully resolved by darkening alone.

At this snapshot the critical shader, physical floor-construction, fog-volume shape and player-readability defects are resolved in the reviewed stills. Composition, key, pool and crown colour are close to the selected direction. Complete the moving encounter recording after the final material decision, then inspect deformation, aim-light motion, attack/defeat readability and room-edge continuity before writing the final acceptance statement.

## Rear-centre player visibility correction — 09:14 UTC

The wider QA suite changes the visibility conclusion. In [room-case03](../evidence/implementation/20261005T091420-verify_full_room/room-case-03.png), player position `(1300,0,85)` lies within illuminated rear mist but outside the four corner fills. Its white pool is clear while head, torso and weapon nearly merge into the veil. In [case09](../evidence/implementation/20261005T091420-verify_full_room/room-case-09.png), player position `(1300,1350,85)` receives the rear-corner fill and remains readily legible. Case03 is a local gameplay-readability defect, not sufficient deliberate dark-edge styling.

Approximate image patches support the direct observation: case03 torso `(669,242)-(676,255)` has medianY74.2, versus adjacent mistY69.5–72.3; the head isY64.0. Case09 torso `(867,239)-(875,253)` isY44.8 against adjacent darknessY0.8–4.1. The latter body is darker in absolute value yet has much stronger usable separation. These patches illustrate contrast, not an automated acceptance threshold. The28 passing room checks cover saved geometry, collision, framing and decoded images; they do not prove body/background visual separation.

The gap follows directly from existing placements: rear corner fills at `(1080,±1080,600)` have950cm attenuation radius, while the rear-centre player's body is more than1200cm from either. Add one owned **Movable point light fixed in world space** around `(1250,0,420)`, channel1 only,650cm attenuation radius,70cm source radius, explicit6000cd and cool-neutral colour approximately `(0.35,0.50,0.55)`. Set volumetric scattering0, indirect lighting0 and specular0/modest; retain direct diffuse contribution and the existing character lighting channels. This positions the source just in front of and above the affected player, with a small range intended to avoid the initial crown. Recheck that exclusion in the saved matched frame rather than assuming point distance alone proves it for every mesh surface.

Do not alter fog density, player pool, global exposure, main key or cloth tint. If6000cd still leaves the figure indistinct, trial8000cd locally rather than widening the light. Require a coherent head/shoulder/weapon silhouette and readable heading at normal display size, with unchanged mist background and ground pool. Re-render case03 and the matched close after integration; keep case09 as the established readable comparison. A movie recorded before this fix is evidence of the preceding state and must be labelled accordingly.
