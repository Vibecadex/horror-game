# GAME-016 editor run

`tools/build_boss_escalation_v1.py` prepares the Phase 2 escalation on the saved boss. It does not launch Unreal by itself. Luther runs the editor commands below. Agents must not set `TEDDY_GAME016_APPLY`.

## What it changes

On apply it imports `Stagger`, `Threat`, and `AttackLeft` onto the owned teddy skeleton (`/Game/TeddyEncounter/Teddy/<Clip>/A_Teddy_<Clip>`, 30 fps, animation only). It then edits `BP_TeddyBoss` and `BP_EncounterHUD` in place:

- State 5 and `bPhase2`. The first hit that leaves HP at or under 150 (144 on the 13th rifle hit from 300) hides `AttackWarning`, leaves state 1 so a pending slam cannot fire, plays `Stagger` once, then `Threat` once, then returns to state 0 and sets `bPhase2`.
- `ReceiveAnyDamage` returns while state is 5. The no-damage cue is a marked no-op only.
- Recovery uses `SelectFloat`: 0.8 s in phase 2, 1.15 s in phase 1.
- Phase 2 anticipation alternates `AttackLeft` and `Attack`, opening on `AttackLeft`. `PlayAnimation(AttackLeft)` is followed by `SetPlayRate`. The rate is `impact_time / 0.92`, with `impact_time = (20-1)/(36-1) * play_length` (about 0.688 on the formula length). It is not hard-coded.
- Phase 2 recovery still ends on looping `Walk` at 0.8 s, so the shipped `Attack` is cut about 0.047 s early. Single-node mode has no crossfade.
- The boss bar goes grey while state is 5, then bright red for 0.15 s.

Class defaults stay phase 1 (`bPhase2` false, health 300), so F5 reloads phase 1. The copied blueprint, the map, the skeleton, and the existing builders are not edited. No animation blueprint, montage, or blend space is created.

## Commands

From the repo root:

```text
python tools/build_boss_escalation_v1.py --plan
python tools/build_boss_escalation_v1.py --plan --json
python tools/astra_setup.py editor-script tools/build_boss_escalation_v1.py
```

The last command is a read-only inspect: it checks anchors and writes a receipt, and it does not save. Apply, in the same PowerShell window, only after the locks below are ours:

```powershell
$env:TEDDY_GAME016_APPLY = '1'
python tools/astra_setup.py editor-script tools/build_boss_escalation_v1.py
Remove-Item Env:TEDDY_GAME016_APPLY
```

Any other command outside the editor exits 2. Inspect and apply write `evidence/game-016/<UTC stamp>-<inspect|apply>/escalation-receipt.json`. `--plan` does not write a receipt.

## LFS locks

Take these before apply:

```text
git lfs lock TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_TeddyBoss.uasset
git lfs lock TeddyBlueprint/Content/TeddyEncounter/Blueprints/BP_EncounterHUD.uasset
```

Apply runs `git lfs locks --verify --json` and continues only when both paths are in `ours`. The expected JSON is an object with `ours` and `theirs` arrays of `{ "path": "..." }`. A non-zero git exit, unreadable JSON, a required path in `theirs`, or a missing path aborts before any edit. If a phase-2 clip `.uasset` already exists, that path must be in `ours` too.

After a successful import, and before commit, also lock:

```text
git lfs lock TeddyBlueprint/Content/TeddyEncounter/Teddy/Stagger/A_Teddy_Stagger.uasset
git lfs lock TeddyBlueprint/Content/TeddyEncounter/Teddy/Threat/A_Teddy_Threat.uasset
git lfs lock TeddyBlueprint/Content/TeddyEncounter/Teddy/AttackLeft/A_Teddy_AttackLeft.uasset
```

`python tools/astra_setup.py editor-script` refuses while any `UnrealEditor.exe` or `UnrealEditor-Cmd.exe` is running, so close the editor first and run one Unreal process at a time.

**External packages after save.** `TeddyEncounter.umap` has no tracked `__ExternalActors__` / `__ExternalObjects__` packages, and this script never saves the map, the skeleton or `BP_Stitchling`. Their byte hashes go in the receipt. After apply, check `git status` and lock any `.uasset` or `.umap` that shows as modified beyond the five paths above. Do not commit a changed map, skeleton or stitchling: restore it from git and report it.

## After the run

Reopen the editor. The commandlet does not stay open. Confirm `TeddyEncounter.Game016` is `escalation-v1` on `BP_TeddyBoss`, and that a fresh PIE still starts in phase 1 at 300 HP.

PIE and standalone, from ENCOUNTER.md:

- The phase change triggers once, at the first HP at or under 150 (the bar shows 144).
- Boss HP does not fall during state 5. `Stagger` does not loop.
- A pending slam is cancelled; a hidden ring deals no damage.
- The boss bar is grey only during state 5, flashes red for about 0.15 s when `Threat` ends, then returns to the original colour. The impact cue is not in this build.
- Phase-2 slams stay at least about 1.72 s apart, and the `AttackLeft` impact lines up with the 0.92 s damage and sound.
- The copied blueprint stays damageable during the window.
- F5, including while paused, restores phase 1 at 300 HP.

