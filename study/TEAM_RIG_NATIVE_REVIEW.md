# Team rigfit: native Unreal review

## Prerequisites and repeatable review

Use this integration checkout, hydrated Git LFS assets, Python 3.11+ and Unreal 5.8.3. Close the game/editor. The saved review needs no scanner service, new package install, native project DLL or certificate. Machine-specific engine settings remain in ignored `tools/project-settings.local.json` / `TEDDY_ENGINE_ROOT`.

Run [REVIEW_TEAM_RIG.cmd](../REVIEW_TEAM_RIG.cmd). It reopens the saved assets, checks skeleton/scale/animation, plays seven clips in an unsaved test world, and saves 15 held native images and a fresh receipt under `evidence/implementation`. It does not save a map or modify assets.

The scanner dependency install is now verified on this workstation: `xatlas 0.0.11` imports; all **35** `python -m unittest tests.test_rigfit -v` tests pass. Another workstation needs the scanner environment only to regenerate or fit new source geometry; the human runs any missing installation.

## Delivered evidence

The [image review](../evidence/team-rig/20261007-native-review/review.html) and [QA findings](../evidence/team-rig/20261007-native-review/QA_REVIEW.md) cover the current saved assets. The [fresh native receipt](../evidence/implementation/20261007T121822-verify_team_rig_fixture/receipt.json) passes **89 checks**. It includes 15 held images and actual advancing PIE animation positions for all seven clips.

| Item | Result |
| --- | --- |
| Provenance | Scanner commit `8b396ab`; exact team source hashes and retained inputs in [SyntheticV1/manifest.json](../Assets/Adapted/BearRigfitReview/SyntheticV1/manifest.json). |
| Input | **Synthetic procedural test bear**, diagnostic position-colour texture. Not Rupert2, a real scan, or approved game art. |
| Saved assets | `/Game/ScannedBears/RigfitReview/SyntheticV1`: mesh, skeleton, physics asset, material, texture and four animations. |
| Skeleton | Exactly 21 expected names/hierarchy, `Hips` root, no extra root. Rest joints agree with source within 0.000014 mm. |
| Size/axes | 47.5242 cm high, base Z=0. glTF metres/+Y-up become Unreal centimetres/+Z-up; forward +Y, left +X. This is the synthetic fixture's size, not Rupert2's. |
| Source clips | Wave, walk, look-around and bend retain their two-second duration. 36 sampled poses, 756 bone positions, maximum source difference **0.455 mm**. |
| Shading | Authored normals retained; default Interchange normal rebuilding caused faceted UV boundaries. |
| Retarget | Mannequin idle, forward walk and attack copied into `/Game/ScannedBears/RigfitReview/RetargetV1`. Six explicit chains, automatic chain-to-chain target alignment, pelvis/FK operations. |
| Playback | Seven saved clips advance and move bones in PIE. Captured poses agree with their expected playback evaluation; every clip has two different rendered poses. |

The retarget operation intentionally has no foot IK or root-motion operation. Saved source animation root settings remain intact: walk/attack enable extraction, walk also forces a root lock. The evaluation harness explicitly respects these settings. This establishes basic retarget compatibility, not a production locomotion system.

## Findings and remaining work

The synthetic bear remains coherent during the four test clips and retargeted poses. Smooth shading is restored, but shoulder/armpit/hip folds and torso creases remain visible. The attack at 0.70 s shows triangular dark defects at the armpit/torso. Walk/attack poses float or slide because these clips and weights have no contact solution. This is suitable for pipeline diagnosis and needs artist weight/topology work before adoption.

The team's original Rupert2 `b001bad18151`, synthetic scan `39973856faee`, and neutral-template comparison GLBs are still absent. The generated fixture exercises the same code and is an easier input. Obtain the original package before completing `bear-scanner/docs/RIG_TEST_UE5.md` for real bears. Do not infer real-scan quality, superiority of one template, or character approval from this test.

Studio's 16-bone draft builder and the static bear-pack importer remain separate. Next integration should preserve a supplied skeletal model as an explicit optional pack artifact, retain source warnings, and use a reviewed skeletal path. This run adds no skeletal auto-import to ordinary scan packs.

The saved chamber, gameplay, controls and previous characters are unchanged. Chamber parity against the selected teal industrial-room references remains open under [CHAMBER_PARITY_BRIEF.md](CHAMBER_PARITY_BRIEF.md).

## Source tools

- `tools/build_team_rig_fixture.py`: uses the installed scanner Python and team modules; requires `--scanner`; refuses an existing output revision. Sources stay under `Assets/Adapted/BearRigfitReview`.
- `tools/import_team_rig_fixture.py`: explicit Interchange skeletal import with source normals and four animation tracks; refuses an existing native destination.
- `tools/repair_team_rig_normals.py`: guarded correction for the first import, only on the owned review mesh. Its LFS lock is required before edits.
- `tools/retarget_team_rig_fixture.py`: creates new review IK rigs/retargeter and animation copies; never overwrites an existing destination.
- `tools/team_rig_source_pose.py`: independent stdlib evaluation of the source GLB hierarchy and quaternion animation.
- `tools/verify_team_rig_fixture.py`: fresh readback, independent source comparisons, retarget checks and PIE captures; no asset writes.

Use new source/native revision names for later inputs. Do not rerun historical builders or overwrite another owner's assets to make a review succeed.
