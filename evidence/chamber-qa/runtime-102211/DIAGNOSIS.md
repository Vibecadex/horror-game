# Initial chamber audit: return-camera failure diagnosis

The original [102211 receipt](../../implementation/20261005T102211-verify_chamber_runtime/receipt.json) remains unchanged: **18/19 checks passed**. The only failed assertion is `native_cutaway_ordinary_gameplay_return`.

All 12 return samples show the original ordinary camera position/rotation, the correctly hidden opposite wall, native environment ticking, and disabled actor/component collision. The failed term is FOV: original gameplay was 54°, while the test's camera manager remained at 41.5°, its first staged value. The intervening reverse and threshold stages also retained 41.5° despite the harness requesting 68°/54°. Thus this failure does not demonstrate a broken native cutaway or changed saved gameplay. It demonstrates a transient test-camera restoration problem that must be repaired and rerun.

The harness held one `CameraComponent` reference and changed editor properties through it across all stages. It now reacquires the director's live component at each stage and uses the reflected runtime `SetFieldOfView` function. The installed Unreal 5.8 `CameraComponent.h` lines 43–46 verify the callable setter and field assignment; Context7's current official-library retrieval did not provide the precise setter implementation, so the installed engine source resolved that detail.

The corrected harness also records active component identity/FOV and asserts the requested component **and** camera-manager FOV during every stage, retaining the original FOV return requirement. No saved game or asset is changed. This strengthens the evidence instead of dropping the failed condition. A fresh engine receipt is required before the diagnosis can be closed.

Complete later readback will be written to `details.json`, with its hash and counts in a compact `receipt.json`, to avoid repeating the large component arrays in the standard runner's console output.

## Resolution

The [fresh 103051 audit](../runtime-103051/INDEPENDENT_REVIEW.md) passes all 20 checks with host exit 0. Every staged manager/component FOV and the original FOV54 return now match. The original failed receipt remains unchanged; the rerun resolves the harness fault rather than relabeling that failure as a pass.
