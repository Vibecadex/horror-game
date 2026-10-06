# Teddy Encounter — chamber continuation

Private Vibecadex team workspace. **The chamber is playable; exact visual parity remains open.** Continue the saved Unreal project against the two selected full-room references.

- [Current chamber brief](study/CHAMBER_PARITY_BRIEF.md): saved state, remaining work and acceptance criteria.
- [Visual study](study/brief/index.html): open locally after cloning for paired references and engine output.
- [Independent final QA](evidence/chamber-qa/final/INDEPENDENT_REVIEW.md) and [comparison image](evidence/chamber-qa/final/comparison.png).
- [Team workflow and continuation prompt](study/TEAM_CONTINUATION.md).

The [fresh-clone verification](evidence/team-handoff/remote-clone-verification.json) confirms all766 Content hashes, hydrated LFS assets, working review links and portable launch paths. This is checkout verification; the independent chamber review still records the open visual gaps.

## Prerequisites and first run

Windows, **Unreal Engine 5.8.3**, Git with Git LFS, and Python 3.11 or newer on PATH. Use your existing authorized Epic installation. Runtime gameplay is Blueprint-only: no project DLL, signing certificate or custom compiled plugin is needed. Blender/FFmpeg support optional authoring/capture; an AI CLI is not required to play or edit.

```powershell
git clone https://github.com/Vibecadex/horror-game.git
cd horror-game
git lfs install --local
git lfs pull
python tools/team_check.py --verify-handoff
.\PLAY.cmd
```

For an engine installed elsewhere, set its root before the check:

```powershell
$env:TEDDY_ENGINE_ROOT = 'D:/Epic Games/UE_5.8'
```

Alternatively copy `tools/project-settings.local.example.json` to `tools/project-settings.local.json` and set `engine_root`. The local file is ignored by Git. No global settings are changed.

**PLAY.cmd** opens `/Game/Maps/TeddyEncounter`. Close the game before **EDIT.cmd**, which opens that same map. The project is `TeddyBlueprint/TeddyBlueprint.uproject`. First launch may compile shaders. Controls: **WASD** move, **mouse** aim, **left mouse** fire, **Space** dodge, **Escape** pause/resume, **F5** restart. `PLAY_BASELINE.cmd` opens the preserved Twin Stick starter.

The check names missing prerequisites and never installs them. Run any installation yourself. `START_ASTRA.cmd` is an optional original-workstation setup workflow with its own CLI/authentication/full-check requirements, not the team's first-run dependency.

## Scanned bears

Phone-scanned bears from the [bear scanner](https://github.com/Vibecadex/bear-scanner) import as ready-to-place props. Clone `bear-scanner` next to this repo (or set `bear_scanner_repo` in `tools/project-settings.local.json`), start the scanner or set `bear_source` to a `model.glb`/folder, close the editor, then:

```powershell
python tools/run_encounter_test.py tools/import_scanned_bears.py
```

For many bears on a first run, set `$env:TEDDY_TEST_TIMEOUT = '1800'` first (default 420 s). Each bear becomes `/Game/ScannedBears/<Name>_<id>/SM_Bear_<Name>`: one Static Mesh with LOD0-2, convex collision and its texture, real size in cm, pivot under the feet. Re-runs skip unchanged bears; rebuilt or renamed bears update their existing mesh. The run fails, with the reason in its receipt, if any bear fails or none is found. The import never touches `/Game/TeddyEncounter`, the map or its Blueprints; placing bears is the map owner's call. On the first run, confirm the facing (expected −X) and the LODs in the Static Mesh editor. Details: `tools/import_scanned_bears.py`.

## Repository contents

The complete saved Blueprint project's Content/Config, starter dependencies, adapted Blender/FBX/textures/audio, original CC0 teddy with provenance, selected references, user-supplied reference video/archive copies, tools, study and retained review evidence are included. Binary files use Git LFS; `.umap`, `.uasset` and `.blend` are lockable.

Generated caches, credentials, raw recording-frame directories, setup/debug logs, recovery ZIPs and the separate native BossShot experiment stay on the original workstation. [Repository scope](study/TEAM_CONTINUATION.md#repository-scope) lists exclusions. Historical reports may refer to those local-only records; they are not fresh workstation verification.

The handoff removes the local Android File Server token and disables that unused server in tracked config. Game Content and input bindings are unchanged. Service authentication is not shipped.

Third-party provenance remains under `Assets/ThirdParty`. Epic starter content retains Epic's terms; no open-source license is applied to the entire repository. Supplied videos/concepts are reference material, not a grant of redistribution rights.
