# Next gaps — draft

5 October 2026. Draft only. This file records a research pass on what comes next. It does not accept parity, import anything, or change the level. Unreal was not opened. The scene writer remains the sole engine writer. Do not treat this draft as art direction.

Selected look: [direction-close-best.jpg](../visuals/direction-close-best.jpg). Inventory and holds stay in [PREPROD.md](PREPROD.md), [VFX_AUDIO.md](VFX_AUDIO.md), and [LIGHTING.md](LIGHTING.md). The scene writer’s current header is the top of `WORK_STATUS.md` (5 October 2026, 08:45 UTC).

## What comes next

A proof of the fight that is already in the level. The scene writer’s own status still lists four evidence gates:

- Grounded-death execution. `A_Teddy_DefeatGrounded` is bound on one boss and two stitchling deaths. That binding has not been shown playing.
- Seven-clip verification.
- Final close and wide captures.
- A normal moving-game recording.

The last movement attempt reached combat and restart, then timed out waiting for `gameplay-audio.wav`. Those frames are not an encoded clip. Shell and dressing stay on disk until that writer places them. FloorV3 covers two of the forty-five floor placements. TeddyV2 has thirteen crown stitches on the original skeleton. Neither has a close or wide plate accepted by this draft.

## Three holes that match public production notes

### 1. Fabric at gameplay size

Epic’s Cloth shading model is a thin fuzz layer. Its extra inputs are Fuzz Color and Cloth. Cloth is the mask: 0 leaves the base color, 1 blends fully to the fuzz color.

