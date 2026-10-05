# Chamber baseline: independent review

**Chamber parity is not reached.** The fresh front and reverse renders confirm major architectural and lighting gaps, not just small finishing differences. Both original PNGs were opened at full size and independently matched to the hashes and dimensions in the [capture receipt](../../implementation/20261005T095951-capture_chamber_views/receipt.json).

[Unchanged full-frame comparison](comparison.png) places the supplied concepts beside actual Unreal output. [Provenance](provenance.json) records source hashes and the aspect-preserving display method. Concepts are 571×378 and 475×320; engine images are native 1920×1280. No image was stretched, cropped or graded for the comparison.

## Principal findings

| Axis | Baseline finding | Needed correction |
| --- | --- | --- |
| Front enclosure | Rear wall occupies a roughly useful frame region, but a blank upper margin and nearly black side walls make it read as an isolated combat platform. Floor/wall junction and service attachment are poorly defined. | Establish a continuous, readable enclosure and corner/return structure. Judge final framing again once the new door and wall faces exist. |
| Front door | The broad flat/X-braced form is dim and heavily veiled. It lacks the target's recognizable wheel, divided leaves, strong chamfered recess and layered threshold. | Add the actual construction cues and provide light that reveals them at the full chamber distance. Brightness alone will not replace the missing shape. |
| Reverse wall | The upper third is overwhelmingly black and there is no visible two-door opposite-wall identity. | Build and reveal the real reverse wall, including both separated door bays, red indicators and intervening structure. This is a defining blocker. |
| Wall services | Individual red points survive, but electrical banks, pipe connections and tank/fan groupings mostly disappear. | Illuminate and integrate major groups with wall attachment, thickness and contact shadows. Small exposed fragments floating in black do not meet the target. |
| Ground | Broad pale smooth floor dominates. Isolated fractured patches and repeated small-chip arcs lack the target's connected plate-scale network and richer wear masses. In reverse, several crack/chip edges become bright thin filaments and glossy patches. | Add coherent multi-scale fractures, dark recesses, larger angular fragments and grouped damp/abraded areas. Avoid a visible patch perimeter and uniform bright bevels. |
| Atmosphere | A bright horizontal cyan veil erases much of the front wall. Reverse has very little readable wall light, while its near floor is already bright. | Reduce sightline veiling and light walls/door faces deliberately. Do not solve black walls by globally increasing exposure or lifting the already bright floor. |
| Gameplay evidence | These captures retain saved scene settings and actor positions, but freeze actors and use architectural cameras. | Recheck ordinary gameplay and camera safety after new wall integration; these stills are not a control or movement test. |

Front camera: `(-4460,180,2820)`, pitch about −30.91°, FOV41.5, looking +X. Reverse camera: `(1450,100,1800)`, pitch about −42.71°, FOV68, looking −X from inside the far wall. The reverse's steeper perspective shows more of the boss's top than the concept; refine wall-height share and floor foreshortening after the wall exists. Current cameras are useful diagnostic hypotheses, not an accepted framing match.

The baseline capture predates the new actor-hidden-state receipt enhancement. It records component visibility only. Later native cutaway verification must include the actor state, actual wall components, both directions and a return to ordinary gameplay, without capture-only visibility overrides.

## Priority

1. Correct full enclosure, front door identity and actual reverse wall landmarks.
2. Reveal both wall directions while removing the front cyan sightline veil.
3. Integrate major service groups, connected floor fractures and dark wear masses.
4. Refine matched cameras and verify that native cutaway behavior preserves the saved gameplay view.

No parity percentage or whole-image brightness pass is assigned. The earlier room test suite remains historical evidence for its unchanged geometry; it cannot certify the forthcoming chamber additions.
