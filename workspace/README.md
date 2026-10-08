# Horror Game workspace manifest

This folder is horror-game's **manifest** for the federated workspace. It describes this project to the hub. The hub itself, with its server, UI, CLI, schemas and decisions, now lives in its own repository: [lutherfourie/federated-workspace](https://github.com/lutherfourie/federated-workspace) (private). See its ADR-004, "standalone workspace, projects integrate via manifest".

The hub reads these files in place and reloads them live. It never writes to this repository.

| File | Purpose |
|---|---|
| `catalog.json` | Members, modules, artifacts (paths relative to this repository, optional pinned SHA-256), services and runbooks |
| `work-items.json` | The tracked work plan: items, modules, dependencies and acceptance criteria. Existing journal records always win on reload. |
| `agent-contracts.json` | Agent task profiles: member, read/write boundaries, artifacts, runbooks, resources and requirements |
| `bindings.example.json` | Member ids mapped to checkout locations. `"."` is this repository. Machine-specific bindings live in the workspace, not here. |
| `ownership.json` | Which workspace team owns each module (attribution only). Teams are defined in the workspace's `teams.json`. |
| `AGENT_RULES.md`, `AGENT_WORKFLOW.md` | Instructions included in agent packets |
| `experiments/` | Preregistered experiment protocols (for example `contact-alternatives-v1`) |

## Using it

1. Clone the workspace repository, for example to `C:\Projects\federated-workspace`.
2. Register this checkout in that repository's gitignored `local/projects.json`:

   ```json
   {"schemaVersion": 1, "projects": [
     {"id": "horror-game", "name": "Horror Game", "path": "C:/Projects/to-deploy/horror-game", "manifest": "workspace"}
   ]}
   ```

3. From the workspace repository, run `WORKSPACE.cmd`, which serves `http://127.0.0.1:8489/`. You can also use the CLI:

   ```sh
   python workspace.py check --project horror-game
   python workspace.py agent next --project horror-game --track game
   python workspace.py agent packet GAME-002 --project horror-game
   ```

   Where `AGENT_WORKFLOW.md` or a catalog runbook says `python tools/workspace.py …`, run `python workspace.py … --project horror-game` from the workspace repository instead.

All runtime state lives in the workspace repository under `local/horror-game/`: the SQLite work journal, local bindings, snapshots, agent packets and results, and verification and experiment receipts. An old `workspace/local/` folder here is ignored by `.gitignore` and no longer used.

A pinned artifact that is missing or changed in this checkout is reported as a project warning, not an error. Worktrees usually lack the large gitignored assets (the bear scan model and anatomy map, for example) and the scan-pipeline evidence packages.

## Changing the manifest

- Add work by appending to `work-items.json`. Don't rewrite items other people own.
- A new module needs a catalog entry and, if a team owns it, an `ownership.json` entry.
- A new member needs a catalog entry and a `bindings.example.json` entry. The hub never crawls neighbouring folders.
- The contract formats are documented in the workspace repository's `schemas/` folder.

The hub is local single-user software. Its origin and token checks protect the local API; they are not team authentication. A completed work item is a workflow record, not visual approval. Snapshots and exports include local paths and work notes, so review them before sharing.

See the [contact experiment](experiments/contact-alternatives-v1/README.md).
