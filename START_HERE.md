# Play or edit Teddy Encounter

**Team checkout:** follow [README.md](README.md) and the [current chamber brief](study/CHAMBER_PARITY_BRIEF.md). `TEAM_CHECK.cmd` validates local prerequisites without launching Unreal. The Astra setup instructions below describe the original workstation; its installed CLI, authentication and setup receipts are not bundled.

**Double-click [PLAY.cmd](PLAY.cmd) to play the implemented encounter.** [EDIT.cmd](EDIT.cmd) opens `/Game/Maps/TeddyEncounter` in Unreal 5.8.3. [ENCOUNTER.md](ENCOUNTER.md) contains controls, editable asset paths, provenance and review evidence. [WORK_STATUS.md](WORK_STATUS.md) is the current implementation record.

Controls: WASD move, mouse aim, left click fire, Space dodge, Escape pause/resume, F5 restart. [PLAY_BASELINE.cmd](PLAY_BASELINE.cmd) still opens the preserved starter. Close the current game/editor before opening another instance.

The setup and implementation-session instructions below remain available for future authoring. They are not required just to play.

For further authoring, START_ASTRA.cmd selects GPT-6 Astra / Max, attaches three upright video reference images, and submits RUN_ASTRA.md. Do not launch a second implementation session while one is active. The authenticated full setup check passed on 4 October 2026 at 21:27 South Africa time; see SETUP_STATUS.md.

The working project is **TeddyBlueprint/TeddyBlueprint.uproject**, using Unreal 5.8.3 and its built-in Blueprint authoring API. Windows protection stays enabled. The earlier native BossShot experiment remains preserved separately.

The corrected encounter now has its own saved level, rigged teddy, six animation clips and runtime Blueprint combat. Setup receipts remain prerequisite evidence; encounter verification and comparison artifacts are linked from ENCOUNTER.md.

## Run or resume

Keep the launcher’s terminal open while Astra works. Send feedback there; Ctrl+C interrupts. Reopen START_ASTRA.cmd to continue from WORK_STATUS.md and saved files. To retain the exact CLI conversation as well, run `START_ASTRA.cmd --resume SESSION_ID`, using the ID printed when Codex exits. Do not run two implementation sessions simultaneously.

The launcher uses the signed **Codex CLI 0.160.0**, the latest stable npm release checked on 4 October 2026, with **GPT-6 Astra / Max** and live search. It explicitly selects the prepared copy, so an older Codex elsewhere on PATH cannot take over. As authorized, this launcher uses **Full Access** with routine command approvals disabled. It can run local tools and access the network without repeated yes prompts. Windows protection, account limits and the task boundaries still apply. General Codex settings are unchanged.

For the Codex desktop app, open this folder, select **GPT-6 Astra / Max**, and paste START_PROMPT.txt. Both routes read the same saved instructions and local reference images. ASTRA_GUIDE.md explains the model choice, workflow and evidence.

| Entry point | Action |
| --- | --- |
| START_ASTRA.cmd | Start/resume the complete implementation request. |
| CHECK_SETUP.cmd | Quick local prerequisites and sign-in check. |
| PLAY.cmd | Play TeddyEncounter if created; otherwise announce and play the Twin Stick starter. |
| EDIT.cmd | Open the same selected level for editing. |
| PLAY_BASELINE.cmd | Play the prepared Twin Stick starter. |
| `python tools/astra_setup.py verify` | Full setup validation, including one bounded Astra model request. |

Close Unreal editor/game instances before full validation. Check evidence/setup/latest-verification.json for the actual outcome; a quick check is not a full pass. The launcher refuses a missing, failed or different-project receipt.

## Installing or updating tools

Installation/update commands are handed to you to run, as requested; the agent does not run npm or other installers on your behalf. The current CLI is already installed. If this prepared copy ever needs restoring, run this in your own PowerShell terminal:

```powershell
npm install --prefix "C:\Projects\to-deploy\horror-game\.tool-cache\codex-cli" --save-exact --no-audit --no-fund @openai/codex@0.160.0
```

The package lock records the exact official download and integrity. A future upgrade should first verify the stable release, then supply the command for that version and update the version/path in tools/project-settings.json after installation. No install or upgrade happens automatically during launch.

## Already prepared

- MASTER_PROMPT.md starts with prerequisites and defines reference-based visuals, controls, animation and delivery.
- RUN_ASTRA.md is the complete execution request; WORK_STATUS.md carries progress between sessions.
- REFERENCE_BRIEF.md and evidence/reference-video contain inspected upright frames and motion sheets, with observed facts separated from proposed controls.
- Assets/ThirdParty/HorrorTeddyBear contains the preserved original teddy and source/license evidence. Adapted mesh, rig, animations and exports are separate under Assets/Adapted/Teddy.
- tools/BLUEPRINT_WORKFLOW.md explains tested Blueprint graph authoring, component/material changes and input setup.
- The launch tools select the installed engine, use project-local temporary/derived data, and attach the references automatically. No new API key or global setting is needed.

## Starter controls and limits

Use WASD to move, mouse to aim, left click or F to fire, Left Shift to dash, and right click or G to use a collected item. These stock bindings were read from the installed assets and are recorded in the full check's blueprints.json. The master prompt requests Space dodge, Escape pause and F5 restart for the finished encounter; those additions are not claimed implemented in the starter.

The preserved native project is BossShot/BossShot.uproject. Its historical scene and evidence remain available, but freshly compiled native modules were blocked by Windows Smart App Control. The active Blueprint route does not depend on them. Do not infer current native playability from old greybox captures.
