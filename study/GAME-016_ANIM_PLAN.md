# GAME-016 animation import plan (prep, text sources only)

8 Oct 2026. Prepared for the Phase 2 escalation in [ENCOUNTER.md](../ENCOUNTER.md) (GAME-016 checklist, steps 1, 5, 6 and 7). Nothing here has been imported or run in Unreal yet. The only sources used were text: `Assets/Adapted/AnimPreprod/manifest.json`, `tools/make_anim_preprod.py`, `tools/adapt_teddy.py`, `tools/import_parity_defeat.py`, [ANIMATION](preprod/ANIMATION.md), plus the tracked content file list. The importer is `tools/build_boss_escalation_v1.py`. [GAME-016_EDITOR_RUN](GAME-016_EDITOR_RUN.md) explains how to run it.

## Clips

| Clip | Role in GAME-016 | State | Source |
|---|---|---|---|
| `Walk` | Chase loop; recovery end returns to it | Exists: `/Game/TeddyEncounter/Teddy/Walk/A_Teddy_Walk` | Shipped |
| `Attack` | Phase 1 anticipation, and every second anticipation in phase 2 | Exists: `/Game/TeddyEncounter/Teddy/Attack/A_Teddy_Attack` | Shipped, 54 frames |
| `Hit` | Hit reaction (unchanged; not played in state 5) | Exists | Shipped |
| `DefeatGrounded` | Death (unchanged) | Exists: `/Game/TeddyEncounter/Parity/Animation/A_Teddy_DefeatGrounded` | Parity import |
| `Stagger` | Phase change, first part | **Missing**: FBX on disk, not imported | `Assets/Adapted/AnimPreprod/Teddy_Stagger.fbx`, 24 frames |
| `Threat` | Phase change, second part | **Missing**: FBX on disk, not imported | `Teddy_Threat.fbx`, 45 frames |
| `AttackLeft` | First and every second phase-2 anticipation | **Missing**: FBX on disk, not imported | `Teddy_AttackLeft.fbx`, 36 frames, peak frame 20 |

**New FBX import needed:** yes, three animation-only imports of FBX files that already exist. No new FBX authoring and no Blender pass are needed.

The three FBX files in the worktree match the manifest sha256 values:
- Stagger `7fb167d8…`
- Threat `b7340638…`
- AttackLeft `c5c923e8…`

All twenty AnimPreprod clips are on the same 16-bone `Teddy_Skeleton` as the shipped clips. Nothing else from AnimPreprod (Telegraph, Recover, IdleHeavy and the rest) is needed for GAME-016.

**Import settings.** These mirror `tools/import_parity_defeat.py`, the import recipe already proven on this project:
- Legacy FBX: `Interchange.FeatureFlags.Import.FBX 0`.
- Animation only, onto `/Game/TeddyEncounter/Teddy/Idle/SK_Teddy_Skeleton`.
- No mesh, materials, textures or physics.
- `convert_scene`, `convert_scene_unit` and `force_front_x_axis`.
- Custom sample rate of 30. DefeatGrounded used 60, but these clips are keyed at 30.
- No custom attributes, and no curve metadata added to the skeleton.

**Destinations.** These follow the existing `PlayAnimation` path convention in `build_boss.py`:
- `/Game/TeddyEncounter/Teddy/Stagger/A_Teddy_Stagger`
- `/Game/TeddyEncounter/Teddy/Threat/A_Teddy_Threat`
- `/Game/TeddyEncounter/Teddy/AttackLeft/A_Teddy_AttackLeft`

Each one is tagged `TeddyEncounter.Owner`. The skeleton must not be saved by this run.

## Frame and timing basis

`make_anim_preprod.py` keys each clip on Blender frames 1..N at 30 fps and exports that range. `adapt_teddy.py` does the same for the shipped clips. Frame 1 imports as t = 0, so:
- an N-frame clip lasts (N−1)/30 s;
- frame k sits at (k−1)/30 s.

The script asserts the imported length is within 0.025 s of this, accepts N/30 too, and records which one matched. All timings it writes into the Blueprint come from the imported lengths, not from these constants.

