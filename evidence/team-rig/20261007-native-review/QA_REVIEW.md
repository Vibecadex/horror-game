# Native team-rig QA — 7 October 2026

**Basic compatibility passes for the synthetic fixture. Real-scan and production character acceptance remain open.**

[Native image review](review.html) · [verification](verification.json) · [delivery identities](delivery-inputs.json) · [repeatable workflow](../../../study/TEAM_RIG_NATIVE_REVIEW.md)

## What was tested

The user installed scanner dependencies. `xatlas 0.0.11` imports and the existing team's `tests.test_rigfit` suite passes **35 tests in 89.345 seconds**. This count is from the installed source, rather than an older PR's stated count. The terminal result is recorded in `verification.json`; a complete test-output file was not captured.

The original Rupert2/test-package runtime GLBs were absent. A new fixture was generated from the team's procedural test bear, landmark detector, rigfit pipeline and four clip generator functions at scanner `8b396ab`. Its source geometry, landmark data, posed fit, rigged GLB, animated GLB and exact source hashes are retained under `Assets/Adapted/BearRigfitReview/SyntheticV1`. It is explicitly labelled synthetic and uses diagnostic position colours.

A separate fresh Unreal process reopened the saved assets. The [current receipt](../../implementation/20261007T121822-verify_team_rig_fixture/receipt.json) passes **89 checks**, with **15 native held-pose captures** and seven clips advancing in Play-in-Editor. The review world is unsaved and uses scale 1, fixed camera and actual imported materials.

## Source versus engine

- Exactly 21 expected bones and the complete parent hierarchy survived import. `Hips` stays the root; no extra root was inserted.
- Rest height is **47.5242 cm**, base Z=0. The synthetic source's metre scale and axes convert to centimetres, Z-up, Y-forward and X-left. Rest joint error is under 0.000014 mm.
- The four two-second source clips were checked at nine times each. An independent stdlib GLB evaluator computed all **756 source bone positions** without calling the team's animation implementation. Maximum difference from saved Unreal animation evaluation is **0.4543 mm**.
- Runtime held poses match expected source/saved retarget evaluation within the test's 2 mm limit. All seven clips advance by approximately 0.7 seconds during their bounded playback checks and move bones. Different held images were produced for both sampled times of every clip.
- New source and target IK rigs map six chains. Basic mannequin idle, forward walk and attack retargets save, reopen and play. Animated segment lengths stay stable. Automatic target-pose alignment was sufficient for this compatibility probe; no manual joint rotation editing was used.

These checks do not measure every skinned vertex or prove production deformation quality. Retarget clips are compared with their saved Unreal playback evaluation, not with a claimed independent ground truth for artistic motion.

## Render findings and corrections

The initial default Interchange import recomputed normals. Native images exposed visible faceting, including the head/ears. The guarded repair changes only the owned mesh's LOD build setting to preserve source normals; future imports specify that setting explicitly. The current saved readback confirms it and the before/after images show smoother shading. Tangents are still generated because the fixture does not provide them.

The source clips move the intended regions: the bear's right arm waves, the legs alternate, the head turns, and the spine bends. The diagnostic texture remains attached. No gross mesh explosion or detached region appeared in the inspected poses.

Remaining visible problems are shoulder/armpit and hip pinching, lumpy torso folds, and imperfect foot contact. The [retargeted attack at 0.70 s](../../implementation/20261007T121822-verify_team_rig_fixture/12-RET_MM_Attack_01-0.70.png) has conspicuous triangular dark defects at the armpit and across the torso; those need weight/topology investigation. Retargeted walk/attack poses can float; neither a foot IK solution nor a grounded gait was authored. Strong paw/arm rotations crease the automatic weights. These are meaningful character-quality gaps even though compatibility checks pass.

Retargeting disables the retargeter's root-motion operation and IK solver but retains the source animations' root settings. Walk and attack enable root extraction; walk also forces root locking. Because `Hips` is the skeleton root, a production locomotion/root setup requires a separate decision and review. This run does not certify it.

## Failed checks retained

- [12:01 editor-only attempt](../../implementation/20261007T120106-verify_team_rig_fixture/receipt.json): saved animation data passed, but editor preview did not refresh its held pose. The final test uses an actual PIE world.
- [12:03 source-clips proof](../../implementation/20261007T120343-verify_team_rig_fixture/receipt.json): four source clips played, before the normal repair.
- [12:14 retarget attempt](../../implementation/20261007T121403-verify_team_rig_fixture/receipt.json): the evaluator's default ignored root locking, unlike playback.
- [12:16 retarget attempt](../../implementation/20261007T121622-verify_team_rig_fixture/receipt.json): attack still differed because enabled root extraction was not represented by the evaluator options.
- [12:18 current proof](../../implementation/20261007T121822-verify_team_rig_fixture/receipt.json): compressed evaluation, saved root-lock rules and enabled root extraction match the runtime player. No tolerance was relaxed to pass these failures.

The [native log excerpts](native-log-excerpts.txt) retain warnings. Retargeting logged dependency-load notices and absent animation curves for these bone-only source sequences. Startup also logs Unreal's built-in diagnostic assertions; the fresh host exited successfully and the scoped checks passed. The blank review world has no navigation mesh. No claim of a warning-free editor is made.

## Preservation and limits

The chamber map SHA-256 remains `616822f1d349a710ddbb8ced99babe8b0dbc95f69c41299f3f82d843faba117d`. No pre-existing tracked game Content, Config or project descriptor changed. New native assets stay under `/Game/ScannedBears/RigfitReview`; no bear was placed into the encounter. Scanner source/local fixes and the existing Studio catalogue were not edited.

The following remain unverified or incomplete: the team's actual Rupert2/neutral-template exports, real-scan skin quality, Studio's separate 16-bone exports in Unreal, physics/collision behaviour, packaged loading, sustained performance, foot planting, production retargeting and user art acceptance. Chamber parity remains a separate open task against the selected industrial-room references.