- [Material Inputs](https://docs.unrealengine.com/material-inputs-in-unreal-engine/)
- [Shading Models](https://docs.unrealengine.com/5.4/en-US/shading-models-in-unreal-engine)

Unreal 5.8 Substrate puts the same idea on the Slab as Fuzz Amount, Fuzz Color, and Fuzz Roughness. The Slab description calls that layer cloth fuzz.

- [Substrate overview](https://dev.epicgames.com/documentation/unreal-engine/overview-of-substrate-materials-in-unreal-engine)
- [UMaterialExpressionSubstrateSlabBSDF](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UMaterialExpressionSubstrateSlab-)

`tools/apply_comfy_surfaces.py` sets `MSM_CLOTH` on `M_Parity_TeddyCloth` and `M_Parity_StitchlingCloth`. The attributes node drives the amount through ClearCoat at 0.32. Fuzz Color and the Cloth mask are not connected in that script. `study/LIVE_BRIEF.md` still says the cloth stayed Default Lit. That sentence is older than the script. A new crop has to decide the read.

The last plate this study judged, `evidence/implementation/20261005T073350-capture_parity_look/01-matched-gameplay.png`, shows a warm brown boss. The crown reads as a dark crack. The weave does not carry at gameplay size. Take that closer crop of TeddyV2 before any more seam mesh.

The Chaos Clothing Tool is a particle simulation. It is a different system from the Cloth shading model.

- [Clothing Tool](https://docs.unrealengine.com/5.7/en-US/clothing-tool-in-unreal-engine/)

Chaos Cloth, ML cloth, and Dataflow cloth stay out of this encounter.

### 2. The round player pool

A spot light’s inner and outer cones only make a soft disc. Full brightness sits inside the inner cone. The ring between the cones is the penumbra.

- [Spot Lights](https://dev.epicgames.com/documentation/unreal-engine/spot-lights-in-unreal-engine)

An IES profile is the documented cheap way to break that round falloff. Epic describes it as faster than a light function. On a spot, the cone still clips the profile. Use IES Brightness left off keeps the actor’s own candela.

- [IES Light Profiles](https://dev.epicgames.com/documentation/unreal-engine/ies-light-profiles)
- [Light Functions](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-light-functions-in-unreal-engine)

No IES assignment was found in the project markdown, Python, or JSON. The hold stays about 16000 cd, relative (105, 0, 170), pitch −80°, inner 15°, outer 26°. Leave the pool unbaked. Do not widen the cone to 48°. The comfy trial at 8500 cd and cones 18/48 was the wide disc and stays retired. Key hold stays 165000 cd, source radius 70, color (0.50, 0.94, 1).

### 3. Feedback you can hear while the fight plays

Across 380-plus indie playtests, the repeated miss is action silence: no footstep, no land, no hit, and no confirmation that an attack connected.

- [Audio issues across 380+ playtests](https://weplaytestgames.com/blog/audio-issues/)

A published chapter-horror checklist treats the vertical-slice exit as an internal play of the core loop where lighting and audio both hold up. It also asks for a small clip library driven by blend trees and animation events, after the silhouette is locked.

- [Chapter-horror production notes](https://www.manillagames.com/poppy-playtime-chapter-3/)

A vertical slice is there to prove the core loop is legible. Visual quality does not stand in for that.

- [Vertical slice](https://game-developers.org/game-development-vertical-slice)

Local record, from [VFX_AUDIO.md](VFX_AUDIO.md):

| File | Seconds | Rate | Status |
| --- | ---: | ---: | --- |
| Rifle | 0.19 | 48000 | On disk. Not auditioned. |
| Slam | 0.80 | 48000 | On disk. Not auditioned. |
| ClothHit | 0.22 | 48000 | On disk. Not auditioned. |
| RoomTone | 16.0 | 48000 | On disk. Not auditioned. |

`tools/make_encounter_audio.py` used seed 74. `MASTER_PROMPT.md` and `REFERENCE_BRIEF.md` already say to review gameplay audio before claiming an audio match. There is no footstep file. `gameplay-audio.wav` never arrived. The only blend space found in tools is the human rifle blend space (`tools/build_combat.py`, `tools/refine_human_animation.py`). The twenty AnimPreprod clips are FBX on disk and are not on the teddy blueprint. Idle, Walk, Crawl, turns, steps, Threat, Search, WeightShift, WalkStop, Brace, Recover, Defeat, and DefeatBreath have no dedicated sound in that sheet. They sit on RoomTone alone.

Those sounds cannot be judged until the clip timing that will actually play is locked. The playtest, once a moving recording includes audio, is the existing minute: start, pipe orbit, the slam in the 220 cm pipe lane, the far door, the power orbit. Boss health 300, player 100, stitchlings 24. No new win condition.

## Reference gap

The candela holds were tuned by eye against the direction still. This study has no grey ball and no HDRI captured in the same camera. The holds are not a measured light match.

## Already covered

The plan already repeats meshes that exist: 303 placements, 107 shell, 41 kit, 110 dressing, 45 floor, four lanes at least 220 cm. Unique room meshes on disk: 10 kit, 17 shell, 36 dressing, plus the parity floor family and FloorV3. Combat footprint X −1400..1480 and Y −1500..1500 stays clear of shell, kit, and dressing.

Leave these unauthored: a new teddy or GLB, a fourth creature, a ceiling or truss, an open hall, a second wheel, a second tank or crate family, a luminous sign, a baked pool or shadow, another debris card, HUD art, a cloth simulation, extra boss phases, a get-up, and a floor-planted knuckle pound. The last two were specified and deliberately left unkeyed.

## Sources checked

Epic documentation retrieved 5 October 2026: Material Inputs, Shading Models (5.4), Substrate overview and Slab BSDF (5.8), Clothing Tool (5.7), Spot Lights, IES Light Profiles, Light Functions (5.6). Production notes: We Playtest Games audio survey, Manila Games chapter-horror checklist, game-developers.org vertical-slice note. Project files read for this draft: `WORK_STATUS.md` header, `tools/apply_comfy_surfaces.py` cloth graph, `study/preprod/VFX_AUDIO.md`, `study/preprod/PREPROD.md`. A project search for footstep, IES, and BlendSpace found the human rifle blend space and the unauditioned-audio warnings. It did not find a teddy blend space, a footstep asset, or an IES assignment.
