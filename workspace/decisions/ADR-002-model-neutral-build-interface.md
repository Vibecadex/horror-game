# ADR-002: Model-neutral build interface

Adopted for local use, 8 October 2026.

The original hub exposed readable records but made an LLM reconstruct its task, context and authority from whole-project documents. Add a shared CLI/API contract with a human Agent build view. Retain Python's installed standard library and existing local journal. No model SDK, framework, hosted orchestrator or credentials are needed for task packaging.

Portable task contracts declare write members, output paths, selected context and shared resources. A compact queue separates scheduling availability from source verification. A packet preserves complete mandatory instructions, allocates a measured character budget among relevant excerpts, names omissions and hashes full sources. It does not claim token-count or performance improvements without measurement.

Reservations are transactional across cooperating processes and persist until explicit release/handoff. Intersections of member-relative paths and declared resources prevent simultaneous writers. They are advisory coordination, not authentication, OS locks or replacements for Git LFS. No background scheduler starts another model or engine.

Start/resume/handoff validate task revisions, contract identity, captured sources, member bindings and Git HEAD/branch. Writable context can change but must appear in the output manifest. Result ingestion verifies declared file scope/bytes and check evidence, preserves limitations and updates workflow to review or blocked. It cannot audit every external edit or verify that a claimed test command actually ran. Evidence and independent review remain necessary.

JSON handoffs are stored transactionally in the journal and exported by content identity. Identical submissions are idempotent. Unknown scale and disputed anatomy remain unresolved; no result can set user acceptance. Existing archived reports retain their original build identity; new verification belongs in a separate evidence directory.
