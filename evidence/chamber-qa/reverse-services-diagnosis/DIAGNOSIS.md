# Reverse service groups: framing and light

The [110142 reverse plate](../../implementation/20261005T110142-capture_chamber_views/02-chamber-reverse.png) has both causes. Existing equipment occupies the extreme edges, and its visible surfaces remain dark. Raising light cannot recover geometry outside the frame.

[Analytical projections](projection-diagnostics.json), calculated by the [read-only script](project_service_bounds.py), use actual saved component bounds from the 105657 room receipt and the recorded reverse camera/3:2 aspect from the 110142 capture. The camera is `(1450,100,1450)` looking at `(-600,100,0)` with horizontal FOV64. These are conservative screen-box projections, not measurements of rendered visibility or exact mesh area.

| Saved service component | Recorded FOV64 | Predicted FOV70 |
| --- | --- | --- |
| RightCabinetA, screen-left | Entire box fits, but occupies only x0.1–8.1% of frame | Entire box fits at x5.5–12.6% |
| RightCabinetB, screen-left | About 46% of projected box clipped | Entire box fits |
| LeftPipeRun_0, screen-right | About 64% of projected box clipped | About 13% clipped |
| LeftPipeRun_1, screen-right | Entire box outside frame | Only about 15% inside frame |

A labelled architectural FOV70 trial is a bounded first adjustment; FOV72 contains the whole far pipe rack's projected box. This should be judged against wall/door proportions by the art director. It does not authorize or require a saved gameplay camera change.

For the remaining darkness, trial two small environment-only accents aimed at the near-end equipment. Suggested starting points, **not verified settings**: cabinet light `(−650,1300,550)` aimed at `(−680,1570,210)`, around 1500cd, radius700cm and source300×100cm; pipe light `(−1000,−1200,620)` aimed at `(−1000,−1545,440)`, around 1200cd, radius700cm and source320×80cm. Retain environment lighting channel2, zero volume/indirect contribution and low specular contribution. Existing broad side washes aim near x+150/+250, farther from these near-end groups.

The saved-game integrator alone chooses and applies the trial. Inspect front and reverse afterward for pale wall patches, floor/character spill or a flattened silhouette before accepting it.
