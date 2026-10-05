# Live study brief

## Current chamber handoff — 5 October 2026

Continue from [CHAMBER_PARITY_BRIEF.md](CHAMBER_PARITY_BRIEF.md) and [TEAM_CONTINUATION.md](TEAM_CONTINUATION.md). The [visual study](brief/index.html) now shows the final chamber targets/captures. Both walls and corrected V2 ground assets are implemented; final chamber and room suites pass28/28 each. Exact chamber parity remains open: continuous erosion, overhead haze, service readability and proportions. The latest native clip ends in player loss.

The sections below record the earlier close-shot integration and Grok work. Their values and gaps are historical, not the current chamber assignment.

5 October 2026. The selected look is [direction-close-best.jpg](visuals/direction-close-best.jpg). The four-panel board is a concept, not a capture. The sections after the integration note below preserve the earlier Grok build log; their settings and captures are historical.

## Current integration — 5 October 2026, 09:27 UTC

The combined selected-reference pass is in [WORK_STATUS.md](../WORK_STATUS.md), with an [active asset manifest](PARITY_ASSET_MANIFEST.md) and [visual review](../evidence/parity/20261005T070301Z/review.html). Root integrated after preserving the completed surface handoff; the separate source-only shell/dressing work was frozen and checked before import.

Current saved assets use TeddyV2's thirteen crown stitches on the original Skeleton, a separate grounded collapse, two revised fracture fields among the same forty-five floor placements, and sibling floor/cloth materials retaining the Grok texture inputs and original graphs. The active cloth really uses Unreal's Cloth model: material attributes route the amount through the exposed ClearCoat input, which maps to the cloth custom-data channel. The Default Lit statements below describe the earlier materials, not the current combined variant.

The room now includes eighty-four non-colliding shell/dressing instances from twenty-one selected meshes. Twenty-seven original boxes are concealed while their collision and transforms remain; existing props are retained. The larger seventeen-plus-thirty-six source catalogs and twenty optional pre-production clips are not all live. The old DefeatBreath is unassigned because it retains the former headstand ending.

The saved look uses FOV54, a focused teal key, a moving white player pool, broad volumetric rear haze and local character-only support at the perimeter. A separately checked rear-centre fill closes a player-visibility gap without illuminating the floor or adding fog. Fog spheres and bright horizontal fog-bar trials are retained only as failed evidence.

Functional evidence now includes 28 room checks, 48 skin/clip/death-route checks and 12 saved-key checks. Final six-view captures are in `evidence/implementation/20261005T092659-capture_parity_delivery`. Exact rendered parity and user acceptance remain separate; the independent review records the remaining stitch, wear and motion differences.

## What is already in the encounter

Preserved from the parity pass `evidence/parity/20261005T070301Z`, which saved and reopened the level:

- Crown and upper-back stitches on the existing sixteen-bone teddy, imported as `/Game/TeddyEncounter/Parity/Teddy/SK_TeddyParity` on that skeleton. The original GLB and `Teddy_Encounter.blend` were not replaced. Source body vertices, UVs, and weights stayed put.
- Six parity floor meshes, 45 non-colliding placements, materials `M_Parity_Aggregate` and `M_Parity_Crack`.
- `TE_Parity_Key`, `TE_Parity_FarFog`, and a player spot `ParityPlayerLight`. Older `TE_Key`, rim, and face fills were turned down. Exposure was not lifted.
- Graphic decals were hidden. The room kit stayed.
- Held plate: `evidence/implementation/20261005T071701-capture_parity_look/01-matched-gameplay.png`. Shaders compiled. Camera pitch −46°, FOV 54, 1280×720.

That plate has the long boss shadow, dark corners, a teal centre, and a visible head seam. The player pool is a hard white disc. The cloth reads as smooth brown. The floor cracks are shallow and even.

## This pass

ComfyUI 0.22.3 ran on a clean local server, port 8195, with pytorch attention. The desktop servers on 8188 and 8189 were left alone. The model is the installed Flux.2 Klein 4B FP8, Qwen 3 4B, and `flux2-vae`. Four steps, euler, cfg 1, 1024 square. No new checkpoint download. The scans are original. They are not img2img of the direction frames, and Hunyuan was not used.

Raw scans: `study/comfy-raw/cloth-weave.png`, `cloth-height.png`, `concrete-damp.png`. Tileable DirectX maps are in `Assets/Adapted/Parity/Surfaces/` and `study/assets/`. The weave is olive and taupe. The concrete scan has sparse dark patches and hairline cracks. `tools/apply_comfy_surfaces.py` puts the weave on the owned parity cloth, keeps `T_Teddy_BaseColor` and `T_AI_Floor_Color`, darkens stitchlings with `M_Parity_StitchlingCloth`, softens the player pool, and hides `TE_Room_FootDebris_*`. It does not move the key, fog, camera, or rig.