A second apply with the tag already set is a no-op success. A graph that already has `bPhase2` (or any other new variable) without the tag is refused. Do not repair it in place.

Apply compiles both blueprints in memory and saves nothing until both compile cleanly. It then writes the tag and saves the HUD, then the boss (Tech review change). Imported clips are saved as they are imported, and a rerun reuses them. If apply stops between the two blueprint saves, restore `BP_TeddyBoss.uasset` and `BP_EncounterHUD.uasset` from git before trying again. Do not retry a half-saved graph, and do not expect the script to revert it.

## Open items

- A true blend of the cut-short `Attack` into `Walk` needs a later choice: an animation blueprint, or a montage driven from single-node. This pass only cuts.
- The no-damage cue (checklist step 9) waits for approval.
- Warning-ring readability on `FloorRecoveryV4` still needs an in-editor capture.

## Run log, 2026-10-08 (Horror Unreal Tech)

Locks taken before any launch: `BP_TeddyBoss.uasset` (55920562) and `BP_EncounterHUD.uasset` (55920563). One Unreal process at a time; none was running before each launch.

| SAST | Mode | Exit | Receipt (`evidence/game-016/`) | Result |
|---|---|---|---|---|
| 21:27:42 | inspect | 1 | `20261008T192751Z-inspect` | `ReceiveAnyDamage.then: expected Health > 0`. No detail on which check failed. |
| 21:33:25 | inspect (dump build) | 1 | `20261008T193333Z-inspect` | Dump: the condition is `K2Node_PromotableOperator` titled `float > float`. Its `function_reference` cannot be read from Python, and the unlinked `B` pin's saved default is `''`. Failed check: `B literal`. |
| 21:35:12 | inspect | 1 | `20261008T193519Z-inspect` | `state 0`: the integer compare is a `K2Node_PromotableOperator` titled `Equal (Integer)` (KismetMathLibrary DisplayName for `EqualEqual_IntInt`), not `integer == integer`. |
| 21:37:00 | inspect | 0 | `20261008T193707Z-inspect` | Passed. All boss and HUD anchors found, saved state `ready`, tag empty. |
| 21:37:22 | apply | 1 (native crash) | none written | `EXCEPTION_ACCESS_VIOLATION` in `UnrealEditor-BlueprintEditorLibrary.dll`, called from Python. Crash report: `.tool-cache/unreal-user/Saved/Crashes/UECC-Windows-B272691942C255BB67D4808B024EDE28_0000`. |

What the apply did before the crash: it imported and saved the three clips (`Teddy/Stagger`, `Teddy/Threat`, `Teddy/AttackLeft`), then added the ten variables to the in-memory boss. About 2.6 s later it crashed, either during the boss graph edit or the in-memory compile. The script did not get to the save step. `git status` afterwards showed `BP_TeddyBoss`, `BP_EncounterHUD`, the map, the skeleton and `BP_Stitchling` unchanged. Nothing needed restoring. The three new clip `.uasset`s are on disk, untracked and locked by lutherfourie, so a rerun's lock check accepts them and reuses them.

Reader fix (accepted equivalent forms only):

- A compare's operator comes from a readable Kismet function name. When that name cannot be read, a `K2Node_PromotableOperator` or `K2Node_CallFunction` with `A`, `B` and a Boolean `ReturnValue` is read by its title: `float > float`, `integer >= integer`, `Equal (Integer)`, `Not Equal (Integer)` and so on. The old pin-shape-only fallback, which accepted any binary operator, is gone. A different operator, a non-Boolean result or another node class fails the `function` check.
- An empty default on an unlinked numeric pin reads as 0, which is the compiler's type default. An empty default on an unlinked Boolean pin reads as false. A linked pin, a non-numeric type or unparsable text still fails.
- Every anchor mismatch raises `AnchorError` with `checks` (which check failed and what it saw) and `node_dump` (class, title, member reference, every pin's direction, type, default and links, and the upstream data nodes). Both go into the receipt as `anchor_failure`.
- Apply now prints `GAME-016 stage: <step>` before each native step, so after a native crash the last stage line in `editor.log` names the step.

Before the next apply: get a human decision on the crash first. One option is to run inspect plus apply once with the breadcrumbs to find the crashing step. Another is to open `BP_TeddyBoss` in the editor and try the same edit by hand. Do not loop applies.

| 21:45:03 | apply (one breadcrumbed retry) | 1, native crash | none; log copied to `evidence/game-016/20261008T194517Z-apply-crash/editor.log` | Null access violation (`0x0`) during the new in-memory refresh compile. The log shows the ten `Could not find a match` lookups, then a fresh burst of `Missing input pin` warnings, then the crash. No callstack frames were flushed. `print` stages never reach `editor.log`; `unreal.log_warning` does, and that is wired in for a future run. Blueprints, map, skeleton and stitchling unchanged. No further launches. |
