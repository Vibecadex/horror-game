# Level design

5 October 2026. Measured plan for the same chamber. Nothing here is placed in the level. The scene agent owns the editor. Coordinates are centimetres. +X is far, +Z is up.

Placements: **303**. Shell 107, kit 41, dressing 110, floor 45. Lights: 5. The drawing is [plan.svg](plan.svg). The records are [layout.json](layout.json).

## Footprint

Combat stays inside X −1400..1480 and Y −1500..1500. The generator refuses a shell, kit, or dressing point inside that rectangle. Floor chips are the exception, and they are the ones already listed in `Assets/Adapted/Parity/Floor/manifest.json`. Dense piles stay off the lanes. Z scale on those chips stays 1. Place them at Z −5.

The near edge is the cutaway, five `SM_ShellCutawaySill` pieces at X −1530 plus two return piers. That sill is 42–68 cm tall. It is not a wall and not a corridor.

The far wall is one narrow bay at Y −1600 and eight 400 cm bays from Y −1300 to 1500, all at X 1720, yaw 90. That run covers Y −1700 to 1700 and puts the interior face on X 1660. Hide `FarWall` when they go in. Each side wall is eight bays at X −1340, −940, −540, −140, 260, 660, 1060, and 1460, so the run meets X −1540 and X 1660. Left centre is Y −1740, yaw 0. Right centre is Y 1740, yaw 180. Yaw 0 faces +Y, yaw 90 faces −X, yaw 180 faces −Y. Hide both `SideWall` boxes. Do not give the shell a collision volume. Confirm the imported front on one bay before repeating it.

## Sides

Left is −Y, pipes. Five `SM_RoomPipeRack` stay at Y −1550. Hangers, flanges, two elbows, three drip trays, the meter, and the downspout cluster under that run. The rack already has the valve. There is no second wheel.

Right is +Y, cabinets and power. The two service cabinets, the shutter niche, the breaker, gang boxes, conduits, and the cable tray stay on this side. One tank here and one tank on the far wall are the same family. Stitchlings enter from this grate side. There are three of them.

The bulkhead stays at (1630, 180, 62), yaw 90, with its own locking wheel. A header dresses the top of the door. It is not a sign. One column sits in the far-left corner only.

## Light

Three red practicals. The pipe pin is (740, −1530, 235) at 180 cd. The power pin is (−920, 1530, 235) at 180 cd. The bulkhead pin is (1630, 400, 240) at 160 cd. A 300 cm and a 240 cm limit keep those spills off the lanes. The key hold is 165000 cd with source radius 70. The player spot hold is relative (105, 0, 170), pitch −80, inner 15, outer 26, about 16000 cd. Corner bounce lights stay turned down. Nothing in this plan is a ceiling, a truss, or a row of spots.

## Beats

| Beat | Where | Clips |
| --- | --- | --- |
| Enter | Cutaway, X about -1400 | IdleHeavy, WeightShift |
| Notice | Boss stays in the centre | Search, Threat |
| Strike | Boss, then the other arm | Telegraph, Attack, AttackLeft, Recover |
| Hit | Boss | Hit, HitLeft, Stagger, Brace, Slump |
| Minions | Right grate, +Y, outside the lanes | Crawl, StitchlingIdle, SwipeLow, StitchlingFlinch |
| Move | Inside X -1400..1480, Y -1500..1500 | Walk, WalkStop, TurnLeft, TurnRight, StepLeft, StepRight |
| Down | On the floor | Defeat, DefeatBreath |

Walk speed stays 105 cm/s for the boss and about 55 cm/s for a stitchling crawl. Turns and steps do not move the root. Defeat breath does not stand the teddy up.

## Circulation

The saved spawns stay. Player start is (−230, 570, 95). The matched plate stood near Z 85. The boss is (250, −230, 232), health 300. The three stitchlings are (650, 600, 65), (−480, −500, 65), and (20, 1070, 65), scale 0.35, health 24. Movement stays WASD relative to the view, mouse aim, left button fire, Space dodge.

Four lanes stay open. The near approach is X −1400..−500 and Y −40..240, 280 cm wide. The pipe orbit is X −1100..1200 and Y −1180..−960, 220 cm wide. The far approach is X 860..1080 and Y −900..1000, 220 cm wide. The power orbit is X −900..1100 and Y 700..920, 220 cm wide. Solid centres stay outside the combat rectangle. The centre between the lanes stays walkable.

## Camera

Pitch stays −46 and FOV stays 54. Height is clamp(max(1.8|dx|, |dy|) + 850, 1700, 5600). The look point is the midpoint shifted toward −X by 0.07|dx|, at Z 160. The camera stays on the −X side of the fight.

Start, with the saved pair, is camera (−1679, 170, 1874), look (−24, 170, 160). Wide, at a separation the rig already allows, is camera (−5522, 0, 5690) when the player is (−1300, −1400) and the boss is (1300, 1400). Far edge, player (1300, 80), is camera (−1945, −75, 2900). Reverse, player (1100, −80), is camera (−1683, −155, 2540), still looking toward +X. At the tall pose a sightline to feet at X −1400 crosses the cutaway near Z 190. The 42–68 cm sill leaves that body visible.

## One minute

Boss health stays 300. Player health stays 100. Each stitchling stays at 24 and drops when the boss drops.

At 0:00 the frame is the start pose. By 0:12 the player is in the near approach and turning onto the pipe orbit. By 0:28 the player is in that 220 cm lane and dodges the existing slam warning. By 0:42 the player takes the far approach. The door stays shut. By 0:55 the player is on the power orbit. Cabinets, the shutter, and the tank on that wall read. The sill stays low. The centre overhead stays open.

## When this is allowed into the level

One writer. Import shell and dressing only after the other session has released the map. Hide the box a mesh replaces. Save, reopen, and look at the matched camera before judging the room. This document is not that capture.
