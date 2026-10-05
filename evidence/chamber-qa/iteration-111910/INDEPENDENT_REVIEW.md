# First crust-bank engine result: failed art iteration

**Do not accept this as a final chamber render.** Both original 1920×1280 PNGs and the [comparison](comparison.png) were independently inspected. [Provenance](provenance.json) preserves the exact successful capture receipt/hashes; a successful capture does not mean the depicted art is correct.

Several entire new crust cells appear as nearly solid black polygonal shapes, particularly the front near-center and right bank, the rear-left bank, and the reverse's left bank. Adjacent cells receiving similar illumination remain textured. The defect follows bank geometry across differently rotated placements. That is a material visual regression, rather than a small stylistic difference from the reference.

The observed pattern is consistent with missing/back-facing cap faces exposing dark underlying surfaces. The integrator and artist are investigating disconnected-face normals in the source exporter. Pixel inspection alone does not prove that cause; explicit top/bottom normal orientation after FBX roundtrip and saved material-slot-name mapping are the appropriate discriminating checks. Raising scene illumination would not correct a per-cell surface failure.

The wider architectural reverse FOV70 and local service accents are useful independent improvements: both left-side cabinets and more of the right pipe group now appear, consistent with the [earlier projection diagnosis](../reverse-services-diagnosis/DIAGNOSIS.md). The front camera, gameplay camera and scene exposure remain separate from that review-camera change.

The original crust source/imported meshes and this failed render remain preserved. The planned repair uses separately named `SM_ChamberCrustBank_A_V2` and `SM_ChamberCrustBank_B_V2` assets, with the same five placements. The independent harness now requires only the separately frozen V2 source manifest; old meshes assigned anywhere in the crust namespace fail the exact identity/count audit. That strengthens provenance but still cannot prove correct appearance. Fresh front/reverse plates must visibly close the black-cell defect before final visual disposition.

The [original import receipt](original-crust-import.json) was copied byte-for-byte before the integrator's V2 rerun could replace its shared output path. SHA256: `9984381a0a2b20389f50da1afcb44ba36fccaa81bec6f10df3a5cbf158359fd9`. It records the old A/B mesh paths; its geometry/import pass must not be mistaken for visual approval.

The later [V2 source review](../crust-v2-source-review/INDEPENDENT_REVIEW.md) records the explicit orientation repair and preservation checks. It does not close this engine-image failure by itself; the fresh saved-engine pair remains decisive.

The subsequent [113224 engine review](../iteration-113224/INDEPENDENT_REVIEW.md) visually closes the solid-black Crust cell defect in both saved directions. Its remaining source-audit and fidelity limits remain explicit.
