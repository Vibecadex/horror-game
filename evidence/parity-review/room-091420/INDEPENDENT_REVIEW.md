# Independent saved-room result

The fresh [saved-room receipt](../../implementation/20261005T091420-verify_full_room/receipt.json) passes **28/28 checks**, and its host exits0. This includes the original22 checks plus the six new extension checks. The saved map contains84 extension actors,46 shell and38 dressing, using21 owned meshes. Ownership, namespace, all primitive/actor collision settings, finite conservative world bounds and clear combat interior pass actual readback.

All12 staged camera cases retain both character bounds, have clear collision traces, and produce zero visible-decoration box intersection hints, now including the extension. Positive control traces still hit the original floor/wall. Saved movement and real dash key routes stop at all four original walls; interior crossing/spawn capsule probes stay clear. This is meaningful functional/geometry evidence, not automatic lighting acceptance.

All six [camera-case images](six-camera-cases.jpg) were opened independently and their hashes match the receipt. Case03 exposed a real separate concern: the rear-center player was heavily veiled by haze above its bright pool. The [unaltered enlarged crop](rear-center-player-crop.png) preserves that finding. The integrator subsequently repaired it with local character-only fill; see the [independent repair review](../rear-092532/INDEPENDENT_REVIEW.md). The historical issue must not be presented as an unresolved current defect once those repaired poses are cited.

[Readback provenance](review-provenance.json) records checks, hashes and image paths. No engine process was launched by this reviewer. Tests use transient actor staging and injected key routes; physical keyboard/gamepad play and subjective acceptance remain separate.
