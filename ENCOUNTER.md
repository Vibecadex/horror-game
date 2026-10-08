# Teddy Encounter

Encounter spec for the chamber slice, based on **`main` @ `0387fe4`** (8 Oct 2026, 19:49 SAST), which includes PR #3, PR #4 and PR #6. [WORK_STATUS.md](WORK_STATUS.md) carries the current status and history.

**Labels:**
- **D**: design doc, or a producer-decided build default (marked "D, Producer 8 Oct"; Luther reviews it in the hub).
- **T**: Tech-verified against the saved Blueprints on 8 Oct 2026, and unchanged on `0387fe4`.
- **L**: Luther-approved design, 8 Oct 2026. Marked *not built* where it is still a Tech task.
- **P**: proposed; needs Tech or Luther.
- **Δ**: changed on `0387fe4`, Tech to reverify.

## Play

[PLAY.cmd](PLAY.cmd) plays `/Game/Maps/TeddyEncounter` and [EDIT.cmd](EDIT.cmd) edits it. Both use Unreal 5.8.3 and `TeddyBlueprint/TeddyBlueprint.uproject`. Run one editor at a time; the launch helper refuses a second one.

**Config (Δ):** `DefaultEngine.ini` sets the editor startup map and `GameDefaultMap` to `/Game/Maps/TeddyEncounter`. `GlobalDefaultGameMode` is `BP_EncounterGameMode_C`; until PR #6 these pointed at the Twin Stick starter. `DefaultGame.ini` names the project "Teddy Encounter" and adds packaging settings, but **no packaged build has been verified.** Tech should confirm a standalone launch lands in the encounter with the encounter game mode. `/Game/Maps/TeddyChamberParity` is a separate visual experiment, not this encounter.

One encounter in saved Blueprints (Python for authoring and verification only; no native module): elevated camera, teddy boss, three stitchlings, independent move and aim, rifle, dodge, telegraphed slam, defeat and F5 restart. Static doors and machinery; no ceiling.

## The teddy (L, 8 Oct 2026)

**The child's teddy is the scanned teddy, and that same teddy is the boss, transformed by the dream.** This overrules the "safe anchor, not an enemy" proposal (Codex pre-production D07).
- **Recognition (E01)** tests whether players spot the scanned teddy inside the boss. *P:* silhouette, colour and distinguishing marks should survive the transformation.
- **Identity source:** the [bear-scanner](study/BEAR_SCANNER_INTEGRATION.md) → [Bear Studio](study/BEAR_STUDIO.md) pipeline feeds the boss's identity.
- **Current state:**
  - The boss is still the CC0 *Horror Teddy Bear Monster* stand-in: 16-bone rig, TeddyV2 skin.
  - Scans import only as static props under `/Game/ScannedBears`.
  - The scanner's 21-bone template has been proven only on a synthetic fixture ([TEAM_RIG_NATIVE_REVIEW](study/TEAM_RIG_NATIVE_REVIEW.md)).
  - A studio rig does not by itself replace the enemy; integration goes through the map owner ([TEAM_CONTINUATION](study/TEAM_CONTINUATION.md)).
- **Combat contract (P):** the scan supplies the look and animation binding only. Collision, the slam radius, speeds and timings below stay fixed whatever the scan's size or rig.

## Controls

| Device | Bindings | Status |
|---|---|---|
| Keyboard and mouse | WASD move relative to the view · mouse aim · LMB fire (unlimited ammo) · Space dodge · Esc pause and controls · F5 restart (also after a win or loss, and while paused) · Alt+F4 quit | D; T |
| Keyboard extras | F fire · G or RMB use item · LShift dodge (not shown on the HUD) | T |
| Gamepad | Left stick move · right stick aim · RT fire · LT use item · LB dodge | T |
| Gamepad pause and restart | **To be added** | L, *not built* |

- Simulated input only (12/12 saved-key checks plus action and cursor tests); physical keyboard and mouse is unverified too.
- **No gamepad-support claim until a physical test (L).**
- "Use item" does nothing yet; there are no items.

## Boss states (T: `tools/build_boss.py`, saved `BP_Boss`)

| # | State | Behaviour | Exit |
|---|---|---|---|
| 0 | Chase | `Walk` loop, steers toward the player | Player ≤ 380 cm → 1 |
| 1 | Anticipation | `Attack` clip, `AttackRing` shown, stands still | Tick timer reaches 0.92 s: strike (ring off, `Slam` sound, damage if ≤ 475 cm) → 2 |
| 2 | Recovery | Clip plays out | After 1.15 s → 0 |
| 4 | Hit reaction | `Hit`; only from Chase, at least 1.3 s apart | After 0.32 s → 0 |
| 3 | Dead | `A_Teddy_DefeatGrounded`, collision off | Final |
| 5 | **Phase change** (L, *not built*) | Entered on the first hit that leaves HP ≤ 150, from any live state. The ring is hidden and any pending slam cancelled (D, Producer 8 Oct). `Stagger` → `Threat`, about 2.3 s. **Invulnerable**; no hit reactions; cannot trigger again | Clips end → 0, `bPhase2` set |
| — | **Phase 2** (L, *not built*) | Anticipation alternates `AttackLeft` / `Attack`; same 0.92 s telegraph and 475 cm radius; recovery 0.8 s | Until Dead |

