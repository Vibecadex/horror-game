# Independent review: diffuse rear haze and character fill

Reviewed the complete 1280×720 [close gameplay](../../implementation/20261005T085410-capture_parity_room/01-matched-gameplay.png), [extreme-distance gameplay](../../implementation/20261005T085410-capture_parity_room/02-gameplay-wide.png), and [architectural overview](../../implementation/20261005T085410-capture_parity_room/03-room-overview.png), plus the unchanged selected reference and preceding 084605 candidate. This is an interim review: the optional room extension and ordinary-input movie remain pending. No engine was launched or shared asset changed by the reviewer.

The previous luminous rear fog bar is absent from both supplementary views. The deeper diffuse cyan haze recedes into the bulkhead and pillars without the hard horizontal luminous strip. This resolves that specific visible defect. The extreme-distance player now has a readable lit head, torso and limbs next to the pool; the figure remains small at this camera distance, so temporal control/aim legibility still needs the normal-input movie.

The close view retains the raised fracture field, perimeter chips, textured cloth, attached crown seam, long connected shadow and player light pool. It is a useful comparable view of the saved gameplay camera, not the architectural camera. The manual player bound exceeds the suggested height tolerance by 0.29 percentage points, with pose and weapon direction contributing; the framing diagnostic is kept false rather than silently relaxed. This is not a reason to churn the saved camera.

| Same semantic region, display luma 0–255 | Reference | 084605 | 085410 |
| --- | ---: | ---: | ---: |
| Far haze | 78.61 | 106.53 | 67.26 |
| Four corner patches | 0.53 | 17.02 | 9.54 |
| Foreground fracture/wear patch | 88.93 | 89.63 | 91.91 |
| Central floor | 117.28 | 128.99 | 131.89 |
| Cloth patch | 48.65 | 72.12 | 72.29 |
| Player pool | 219.44 | 209.23 | 210.01 |

The current boss-shadow/nearby-floor ratio is 0.200 against reference 0.200. Pool/surround is 1.935 against 2.011. These corroborate useful local light relationships, not silhouette or artistic equality. Foreground fracture detail RMS remains 6.54 versus reference 7.71; contrast standard deviation is 18.12 versus 23.79. V3 is clearly stronger than the previous sparse scratch field and should be preserved. Its cracks remain finer, less connected and less darkly recessed than the selected image.

The haze shape is now preferable. Its close patch is moderately below the reference after the former overshoot. If one scalar refinement is attempted, a small rear-source-only trial around +10% is reasonable; displayed luma does not scale linearly with light intensity, so this is a trial, not a conversion formula. Reinspect both wide views and reject any returning luminous band. A global exposure increase would worsen the brighter central floor, lifted corners and warm bright cloth.

Remaining close-image differences are mainly material/art direction: the cloth is warmer/brighter and less clearly woven, crown stitches are finer and sparser than the reference's chunky crossed repair, connected floor cracking is less prominent, and the selected image's bottom corners are substantially darker. The player silhouette is brighter with the useful added fill. The foreground fracture mean is close, but that alone cannot accept its crack shapes or depth.

[Full comparison](comparison.jpg), [marked regions](regions.jpg), [detail crops](details.png), [measurements and source hashes](metrics.json), and [methods](README.md) preserve this review. Four derived images fully decoded; the close source hash matches its capture receipt. Earlier candidates and the 48-check runtime result remain separate evidence. **The two targeted wide-view defects improved/resolved as described; final full-room visual disposition is intentionally still open pending the final shell and movie.**
