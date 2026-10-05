# Boss-scene study

5 October 2026. The subject is the boss shot named in `C:\Projects\to-deploy\horror-scene\End_of_Abyss_Look_Studio_Brief_v0.1.pdf`, checked against the clip that brief was written from.

The clip is the last fifteen seconds of a win against the **Husk Cluster**. The camera stays high and looks down across a dark teal floor. The mass stands on that floor. Fog, scale, and two red practicals do the visual work. The brief’s low, upward, hanging-mass camera is a different shot.

## Sources

Observed:

- [@GrittyGamingGG, “First boss down,” 2 October 2026](https://x.com/GrittyGamingGG/status/2105885615095206303). The attached video is 1920×1080, 14.8 seconds, 887 frames. Stills below were taken from that file at 2 fps.
- The phone recording `horror-scene\WhatsApp Video 2026-10-04 at 16.53.31.mp4` is a portrait screen capture of that post, rotated, with another feed video mixed in. It is not a second scene.
- On-screen label at 2.5 seconds: **HUSK CLUSTER**, over a boss bar that is already nearly empty. See `plates/boss-name-02.5s.png`.

Read, and kept separate from the frames:

- The three-page studio brief, plus the Godot and Unreal step sheets in the same folder. Those sheets prescribe a hanging mass and a low hero camera.
- Epic Games Store hands-on, “End of Abyss Hands-On: Body Horror on a Brutalist Canvas.” It describes an up-and-back camera: low and tight in corridors, high overhead in open rooms, and a choice to avoid fading large pieces of the set in front of the lens. Marcus Ottvall is quoted on authored cameras that separate exploration framing from combat framing.
- Public walkthroughs and the logbook list treat Husk Cluster as the first story boss, before the shuttle to Factory East. Drowned Husk is a later Waterworks boss. This study does not use their attack lists.

Frame grade, sampled every fourth pixel: mean colour stays near RGB (3, 26, 33). Pixels above a modest brightness are about 7–16% of the frame. Saturated red pixels are a handful. The image is crushed teal, with red only as small practicals.

Audio on the post was not auditioned.

## What the fifteen seconds do

| Time | What is on screen |
| --- | --- |
| 0.0–2.0 | Fight already ending. Pale fleshy mass on the left, player to its right with a flashlight, at least one smaller creature. Boss bar is up and nearly spent. |
| 2.0–7.5 | Player circles and fires a thin tracer. Three or four smaller creatures move between the player and the mass. Camera stays elevated and keeps both in frame. A red practical sits on a door frame at the right. |
| 7.5–9.0 | The mass flashes brighter while the player fires from the left. Smaller creatures are still standing. |
| 9.0–12.0 | Player keeps distance. The mass remains a grounded pile. The far corner of the room is gone in the teal. |
| 12.0–14.8 | Boss bar leaves. “NEW DATABASE ENTRY” appears. A body near the pile has a small warm glint. The player walks toward the right-hand door. The pile stays readable. |

Plates: `plates/contact-2fps.png`, `plates/00.0s.png`, `plates/02.5s.png`, `plates/08.0s.png`, `plates/12.5s.png`.

## What the shot is made of

**Camera.** High three-quarter view for the whole clip. Floor, contact shadow, and the faces of the side walls are all visible. The horizon is absent. The camera slides to keep the player and the mass together as the player circles. There is no cut to a low hero angle, and no blend during these fifteen seconds.

**Scale.** The player is a small dark figure. The mass is the largest body in the room, several times the player, and still leaves most of the frame as floor and fog. Smaller creatures sit between those two sizes and make the mass easier to read. A bright-pixel measure was too contaminated by the flashlight and muzzle specks to quote as a frame percentage.

**Creature.** One grounded mound: pale, wet-looking, irregular, with limbs and spikes in the silhouette. It casts a hard dark pool on the floor. At the end it collapses in place. It does not hang, and it has no separate hero specular.

**Light.** One cool, dim world. Fill is the fog. Two small red practicals, one on each side door in the wider frames, are the only warm colour until the death glint. The player’s flashlight is a local cool pool, not a second sun.

**Room.** A brutalist chamber. No sky. The far wall disappears. Near walls and door frames stay just readable so the player’s path does not vanish.

**Interface, recorded and left alone.** Health and stamina ticks at the top left, weapon icons and a count at the lower left, the red boss name and bar at the bottom, then the database line. Copying that interface is outside this study.

## Where the brief and the clip part

The brief is right about the feeling: teal murk, a huge organic mass, a small silhouette, a couple of red practicals, fog as the far wall, and a warning not to copy the story, the exact creature, the combat rules, or the interface. A teddy or another grounded creature can carry the same lesson.

These brief claims do not match this clip:

- The camera section calls for a low angle looking up, with the mass filling the upper frame. The clip looks down.
- The step sheets say the mass hangs in the volume, and that a creature sitting on the floor is the wrong scene. This creature sits on the floor.
- The brief ties the teal look to the Drowned Husk in the waterworks. The label on this clip is Husk Cluster, a different story boss.
- The framing rule of “creature 40–70% of the frame” is a target the brief invented. In the clip the mass is dominant and still surrounded by floor.
- The clip has no camera-volume blend and no two-second hero hold. It is ordinary combat framing through a kill and a short walk-away.

The Godot-first week in the brief teaches a shot this clip does not contain.

## Lesson to keep

Build the read in this order:

1. An elevated camera that shows the floor and both bodies, with enough arm length that the player stays small.
2. Exponential teal fog thick enough to erase the far wall and thin enough that both silhouettes separate. Manual exposure, so the blacks stay crushed.
3. One dim cool key. Two small red practicals deep in the volume. No sky light.
4. A grounded mass, large beside the actor, with a contact shadow. Idle motion can be slow. Detail comes after the grey shape already feels huge.
5. One or more smaller bodies between the actor and the mass, so scale has a middle step.
6. One readable ending in the same camera: the mass collapses, the bar goes, the actor can walk away.

Their attack pattern, phase changes, weapons, and interface stay out of scope.

## Relation to the encounter already built

`TeddyBlueprint` map `/Game/Maps/TeddyEncounter` already aims at this family of shot: a fixed elevated combat view, teal darkness, a grounded creature, and smaller creatures in the same room. The historical low-angle BossArena matches the brief’s camera section and does not match this clip.

The remaining gap is visual, not a camera rewrite. The reference mass is a pale irregular cluster. The encounter’s subject is the adapted teddy, which is the agreed substitute. The arena reads more regular than this chamber, and the warning ring is a proposed aid rather than something visible in the clip.

## If the study continues into a greybox

A new blockout passes when a still from the elevated camera shows all six of these at once: far wall gone, mass on the floor, mass clearly larger than the actor, actor still a separate dark shape, only the red practicals reading as warm colour, and a collapse that reads without a cut. That check belongs in the existing Unreal encounter project. It does not need a second engine.