- **No animation notifies (T).** Slam damage and sound come from the state timer.
- **Stitchlings (T: `build_stitchlings.py`).** `BP_Stitchling` is a copy of this graph, not a child, with its own values. It plays `Crawl` and dies when the boss dies.

## Combat numbers

| Value | Number | Status |
|---|---|---|
| HP: boss / player / stitchling | 300 / 100 / 24 (×3) | D; T |
| Rifle damage | 12 per hit (boss 25 hits, stitchling 2) | T: `build_combat.py` |
| Fire rate | 0.33 s between shots while held | T |
| Boss time to kill | About 8.25 s of on-target fire, plus the about 2.3 s invulnerable window | T; L (derived) |
| Projectile | 3200 cm/s, 1.6 s life | T |
| Slam damage | 24 | T |
| Telegraph | 0.92 s | D; T |
| Slam radius | 475 cm, centre to centre | T |
| Attack trigger | 380 cm | T |
| Time between slams | At least ≈2.07 s (0.92 + 1.15) | T (derived) |
| Phase 2 trigger | First HP ≤ 150; at 12 per hit that is 144, on the 13th hit | L (threshold derived) |
| Phase 2 recovery | 0.8 s | L, *not built* |
| Phase 2 time between slams | At least ≈1.72 s (0.92 + 0.8) | L (derived) |
| Boss walk speed | 105 cm/s as saved (`build_boss.py` sets 125; `build_stitchlings.py` overrides it) | T |
| Dodge | 0.8 s cooldown · 0.26 s invulnerability · about 345–350 cm (LaunchCharacter 2500) | D; T |
| Stitchling | Trigger 190 cm · radius 215 cm · 10 damage · 55 cm/s · 0.92 s telegraph and 1.15 s recovery inherited | T |
| Spawns | Player (−230, 570); boss (250, −230); stitchlings (650, 600), (−480, −500), (20, 1070) | D: [LEVEL_DESIGN](study/preprod/LEVEL_DESIGN.md) |

**HUD (T):**
- Player bar.
- Boss bar "THE UNRAVELLED".
- Controls line.
- Messages: `PAUSED`, `YOU FELL / F5 TO RESTART` and `THE STITCHES GIVE WAY / F5 TO RESTART`.

## Locked defaults (L)

1. **FOV 54.** Gameplay pitch is −46°, and the camera widens with player/boss separation (T; WORK_STATUS 5 Oct). The 48 in ROOM_ART_DIRECTION is historical.
2. **Walkable area at the walls' inner faces:**
   - X −1380 / +1440, Y ±1460 (T).
   - PR #3 kept 28/28 room checks, including the four collision bounds, so this is unchanged on `0387fe4`.
   - Other docs quote wall centrelines.
3. **Self-hiding camera-side wall, as built:**
   - A 100 cm front boundary.
   - `TE_Chamber_FrontCutaway` (`BP_ChamberCutaway`) hides when the camera's X < −1490 and shows from inside. This supersedes the "40–70 cm sill" docs.
   - **Δ:** PR #3 re-saved `BP_ChamberCutaway` in the bay pass (hash `e43fe006…` → `678a4ff5…`). Its 34/34 runtime audit, including the threshold transitions, passed on 5 Oct, but Tech should recheck it on `0387fe4`.
4. **Restart is F5 only, scoped to this chamber slice.** F5 reloads the level and there are no checkpoints. Save and Continue come later, at journey level.
5. **Gamepad:** pause and restart are to be added (*not built*). No support claim until a physical test.

**Room changes since `3a1d254` (Δ, art only):**
- Visible floor is now `FloorRecoveryV4`.
- Bay depth spots, smaller red practicals and a lower overhead rect.
- Exposure stays 3.8. The floor trace still hits `TE_ArenaFloor` at Z −5.
- Tech should recheck that the warning ring and creatures read clearly on the new floor and lighting.

## Phase 2 escalation (L, approved 8 Oct 2026, *not built*)

This reverses the `study/preprod/NEXT_GAPS_DRAFT.md` exclusion of "extra boss phases", with Luther's approval on 8 Oct 2026. It also supersedes the chamber-pass note "do not add a … phase" (WORK_STATUS, 5 Oct) for this phase only.

Summary: nominal trigger 150 HP (crosses at 144); about 2.3 s invulnerable `Stagger` → `Threat`; then 0.8 s recovery and alternating `AttackLeft` / `Attack` on the same telegraph and radius. Stitchlings unchanged.

