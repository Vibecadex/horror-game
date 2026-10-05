# FloorV3 and rear-atmosphere candidate review

Independently opened the saved [close gameplay](../../implementation/20261005T084605-capture_parity_room/01-matched-gameplay.png), [widest gameplay](../../implementation/20261005T084605-capture_parity_room/02-gameplay-wide.png), and [architectural overview](../../implementation/20261005T084605-capture_parity_room/03-room-overview.png). The close candidate hash matches its receipt. Comparison artifacts retain the unchanged full images and manually inspected semantic masks.

**The close view is the strongest candidate reviewed so far. Full-room parity remains incomplete.** Luminous far haze, distant red points, connected floor plates/chips, textured stitched cloth, a strong grounded boss shadow and the player light pool now coexist coherently. The foreground fracture construction is meaningfully closer to the selected target. Preserve those improvements while correcting the remaining spatial lighting problems.

The current wider gameplay and overview reveal an obvious horizontal luminous fog bar across the rear wall. It reads as a bright strip rather than diffuse volumetric depth. The close haze is also somewhat overbright: sampled display luma 106.53 versus target 78.61. Its four corner patches are 17.02 versus target 0.53. Red points are now visible. The widest gameplay player remains very small/faint and is located primarily by its flashlight patch; a good close comparison cannot clear that edge-readability limitation.

Upper cloth remains warmer/brighter and less visibly woven than target. The stitch seam is present and attached, but the target has chunkier cross-stitches and worn seam margins. FloorV3 now supplies the important interconnected plate structure; the remaining floor difference is stronger grouped dark cavities and varied fissure widths, not an absent floor construction.

## Fixed foreground-wear region

Used the same manually specified foreground polygon in all three 1280×720 images; no exposure normalization, warping or threshold optimization was applied.

| Diagnostic | Before FloorV3 (074707) | FloorV3 (084605) | Selected target |
| --- | ---: | ---: | ---: |
| Display luma mean |100.23|89.63|88.93|
| Display luma standard deviation |17.05|17.83|23.79|
| Detail RMS after 2 px blur |6.06|6.54|7.71|
| Fraction above display luma 80 |91.14%|68.32%|63.34%|

V3 moves foreground mean and bright coverage much closer and adds visible joined fractures. The remaining contrast/detail gap agrees with the visual need for broader dark cavity grouping and uneven crack widths. These values do not prove geometry depth by themselves, and adding arbitrary noise would not improve the art.

The close boss shadow-to-floor ratio is 0.198 versus target 0.200, and player-pool-to-surround ratio 1.979 versus 2.011. Preserve those relationships while reducing the rear light's excessive haze energy and smoothing its obvious bar-shaped distribution. Keep floor edits local and restrained. Ordinary motion, fresh corner captures and user acceptance remain separate gates.
