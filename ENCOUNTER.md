# Teddy Encounter

Run [PLAY.cmd](PLAY.cmd) to play the corrected encounter. [EDIT.cmd](EDIT.cmd) opens its editable level. Both use the installed Unreal 5.8.3 and `TeddyBlueprint/TeddyBlueprint.uproject`, map `/Game/Maps/TeddyEncounter`. Close an existing editor before launching another instance. The launch helper prevents concurrent editors.

This is one playable encounter: an elevated camera, a rigged monstrous teddy, three crawling stitchlings, independent movement and aim, rifle fire, dodge, a telegraphed boss slam, damage, defeat and restart. Gameplay executes in saved Blueprints; Python is used for authoring and automated verification. No native project DLL or packaged distribution is required for this local launch.

The chamber now follows the supplied [front](study/visuals/chamber-target-front.png) and [reverse](study/visuals/chamber-target-reverse.png) references: a wide B-3 pressure bulkhead and wheel, two reverse service bays, structural piers, weathered walls, pipes, tanks, cabinets, low perimeter drains and broken concrete plates. The fourth wall automatically hides when the elevated camera moves outside it and remains visible from inside the room. Doors and machinery are static scenery; the ceiling stays open for the gameplay camera. The earlier [close reference](study/visuals/direction-close-best.jpg) still guides the encounter's teal character and moving white player pool. [Open the chamber comparison](evidence/chamber/20261005T095028Z/review.html).

## Controls

| Input | Action |
| --- | --- |
| WASD | Move relative to the combat view |
| Mouse | Aim independently across the arena |
| Left mouse button | Fire; ammunition is unlimited |
| Space | Dodge; 0.8-second cooldown and brief invulnerability |
| Escape | Pause/resume and show controls |
| F5 | Restart, including after victory or defeat |
| Alt+F4 | Close the game window |

These are proposed PC bindings, not bindings recovered from the reference. The 5 October QA repair corrected invalid Space/Escape/F5 mappings. Twelve fresh checks now exercise simulated keys through the saved mapping context, including restart while paused. Separate tests cover actions and cursor aiming. Physical keyboard/mouse and gamepad play remain unverified.

The boss has 300 health and a roughly 0.92-second warning before its slam. The player has 100 health. Each of the three stitchlings has 24 health; the remaining stitchlings collapse when the boss is defeated. Aim, move and shoot together; dodge outside the warning circle before the strike.

## Editable work and provenance

Owned Unreal assets are under `/Game/TeddyEncounter`, with the earlier selected-reference additions in `/Game/TeddyEncounter/Parity` and the latest room work in `/Game/TeddyEncounter/Chamber`. Camera framing tracks the player/boss pair at a fixed -46-degree elevation, FOV54, and widens for separation. Source starter animation clips remain shared read-only references; modified animation graphs and blend spaces are owned copies. The [earlier asset manifest](study/PARITY_ASSET_MANIFEST.md) and [chamber brief](study/CHAMBER_PARITY_BRIEF.md) distinguish active imports from preserved variants. Broad historical builders can overwrite later art assignments; they are not required to play or edit the saved encounter.

