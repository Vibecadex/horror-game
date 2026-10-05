# Full asset list

5 October 2026. Built from [parity-expanded-reference.png](visuals/parity-expanded-reference.png), its [prompt](visuals/parity-expansion-prompt.txt), [PARITY_ART_DIRECTION.md](PARITY_ART_DIRECTION.md), and [PARITY_QA.md](PARITY_QA.md). The selected still is [direction-close-best.jpg](visuals/direction-close-best.jpg). That still sets the look. The four-panel board is the room expansion of the same place. Neither image is an Unreal capture.

Current build status is [LIVE_BRIEF.md](LIVE_BRIEF.md). The crown seam, floor kit, and player light from this list are already in the encounter. This list stays the inventory.

The encounter already has a teddy, three stitchlings, a rifle, a floor material, four graphic decals, and the industrial room kit. This list is what the board still needs on top of that, and what must stay.

Status words:

- **In encounter** — saved in `/Game/TeddyEncounter` and visible in the current level.
- **On disk** — authored under `Assets/Adapted/` and not yet the placed look.
- **Revise** — the file stays; its material, scale, or placement is wrong for this board.
- **Author** — no file yet.
- **Do not author** — the board or an older note might suggest it; the written direction refuses it.

## Matched combat

The first panel is the playable shot: one olive teddy, three smaller creatures of the same family, an armed human, a white ground pool, a long grounded shadow, a cracked floor, and a few red points in teal haze.

| Asset | Job on the board | Where it is | Status |
| --- | --- | --- | --- |
| `SK_Teddy` / `Teddy_Encounter.blend` | 4.6 m boss, sixteen bones, existing UV | `Assets/Adapted/Teddy/`, `/Game/TeddyEncounter/Teddy` | In encounter. Do not replace the mesh or GLB. |
| `A_Teddy_Idle`, `Walk`, `Crawl`, `Attack`, `Hit`, `Defeat` | Grounded motion. Stitchlings use the compressed crawl. | `Assets/Adapted/Teddy/Teddy_*.fbx` | In encounter. |
| `T_Teddy_BaseColor` | Olive/taupe cloth identity under teal light | `Assets/Adapted/Teddy/Teddy_BaseColor.png` | Revise in the material. The map already has brown/taupe variation. Current desaturate 0.5 and multiply 1.30–1.65 reads as pale stone. |
| `T_AI_Plush_Normal`, `T_AI_Plush_Roughness` | Fine weave, high roughness, grazing breakup | `study/assets/` and `Assets/Adapted/Arena/` | Revise use. Tile is 7.5×6.2 at strength 0.62. Weave should read as 2–6 mm fibre and 1–2 cm clumps, not stones. |
| `M_QA_TeddyCloth`, `M_TeddyCloth` | Boss and stitchling surface | `/Game/TeddyEncounter/Materials` | Revise. Default Lit fallback. Belly stays dark. Minions use the same family and stay darker than the boss. |
| Crown seam | One irregular head/back seam: two fabric lips and 8–14 separate thread bridges | None | **Author** on the existing rig. Thread about 1–2 cm thick, crossings 10–16 cm, interval 8–14 cm, lip 1–3 cm. Skin it to the head. A painted black stripe is not this asset. |
| Ear or shoulder seam | Second construction line, quieter than the crown | None | Author only after the crown reads. It must not compete. |
| `BP_Stitchling` | Three small creatures, same cloth, 0.35 scale, crawl silhouette | `/Game/TeddyEncounter/Blueprints` | In encounter. No new species. |
| `BP_EncounterPlayer` | Dark armed silhouette | Encounter blueprint | In encounter. |
| `ServiceRifle` | Thin weapon on the player | `Assets/Adapted/Arena/ServiceRifle.fbx` | In encounter. |
| Player hotspot | Neutral-white pool about one player tall, on the aimed ground, soft edge, small bright core | No separate asset. It is a light on the player aim. | **Author** the light behavior. Do not paint the pool into the floor texture. |
| `TE_Key` | One overhead cool pool on the upper-middle floor, compact enough for a long boss shadow | Level actor | Revise. The board’s floor is much brighter in the middle than the current capture. |
| Boss contact shadow | Long dark shape toward the camera, stuck to the feet | Comes from `TE_Key` and the mesh | Revise with the key. Do not bake a shadow into a texture. |
| `TE_LowMist` | Teal upper haze, clear feet | Level actor | Revise density and height. Far creatures stay silhouettes. |
| Red practicals | A few pixels wide at 1280×720, short spill, no red floor pool | Existing `TE_Room_Beacon*` and edge glow | Revise intensity. Two or three visible in a normal frame. |

## Cloth and floor detail

The close panel is the acceptance crop for priority 2 and 3. Fractures branch and taper. Chips have thickness and their own shadows. Damp reads darker, with a small moving highlight. The cloth is woven and sewn.

