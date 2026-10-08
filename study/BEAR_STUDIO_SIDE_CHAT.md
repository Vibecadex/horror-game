# Bear Studio - Side chat review

User-requested destination: ChatGPT's native Side chat. Open `/side` in the chat composer. That panel is not exposed through this session's tools, so this file is a prepared review prompt, **not a claim that a Side chat consultation happened**.

Official command documentation: https://learn.chatgpt.com/docs/reference/slash-commands#available-slash-commands

## Paste into Side chat

Review the teddy-authoring workflow being built in this fork. Act as a character technical artist and tools product reviewer. Give concrete missing workflows, failure cases and acceptance checks; do not modify project files.

The goal is a local Bear Studio where the team can catalogue scanned teddies, inspect their quality, create editable draft rigs, test deformation and animation, and export versioned handoffs. Preserve the saved horror chamber and original scans.

Implemented direction:

- Immutable source copies with SHA-256, provenance, source quality reports and scanner identity. Persistent searchable catalogue with names, tags, roles and notes.
- Inspect textured/clay/wireframe geometry and source LODs. A finished bundled sample includes a substantial support box; source quality is provisional.
- Seated and upright rig recipes with editable normalized landmarks, symmetry, an explicit derived crop preview, real bones and normalized skin weights.
- Pose and clip controls; finite geometry, weights, bind-pose and non-root deformation checks; binary GLB export/reload checks. Draft rigging remains distinct from human visual acceptance.
- Immutable rig revisions and test findings pinned to their exact source and rig. Original, derived GLB, recipe, validation and manifest downloads.
- A retained CC0 Quaternius source library with 43 clips, per-file hashes and license. Draft transfer adapts humanoid rotations to teddy bones, preserves the teddy rest pose and excludes root travel. Three clips have numerical export/reload checks; foot planting and full-library visual review remain open.
- Scanner reconstruction remains an independent blocked dependency on this machine. The studio accepts finished exports; it must not imply new scans succeeded.
- Local loopback service, no native Unreal module, package installer, firewall/trust changes or automatic chamber replacement.

What should we improve first for a trustworthy and useful teddy-production tool? Rank essential fixes, useful next features and advanced work. Separate what automated checks can establish from what an artist must review.

Return recommendations to the main chat for integration. Treat this prompt as review context; the user's main request controls scope.