- [Teddy_Encounter.blend](Assets/Adapted/Teddy/Teddy_Encounter.blend): adapted mesh, weighted 16-bone rig and six exported clips: idle, walk, crawl, attack, hit and defeat. The latest ground-contact pass is described in [motion-refinement.json](Assets/Adapted/Teddy/motion-refinement.json). Walk/crawl use baked foot targets matched to gameplay speed.
- [Teddy_ParityV2.blend](Assets/Adapted/Parity/TeddyV2/Teddy_ParityV2.blend): thirteen weighted crown stitches and a separate dark seam, on the original body/UVs/weights and existing Skeleton. The saved encounter uses this skin for all four creatures. [Teddy_DefeatGrounded.blend](Assets/Adapted/Parity/DefeatGrounded/Teddy_DefeatGrounded.blend) adds the active grounded collapse; one boss and both stitchling death routes use its separate clip. The original six clips remain preserved.
- [Arena_Art.blend](Assets/Adapted/Arena/Arena_Art.blend) and [Encounter_Details.blend](Assets/Adapted/Arena/Encounter_Details.blend): original procedural rifle and warning ring, plus separately generated concrete textures. Authoring scripts and seeds are retained in `tools/` and the adapted asset provenance files.
- [IndustrialRoom_Kit.blend](Assets/Adapted/Room/IndustrialRoom_Kit.blend): ten original modular meshes, 49,280 triangles in the unique source kit. The existing room's 126 actors remain; 27 plain wall/pilaster boxes are now concealed while their collision and transforms are preserved. The selected shell/dressing extension adds 84 non-colliding instances of 21 meshes. The larger source catalogs and twenty optional animation clips are not all imported or assigned.
- [ParityFloor_Kit.blend](Assets/Adapted/Parity/Floor/ParityFloor_Kit.blend) and [ParityFracture_V3.blend](Assets/Adapted/Parity/FloorV3/ParityFracture_V3.blend): 45 non-colliding floor placements, including two revised fracture fields with worn tops and interrupted edges.
- [Chamber kit](Assets/Adapted/ChamberParity/manifest.json): new pressure door, wheel, reverse service bays and drums, with editable Blender source. Current floor sources are [FloorNormalsV2](Assets/Adapted/ChamberParity/FloorNormalsV2/manifest.json), [SlabsNormalsV2](Assets/Adapted/ChamberParity/SlabsNormalsV2/manifest.json) and [CrustNormalsV2](Assets/Adapted/ChamberParity/CrustNormalsV2/manifest.json): five connected fields, four sparse slab groups and five broader broken banks. The correction records include source/FBX face-direction and closed-volume audits. Earlier sources/imports remain preserved; 43 of the old 45 floor actors are visually hidden, with their transforms and collision retained.
- [Wall albedo](Assets/Adapted/ChamberParity/WallSurface/T_ChamberWall_Albedo.png), [exact prompt](Assets/Adapted/ChamberParity/WallSurface/prompt.txt) and [provenance](Assets/Adapted/ChamberParity/WallSurface/manifest.json): one built-in imagegen result, saved byte-for-byte, combined with retained normal/roughness inputs in new world-aligned wall materials. It is generated artwork, not a measured surface scan. The earlier wall material assets remain intact.
- [AI surface provenance](Assets/Adapted/Arena/ai-provenance.json): the separate user-owned Grok pass supplied nine generated floor/plush/decal maps. Later [ComfyUI maps](Assets/Adapted/Parity/Surfaces/provenance.json) and a separately generated concrete diffuse feed the active sibling materials. The current cloth uses Unreal's Cloth shading model and the original teddy base colour. Grok's earlier material graphs remain preserved; the prominent graphic decals are hidden. None of these textures was extracted from the reference video.
- The teddy derives from **Horror Teddy Bear Monster by Aiden Reynolds**, listed as CC0 1.0. [Original provenance](Assets/ThirdParty/HorrorTeddyBear/provenance.json) includes the source link, archived license evidence and hash. That record describes the unrigged download; adaptation/import work is recorded separately. The original GLB remains unchanged.
- Human mesh/animations and the underlying input logic derive from Epic's installed Twin Stick starter. They retain their original Epic terms; the teddy's CC0 listing does not relicense them.
- Ambience, rifle and slam sounds are original deterministic synthesis. [Audio provenance](Assets/Adapted/Audio/provenance.json) labels them as proposed original sound design. The source video's audio was not auditioned, and no audio match is claimed.

## Evidence and review

[Chamber comparison](evidence/chamber/20261005T095028Z/review.html) presents both supplied references beside direct 1920×1280 Unreal views, the pre-pass room and native moving gameplay. The comparison cameras are architectural views; ordinary gameplay retains FOV54 and its existing tracking. The [independent chamber review](evidence/chamber-qa/final/INDEPENDENT_REVIEW.md) separates visible reference differences from functional results. Current evidence covers 28 chamber ownership/placement/cutaway checks and 28 room/collision/camera checks. The silent native movie uses simulated input in a separate QA copy, with ordinary AI and health enabled. This take ends in player defeat and the F5 restart prompt; it does not establish a new boss-defeat result.

The [earlier selected-reference review](evidence/parity/20261005T070301Z/review.html) preserves its 48 skin/animation/death-route and 12 saved-key checks. Those character and input assets are unchanged in the chamber pass. Its independent rear-centre character-light repair is also retained.

The earlier [combined room review](evidence/full-room/20261005T050433Z/review.html), [repair review](evidence/qa-repair/20261005T042900Z/review.html) and [delivery evidence](evidence/delivery/README.md) remain preserved as history.

The full architecture is an authored extension guided by the selected concepts. Remaining chamber differences include more localized fracture patches and fine surface grain, more regular wall panels, weaker overhead haze and darker service recesses. The existing character anatomy and motion were outside this chamber pass. Exact visual parity and user acceptance are not established. Physical-device play, audio matching, packaged delivery and sustained performance remain unverified.

[PLAY_BASELINE.cmd](PLAY_BASELINE.cmd) opens the preserved Twin Stick starter. The separate native BossShot/BossArena experiment and source originals remain preserved. [WORK_STATUS.md](WORK_STATUS.md) records current results, failed approaches and continuation boundaries.
