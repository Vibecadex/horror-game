# Remote team continuation — 7 October 2026

## Prerequisites

Continue in the `codex/integrate-bear-scanner` worktree. Keep the separate scanner checkout and its local fixes. Use the saved chamber and respect LFS ownership. The Studio and static pack import require no new package installation on this workstation.

For the team's newer **rig-fitting** tools, the installed scanner environment is missing `xatlas`. The user runs dependency installation:

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

The team's `scanner/rigfit.py` and `scripts/rig_test_package.py` are present. Their intended 21-bone test inputs (Rupert2 `b001bad18151` and synthetic `39973856faee`) are scanner runtime data, not committed source assets. No release or Actions artifact was available from the remote repository during this check. Obtain those exported test GLBs or prepare suitable complete scans after installing the missing dependency; the bundled example's incomplete landmarks are not equivalent input.

Then run the team's native checklist (`bear-scanner/docs/RIG_TEST_UE5.md`) in a separate review namespace: verify skeleton hierarchy, bind pose, scale, facing, four test clips, skin deformation and retargeting. Keep source warnings and actual render findings. Browser rig checks and static-prop imports do not establish that skeletal workflow.

Chamber parity remains a separate open art task against the original elevated teal chamber references. Resume architecture/light/material refinement on the saved level after the current asset owner is established; importing the team example is not a room-parity improvement.
