# Visual fidelity study

5 October 2026. How to move the saved Teddy Encounter closer to the Husk Cluster plates, using those frames, the delivery stills, and current Unreal 5.8 rendering docs. The teddy stays the subject. This does not copy the reference creature, its interface, or its combat.

No encounter asset was changed for this note.

How to produce the missing surfaces with AI, and what has to stay a lighting pass, is in [AI_FIDELITY.md](AI_FIDELITY.md). Picture boards are in [study/visuals/filmstrips.png](visuals/filmstrips.png) and [study/visuals/details.png](visuals/details.png). Full-size frames are in `study/visuals/src/`. `direction-wide.jpg` and `direction-close.jpg` are look studies made from the gameplay still. They are not captures.

## What the pictures actually differ by

Reference plates are the clean 1920×1080 post, sampled here at 960×540: `study/plates/02.5s.png`, `08.0s.png`, `12.5s.png`. The encounter side is `evidence/delivery/gameplay-still.png` and the right half of `evidence/delivery/comparison-10.png`.

Sampled every third pixel, luminance above 40 counted as “bright”:

| Plate | Mean RGB | Bright share |
| --- | --- | --- |
| Reference, 2.5 s | 3.4, 25.8, 32.7 | 13.6% |
| Reference, 8.0 s | 3.4, 25.8, 33.2 | 13.8% |
| Reference, 12.5 s | 3.7, 24.9, 31.7 | 11.7% |
| Encounter gameplay still | 6.3, 19.6, 25.3 | 1.3% |

The reference is a crushed black with a broad teal midtone across the floor. The encounter is darker in that midtone band and less cyan. Its readable structure is a lit tile grid, a smooth pale teddy, three smooth stitchlings, a lit human, and a red sconce on a near corner. The reference’s readable structure is a mottled floor, a pale irregular mass with a large contact shadow, small dark creatures, a near-silhouette player inside a flashlight pool, and tiny red points deep in the fog.

The comparison plate already names the three art gaps: smoother creature, more regular floor and walls, and plainer motion. The grade numbers add a fourth: the encounter has no local teal pool, so raising global exposure would lift the corners along with the action. The reference keeps the corners crushed and lets the floor around the fight sit in that teal band.

## Why the current lighting flattens the room

The last broad lighting pass in `tools/refine_qa_visuals.py` aims four cool point lights at the arena (`TE_Key` 65000, `TE_Rim` 14000, `TE_PlayerFill` 9000, `TE_FaceFill` 4500), with radii of about 20–23 m and source radii of 150–200 cm. The directional fill is only intensity 2. Fog density is 0.035 with volumetric fog on. The teddy cloth material built in `tools/refine_scene_lighting.py` is a desaturated albedo multiplied by 1.15 and a constant roughness of 0.9. There is no normal, no fuzz, and no subsurface. Later camera work changed the view; the delivery still is the picture to trust, and it still shows the even floor and the smooth bodies.

