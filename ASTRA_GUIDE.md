# Using GPT-6 Astra for this encounter

The prepared entry point is **START_ASTRA.cmd**. It uses the signed, project-local Codex CLI 0.160.0, selects `gpt-6-astra` with `model_reasoning_effort="max"`, attaches three real video reference images and asks the agent to execute RUN_ASTRA.md. Use the existing ChatGPT sign-in; this workflow does not require a separate API application or API key. Model access and local tool execution are checked with an actual authenticated request, not inferred from a configuration file.

## Why this setup fits the task

This work combines visual interpretation, gameplay, asset preparation and repeated engine verification. Astra is the requested integration owner: it can inspect the supplied references, author scripts and saved game assets, run Unreal/Blender, examine rendered results and revise the implementation. Its useful role is that complete feedback loop. A detailed text description alone cannot establish that the scene matches the reference.

The selected model identifier and Max effort are verified against this installed Codex environment. Availability in another account or client should be checked there. The launcher selects them for this invocation and does not rewrite global settings. The exact CLI switches are also documented in OpenAI’s [developer command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

The precise evidence is that the launcher explicitly requests `gpt-6-astra` / `max`, and the authenticated setup request completed with working tools. The receipt's `model_requested` field is not a server-echoed model identity or a quality benchmark. Keep the established Max setting for this run. We have not compared it with High; if latency or usage becomes a concern, evaluate the same bounded composition task from the same starting state with the same references and acceptance criteria before changing effort. OpenAI's [reasoning-effort guidance](https://developers.openai.com/api/docs/guides/deployment-checklist#set-up-reasoningeffort) treats higher effort as a quality/latency tradeoff to measure. API Pro mode and service tiers are separate concepts; this launcher does not configure them.

The full check deliberately uses Astra’s actual shell and workspace permissions. Earlier tests showed why this matters: a host-side build could succeed while a later agent run failed to load its unsigned game DLL. A model accepting a prompt is not enough to establish the engine workflow.

## Why the project now uses Blueprints

Windows Smart App Control blocked freshly rebuilt native BossShot DLLs. There is no available signing certificate or service. The active project therefore uses Unreal’s installed Blueprint runtime and **UE5.8 BlueprintGraphEditor**, which creates and edits gameplay graphs through the built-in Python editor plugin. No custom native module or extra plugin is involved, and Windows protection remains enabled.

The installed headers expose graph creation, events, calls, variables, branches and pin connections. Local execution has created a new graph, compiled and saved it, reopened it in another process, and executed its state change in gameplay. An ordinary `-game` session also executed the saved behavior and produced a rendered capture. Python is used to author the project; the resulting gameplay runs as Blueprints.

Epic’s [Twin Stick template](https://dev.epicgames.com/documentation/en-us/unreal-engine/top-down-template-in-unreal-engine) provides a working starting point for movement, aiming, projectiles and pursuing enemies. The prepared copy also contains dash logic. Custom horror behavior still needs implementation. See tools/BLUEPRINT_WORKFLOW.md for exact tested authoring calls and the extension recipe.

## How the master prompt is structured

1. **Prerequisites first.** Read the reference, active project, tool receipts and downloaded model limitations before editing.
2. **Observed facts.** Elevated oblique camera, a small armed human, a grounded large pale enemy, worn visible floor, cool atmospheric light, dark edges and restrained red accents. Phone/social overlays are excluded.
3. **Deliberate substitution.** A monstrous teddy replaces the main creature. The downloaded textured GLB is a candidate, not an animated final enemy.
4. **Proposed controls.** WASD, independent mouse aim, left-click fire, Space dodge, Escape pause and F5 restart. Exact original bindings are not visible in the recording. Reload applies only if finite ammunition is implemented.
5. **A complete playable target.** Grounded animation, pursuit, attack telegraph, damage, feedback, defeat, surrounding threats and restart.
6. **Evidence.** Save/reopen, runtime behavior, comparisons at representative camera positions, a short gameplay recording and measured performance. Functional success, visual fidelity and user acceptance stay separate.

MASTER_PROMPT.md holds the stable target. RUN_ASTRA.md instructs execution. REFERENCE_BRIEF.md records observations and uncertainties. WORK_STATUS.md records current progress and next actions. This avoids having to rebuild the context from a long chat when a run is resumed.

Grok Heavy reviewed those actual files and launch settings in the browser on 4 October 2026. Its advice was checked against local code and the [official Astra prompting guidance](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#prompting-best-practices). The updated execution prompt starts with a bounded evidence milestone, then the playable encounter. It calls for scoped autonomy, checks appropriate to each change, one shared-asset writer and durable resume notes. The [review record](C:/Projects/to-deploy/horror-game/evidence/reviews/grok-heavy-astra-20261004/REVIEW_SUMMARY.md) distinguishes applied prompt changes from pending capture/input tooling changes. These are local prompt improvements, not a new framework or a claim of game completion.

## Give Astra useful visual feedback

Keep the actual source frames available throughout the run. The 22.99-second phone recording includes rotated gameplay and unrelated feed interruptions; upright frames at seconds 5, 10 and 16 are attached automatically. Motion sheets remain available when a single frame is insufficient.

Ask for comparable in-engine captures after the camera/composition pass, the material/lighting pass and the animated combat pass. Compare the player-to-monster relationship, grounded weight, floor readability, localized light and peripheral darkness. Fix the largest discrepancy first. Adding effects to the wrong camera angle will not bring the scene closer to the reference.

Useful feedback names an observable mismatch: “The teddy is too small in the frame; keep the camera elevation and increase its apparent size,” or “The floor is uniformly bright; bring back localized pools of light and darker edges.” The master prompt asks Astra to make these comparisons itself and continue through repairable issues.

The source audio has not been auditioned. The prompt requires that review before any audio-match claim, otherwise sound design must be labelled as proposed original work.

## Run, inspect and resume

Double-click START_ASTRA.cmd for implementation. Use `START_ASTRA.cmd --resume SESSION_ID` to resume the exact saved CLI conversation after an interruption; the existing reference attachments remain in that conversation. The launcher verifies its selected CLI version, fixes an inherited `TERM=dumb` locally, and holds a single-writer lock. Use PLAY.cmd to inspect the saved encounter once created; before then it opens the labelled stock starter. EDIT.cmd opens the project in Unreal. Keep one editor/asset writer active at a time. Send corrections in the running Astra session.

On 4 October the user explicitly authorized the necessary command permissions without repeated yes prompts. The launcher therefore selects `--sandbox danger-full-access --ask-for-approval never` for this invocation, matching OpenAI's documented [Full Access mode](https://learn.chatgpt.com/docs/sandboxing). This removes the CLI filesystem/network sandbox boundary; it is not a workspace-only technical restriction. AGENTS.md still confines the task to the authorized encounter, preserving originals and excluding purchases, publishing and unrelated changes. Global Codex settings and Windows protection remain unchanged. Installation/update commands are supplied to the user rather than executed automatically, as requested.

When the desktop bridge's required host environment is absent, this standalone launcher disables only that unavailable `node_repl` MCP connection for the invocation. Built-in shell and image inspection remain available. Context7 can reuse the installed entry point recorded in AGENTS.md without another npm install. The initial diagnostic report also contains non-blocking warnings for two ignored shared settings and historical thread-index differences; those shared records have not been rewritten.

For the desktop app, select Astra / Max in the model controls before pasting START_PROMPT.txt into this project. Prompt text alone does not change the selected model. Confirm the displayed selection; the app and CLI have separate execution contexts, so a desktop run should rely on its own actual tool results. The prepared launcher's full receipt is specifically a CLI execution receipt.

CHECK_SETUP.cmd is a quick local check. The full validator runs one bounded model request plus actual engine tests and saves a source/content backup. Read SETUP_STATUS.md and evidence/setup/latest-verification.json for its result. Account limits and platform controls still apply. The CLI update does not require repeating the full Unreal setup probe; verify the updated executable, launch arguments, actual resumed-session settings and continuing tool execution.

Setup readiness means Astra has the tools, sources, active project, custom gameplay authoring route and verified execution path. It does not mean the finished horror visuals, teddy rig, final bindings, packaged release or user approval already exist. Those are the next implementation run’s deliverables.