| Quantity | Value |
|---|---|
| Stagger | 23/30 = 0.767 s |
| Threat | 44/30 = 1.467 s |
| Phase change (Stagger → Threat) | 2.233 s (ENCOUNTER.md: "≈ 69 frames ≈ 2.3 s" counts frames, not intervals) |
| Shipped Attack | 53/30 = 1.767 s ("1.8 s") |
| Phase-2 cycle | 0.92 s telegraph + 0.8 s recovery = 1.72 s |
| Attack cut in phase 2 | 1.767 − 1.72 ≈ 0.047 s (≈ 1.4 frames) |
| AttackLeft impact | frame 20 → 19/30 = 0.633 s at rate 1.0 |

## AttackLeft retime: play rate (Tech choice)

**Choice:** `SetPlayRate(impact_time / 0.92)` straight after `PlayAnimation(AttackLeft)`. That gives 0.633 / 0.92 ≈ **0.688**, and the impact lands on the 0.92 s damage and sound timer. The checklist says "≈ 0.73". It took the impact as 20/30 = 0.67 s, which would land the impact about 46 ms early, so the script computes the rate from the imported clip length instead.

**Why a play rate rather than a held pose:**
1. **One node, nothing to undo.** UE 5.8's `PlayAnimation` calls `UAnimSingleNodeInstance::SetAnimationAsset(asset, false)`, whose default `InPlayRate` is 1.0 (read in the engine source). Every other clip therefore resets to normal speed by itself. A held pose would need extra tick states to freeze and resume the clip. Each of those states would also have to be cancelled correctly on a phase change, a death or a hit, and that is exactly the edge case GAME-016 QA checks.
2. **It fits the cycle.** At 0.688 the whole clip lasts 35/30 / 0.688 ≈ 1.695 s, under the 1.72 s phase-2 cycle. So AttackLeft never gets cut, and only the shipped Attack does.
3. **It matches the existing telegraph.** The raise-and-pitch arc stretches evenly over the same 0.92 s as the shipped Attack, which reaches its raised peak at ≈ 0.88 s. A hold would add a frozen beat that no other boss move has.
4. **It needs no new asset.** A held pose would need a re-keyed clip (Blender) or an animation edit in the editor.

**Risk:** slowing to 0.69× softens the left-arm snap. The checklist asks for a capture to confirm it reads well. If it doesn't, the fallback is a held pose, which needs new tick states, or a re-keyed clip.

## Blends

- The boss mesh runs in `ANIMATION_SINGLE_NODE` (`build_encounter_scene.py`) with no AnimBP or montages. Every existing transition is an instant `PlayAnimation` switch: Walk→Attack, →Hit, →Defeat. Single-node mode has no crossfade.
- **Step 7 as built.** In phase 2, the existing recovery-end path switches to `Walk` at 0.8 s, about 0.047 s before `Attack` ends. Recovery is not lengthened (Producer default). The last ≈ 1.4 frames of Attack are the arms settling back toward the idle base, so the pop should be small. Only a capture can confirm that.
- **A true blend is a separate decision.** It needs either:
  - a boss AnimBP with a state machine or inertialisation, or
  - Attack/AttackLeft played as montages over a Walk base in the single-node instance.

  Either way it means new binary assets and editor verification, and it is out of scope for this prep.
- Stagger → Threat is also a switch, timed from the imported Stagger length. Both clips start from Idle frame 1, but Stagger ends back at idle, so the joint is pose-continuous.
- Threat ends at its last key, and the boss then switches to `Walk`. Threat ends partly raised, so this is the most visible pop in the change. It is worth checking in the capture.
- `Stagger` and `Threat` play with `bLooping=false`.

## Locks for the editor run

| Path | When | Current holder (8 Oct, 20:27 SAST) |
|---|---|---|
| `TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_TeddyBoss.uasset` | Before the run (the script refuses otherwise) | Unlocked |
| `TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_EncounterHUD.uasset` | Before the run (the script refuses otherwise) | Unlocked |
| `TeddyBlueprint/Content/TeddyEncounter/Teddy/{Stagger,Threat,AttackLeft}/A_Teddy_*.uasset` | New files: lock right after the import, before commit | n/a |

The run must leave these unchanged; the receipt hashes them before and after:
- `BP_Stitchling.uasset`
- `SK_Teddy_Skeleton.uasset`
- `Maps/TeddyEncounter.umap`

No boss AnimBP or montage assets exist.
