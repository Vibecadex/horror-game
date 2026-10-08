# Horror Game federated workspace

The local development hub connects independently owned repositories, worktrees, tools, reference assets and evidence. The saved Unreal encounter remains the game implementation. This workspace owns its catalog, plans, local work records and inspection snapshots; it does not take ownership of its members' files.

## Start

Run `WORKSPACE.cmd` from the integration checkout. It uses installed Python 3.11+ with the standard library, starts the local hub at `http://127.0.0.1:8489/`, and opens it. No installation, cloud service or engine launch is performed. `REVIEW_REPORTS.cmd` remains the separate evidence-review launcher on port 8488.

`python tools/workspace.py check` validates the catalog, artifact identities and connected source records. `python -m unittest discover -s tools/federated_workspace/tests` verifies persistence, concurrency, federation boundaries and HTTP controls. The first launch creates ignored machine-local bindings and a SQLite work journal under `workspace/local/`. Copy `bindings.example.json` to `local/bindings.json` and set checkout locations when moving to another machine.

## Working model

1. **Overview** shows the current game and workspace tracks, blockers and connected services.
2. **Work board** records a work item's owner, status, rationale and evidence. Updates survive refresh/restart; concurrent stale edits are rejected. A completed work item is a workflow record, not visual approval.
3. **Federation** exposes each member's authority, path, branch, local changes, dependencies and inspection time. Members retain separate Git histories. No automatic pull, merge, lock acquisition or cross-repository write occurs.
4. **Assets & references** separates concept direction, scan sources, working diagnostics and runtime candidates. Inspection does not promote an asset.
5. **Evidence & gates** connects reports to source hashes, declared scope and unresolved decisions. Existing report pages remain independently owned.
6. **Runbooks** provide reviewed entry points with prerequisites and expected evidence. Commands are copied for deliberate execution; browser actions never execute arbitrary shell text.
7. **Activity** records work transitions and reviewer observations. The journal and current work state can be exported together.
8. **Agent build** prepares bounded, hash-identified assignments for a coding LLM. It exposes task scope, availability, persistent reservations and structured handoffs. Start with `python tools/workspace.py agent next --track game`, then `agent packet GAME-002`. Read [the agent workflow](AGENT_WORKFLOW.md) for reserve/check/finish/release commands and guarantees. Models are not launched automatically.

`catalog.json` is the portable module/artifact/runbook contract. `work-items.json` is the initial work plan. `schemas/` documents the interchange records. Local bindings resolve member IDs to this machine's paths. New members require a catalog entry and explicit binding; the hub does not crawl neighboring folders.

## Scaffold scope and implementation sequence

- Establish the catalog, authority boundaries, adapters, persistent work journal, API, UI, startup, contracts and checks first.
- Connect the current game/scanner/evidence records without editing their originals.
- Register game work with acceptance criteria and dependencies. First game deliverable: a preregistered contact-alternative experiment against the frozen V2 map. Then author and review a reversible candidate before standing or walk refinement.
- Chamber work remains a separate branch/candidate. Verify its present revision, lock ownership and baseline before resuming art changes. Its historical checks are not fresh acceptance.
- Evolve the game and workspace through paired work items: each game experiment supplies source identities, evidence and a decision; the workspace adds only the controls needed to inspect and record them.

## Preservation and limitations

The hub is local single-user software. Local HTTP origin/token checks prevent unrelated webpages from posting to its API; they are not team authentication. Hosted collaboration, remote execution and multi-user permissions are future work, not deployed capabilities. No external agents are dispatched by the scaffold.

Remote Git synchronization and repository visibility are not inferred from local refs. Tool health is a timed observation, not perpetual availability. LFS locks and runtime tests require their own current checks. Existing report links can be unavailable if their service is stopped; the runbook remains available.

Unknown scale, contact ownership, photographic coverage and visual acceptance remain explicit. Read-only source access is enforced by the hub's API and file allowlist; opening an IDE does not make its editors read-only.

Snapshots and exports include local paths and work notes. Review them before sharing. No credentials, caches, arbitrary project files or Unreal binary packages are served. The immutable evidence report and game sources are not changed by workspace updates.

See [federation decision](decisions/ADR-001-local-federation.md), [contact experiment](experiments/contact-alternatives-v1/README.md) and [contracts](schemas/README.md).
