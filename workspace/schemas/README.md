# Workspace contracts

Version 1 uses explicit JSON records and a versioned SQLite work journal. `catalog.schema.json` documents the portable catalog; `work-update.schema.json` and `observation.schema.json` describe browser write requests. The application validates these request shapes, allowed identifiers, dependencies, source availability and expected revisions in Python without a third-party schema package.

## Adapter output

A source snapshot has `schemaVersion`, `id`, `observedAt`, `catalogSha256`, `members`, `artifacts`, `services` and `scope`.

- Member: `id`, resolved local `path` or null, `state`, inspection time, optional Git observation (`branch`, `head`, `localChangeEntries`, remote freshness explicitly not fetched).
- Artifact: portable catalog record plus `state`, inspection time, observed SHA-256/byte count when readable and a scoped `/artifact/<id>` route for approved display types. `verified` means a pinned expected digest matched. `observed` means readable with a recorded digest, without a pinned expected version. `changed`, `missing`, `unavailable` and `unbound` remain distinct.
- Service: explicit loopback endpoint plus inspection time and identity result. A responding port alone is insufficient; the expected application and workspace or immutable manifest must match.

## Work and events

Work combines the tracked initial plan with persistent status, owner, rationale, evidence IDs, revision and update time. Dependencies are recomputed from the same database transaction. Stale `expectedRevision` or `expectedSnapshot` returns HTTP 409 without a write. Completion requires available, unchanged supporting evidence and completed dependencies. Reopening a prerequisite requires active/completed dependent work to be reopened first. It is a workflow claim and never sets a review gate.

Events append a monotonically increasing sequence, UTC timestamp, kind, entity ID and payload. Work updates retain before/after records. Observations retain their source snapshot ID. There is no source mutation, journal deletion, arbitrary path or command-execution API.

## HTTP surface

| Operation | Purpose |
|---|---|
| `GET /api/health` | Application and root identity for local launcher reuse |
| `GET /api/workspace` | Catalog, inspected source snapshot, work, events and session write token |
| `GET /api/export` | Same records without the write token, suitable for deliberate saving |
| `GET /artifact/<catalog-id>` | Exact inspected source bytes; changed bytes return 409 |
| `POST /api/refresh` | Reinspect the explicit sources; never sync Git or write members |
| `POST /api/work/<work-id>` | Version-checked workspace-owned work record |
| `POST /api/observations` | Append a scoped reviewer observation |

Writes require JSON, same local Origin/Host, a session token and a bounded body. The browser does not submit shell commands or filesystem paths. No CORS grant is provided. This protects the local application boundary; it is not hosted-team authentication.

## Agent build contract

`workspace/agent-contracts.json` declares task profiles and explicit overrides. `agent-result.schema.json` documents the result shape; `tools/federated_workspace/agents.py` also enforces semantic and filesystem constraints without a schema dependency.

- `GET /api/agent/queue`: compact queue, current workflow revisions and scheduling reasons.
- `POST /api/agent/packet`: `{taskId, budgetCharacters}` saves context and returns packet JSON; no reservation or model execution.
- `GET /api/agent/packets/<packet-id>`, `/api/agent/prompt/<packet-id>`, `/api/agent/template/<packet-id>`: exact saved identity and corresponding display/export forms.
- `POST /api/agent/start`: `{packetId, owner}` reserves paths/resources and updates local workflow.
- `POST /api/agent/release`: `{runId, reason}` releases the reservation without overwriting newer human workflow changes.
- `POST /api/agent/finish`: `{runId, result}` validates the structured handoff and writes task/event/result in one transaction.

All POSTs retain the existing loopback/origin/token and body-size controls. CLI equivalents share the same implementation; `agent check RUN_ID` validates a resume point. Reads expose no arbitrary paths. Packets contain full source hashes, measured context characters, explicit inclusions, task revision, member roots, Git identities, contract/work-plan hashes, criteria and separate gates. Results are self-reported checks with verified declared output identities, not independent test execution.

## Adding a member

Add a stable module/member identity, authority and write boundary, explicitly bind its root in ignored local configuration, and provide a narrowly scoped adapter and artifact declarations. Add unavailable/mismatch tests and an actual evidence use case before calling the adapter connected. External source schemas are not rewritten to resemble workspace records.