| Asset | Job on the board | Where it is | Status |
| --- | --- | --- | --- |
| `T_AI_Floor_Color` | Broken concrete albedo, no grout grid | `study/assets/T_AI_Floor_Color.png` | In encounter, via `M_QA_Concrete`. Keep. Albedo scale is 0.20, UV 9×7 on the 60 m slab. |
| `T_AI_Floor_Normal` | Fine aggregate and shallow lips | `study/assets/T_AI_Floor_Normal.png` | In encounter. Keep. |
| `T_AI_Floor_Roughness` | Dry 0.75–0.95, sparse damp 0.40–0.65 | `study/assets/T_AI_Floor_Roughness.png` | Revise the material. The map is currently crushed into 0.78–0.96, so wet and dry look the same. |
| Damp mask | Irregular darker patches, fragmented edges, not a lobed logo | None | **Author** only if the revised roughness cannot make sparse damp areas. No mirror puddle. |
| `SM_ParityFractureField_A` | Low plates, real bevels, field about 6.3×5.0 m, under 3 cm high | `Assets/Adapted/Parity/Floor/` | On disk. Place 2–3, yaw varied, XY scale 0.65–0.95, Z scale 1, no collision. |
| `SM_ParityFractureField_B` | Branching hairline cracks, no backing sheet | same kit | On disk. Place 5–8. |
| `SM_ParityEdgeSpall` | Perimeter chips, up to about 10 cm high | same kit | On disk. Long axis along the wall, outside the walk ring. |
| `SM_ParityRubbleScatter_A`, `_B` | Unequal flakes, a few centimetres high | same kit | On disk. Alternate them. 8–12 of A is the manifest start; do not stamp one scale. |
| `SM_ParityMicroChips` | Close aggregate, about 1 cm high | same kit | On disk. Foreground and a light pass through the centre. No collision. |
| `M_Parity_Concrete`, `Aggregate`, `Dark` | Slot materials for that kit: continuous with the floor, lighter fractures, near-black crack bottoms | None in engine | **Author** as instances or siblings of `M_QA_Concrete`. No emissive. |
| `T_AI_Decal_Crack` | Was a long zigzag | `study/assets/` | Retire from the shot. The board’s cracks are hairline to a few centimetres, and they taper. |
| `T_AI_Decal_Stain` | Was a lobed puddle | `study/assets/` | Retire from the shot. |
| `T_AI_Decal_Debris` | Was a flat rubble stamp | `study/assets/` | Retire from the shot. Raised meshes replace it. |
| `T_AI_Decal_Scuff` | Flat scratches | `study/assets/` | Retire from the centre. A fragment may survive only if it disappears into the base concrete. |
| `TE_AI_Decal_01`–`04` | Placed copies of those four maps | Level | Revise by fading, shrinking, and moving them off the read, or remove them when the parity meshes are in. Keep the source PNGs. |
| `TE_Room_FootDebris_*` | Box scatter at the wall foot | Level, from the room builder | Replace with the parity chips where a raised fragment is visible. |

Placement counts and centimetre coordinates are already in `Assets/Adapted/Parity/Floor/manifest.json`. Dense piles stay outside the movement bounds. The centre keeps several player-width lanes.

## Full chamber

The second panel is the same floor and the same four creatures, pulled back. The shell is a worn containment room. The camera-facing wall and the overhead slab are open only in this explanatory view. Gameplay keeps the low −X cutaway and the open centre.

| Asset | Job on the board | Where it is | Status |
| --- | --- | --- | --- |
| `SM_RoomBulkhead` | Sealed rear door, about 5.0×4.8 m | `Assets/Adapted/Room/SM_RoomBulkhead.fbx` | In the room kit. Confirm the imported mesh has a wheel. If it does not, author one static wheel on that door. No glowing sign. |
| `SM_RoomPilaster` | Wall supports, about 1×5 m | `SM_RoomPilaster.fbx` | In the room kit. Break the bright repeating outline with light and haze, not a new mesh. |
| `SM_RoomVentFan` | Recessed fan, 2.5 m, static | `SM_RoomVentFan.fbx` | In the room kit. |
| `SM_RoomUtilityTank` | Vertical vessels, about 1.6×4.2 m | `SM_RoomUtilityTank.fbx` | In the room kit. One family is enough. |
| `SM_RoomServiceCabinet` | Right-wall cabinets, about 1.8×2.7 m | `SM_RoomServiceCabinet.fbx` | In the room kit. |
| `SM_RoomPipeRack` | Horizontal runs, 5 m | `SM_RoomPipeRack.fbx` | In the room kit. Left wall is pipes. Right wall is cabinets. Do not mirror them. |
| `SM_RoomFloorGrate` | Discontinuous drains, 4×0.9 m | `SM_RoomFloorGrate.fbx` | In the room kit. Recess them. They are not a stripe across the fight. |
| `SM_RoomCargoCrate`, `SM_RoomCableSpool` | Low clutter at the wall | same folder | In the room kit. Peripheral only. |
| `SM_RoomStripLight` | Fixture housing, 2 m | `SM_RoomStripLight.fbx` | In the room kit. The emissive slot stays a slit. The red point comes from a small light, not a bright bar. |
| `M_Room_Concrete`, `PaintedSteel`, `Oxide`, `Recess`, `CoolFixture`, `WarningLens`, `EdgeSteel`, `DampStain` | Four families: charcoal concrete, worn green-grey steel, oxidised pipe, dark recess | `/Game/TeddyEncounter/Room/Materials` | Revise. Teal is the light, not a color baked into every wall. Rust stays muted. |
| Far wall, side walls, cutaway sill, cornice, footing, gutter, recesses, fittings | Shell around the combat footprint | `Assets/Adapted/RoomShell/` (17 FBX). The encounter still has the boxes. | On disk, not imported. Place instead of the shell boxes. Inner play space stays about X −1400..1480 and Y −1500..1500. No second collision shell. |
| Panels, conduits, cable loops, elbows, flanges, breaker, hatch, louver, column, and the rest of the perimeter vocabulary | The repeated parts that make the chamber read as a room | `Assets/Adapted/RoomDressing/` (36 FBX) | On disk, not imported. Cluster them on the walls. Left wall keeps the pipes. Right wall keeps the cabinets and the new breaker. No second wheel, tank, or crate. |
| `IndustrialRoom_Kit.blend` | Source of the FBX kit, 49,280 triangles | `Assets/Adapted/Room/` | On disk. Edit the blend, then re-export. Do not overwrite an unowned asset. |