Cloth stays Default Lit. The earlier Cloth-shading pin was not a real custom-data amount.

## Latest plates

Shaders compiled. No `Failed to compile` in the capture logs. Manual exposure is still +3.8.

- Matched gameplay: `evidence/implementation/20261005T073350-capture_parity_look/01-matched-gameplay.png`
- Wide gameplay and four architectural views: `evidence/implementation/20261005T073442-capture_room_gallery/`

The matched plate shows a warm brown boss, a dark crown seam, three smaller creatures of the same family, a long shadow, dark corners, damp floor patches, and a softer player pool than the hard disc in `20261005T071701`. The wide plate shows two pin-sized red practicals and the same teal centre. The rear bulkhead plate shows the sealed door and one red point. A valve wheel is not obvious at that exposure.

The three largest remaining differences:

1. The crown seam reads as a dark crack. The separate thread bridges and the weave do not carry at gameplay size.
2. The floor cracks still look drawn. The damp patches help, and the rubble is too shallow to read as chips.
3. The player pool is rounder and hotter than a soft ground patch, and the player stays bright. At the wide corner the player is a small dim shape.

## Movement attempt

`evidence/implementation/20261005T073618-record_encounter` played the saved encounter: a dodge, a hit that took the player to 76 health, and boss health falling under fire. It then restarted and timed out at phase 10 while waiting for `gameplay-audio.wav`. There is no encoded clip. The editor exited afterward.

## Still open

- An encoded movement clip. The combat sequence itself ran.
- A closer cloth crop before any more seam geometry.
- Do not re-run `tools/apply_parity_look.py` over this pass. It rebuilds the parity floor and cloth materials without these maps.

## Do not author

A new teddy or GLB, a Hunyuan or TRELLIS replacement, a fourth creature, a ceiling, an open hall, a luminous sign, or a baked player pool.

## Room shell, off the level

The scene pass still owns the editor. These files were not imported.

`Assets/Adapted/RoomShell/` has 17 modular FBX meshes, 5,800 triangles, for the chamber boxes: walls, plinth, cornice, footing, gutter, cutaway, rear recess, shutter niche, pipe saddle, beacon cage, corner riser, conduit curb, upper bracket, cable tray, outer leaf, and ground apron. The ten-piece room kit is unchanged. The bulkhead wheel and the pipe-rack valve were not duplicated. Placement notes are in `README.md` and `manifest.json`.

`Assets/Adapted/RoomShell/Surfaces/` holds four tileable families: charcoal concrete, worn green-grey steel, muted oxide, and a near-black recess. Roughness stays in the art-direction bands. There is no teal wash and no player pool.

`Assets/Adapted/RoomDressing/` adds 36 more modules, 8,104 triangles: wall panels in three widths plus a tall bay, ribs, repair plates, wall spalls, conduits, elbows, tees, junction boxes, cable loops and drops, pipe elbows and flanges, hangers, a breaker, gang boxes, bundles, a threshold, anchors, a square drain, kickers, a louver, a closed hatch, a hose coil, a corner column, a door header, corner guards, unistrut, drip trays, a downspout, a dark meter, clamps, escutcheons, and a duct boot. Same five material slots. No wheel, tank, crate, or ceiling. The list is in `Assets/Adapted/RoomDressing/README.md`.

## Pre-production, off the level

`study/preprod/PREPROD.md` is the index. It adds concept stills, a reference order, twenty in-place clips, a 303-placement plan, a light and camera note, and a material and cue sheet. Unreal was not opened. The source teddy blend was not written back.

`Assets/Adapted/AnimPreprod/` holds `Teddy_<Clip>.fbx` for TurnLeft, TurnRight, StepLeft, StepRight, Telegraph, Recover, AttackLeft, Stagger, IdleHeavy, Threat, WalkStop, StitchlingIdle, StitchlingFlinch, DefeatBreath, Brace, HitLeft, SwipeLow, Search, Slump, and WeightShift. Pitch stays on local X. Turns use local Y, because 25° of spine Z folded the chest. DefeatBreath starts on Defeat frame 72 and does not stand up. Clay stills are in `previews/`. They are not a gameplay capture.

The plan in `study/preprod/layout.json` repeats the existing shell, kit, dressing, and floor meshes. The combat rectangle stays empty of those props. Left stays pipes. Right stays cabinets. Three red pins. The key hold cited there is 165000 cd and source radius 70. The player-spot hold is the tighter cone, not the 48° trial.
