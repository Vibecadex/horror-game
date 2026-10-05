# Room shell kit

Off the level. `tools/build_full_room.py` imports `Assets/Adapted/Room/SM_*.fbx` only. This folder is a later opt-in.

These meshes replace the chamber boxes: far wall, side walls, plinth, cornice, foundation, gutter, cutaway sill, rear insets, pipe standoffs, and beacon housings. The ten-piece room kit stays where it is. The bulkhead already has a locking wheel. The pipe rack already has a valve. Neither is repeated here.

Units are metres in Blender and centimetres after the room kit's FBX settings. The detailed face is local −Y. The existing import presented that face toward Unreal +Y. Confirm before placing. Wall origins match the old box centers: far wall X=1720, side walls Y=±1740, interior face 60 cm toward the arena.

When a mesh goes in, hide the box it replaces. Do not stack both, and do not give these a second collision shell.

| Mesh | Job |
| --- | --- |
| `SM_ShellWallBay` | 4.00 m retaining bay, 1.20 m thick, 7.60 m tall, dark 80 cm plinth |
| `SM_ShellWallBayNarrow` | Same section, 2.00 m, to finish a span |
| `SM_ShellCornice` | Steel ledge. Seat it at Z=760. Brackets hang below the seat |
| `SM_ShellFoundation` | Chamfered footing, projects into the room |
| `SM_ShellGutter` | 48 cm drain with a recess only in the middle |
| `SM_ShellCutawaySill` | Broken foreground curb, 42–68 cm, not a wall |
| `SM_ShellCutawayReturn` | 1.1 m pier at the two near corners |
| `SM_ShellRearInset` | Framed far-wall recess and header |
| `SM_ShellShutterNiche` | Right wall only, shutter partway down |
| `SM_ShellPipeStandoff` | Saddle under the left pipe run |
| `SM_ShellBeaconHousing` | Small cage and a 4×18 cm slit. Red stays a light |
| `SM_ShellCornerRiser` | Far-corner pier and elbow, outside the footprint |
| `SM_ShellUtilityCurb` | Far conduit curb. A few lumps are built in |
| `SM_ShellUpperBracket` | 0.8 m inward arm. No lamp and no span |
| `SM_ShellCableTray` | Right-wall ladder tray |
| `SM_ShellDarkBacking` | Outer leaf behind the three tall walls |
| `SM_ShellOuterApron` | Dark ground outside the shell |

Surface maps are in `Surfaces/`: charcoal concrete, worn green-grey steel, muted oxide, and a near-black recess. Roughness stays in the art-direction bands. They do not contain a teal wash or a player pool.

Generator: `tools/make_room_shell.py`. Surfaces: `tools/make_room_shell_surfaces.py`.
