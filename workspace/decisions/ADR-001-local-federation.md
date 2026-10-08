# ADR-001: Local federation with explicit member authority

Status: adopted for the scaffold, 8 October 2026.

The game integration worktree, chamber experiment and scanner are separate working authorities with existing local changes. Consolidating their files or treating one branch as their combined state would lose that distinction.

Use a local hub with explicit member bindings, read-only Git/file/service adapters and one workspace-owned work journal. Store portable contracts in Git; store machine paths, local observations and database state in ignored `workspace/local/`. Save reproducible verification under `evidence/federated-workspace-v1/`.

The browser may change only work-item records and append observations through validated API operations. Source files, source gates and review dispositions are immutable to those operations. Artifact routes are catalogued IDs, never arbitrary paths. Bind the HTTP service exclusively to loopback. Serve no directory listing, arbitrary command runner, third-party scripts or remote collaboration API.

Each snapshot declares when it inspected a member and whether evidence is missing, changed, verified or unbound. A stale or missing adapter must never produce a green success state. Historic receipts keep their original date and scope. Unknown remote freshness is displayed as unknown.

SQLite transactions and expected revisions prevent lost updates. Events record before/after states, rationale and evidence IDs. A dependency blocks workflow completion; workflow completion never closes format, preservation, anatomy or acceptance gates automatically.

This foundation provides a useful local federation. It is not a hosted deployment, merged repository, autonomous agent team or permission system for external tools. Those require explicit future work and evidence.