Epic’s volumetric-fog page says the volumetric grid is centered on the camera and cannot be detached for a top-down view. An elevated combat camera therefore loses far-field fog unless density is carried by something that is not that camera grid. Local Fog Volumes are the documented tool for that: a scalable sphere, visible at any distance, and usable together with volumetric fog. [Volumetric Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine), [Local Fog Volumes](https://dev.epicgames.com/documentation/en-us/unreal-engine/local-fog-volumes-in-unreal-engine).

The same fog page says scattering distribution near 1 only shows shafts when the camera looks toward the light, and that a fast light such as a flashlight leaves trails in the volume. For this downward camera, a moderate distribution (the page’s own 0.2 starting point, up toward 0.6) beats a 0.9 “shaft” setting. A player flashlight should use Volumetric Scattering Intensity 0.

## Work order

Each step has a picture check. Stop when the check fails and fix that step before the next.

**1. One key, two reds, one flashlight.** Drop the wide cool fills until a single cool key above and behind the mass supplies the contact shadow. Keep two red practicals small, deep, and short-range, with volumetric scattering high enough to bloom in the fog and low enough that they do not paint a nearby wall. Parent a short cool spot to the player as the flashlight pool. Set that spot’s volumetric scattering to 0 so it does not trail. Check: the mass has a dark pool under it, the player stands in a local teal patch, and the near corner is no longer a red wall.

**2. Fog that eats the far wall.** Raise exponential density only until a body at roughly 8 m is still a silhouette. Add one Local Fog Volume over the far half of the room, albedo a dark teal `(0.04, 0.10, 0.13)`, so the rectangular corner leaves the frame. Set volumetric view distance in centimetres to cover the arena (about 3000–6000). Check: the far architecture is gone, and the player and the teddy still separate.

**3. Break the floor grid.** The tile lines are the loudest “this is a blockout” signal. Cover them with deferred decals rather than a new floor mesh. On Fab, the damage-and-grunge decal category currently lists free Quixel Megascans entries for concrete crack, mud stain, oil stain, and leakage: [Fab damage decals](https://www.fab.com/category/decal/damage-grunge). Confirm the listing still says Free before any download. Megascans claimed earlier stay under the license they were claimed with; the old “everything is free” window closed at the end of 2024, and a paid listing needs a separate yes. Scatter a few decals at different scales and rotations, and multiply a large grunge into the floor base color and roughness so the grout lines die. Check: a still no longer reads as square slabs.

**4. Cloth response on the teddy, at this camera distance.** Epic’s cloth shading model is the match for a plush body: it adds a fuzz layer through Fuzz Color and the Cloth input, on top of base color, roughness, and normal. [Shading models](https://dev.epicgames.com/documentation/en-us/unreal-engine/shading-models-in-unreal-engine). Drive roughness from a texture, darker in the seams, instead of the constant 0.9. A subsurface profile is available, and the subsurface shading model uses Opacity as scatter amount, with a useful starting value around 0.1 rather than the default 1. Epic’s skin guide also says subsurface is hard to see from far away, and that base color has to read at distance. At this elevated framing, fuzz, cavity darkening, and a broken silhouette will show before a skin profile does. Keep the teddy’s identity. Check: the silhouette is uneven and the belly is darker than the shoulders, while the character is still obviously a teddy.

**5. Grade the shadows teal, and add fine grain.** Use the post-process shadow color controls and film grain, with grain stronger in the shadows. [Post Process Effects](https://dev.epicgames.com/documentation/en-us/unreal-engine/post-process-effects-in-unreal-engine). Leave global exposure bias where the delivery still sits. A brighter bias would lift the corners that step 2 is trying to crush. The missing teal is local light plus shadow grading. Check: a new 1280×720 still lands nearer the reference midtone, roughly G and B in the mid-20s to low-30s, with the bright share above a luminance of 40 somewhere around 8–16%, and the image corners still near black.

**6. Darken the small bodies.** The stitchlings are the scale step between the player and the boss. Push their albedo down and their roughness up so they read as dark shapes on the teal floor, the way the smaller creatures do in the 8-second plate. Dim the warning ring for any fidelity still; it is a gameplay aid and it is brighter than anything in the reference frame.

## What these sources say to skip

Volumetric fog already replaces inscattering inside its view distance, so tuning Fog Inscattering Color will not paint the far murk while volumetric fog is on. Caustics, a water surface, and Nanite on small rubble stay out. Remodeling the teddy into the Husk Cluster is a different project. Buying a decal pack is a separate authorization. A second engine is not required; every control above exists in Unreal 5.8.

## Done when

One held plate from `/Game/Maps/TeddyEncounter`, same elevated camera, shows all of these together: far corner gone, teddy on the floor with a contact shadow, player inside a small cool pool, only distant reds reading as warm, floor no longer a tile grid, and a sampled grade inside the band in step 5. Gameplay receipts stay valid after the light and material pass. Exact match to the licensed game, and user acceptance, stay separate from that check.
