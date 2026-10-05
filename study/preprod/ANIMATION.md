# Animation

5 October 2026. Twenty in-place clips on the existing sixteen-bone rig. They are on disk in `Assets/Adapted/AnimPreprod/`. They are not imported. The source blend `Assets/Adapted/Teddy/Teddy_Encounter.blend` was opened and saved aside. Its timestamp did not change.

The six shipped clips stay as they are: Idle 90, Walk 37, Crawl 37, Attack 54, Hit 16, Defeat 72, all at 30 fps. Walk is a 75.6 cm stride over 1.2 s, played at 105 cm/s. Crawl is the stitchling cycle, about 113 cm on the full rig, played at 0.35 scale and about 55 cm/s. `Walk_PreContact` is in the source blend and is not a shipped runtime clip.

## Channels

These match `tools/adapt_teddy.py`, which keyed the six shipped clips.

- Pitch is local X. Positive spine or thigh X pitches forward. Negative upper-arm X raises the arm. The framed telegraph is that raise.
- A few degrees of local Z is the sway already in Idle and Hit. Twenty-five degrees of spine Z folded the chest into a bow, so the turns do not use it.
- Larger yaw on this rig is local Y. The framed turn stays upright. There is no twist bone, no neck, and no finger.
- Character left is +X. The rig faces −Y.
- Root travel stays in the blueprint. These clips do not walk the root across the floor.
- Defeat tips the root on X. `DefeatBreath` starts from Defeat frame 72 and does not stand the body up.

Pose stills are clay frames in `Assets/Adapted/AnimPreprod/previews/`. They hide the armature. They are not gameplay captures.

## Clips on disk

| Clip | Frames | Peak | Base | What it is |
| --- | ---: | ---: | --- | --- |
| `TurnLeft` | 24 | 12 | Idle 1 | Spine and head yaw +22° / +14° on Y, left knee softens. Returns to idle. |
| `TurnRight` | 24 | 12 | Idle 1 | The same yaw, the other way. |
| `StepLeft` | 20 | 8 | Idle 1 | Pelvis yaw 6°, left thigh pitches, left shin bends. |
| `StepRight` | 20 | 8 | Idle 1 | The other foot. |
| `Telegraph` | 18 | 18 | Idle 1 | Right arm rises on negative X and holds through the last frame. |
| `Recover` | 16 | 1 | Idle 1 | Starts pitched forward with the right arm low, returns to idle. |
| `AttackLeft` | 36 | 20 | Idle 1 | Left arm raises, then pitches forward. The shipped Attack is both arms. |
| `Stagger` | 24 | 8 | Idle 1 | Chest forward, small yaw, both arms out from the body. |
| `IdleHeavy` | 120 | 60 | Idle 1 | Slow breath. Spine and head pitch a few degrees. Loops back to the start. |
| `Threat` | 45 | 22 | Idle 1 | Chest tips back and both arms rise part way. Not the strike. |
| `WalkStop` | 16 | 1 | Idle 1 | A planted stride settles to idle. The root does not travel. |
| `StitchlingIdle` | 60 | 30 | Idle 1 | Low lean and a small head yaw. Play it at actor scale 0.35. |
| `StitchlingFlinch` | 12 | 4 | Idle 1 | Short tuck from that low lean. |
| `DefeatBreath` | 48 | 24 | Defeat 72 | A small spine and head pulse on the grounded pose. |
| `Brace` | 20 | 10 | Idle 1 | Both forearms come in. |
| `HitLeft` | 18 | 6 | Idle 1 | Chest and head yaw left, left arm pitches. |
| `SwipeLow` | 28 | 16 | Idle 1 | Low right-arm swipe for a stitchling. Stays in the crawl family of pitches. |
| `Search` | 72 | 24 | Idle 1 | Head and spine yaw left, then right, then home. |
| `Slump` | 30 | 1 | Idle 1 | Starts folded forward and stands back to idle. |
| `WeightShift` | 90 | 45 | Idle 1 | Hips and the left thigh shift, then return. |

Each file is `Teddy_<Name>.fbx` with the armature and the mesh, one action, axis forward −Y, axis up Z. Import as animation onto the encounter skeleton. Do not replace `SK_Teddy` or the GLB.

## Contact

Standing support is the feet. Crawl support is the feet and the hands, and the stitchling clip is still the full-size rig played small. A new clip must not drive a hand through the floor. The shipped attack raises the arms and slams the chest. It does not plant a knuckle. `AttackLeft` and `SwipeLow` follow that. They pitch the arm. They do not add a floor-plant bone.

Turns and steps are not a full 45° spin and not a 30 cm sidestep of the root. The actor facing is still the blueprint. These clips cover the pose the shipped walk cannot make, because that walk keeps pelvis yaw at 0.

## Blends

Keep blends short. Idle into IdleHeavy can be slow, about a quarter second. Telegraph into the shipped Attack should meet the raised arms, not Attack frame 1, or the arms drop. Hit, HitLeft, and Stagger can interrupt. DefeatBreath plays only after Defeat. It never blends back to Idle.

Boss Walk does not blend into Crawl. The stitchling does not play the standing idle.

## Not in this export

A get-up, a face, a cloth simulation, a finger, a fourth creature, and a new skeleton. A longer key list was drafted for turns with a real foot plant, a left and right walk-stop, a one-arm pound that touches the floor, and a crawl twitch. Those need a pass that copies Walk frames and checks sole height. They are not in the FBX folder. The twenty clips above are the ones that were keyed and framed.