**No-damage cue (P, awaiting approval)** for shots absorbed during the window:
- *Impact:* the projectile still hits and disappears, with an about 0.05 s grey flash from a desaturated sibling of `M_Muzzle`. No dust.
- *Sound:* `ClothHit` at about 0.6× pitch and about 0.1 volume.
- *Reaction:* none.
- *HUD:* the boss bar is grey for the window, then flashes red for about 0.15 s when `Threat` ends.

## GAME-016 build checklist (escalation)

Work under LFS locks on the touched assets. Edit the saved Blueprints directly; **do not rerun the historical builders** (`build_boss.py` and others refuse once the map exists).

1. **Import** `Stagger`, `Threat` and `AttackLeft` from `AnimPreprod` onto the teddy Skeleton, as owned assets under `/Game/TeddyEncounter`. Confirm `Stagger` + `Threat` ≈ 69 frames at 30 fps (≈ 2.3 s).
2. **Phase state.** In `BP_Boss`, add state 5 and `bPhase2`. Enter on the first damage that leaves HP ≤ 150 with `bPhase2` false, from any live state. Cancel any pending strike, hide `AttackRing`, play `Stagger` → `Threat`, then go to 0 and set `bPhase2`.
3. **Damage ignore.** In `ReceiveAnyDamage`, return early while state = 5: no HP change, no hit reaction. Fire the no-damage cue if approved.
4. **Recovery switch:** Recovery duration = `bPhase2` ? 0.8 : 1.15 s.
5. **Alternating clips.** In phase 2, Anticipation toggles `AttackLeft` / `Attack` on each entry (starting with `AttackLeft`: D, Producer 8 Oct). The timer, ring, sound and radius are unchanged.
6. **AttackLeft retime.** Its impact (frame 20, ≈ 0.67 s; [ANIMATION](study/preprod/ANIMATION.md)) must land at the 0.92 s timer. Tech chooses between a ≈ 0.73 play rate and a held anticipation pose, whichever reads better in a capture, and records the choice in the PR (D, Producer 8 Oct).
7. **Attack cut short.** The 1.8 s `Attack` clip exceeds the 1.72 s phase-2 cycle by ≈ 0.08 s. Blend into `Walk`; accept the small cut rather than lengthening recovery (D, Producer 8 Oct).
8. **HUD.** `BP_EncounterHUD` greys the boss bar while state = 5, then flashes red for ≈ 0.15 s on exit.
9. **No-damage cue (P).** Grey `M_Muzzle` sibling at impact, plus pitched-down `ClothHit` (VFX_AUDIO). Build it only after approval.
10. **Leave `BP_Stitchling` alone.** It is a copy, so it keeps 1.15 s recovery; don't re-duplicate the boss.

**QA:**
- Triggers once, at the first HP ≤ 150 (shows 144).
- Zero boss HP loss across the window, so a lethal hit can't land in it. `Stagger` never loops.
- A pending slam is cancelled when the change starts; no damage arrives from a hidden ring.
- The cue and grey bar appear only in the window; the bar restores when `Threat` ends.
- Phase-2 slam gap is at least ≈ 1.72 s, and each clip's impact matches the 0.92 s damage and sound.
- Stitchlings stay damageable in the window. This is an *assumption*: the decision names only the boss.
- F5 (including while paused) restores phase 1 at 300 HP.

## Known issues (D: PR #1 notes)

- The boss keeps attacking a dead player.
- Dead stitchlings may replay their death when the boss dies.
- F5 always opens `/Game/Maps/TeddyEncounter`.
- An edge-test evade passed with the player out of range (≈ 627 vs 475 cm).

## Open decisions (Luther)

1. Keep LT and G/RMB "use item", or remove them?
2. Move the slam (damage and sound) to an animation notify?
3. Audio goal: readability first, then dread?
4. Skip the intro on retry?
5. Approve the no-damage cue as specified?

## Provenance and limits

- **Owned assets:** `/Game/TeddyEncounter` (`/Parity`, `/Chamber`), with room and asset provenance in [study/PARITY_ASSET_MANIFEST.md](study/PARITY_ASSET_MANIFEST.md) and [study/CHAMBER_PARITY_BRIEF.md](study/CHAMBER_PARITY_BRIEF.md).
- **Current teddy:** *Horror Teddy Bear Monster* by Aiden Reynolds, CC0 1.0 ([provenance](Assets/ThirdParty/HorrorTeddyBear/provenance.json)). Adapted 16-bone rig, six clips plus `DefeatGrounded`, TeddyV2 skin.
- **Human mesh and input:** Epic Twin Stick, under Epic's terms.
- **Sounds:** original synthesis ([audio provenance](Assets/Adapted/Audio/provenance.json)).
- **Not established:**
  - visual parity
  - user acceptance
  - physical-device play
  - audio match
  - packaged delivery
  - performance
  - scanned-teddy boss integration
