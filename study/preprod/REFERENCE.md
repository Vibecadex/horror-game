# Reference

5 October 2026. What each reference is allowed to decide. The level stays with the scene agent. These notes do not import, recapture, or replace a mesh.

## Look

| Source | Decides | Does not decide |
| --- | --- | --- |
| [direction-close-best.jpg](../visuals/direction-close-best.jpg) | The selected grade: warm olive teddy, teal centre, dark corners, long shadow, white ground pool. | A new exposure. Manual exposure stays +3.8 EV. |
| [parity-expanded-reference.png](../visuals/parity-expanded-reference.png) | The same room pulled into four panels: combat, chamber, cloth and floor, reverse. | An Unreal plate. It is a board. |
| [concept/](concept/) | Beats and crops that still match the two files above. | A roof, a hall, a fourth creature, painted teal, or a second prop family. Rejected frames are listed in [concept/rejected/README.md](concept/rejected/README.md). |
| `20261005T073350` matched plate | What the running encounter actually showed after the comfy cloth pass. | Acceptance. Parity is not accepted. |

Three reads are still open on that plate: the crown seam looks like a crack, the floor cracks look drawn, and the player pool is still a round hotspot.

## Room, in centimetres

+X is far. The camera looks toward −X. Ground is about Z 0. The arena floor actor top is Z −5. Combat footprint is X −1400..1480 and Y −1500..1500.

| Part | Measure |
| --- | --- |
| Far wall | Inner face X ≈ 1660. Box center X = 1720. Thickness 120. |
| Side walls | Inner face Y ≈ ±1680. Box centers Y = ±1740. |
| Cutaway | Low sill around X −1540, visible height about 40–70. Not a fourth wall. |
| Bulkhead | `SM_RoomBulkhead` at (1630, 180, 62), yaw 90. It already has the locking wheel. |
| Left, −Y | Pipes. Five `SM_RoomPipeRack` at Y −1550, yaw 0. The rack already has a valve. |
| Right, +Y | Cabinets at Y 1580, yaw 180. One tank on this wall is the same tank family. |
| Key | `TE_Parity_Key` about (900, 60, 1600), aimed at (100, 0, −5), color (0.50, 0.94, 1). Hold is 165000 cd and source radius 70. |
| Player pool | Spot on the player. Held baseline: relative (105, 0, 170), pitch −80, inner 15, outer 26, about 16000 cd. Not a texture. |
| Witness camera | Player near (−230, 570, 85). Camera near (−1679, 170, 1874). Pitch −46. FOV 54. 1280×720. |

Left and right are not mirrors. The reverse view uses the same meshes.

## Files that already exist

Unique room meshes on disk, none of the shell or dressing imported:

- 10 in `Assets/Adapted/Room/`
- 17 in `Assets/Adapted/RoomShell/`
- 36 in `Assets/Adapted/RoomDressing/`
- 6 parity floor meshes in `Assets/Adapted/Parity/Floor/`, with `recommended_placements` in that manifest

Cloth identity stays `T_Teddy_BaseColor`. The rig stays the sixteen-bone teddy. Shipped clips are Idle, Walk, Crawl, Attack, Hit, and Defeat. Twenty more in-place clips are in `Assets/Adapted/AnimPreprod/`. They are not imported.

## Surfaces

Shell maps in `Assets/Adapted/RoomShell/Surfaces/` are the wall targets: charcoal concrete, worn green-grey steel, muted oxide, near-black recess. Roughness stays inside the bands already measured for those maps. Teal is not in the textures.

Floor roughness target: damp 0.40–0.65, dry 0.75–0.95. The comfy dry mask is the splitter. Damp is darker concrete, not a mirror and not a cyan paint.

## Audio names already in the project

`ClothHit`, `Rifle`, `RoomTone`, `Slam`. They have not been auditioned. `AttackRing` and `M_QA_AttackWarning` stay, and the warning stays dim on fidelity stills. No new audio files are part of this pass.

## How to use a new picture

A picture can support a placement only when the mesh it suggests already has a name in Room, RoomShell, RoomDressing, or the parity floor kit. If the picture needs a ceiling, a truss, a corridor, a second wheel, a second tank, or another creature, the picture is wrong.
