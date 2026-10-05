# First V2 runtime pose review and harness correction

Read the [original runtime receipt](../../implementation/20261005T074830-verify_parity_runtime/receipt.json) and opened all six full-size captured PNGs: Idle, Walk, Crawl, Attack, Hit and Defeat. The [full-frame sheet](all-six-poses.jpg) and [unrescaled skin crops](skin-crops.png) are supplementary navigation aids; each source image was also inspected independently.

## Demonstrated harness error

All six reported failures concern `*_sixteen_original_bones_and_pose_motion`. Each sample actually contains the original imported hierarchy `TeddyRig` followed by the16 authored deform bones, in the expected order. The original authoring source `tools/adapt_teddy.py` names its Blender armature object `TeddyRig`; the unchanged original skeleton asset identity is recorded in this runtime receipt. The harness incorrectly treated the Blender deform-bone count as the entire imported Unreal component bone count.

Measured maximum bone movement between the first and last samples is0.82cm Idle,56.10cm Walk,56.09cm Crawl,132.37cm Attack,3.80cm Hit and317.77cm Defeat. Original clip identity, animation-time progression, finite bones/bounds, V2 mesh identity and all six image decodes passed. No animation was static because of the failed name-count assertion.

The corrected harness requires the explicit17-name imported list and additionally compares original/V2 parent links, verifies that original `TeddyRig` has child `root`, and retains the actual deformation/progression threshold. It does not accept arbitrary extra bones. The failed receipt and images remain unchanged; a fresh run is required before reporting a passing corrected suite.

A second harness issue was visible in the samples: the first frame after each paused screenshot advanced the next animation directly to0.4s. This meant the0.5s Hit clip was sampled only near its end. The corrected script drains the first resumed game tick before starting the next clip, preserving natural playback while allowing early/middle Hit poses to be sampled. This is a sampling fix, not an animation asset edit.

## Visual skin findings

- In Idle, Walk, Crawl, Attack and Hit, the crown seam remains visibly aligned to the upper head. No detached seam island, dramatic stretched thread spike, missing body section or exploding mesh is apparent in these six inspected poses.
- Cloth has visibly more surface texture than iteration2. The surface reads as rough/fuzzy brown material; the selected target's olive woven grain and heavier cross-stitches remain a separate quality difference.
- The conservative component render bounds are identical across all poses, as expected for static culling bounds. They do not measure deformed mesh contact and must not be used to clear ground penetration or floating.
- The Defeat view is an awkward rolled/elevated pose with a partly detached-looking shadow beneath the body. Some joints are naturally above the floor in a rolled pose; their heights alone do not prove floating. Nevertheless, a convincingly grounded collapse is not established by this still and should be checked in ordinary motion or against deformed surface vertices before claiming it.
- The Attack capture contains some noisy/block-like shadow breakup beneath the forelimb. A settled moving capture is needed to distinguish temporal shadow accumulation from a persistent artifact.

This limited skin review does not clear camera extremes, ordinary AI transitions, physical controls or final visual parity. Corrected suite results and motion evidence remain pending.
