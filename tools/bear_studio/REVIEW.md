# Bear Studio implementation review

Reviewed 6 October 2026. The backend author reviewed the separately authored studio UI, rigging and animation-transfer modules. The integrator performed browser rendering and workflow checks. This is implementation and artifact evidence, not character-art approval or Unreal skeletal verification.

## Findings corrected

- Saving a rig originally left other controls enabled during asynchronous export. Controls now lock immediately; the save captures its bear, source identity, recipe and handle, then checks that the draft is still current before submission. Source changes clear stale editor state and discard stale GLB loads.
- A refresh originally updated only the catalogue list, retaining the selected record's stale revision. Refresh now updates the selected record while preserving unsaved fields; conflicts retain editor input and require refresh before another metadata save.
- Added animation clips could be lost without warning after saving only landmarks. Unsaved-work guards now include an unsaved rig and test notes, including selection changes, rebuilds, saved-rig opening and browser unload.
- Browser-native confirmation prompts were replaced with an asynchronous in-page Cancel / Discard dialog. The code retains the original pending action, blocks competing actions, defaults focus to Cancel, and treats Escape or dialog cancellation as keeping changes. This final dialog has been reviewed in code; its new buttons have not yet been exercised in the browser evidence below.
- The frontend's encoded Unicode filename did not match the raw backend filename contract. The backend now decodes once before validating the filename; encoded paths remain rejected.
- A recipe could contain a source identity contradicting otherwise valid request fields. Draft and rig saves now reject contradictory embedded source revisions/hashes without changing the bear.
- Joint-coordinate help now describes the original source bounds, not cropped dimensions. Test history keeps the API's newest-first order. Discarded source and preview resources are released.

## Evidence inspected

| Check | Result and scope |
| --- | --- |
| [Backend test receipt](../../evidence/bear-studio/20261006T134902Z/backend-tests.json) | **21/21 passed**, run directly by this reviewer and repeated by the integrator. Persistence, idempotent import, concurrent save conflict, immutable source/rig revisions, source-linked recipes and tests, real skin/weight/animation parsing, scanner rebuild race, scoped downloads, Host/Origin guards, filenames and limits. All test writes use temporary stores. Command: `python -m unittest discover -s tools/bear_studio -p test_*.py -v`. |
| [Final browser rig and motion regression](../../evidence/bear-studio/20261006T134902Z/final-rig-regression.json) | **24/24 passed** in actual Three.js r170, receipt inspected. Uncropped and 52% cropped samples export/reload with 16 bones and actual non-root deformation. Corrupt/nonfinite weights, invalid joints and stale landmark exports fail cleanly. Temporary influence colours are not exported; a hidden owned rig still exports its complete skin. This supersedes the retained 18-check earlier receipt. |
| Same browser receipt, animation cases | Three imported source clips (`Sitting_Idle_Loop`, `Hit_Chest`, `Walk_Loop`) produce measured vertex motion. An exported bear reloads with eight clips and retained animation provenance. The 52% crop removes 2,840 triangles and retains 3,350 vertices / 5,160 triangles. |
| [Launcher checks](../../evidence/bear-studio/20261006T134902Z/launcher-checks.json) | **4/4 passed**, receipt inspected. Existing correct service is reused; the occupied scanner port and invalid port are refused. |
| [Rendered studio](../../evidence/bear-studio/20261006T134902Z/studio-inspect.jpg) | Direct 1280×720 viewport capture inspected. The bear and its support are visible, with source identity, source warnings, rig state and human review separately labelled. |
| [Saved rig r2](../../evidence/bear-studio/20261006T134902Z/saved-rig-r2.glb), [recipe](../../evidence/bear-studio/20261006T134902Z/saved-rig-r2.recipe.json), independent live HTTP read | Bear `bear_7ee1160b65c449be` has source r1, two saved rig revisions and a test pinned to rig r2. Downloaded and retained r2 independently parse with one skin and six real clips, including `UAL · Sitting_Idle_Loop`. Its 1,881,796-byte GLB hash is `48fbd2c9520ae1f898366b6e5fa747e3958ea88bbdcd4eefb4ee7da37ddc798c`, matching the catalogue. Source bytes, embedded source identity and CC0 animation provenance match. Human review remains `unreviewed`. |
| [Service restart](../../evidence/bear-studio/20261006T134902Z/restart-check.json), [catalogue snapshot](../../evidence/bear-studio/20261006T134902Z/catalogue-before-restart.json) | The integrator stopped and restarted the owned service. The complete catalogue before/after is equal, including source r1, rigs r1/r2, the r2 test and pending human review. Receipt inspected. |

Source lineage is explicit: the bundled sample retains its original hash and scan warnings; the immutable derivative stores a source revision/hash, recipe, structural report and GLB. Animation loading verifies the retained creator GLB hash before use. Imported motion records author, CC0 license, exact source hash/clip, strength, angular cap, method and review status in exported GLB metadata. Adding a clip creates an unsaved draft; it does not attach new test evidence to the previous saved rig.

The UI distinguishes source scan checks, draft rig structure, test records and human review. Saving landmarks alone creates no rig. The backend independently checks the saved artifact's actual skin, joints, weights and animation channels instead of accepting a client success label.

## Limits

This sample includes a fused supporting box. Cropping removes whole triangles and leaves an underside needing cleanup; its original collision becomes stale. Heuristic weights and transferred humanoid rotations require visual inspection around touching limbs and seams. The motion regression records ground penetration in some poses (about 9.9 mm below the floor in its cropped motion case). Root travel, foot planting, collision, anatomical fit, game readiness and visual acceptance are not certified. The saved Unreal chamber and existing static-prop importer are separate from this browser rig workflow.

No further code-review blocker was found. The new in-page Cancel / Discard button paths remain a browser-verification gap at this review update; code inspection is not a claim that those clicks have run. The integrator's UI workflow receipt should identify the separately executed save, motion, test and download paths.
