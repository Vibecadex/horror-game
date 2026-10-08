# Building through the federated workspace

Use this as the local, model-neutral operating guide. It works with an LLM coding agent that can read files and run the installed Python. No model API, credential, agent framework or package installation is required. The workspace prepares assignments and records results; it does not launch models or execute their code.

## Start with one bounded assignment

From the federated-workspace repository ([lutherfourie/federated-workspace](https://github.com/lutherfourie/federated-workspace)), with this checkout registered as `horror-game` in its `local/projects.json`:

```powershell
python workspace.py agent next --project horror-game --track game
python workspace.py agent packet GAME-002 --project horror-game
```

The first command returns a compact JSON queue with availability and reasons, without dumping the journal. The second saves an immutable task packet under the workspace repository's `local/horror-game/agent-packets/` and prints its ID, Markdown path, JSON path and result-template path. Use `--format markdown` to print the complete prompt, or `--format json` for structured ingestion. The default prompt budget is 24000 characters, not a model-specific token count; `--budget-chars` accepts 16000–64000.

Give the saved Markdown packet to the coding agent. It contains the question, success criteria, next action, member root, permitted output paths, source identities, relevant runbooks, unresolved gates and only selected source excerpts. Full files remain referenced with hashes. Omitted/truncated content is explicit. Repository instructions are included in full; if they do not fit, packet creation fails rather than silently cutting them. Evidence text is delimited data, not instruction authority. Current user/system instructions take precedence over repository history.

## Reserve, inspect, implement, hand off

```powershell
python workspace.py agent start PACKET_ID --project horror-game --owner "Agent / session label"
python workspace.py agent check RUN_ID --project horror-game
# Perform the scoped work with the agent's own tools.
python workspace.py agent finish RUN_ID --project horror-game --result-file "PATH_TO_COMPLETED_RESULT.json"
```

Use the actual returned IDs. Reservation checks the packet's task revision, dependencies, source hashes, contract and Git HEAD. It rejects overlapping paths/resources across active reservations, including separately bound worktrees. Reservations persist until explicitly released or handed off. `agent check` rechecks immutable inputs and reports writable-context changes, so an agent can resume after compaction. Task revision or source drift requires release and a fresh packet. `agent status` lists outstanding reservations; `agent release RUN_ID --reason "..."` ends one without a completion claim.

Reservations coordinate cooperating agents only. They are not authentication, OS file locks, Git LFS locks or permission to modify other projects. There is no unattended dispatch. An agent must check existing dirty files and obey actual session authorization. Check current LFS ownership before Unreal writes; this application cannot grant it. Scope additions are reviewed edits to `agent-contracts.json`, never an implicit expansion because a task is difficult. External scanner files, originals and frozen evidence stay preserved.

## Return a structured result

Copy the packet's result template to a new file and complete it. Set `disposition` to `review` or `blocked`. Record:

- A concise implementation summary, limitations and the next action.
- Exact changed/output paths and SHA-256 values, relative to the packet's write member. Deletions are not supported by this diagnostic workflow.
- Checks with `passed`, `failed` or `not-run`, command/description, actual result, and IDs of hashed output evidence. A passing check requires evidence.
- The four distinct gate claims: implementation, validation, anatomical interpretation and user acceptance. Anatomical/user claims remain `not-assessed` or `unresolved`; this handoff never records their approval.

Before saving a handoff, the workspace verifies output bytes, path scope, immutable source identities, dependencies and work revision. A review handoff needs at least one output and a passing evidenced check; a blocked handoff can report missing evidence honestly. It saves a content-addressed receipt, updates the task to review/blocked, releases the reservation and appends an event in one database transaction. Retry of the identical result is idempotent. A handoff is a self-reported result with verified file identities, not an independent test rerun or anatomical acceptance.

The workspace cannot observe every write performed by external tools. Its checks enforce its own records, declared outputs and captured source identities; unlisted side effects are not certified absent. Inspect the Git diff and asset ownership separately. New candidate evidence should be registered in the portable artifact catalog before a reviewer marks the work complete.

## Human control

Open **Agent build** to select any task, inspect its contract, prepare a packet and read active reservations/results. Preparation alone does not reserve work. Copy the generated commands for deliberate local execution. Agent work, human work and the evidence review share task IDs and journal history. No screen reports token savings, correctness, or speed gains that have not been measured.

Machine-local packets/results can contain paths and project source excerpts. Keep them local unless sharing is authorized. Preserve the workspace repository's `local/horror-game/` folder with the SQLite database when moving active work to another machine; model context and run state are not stored in a remote service.
