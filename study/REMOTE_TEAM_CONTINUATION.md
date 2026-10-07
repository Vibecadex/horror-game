# Remote team continuation — 7 October 2026

## Prerequisites

Continue in the `codex/integrate-bear-scanner` worktree. Keep the separate scanner checkout and its local fixes. Use the saved chamber and respect LFS ownership. The Studio and static pack import require no new package installation on this workstation.

The user completed the scanner dependency sync on 7 October. `xatlas 0.0.11` imports successfully, all **35** `tests.test_rigfit` tests pass, and the team's fit/export path has now run locally. On another workstation, the human installs missing scanner dependencies:

```powershell
Set-Location 'C:\Projects\to-deploy\bear-scanner'
uv sync --locked
```

Do not run installers, alter firewall rules, or disable Application Control from an agent. The scanner's older OpenMVS reconstruction blocker remains separate from importing finished packs.

## Included work

Fresh fetches found every remote branch tip already reachable from the two working heads. Horror-game includes Grok's chamber, both team tooling branches, Bear Studio, and the main-branch handoff fixes merged in `313e74f`. Bear-scanner is at `8b396ab`, including bear packs, rig readiness, rigfit prototype/quality work and the animation capture guide. No experimental branch was silently omitted or substituted for a later reviewed main-branch version.

The latest API-5 Unreal importer is pinned from scanner `8b396ab`, retaining the verified UE 5.8 staged-material save and the game's Nanite correction. Native readback exposed upstream ID normalization (`example-real-bear` becoming `example_real_bear`). The game copy now keeps opaque IDs intact and refuses unowned meshes or a colliding package belonging to another bear. Exact upstream/adapted hashes and deviations are in `tools/vendor/bear_scanner_importer.provenance.json`.

## Working now

- Run `BEAR_STUDIO.cmd`. The local catalogue imports GLBs, live versioned scanner packs and one-bear ZIPs. File sizes/hashes, version ordering, source reports, capture pose and landmark warnings are retained. Existing rigs/tests remain attached to their original source revisions.
- `IMPORT_BEARS.cmd` accepts a finished pack folder, ZIP, GLB or the scanner API. These are **static props**. The retained team example is `Assets/ThirdParty/BearScannerPackSample`; its saved native review asset is under `/Game/ScannedBears/TeamPackSample`.
- The existing catalogue and previous source sample were preserved. The team example is an additional record, with its incomplete landmarks and support geometry visible. It is not an approved creature.

The [current verification report](../evidence/team-integration/20261007T111927Z/QA_REVIEW.md) includes browser capture, saved native LOD renders and the retained failed identity audit followed by its correction. The chamber and gameplay assets were not changed by this integration.

## Next character work

The team's `scanner/rigfit.py` and `scripts/rig_test_package.py` now have a [native compatibility review](TEAM_RIG_NATIVE_REVIEW.md). A clearly labelled synthetic fixture was generated with the team's procedural test geometry, rig fitting and four test clips. Its saved 21-bone mesh, four clips and three mannequin retargets pass **89** fresh-editor/PIE checks with 15 native captures. Run `REVIEW_TEAM_RIG.cmd` to repeat that review without installing dependencies or authoring assets.

The intended original test inputs (Rupert2 `b001bad18151` and synthetic `39973856faee`) are still missing scanner runtime data. No release or Actions artifact was available during the preceding remote check. Obtain those exported GLBs, including the neutral-template comparison, to complete the team's real-scan checklist. The bundled example's incomplete landmarks and this new synthetic fixture are not equivalent inputs.

The native import must preserve authored normals (`recompute_normals=False`); default normal rebuilding produced faceted UV boundaries. Basic mannequin idle/walk/attack retargeting works with six mapped chains and automatic target-pose alignment. Foot IK/root-motion production setup, shoulder/hip weights, contact and actual real-bear quality remain open. The prototype is not wired into Studio's separate 16-bone builder or the static bear-pack importer. No encounter creature was replaced.

Chamber parity remains a separate open art task against the original elevated teal chamber references. Resume architecture/light/material refinement on the saved level after the current asset owner is established; importing the team example is not a room-parity improvement.
