# Pre-production

5 October 2026. Expanded study for the Teddy Encounter. The scene agent still owns the level. None of this is imported, and Unreal was not opened.

The selected look remains [direction-close-best.jpg](../visuals/direction-close-best.jpg). The four-panel board remains [parity-expanded-reference.png](../visuals/parity-expanded-reference.png). This folder is the pass around them: concept, reference, animation, level design, light, and the material and cue sheet.

| Desk | File | What it produced |
| --- | --- | --- |
| Concept | [CONCEPT.md](CONCEPT.md), [concept/](concept/) | Five stills kept, five rejected. |
| Reference | [REFERENCE.md](REFERENCE.md) | Which picture is allowed to decide a measurement. |
| Animation | [ANIMATION.md](ANIMATION.md) | Twenty in-place clips on the existing rig. FBX in `Assets/Adapted/AnimPreprod/`. |
| Level design | [LEVEL_DESIGN.md](LEVEL_DESIGN.md), [layout.json](layout.json), [plan.svg](plan.svg) | 303 placements. Four lanes. Combat footprint left clear. |
| Light and cameras | [LIGHTING.md](LIGHTING.md) | Key, pool, three red pins, twelve witness frames. |
| Material, VFX, audio | [VFX_AUDIO.md](VFX_AUDIO.md) | Gameplay-size reads, ring and shadow cues, four unauditioned sounds. |
| Next gaps (draft) | [NEXT_GAPS_DRAFT.md](NEXT_GAPS_DRAFT.md) | Earlier research draft. The 09:30 status is newer. Not art direction. |
| Interactive brief | [../brief/index.html](../brief/index.html) | Reconciled site: camera, models, atmosphere, gameplay, citations. Open locally. |

## Counts

Room meshes that already existed: 10 kit, 17 shell, 36 dressing, 6 floor. This pass does not add another mesh family. It repeats those meshes until the plan has 107 shell, 41 kit, 110 dressing, and 45 floor placements. Five concept stills are kept. The wide frame that grew a vault wheel is with the rejects.

Animation that already shipped: six clips. This pass adds twenty, keyed with the same pitch-on-X and yaw-on-Z channels as `tools/adapt_teddy.py`.

## Still not done

The shell and the dressing are not in the level. The new clips are not on the blueprint. The crown still reads as a crack on the last matched plate, the floor chips still look drawn, and the player pool is still round. There is no encoded movement clip. Source audio has not been auditioned.

A get-up, a floor-planted one-arm pound, separate left and right walk-stops, and a crawl twitch were specified and were not keyed. They need sole-height checks against Walk frames.

## Do not author from this folder

A new teddy or GLB, a Hunyuan or TRELLIS mesh, a fourth creature, a ceiling, a truss, an open hall, a second wheel, a second tank or crate family, a luminous sign, a baked pool or shadow, another flat debris card, or HUD art.
