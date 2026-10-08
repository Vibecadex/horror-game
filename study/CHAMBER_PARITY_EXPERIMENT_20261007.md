# Isolated chamber parity attempt — 7 October 2026

This is the user-requested side-branch attempt against the supplied full-chamber image. **It improves the saved room; exact parity and user approval remain open.** It does not continue the scanner integration or replace the shared encounter.

- Branch: `codex/chamber-parity-20261007`, created from `9defbdd` (contains the saved chamber and fetched main fixes).
- Original-workstation worktree: `C:/Users/4elut/.codex/worktrees/chamber-parity-20261007/horror-game`.
- Candidate: `/Game/Maps/TeddyChamberParity` in `TeddyBlueprint/TeddyBlueprint.uproject`.
- New assets: `/Game/TeddyEncounter/ChamberParity20261007`, metadata `ChamberParity.Owner=chamber-parity-20261007`.
- [Interactive reference/before/after review](../evidence/chamber-parity/20261007/review.html).
- [Exact user-supplied reference](../evidence/chamber-parity/20261007/user-reference.png); the stored earlier concept is a different file. Their hashes are retained in [baseline.json](../evidence/chamber-parity/20261007/baseline.json).

## Play and edit

Close any running Unreal editor/game, then run `PLAY_CHAMBER_PARITY.cmd` from this worktree. `PLAY_CHAMBER_PARITY.cmd --edit` opens this candidate for editing. The launcher changes only its own process settings. Ordinary `PLAY.cmd` continues to open the preserved `/Game/Maps/TeddyEncounter`.

Controls remain WASD movement, mouse aim, left mouse fire, Space dodge, Escape pause/resume, F5 restart. This pass verifies injected key paths, not physical-device input. No package installation, native compilation, global settings or security changes were required.

## Implemented candidate

The wall shells and pilasters are 1.35 times their prior height, with the bulkhead 1.32 times its prior height. Cornices, wheel, door indicators, rear fan and overhead fixture have corresponding placements. These are saved actor-instance changes; shared mesh and Blueprint assets remain unchanged. The native opposite-wall cutaway still controls the same Blueprint instance.

The visible recovery floor mesh is preserved. Six new material graphs are assigned to its placed component. They use retained authored floor textures with clearer fractures and bounded damp variation. A first overly glossy/cloudy trial was rejected; the current wet roughness is 0.60 and dry roughness 0.94, with reduced specular response.

710 original closed concrete fragments contribute 15,988 triangles across four visible banks. Their underside vertices are raycast onto the preserved recovery FBX with a 2 mm embed. Blender export/reimport dimensions and triangle counts pass; authored fragments are manifold. The second source revision uses larger fragments; the first stays hidden as iteration history. Seven new front drainage pieces reuse the existing grate mesh. Added floor decoration has no collision.

The candidate reduces the broad key, wall and corner washes, adjusts the foreground return, and adds a local overhead spotlight plus upper fog volume. The volume includes a weak teal emissive contribution. Native fog rendering flags are confirmed enabled, but the reference's suspended light column is still materially stronger. Manual exposure remains +3.8; no screenshot grading, cropping or warping is used.

Characters, animation, controls, gameplay Blueprint assets, ordinary camera and collision floor are preserved. The original room plus all 826 baseline Content/Config/source files are byte-identical.

## Evidence and QA limits

| Evidence | Result |
| --- | --- |
| [Fresh baseline](../evidence/implementation/20261007T134917-capture_chamber_views/receipt.json) | Four native 1440×960 views of the original map. |
| [Final authoring](../evidence/implementation/20261007T141818-author_chamber_parity_20261007/receipt.json) | Revision 4 saved and explicitly reloaded in Unreal 5.8.3. |
| [Final native captures](../evidence/implementation/20261007T142109-capture_chamber_views/receipt.json) | Full room, original front, reverse, and held ordinary gameplay camera. |
| [Native room runtime](../evidence/implementation/20261007T141010-verify_full_room/receipt.json) | 28/28: clear routes and spawn capsules, wall walk/dash blocking, twelve camera pairs, six decoded gameplay views. |
| [Separate host audit](../evidence/chamber-parity/20261007/qa.json) | 26/26: 826-file preservation, characters/camera/collision state, new decoration, material assignment, native cutaway, and geometry identity since the runtime run. |

Runtime checks ran on revision 2 geometry. Revisions 3–4 alter only lighting/materials and a non-colliding fog volume. The host audit compares all saved mesh transforms, visibility, material paths and collision modes to retain the geometry coverage. The revised material bytes are new owned assets. The room test's original 700 cm height bound remains unchanged for the original map; the candidate has an explicit 935 cm bound for its 926.5 cm far shell.

This is a separate QA process using existing runtime checks plus a host preservation audit. The author also reviews the images; **no independent agent review or user visual acceptance is claimed**. No new combat movie, physical-device check, audio matching, package build or sustained performance certification was done.

Architectural plates hold characters and hide HUD; environment Blueprint ticks remain active. Both maps use the same camera for each before/after pair. The added full-room camera is location `(-4250,180,3380)`, target `(100,180,80)`, FOV 47°, native 3:2. The historical front/reverse cameras remain available. Gameplay stays at pitch −46° and FOV 54°.

## Remaining visual work

1. The suspended teal shaft is still weak and the peripheral equipment loses more detail in darkness than the reference.
2. The floor has more visible erosion and fragments, but its long straight splits, regular shards and patterned texture are still apparent. The target has more convincing broken slab margins and larger connected damage.
3. Side services, upper-wall construction and reverse recess depth remain simpler; stretching existing architecture is not a substitute for more detailed construction.
4. Camera composition is approximate. The review camera exposes the full room but is not part of gameplay. Character anatomy/pose differences remain outside this chamber pass.

## Continue or reproduce

Use one Unreal writer. Lock the candidate map and any existing owned packages before editing. Do not force or release the original encounter lock. New settings live in [chamber-parity-20261007.json](chamber-parity-20261007.json); new source art is under `Assets/Adapted/ChamberParity/Parity20261007/DebrisV2`.

```powershell
python tools/run_encounter_test.py tools/author_chamber_parity_20261007.py
$env:TEDDY_CHAMBER_MAP='/Game/Maps/TeddyChamberParity'
$env:TEDDY_CHAMBER_FULL='1'
$env:TEDDY_CHAMBER_WIDTH='1440'
$env:TEDDY_CHAMBER_HEIGHT='960'
python tools/run_encounter_test.py tools/capture_chamber_views.py
python tools/run_encounter_test.py tools/verify_full_room.py
# Use the new run paths printed above:
python tools/review_chamber_parity.py --capture evidence/implementation/<capture-run> --room-check evidence/implementation/<room-run>
python tools/build_chamber_parity_review.py
```

The initial authoring run failed on Blender's `Concrete_001` slot suffix before saving the candidate changes. Its newly created template map needed its ownership tag persisted. A one-time, exact-SHA recovery records that operation; it cannot adopt arbitrary maps. Failed and rejected trials remain in evidence, and the original map was never saved by this pass.

Technical references used: [Epic local fog volume component](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/ULocalFogVolumeComponent), [Epic exponential height fog component](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UExponentialHeightFogComponent), [Blender mesh API](https://docs.blender.org/api/current/bpy.types.Mesh.html), and installed Unreal 5.8.3 headers. Existing tools were reused; no installations were run.
