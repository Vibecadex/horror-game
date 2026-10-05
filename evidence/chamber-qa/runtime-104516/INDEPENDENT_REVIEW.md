# Chamber06 saved geometry and native cutaway review

**22/22 checks passed; host exit 0.** Independently read the [receipt](../../implementation/20261005T104516-verify_chamber_runtime/receipt.json), verified the hash of its complete [details](../../implementation/20261005T104516-verify_chamber_runtime/details.json), and read the [host result](../../implementation/20261005T104516-verify_chamber_runtime/host-result.json).

The actual saved readback contains 23 chamber actors and 35 mesh components. The five exact `FrontPier_0..4` components use the retained room-pilaster mesh, with actual bounds outside the combat guard. The native cutaway retains 19 mesh components and owns exactly one `ReverseOverheadPool` SpotLightComponent. Previous source, tag, floor, collision, bounds and beacon assertions remain passing.

All five runtime cases contain 12 passing consecutive samples. Native wall hidden/visible state changes correctly outside/inside the front threshold, including external-front and internal-reverse probes. The overhead light belongs to that same actor and its owner's hidden state follows every transition. Active component and manager FOVs match each requested stage; ordinary position/rotation and FOV54 return correctly with native ticking active. These are ownership/state observations, not a photometric measurement of light contribution.

The [104400 visual comparison](../iteration-104400/comparison.png) independently confirms that the central replacement pier is now visible in front of the wall backing; its prior base-only occlusion defect is resolved. Existence/bounds checks alone would not establish that repair.

The earlier failed return-camera receipt and both earlier passing revisions remain preserved. This run predates the planned additional sparse large-slab mesh/clusters. Those additions require exact frozen-manifest identity/count and bounds verification before a final current-scene claim. The old full-room/input suites and ordinary gameplay recording remain separate coverage.
