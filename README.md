# Teddy Encounter — chamber continuation

Private Vibecadex team workspace. **The chamber is playable; exact visual parity remains open.** Continue the saved Unreal project against the two selected full-room references.

This fork integrates Bear Scanner with the saved chamber. See [scanner setup and verification](study/BEAR_SCANNER_INTEGRATION.md).

The [remote team continuation](study/REMOTE_TEAM_CONTINUATION.md) records the latest pack integration, verification and remaining rig-test prerequisites. Bear Studio now imports the team's versioned packs and retains their source checks and landmarks.

The team's 21-bone rigfit prototype now has a [native Unreal compatibility review](study/TEAM_RIG_NATIVE_REVIEW.md), including four source clips and three mannequin retargets on a synthetic fixture. Run `REVIEW_TEAM_RIG.cmd` to repeat the saved-asset and playback checks. Real-scan and production character acceptance remain open.

**Bear Studio:** run [BEAR_STUDIO.cmd](BEAR_STUDIO.cmd) for the local teddy catalogue, inspection, draft rigging, animation testing and versioned exports. [Studio guide](study/BEAR_STUDIO.md) covers prerequisites, source preservation and the review workflow. The saved chamber remains a separate playable destination.

- [Current chamber brief](study/CHAMBER_PARITY_BRIEF.md): saved state, remaining work and acceptance criteria.
- [Visual study](study/brief/index.html): open locally after cloning for paired references and engine output.
- [Current bay and atmosphere note](evidence/chamber/20261005T170149Z/BAY_ATMOSPHERE_QA.md). The [floor recovery](evidence/chamber/20261005T161155Z/FLOOR_RECOVERY_QA.md) and [its image review](evidence/chamber-qa/grok-20261005T163731/INDEPENDENT_REVIEW.md) are the prior floor candidate.
- [Team workflow and continuation prompt](study/TEAM_CONTINUATION.md).

The [pre-Grok QA](evidence/chamber-qa/final/INDEPENDENT_REVIEW.md) and the [766-file clone receipt](evidence/team-handoff/remote-clone-verification.json) are the historical handoff. They do not accept the recovery floor. The current candidate's map and source hashes are in [delivery-inputs.json](evidence/chamber/20261005T161155Z/delivery-inputs.json).

## Prerequisites and first run

Windows, **Unreal Engine 5.8.3**, Git with Git LFS, and Python 3.11 or newer on PATH. Use your existing authorized Epic installation. Runtime gameplay is Blueprint-only: no project DLL, signing certificate or custom compiled plugin is needed. Blender/FFmpeg support optional authoring/capture; an AI CLI is not required to play or edit.

```powershell
git clone https://github.com/Vibecadex/horror-game.git
cd horror-game
git lfs install --local
git lfs pull
python tools/team_check.py
.\PLAY.cmd
```

`python tools/team_check.py --verify-handoff` hashes the original Content files from the first handoff. It is expected to fail after this recovery and any later art. The command above is the first-run check.

For an engine installed elsewhere, set its root before the check:

```powershell
$env:TEDDY_ENGINE_ROOT = 'D:/Epic Games/UE_5.8'
```

Alternatively copy `tools/project-settings.local.example.json` to `tools/project-settings.local.json` and set `engine_root`. The local file is ignored by Git. No global settings are changed.

**PLAY.cmd** opens `/Game/Maps/TeddyEncounter`. Close the game before **EDIT.cmd**, which opens that same map. The project is `TeddyBlueprint/TeddyBlueprint.uproject`. First launch may compile shaders. Controls: **WASD** move, **mouse** aim, **left mouse** fire, **Space** dodge, **Escape** pause/resume, **F5** restart. `PLAY_BASELINE.cmd` opens the preserved Twin Stick starter.

The check names missing prerequisites and never installs them. Run any installation yourself. `START_ASTRA.cmd` is an optional original-workstation setup workflow with its own CLI/authentication/full-check requirements, not the team's first-run dependency.

## Scanned bears

Phone-scanned bears from the [bear scanner](https://github.com/Vibecadex/bear-scanner) import as ready-to-place props. This fork includes a pinned UE importer with verified reimport fixes. Start the scanner and configure its address, or supply a local scanner export. Close the editor, then:

```powershell
.\IMPORT_BEARS.cmd
```

The launcher allows 30 minutes for a first import (or respects `TEDDY_TEST_TIMEOUT`). Each bear becomes `/Game/ScannedBears/<Name>_<id>/SM_Bear_<Name>`: one Static Mesh with LOD0-2, convex collision and its texture, real size in cm, pivot under the feet. This fork disables Nanite for these props so the authored LODs remain active. Re-runs skip unchanged bears; rebuilt or renamed bears update their existing mesh. The run fails, with the reason in its receipt, if any bear fails or none is found. Placement remains a separate map-authoring step.

Pass a local GLB or scan folder with `.\IMPORT_BEARS.cmd "D:\Scans\Rupert.glb"`. For a worktree or a scanner on a different port, set `bear_scanner_repo` and `bear_scanner_url` in the ignored `tools/project-settings.local.json`. The verified local workshop uses `http://127.0.0.1:8471`; other machines must use their own scanner address. The command starts no installer or scanner service.

## Repository contents

The complete saved Blueprint project's Content/Config, starter dependencies, adapted Blender/FBX/textures/audio, original CC0 teddy with provenance, selected references, user-supplied reference video/archive copies, tools, study and retained review evidence are included. Binary files use Git LFS; `.umap`, `.uasset` and `.blend` are lockable.

Generated caches, credentials, raw recording-frame directories, setup/debug logs, recovery ZIPs and the separate native BossShot experiment stay on the original workstation. [Repository scope](study/TEAM_CONTINUATION.md#repository-scope) lists exclusions. Historical reports may refer to those local-only records; they are not fresh workstation verification.

The handoff removes the local Android File Server token and disables that unused server in tracked config. Game Content and input bindings are unchanged. Service authentication is not shipped.

Third-party provenance remains under `Assets/ThirdParty`. Epic starter content retains Epic's terms; no open-source license is applied to the entire repository. Supplied videos/concepts are reference material, not a grant of redistribution rights.
