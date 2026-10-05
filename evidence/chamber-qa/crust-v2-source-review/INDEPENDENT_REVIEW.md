# Crust V2 repair source review

The [V2 source preview](../../../Assets/Adapted/ChamberParity/CrustNormalsV2/crust-normals-v2-overview.png) was independently inspected. Both banks show complete broad plate faces in the backface-culling preview, with no obvious missing cap cells. The exact [frozen V2 manifest](../../chamber/20261005T095028Z/chamber-crust-v2-reviewed.json) hash is `c3e16e52b8611bc6fd5024f2530824bd06f7e6512319b2eea6e7ea052d21acef`.

[Independent provenance checks](provenance.json) confirm both original A/B FBX byte hashes still match the frozen originals, both new FBX hashes match the V2 manifest, and all five declared placement values/bounds remain unchanged. The old source meshes and [failed engine/import evidence](../iteration-111910/INDEPENDENT_REVIEW.md) remain preserved.

The artist's detailed source and FBX-roundtrip records were read and consistency-checked; QA did not rerun Blender. They identify 624 incorrectly oriented cap/underside triangles in original A and 536 in original B. Both V2 source and FBX readback report zero wrong caps/undersides, 39 closed positive-volume solids per mesh, upward Concrete-family/Crack faces and downward Dark undersides. Vertex positions/UVs are reported preserved; four tiny B bevel returns are classified as Aggregate. These are explicitly source-side records, not proof of the saved Unreal appearance.

The runtime harness requires only exact A_V2/B_V2 paths from this frozen source and rejects any assigned old crust mesh anywhere in that namespace. The same five placement, vertical-scale, world-height and NoCollision assertions remain. Fresh engine pixels must close the black-cell failure before the repair can be accepted visually.
