# BossShot: video reference and corrected direction

Updated 4 October 2026 for the user's request to recreate the supplied video's visuals, atmosphere and controls, with a downloaded teddy-bear monster model. This replaces the earlier interpretation of a low cinematic camera looking up at suspended primitives.

## Reference and inspection

Source: `C:\Projects\to-deploy\horror-scene\WhatsApp Video 2026-10-04 at 16.53.31.mp4`. The original remains unchanged. SHA-256: `289b314d3578e76e7a8e916c31ef653c0bbea2fb97e21eea2100cb063069fdeb`.

The 22.99-second file is a 384 x 848 phone recording at 60 fps. Its landscape gameplay is rotated within that recording. We inspected whole-clip chronological stills and more frequent gameplay samples, with upright keyframes. Phone rotation, social-feed interruptions, interview footage, status bars, reaction buttons, playback controls, and the caption are outside the game target. They must not become the recreated game's UI. Source seconds around 5-18 contain the most useful continuous gameplay. Some of the native HUD and player motion are obscured by the social overlay.

Evidence under `evidence/reference-video/`:

- `contact-sheet.png`: whole recording sampled once per second, left to right and top to bottom from source second 0.
- `upright-05.png`, `upright-10.png`, `upright-16.png`: full upright keyframes showing composition, aiming, and movement around the boss.
- `motion-sheet-00.png`, `motion-sheet-01.png`: approximately 0.25-second gameplay samples, starting around source seconds 5 and 12 respectively. Retained overlays make the limits of the evidence visible.
- `inspection.json`: source metadata, hash, transformations and inspection limits.

## What the images establish

| Aspect | Observed target | Consequence for the next build |
| --- | --- | --- |
| Camera | Elevated, oblique view looking down across the floor; player and creature share the combat frame. | Use an overhead combat camera with gentle tracking. A low-angle trigger shot is not the primary control view. |
| Scale | Small armed human against a bulky, grounded creature several times larger in the image. | Tune screen-space proportions using the upright frames. The clip does not establish exact world dimensions or a 10-15x height ratio. |
| Creature | Pale irregular upper surface, heavy dark body, appendages and strong floor contact/shadow. | Preserve its imposing weight and readability when substituting the requested monstrous teddy. Do not retain the floating sphere-and-cones silhouette. |
| Arena | Worn, mottled dark floor, shadowed boundaries, sparse visible detail, space to circle the boss. | Build a textured arena with credible contact and depth; avoid an exposed edge of a featureless square plane. |
| Lighting | Desaturated blue/teal haze, a localized cool pool of light, deep perimeter shadows, small red glows toward the edges. | Balance visibility against darkness. Match the image rather than inheriting numerical light counts or fog values from the PDFs. |
| Combat | Player changes position around the creature while directing a thin pale aiming line toward targets; bright cyan/white weapon flashes or projectiles; smaller crawling enemies appear nearby. | Independent movement and aiming, firing and hit response belong in scope, with a bounded boss encounter and a few secondary threats. |
| Interface | Subtle native bars/icons are partly visible beneath a social-media overlay. | Use restrained health/ammo feedback only as needed for the encounter. Do not reconstruct unreadable labels or copy the social interface. |

At roughly seconds 5-7 the player is to the creature's right. Around seconds 8-12 the player moves toward the foreground and left while aiming back toward the creature. Later frames return the player toward the right, with creature turns/reactions and weapon flashes. The sequence supports movement around the enemy and independent aiming; it does not reveal a keyboard, controller, exact button map, cooldowns, damage values, or exact camera settings.

## Requested change and proposed controls

The teddy-bear monster is the user's requested substitution for the video's main creature, not a claim that the original clip contains this downloaded teddy.

Proposed desktop defaults: **WASD** moves relative to the screen, **mouse** aims independently, **left mouse button** fires, **Space** performs an evasive dodge, **Esc** pauses, and **F5** restarts the encounter. If finite ammunition/reloading is implemented, **R** reloads. Dodge mechanics and these bindings are implementation proposals; the clip does not confirm them. Preserve readable motion, weight, aiming direction and response when tuning. Gamepad support can use equivalent twin-stick behavior if implemented, but is not verified by this inspection.

Audio exists and an excerpt was extracted, but the inspection interface could not audition it. No exact sound palette or source soundtrack has been verified. Review the gameplay audio before claiming an audio match; otherwise label original ambience, footsteps, weapon and creature sounds as proposed sound design.

## Downloaded teddy candidate

Downloaded [Horror Teddy Bear Monster by Aiden Reynolds](https://www.summerengine.com/asset-store/horror-teddy-bear-monster-a2f0ecaa), listed by the source under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), to `Assets/ThirdParty/HorrorTeddyBear/horror-teddy-bear-monster.glb`.

The existing asset is described as AI-generated with Meshy 6. Its GLB is valid and imports in Blender 5.2: one mesh, 3,660 triangles, one embedded 2048 x 2048 colour texture and UVs. It has **no skeleton and no animations**. Unreal 5.8 import is now verified, with a saved static mesh, material and texture under `/Game/SetupValidation/HorrorTeddy_9fe8c87a`; exact paths are in the setup import receipts. That establishes import compatibility, not final enemy readiness. Download provenance, source license evidence and hashes are retained; `evidence/asset-research/teddy-front.png` and `teddy-reverse.png` are renders of the actual downloaded mesh.

It is a starting candidate, not approved final art. Visible limitations include a faceted silhouette, thin limbs, awkward foot shapes and basic texture detail. Assess whether proportion changes, mesh cleanup, improved cloth/fur surface detail, rigging and animation can achieve the intended quality. Replace it with a better licensed model if that is the more effective route; a downloaded file alone does not satisfy the visual target.

## Current status

`MASTER_PROMPT.md` defines the revised implementation target. The earlier prompt is preserved at `evidence/revisions/MASTER_PROMPT.greybox-v1.md`. The existing Unreal greybox remains available and unchanged by this prompt revision. Its movement/camera tests establish that earlier implementation's behavior, not reference fidelity or completion of the newly requested combat and art work.
