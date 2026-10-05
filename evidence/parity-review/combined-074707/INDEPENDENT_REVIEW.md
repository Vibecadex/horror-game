# Combined saved candidate review

Independently inspected the [combined Unreal capture](../../implementation/20261005T074707-capture_parity_look/01-matched-gameplay.png), its receipt, the selected reference, and generated [comparison](comparison.jpg)/[detail crops](details.png). Candidate SHA-256 matches the capture receipt. This is the saved gameplay view with held subjects, hidden HUD and player aim staged toward the boss; it is not an ordinary-play acceptance capture.

**Disposition: substantial material, floor and shadow improvement; visual parity remains incomplete.**

Physical chips now occupy more convincing perimeter bands and show readable edges/contact. The cloth is textured rather than smooth clay. V2's seam crosses the crown clearly. The boss shadow has a softer penumbra, and the player pool is more integrated with actual floor detail instead of a flat white disc. Tiny red distant fixtures now exist, though they are very faint. These are direct rendered observations, not conclusions from asset counts or material compiler success.

The most significant remaining gap is upper-frame atmosphere: the selected image carries luminous teal haze and readable red points, while this candidate's upper third is much darker. The bottom corners remain lifted relative to target. The upper teddy surface is warmer/browner and brighter than the target's olive/grey woven cloth. Central ground still reads as mottled concrete with chips and relatively faint thin cracks, rather than the target's connected fractured plates with wide fissures and chipped rims. These details should be corrected locally without undoing the now-close player-pool/floor balance.

| Diagnostic | Target | Combined candidate |
| --- | ---: | ---: |
| Whole-image display luma |57.36|58.10|
| Central floor display luma |117.28|126.64|
| Far haze display luma |78.61|35.99|
| Four corner patches display luma |0.53|10.12|
| Upper cloth display luma |48.65|69.91|
| Pool / surrounding floor ratio |2.01|1.95|
| Boss shadow / surrounding floor ratio |0.20|0.17|

The near-equal whole-image average is a useful example of why metrics cannot certify parity: the wrong spatial distribution of brightness is still obvious. Per-region masks are approximate, and body framing retains the tiny player-height diagnostic miss documented in iteration2. No image was warped, exposure-normalized or retouched to improve comparison.

The [six-pose review](../poses-074830/INDEPENDENT_REVIEW.md) separately addresses the new skin and a demonstrable harness bone-count error. The saved floor/light/clip checks from that run were positive, but its receipt remains failed until the corrected harness runs. Final edge/corner, ordinary movement, collapse grounding and artistic acceptance remain separate.
