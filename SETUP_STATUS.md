# Setup status — Blueprint route

Updated 4 October 2026, 21:27 South Africa time. **Setup is fully verified for the prepared Astra implementation run.** The authenticated Astra / Max check passed with the active Blueprint project and existing Codex permissions. Double-click START_ASTRA.cmd. The durable receipt is evidence/setup/20261004T192426/verification.json; evidence/setup/latest-verification.json also reports ready: true.

The active project is TeddyBlueprint/TeddyBlueprint.uproject in Unreal 5.8.3. It uses Epic’s Blueprint Twin Stick starter and built-in BlueprintGraphEditor authoring. No new native project module, signing certificate, additional plugin or Windows security change is required.

## Verified execution

The actual Astra tool receipt is evidence/setup/20261004T192426/astra-probe/engine/engine-probe.json. Independent host validation also passed in evidence/setup/blueprint-final-host-2/engine-probe.json.

- All 34 quick prerequisite checks pass: engine/plugins, tools, sign-in, files, original hashes and storage.
- Astra read a fresh nonce, wrote it back through its shell tool, inspected the attached references, correctly identified the elevated view/player position and selected the intended target level.

- Sixteen shipped Blueprint assets load and compile; the starter’s level content loads.
- The downloaded teddy imports into an isolated namespace as a saved static mesh, material and texture.
- A fresh custom Blueprint graph is generated, compiled and saved; a second engine process reloads it and verifies its state change during play.
- Seven runtime checks pass: possession, saved generated behavior, movement, aiming, firing, enemy spawning and three actual 1280 x 720 captures.
- A separate ordinary `-game` launch executes the same saved Blueprint, captures an additional 1280 x 720 frame and exits through its authored behavior.
- Seven launcher regression tests pass, including failure receipts, mismatched projects, fresh evidence and level selection.

The full check saved a 506-file source/content backup and verified the preserved BossArena map hash. It ran without changing Windows protection, requiring native compilation or extending Codex writable roots. Rendered evidence is in the same Astra engine folder: runtime/runtime-01.png through runtime-03.png and standalone.png.

Runtime controls were exercised through Unreal’s Enhanced Input action injection. This verifies the gameplay action path; physical keyboard, mouse and gamepad testing is not claimed. The ordinary game launch uses the installed editor executable, not a packaged distribution build. These are setup tests of the starter, not the final TeddyEncounter.

## Earlier native attempt

Windows Smart App Control is enabled and blocked the earlier unsigned BossShot game DLL after compilation, in both CLI and desktop Astra checks. The user confirmed no trusted signing certificate or service is available. The working solution uses Unreal’s supported Blueprint runtime instead. The preserved native experiment still has that limitation.

Historical failed receipts remain at evidence/setup/20261004T184500/verification.json and evidence/setup/desktop-astra-receipt.json. The prior documents are preserved under evidence/revisions/native-setup-attempt/. Source originals and BossArena remain unchanged. No certificate stores, Windows protection or global Codex configuration were changed.

The active Blueprint launcher uses the existing Codex sandbox/approval policy without additional writable roots. Temporary files and derived data use project-local paths. The native cache-alias diagnosis remains historical and is not a requirement for this route.

## What setup does not claim

The finished horror environment, teddy rig/animations, custom boss encounter, proposed final bindings and visual acceptance are future implementation work described in MASTER_PROMPT.md. Original source audio has not been auditioned. Teddy model provenance is preserved; it is an unrigged starting candidate.

Epic documents the [Twin Stick starter](https://dev.epicgames.com/documentation/en-us/unreal-engine/top-down-template-in-unreal-engine) and the enhanced Blueprint scripting API in its [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes). Installed headers and actual execution receipts are the version-specific authority used here.

> **Written for the original workstation's Astra run** (START_ASTRA.cmd, 4-5 October 2026), with its paths and tools. On a team checkout it is background: start at [README.md](README.md) and [study/TEAM_CONTINUATION.md](study/TEAM_CONTINUATION.md), and continue the saved project rather than rebuilding it.
