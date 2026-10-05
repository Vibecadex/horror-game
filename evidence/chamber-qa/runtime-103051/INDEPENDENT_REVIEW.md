# Saved chamber and native cutaway audit

**20/20 checks passed; host exit 0.** Independently read the [compact receipt](../../implementation/20261005T103051-verify_chamber_runtime/receipt.json), verified its recorded hash against the complete [details](../../implementation/20261005T103051-verify_chamber_runtime/details.json), and read the [host result](../../implementation/20261005T103051-verify_chamber_runtime/host-result.json).

The saved readback contains 22 chamber actors and 35 static-mesh components: seven kit placements, the 19-component native cutaway, five floor instances using three source meshes, and four explicitly allowlisted beacon cubes. Ownership/source identities, disabled actual actor/component collision, finite conservative world bounds, unchanged floor vertical scale and the open combat guard all pass. There is exactly one new bulkhead body and one wheel. Both real service-door meshes are present in the cutaway.

| Native runtime case | Independently observed result |
| --- | --- |
| Ordinary startup | Camera `(-1678.79,170,1874)`, pitch −46°, FOV54; opposite wall hidden, native environment tick active. |
| External front position | Wall hidden throughout 12 samples; manager/component FOV41.5 matches the staged request. |
| Internal reverse position | Wall visible throughout 12 samples; manager/component FOV68 matches the staged request. |
| Camera 25 cm outside threshold | Wall hidden throughout 12 samples; FOV54. |
| Camera 25 cm inside threshold | Wall visible throughout 12 samples; FOV54. |
| Return to ordinary gameplay camera | Original position/rotation and FOV54 restored; director and environment ticks active, wall hidden throughout 12 samples. |

Collision remains disabled in every sampled state. The harness never forces wall visibility or disables the environment Blueprint tick. Its camera poses are explicit functional probes; the later revised artistic camera framing is evaluated by the separate gallery.

The [102211 failure](../runtime-102211/DIAGNOSIS.md) remains preserved. Reacquiring the active component and using its reflected runtime FOV setter resolves the transient harness restoration error. The strengthened checks confirm every staged FOV as well as the ordinary return; no saved game fix was needed for this test issue.

This is bounded saved-geometry and native-visibility evidence. It does not certify visual parity, wall-pop aesthetics, all ordinary gameplay positions, physical-device input, sustained performance or user acceptance. The existing room/input suite and fresh rendered gameplay remain separate evidence. Later material/light-only changes require new visual review, not a claim that this earlier audit was rerun.

Chamber05 subsequently replaces the five simple cutaway piers with retained room-pilaster meshes and attaches a reverse overhead light to that actor. Those new geometry/component identities postdate this receipt. The harness has been extended with exact component/path allowlisting and native light-owner hiding observations; its next run must verify them before this earlier result can be treated as current.