## Reverse view

The fourth panel uses the same meshes from the opposite side. The dark opening is the cutaway and the depth of the room, not a new corridor.

No reverse-only mesh. The same bulkhead, pilasters, tanks, pipes, grates, floor kit, teddy, and player pool have to hold from both gameplay directions. A prop that only works in the matched-combat framing is incomplete.

## Light, in the order the notes allow

These are level actors and one player component. They are part of the list because the board is mostly light.

1. `TE_Key` broader and brighter on the upper-middle floor, still compact enough for the long shadow.
2. Pull down `TE_Rim`, `TE_PlayerFill`, `TE_FaceFill`, `TE_AmbientFill`, and the four `TE_Room_CornerBounce_*` where they lift the corners.
3. Player hotspot, near white, separate from the teal field.
4. `TE_LowMist` for the upper veil. Near the floor, contact stays clear.
5. Two or three red practicals, pin-sized.

Manual exposure stays put until a matched capture shows the centre bright and the corners darker. A global exposure lift is not an asset and is the wrong fix.

## Do not author

- A new teddy, a Hunyuan or TRELLIS mesh, or a replacement GLB.
- A fourth creature species, a second boss, or a hanging mass.
- A ceiling slab over the fight, a stage truss, or rows of spotlights.
- An open traversable hall behind the bulkhead.
- A luminous B-3 sign. The mark on the board is a faint stencil. It is not a required asset. If a mark is added later, it is non-emissive and a few pixels wide.
- A second tank, crate, or barrel family.
- A baked player pool, a baked boss shadow, or a teal tint baked into the concrete.
- Another copy of the zigzag crack, the lobed stain, or the flat debris card.
- HUD art for this pass. The comparison plates hide the HUD on purpose.

## Already enough, leave the source alone

Original teddy GLB, Twin Stick starter, native BossShot, and the downloaded originals stay where they are. Adapted exports stay in their own files. Audio (`ClothHit`, `Rifle`, `RoomTone`, `Slam`) is not part of this look. `AttackRing` and `M_QA_AttackWarning` stay, and the warning stays dim on fidelity stills.

## Work order

The parity note’s gates, with the files above:

1. Key, haze, dark corners, player pool. No new mesh.
2. Retire the four graphic decals. Place the six parity floor meshes. Revise floor roughness so damp and dry differ.
3. Rebalance teddy color. Author the crown seam on the existing rig. Check it on a turn and an attack.
4. Swap box foot-debris for the parity chips. Keep the room kit. Hide the bright pilaster outline with light, not with more geometry.
5. Save, reopen, and shoot the matched view, two edges, the wide view, and one ordinary movement clip.

A compiled material or a histogram is not one of these gates. The three largest remaining differences get named after each pass.

## Pre-production added 5 October 2026

These repeat files that already exist, or they are performance clips on the existing rig. They are not imported. The index is [preprod/PREPROD.md](preprod/PREPROD.md).

| Set | Where | Status |
| --- | --- | --- |
| Five concept stills and five rejected frames | `study/preprod/concept/` | On disk. The selected still and the four-panel board still outrank them. |
| Twenty in-place clips | `Assets/Adapted/AnimPreprod/Teddy_*.fbx` | On disk. Same sixteen bones. Do not replace the mesh or the GLB. |
| 303 placements | `study/preprod/layout.json`, `plan.svg` | Document only. 107 shell, 41 kit, 110 dressing, 45 floor. Four lanes, saved spawns, four camera poses. |
| Light, camera, material, and cue notes | `study/preprod/LIGHTING.md`, `VFX_AUDIO.md` | Notes. Key hold 165000 cd, source radius 70. Player spot hold is the 26° cone at about 16000 cd. The four sounds are still not auditioned. |

No new mesh family, no second wheel, no ceiling, and no fourth creature came out of this pass.
