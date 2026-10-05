# Fracture field V3

Separate replacement for `SM_ParityFractureField_A`; the previous Floor kit is preserved.

- Editable source: `ParityFracture_V3.blend` and `tools/make_parity_fracture_v3.py`.
- Import `SM_ParityFractureField_A_V3.fbx` as a new static mesh. Do not overwrite the old mesh.
- Coordinates: metres, +Z up, underlying floor at local Z=0; same local origin convention as the existing kit.
- Use the current Field_A actor placement/rotation/XY scale. Keep Z scale1, assign `NoCollision`, disable actor collision.
- Bind `Concrete` to the current world-aligned floor; `ConcreteLight`/`ConcreteDark` use the same aligned maps with base-colour multipliers1.18/0.82. Bind `Aggregate` and `Dark` to the established edge/recess materials.
- `manifest.json` records exact dimensions, export hash, slot names, interrupted boundaries, measured detached-fragment spans and FBX roundtrip checks. Seventeen detached fragments have actual longest spans20–40cm.
- `fracture-v3-overview.png` and `fracture-v3-depth.png` are Blender construction previews with neutral temporary inspection materials. They are not Unreal fidelity evidence.

The new field uses interrupted, jittered, variable-width fracture paths; selective corner chips; mostly flush concrete with a few shallow lifted plates; correlated lighter/darker wear groups; and a torn perimeter. Its highest surface is under3.3cm. Unreal import, material binding and actual gameplay comparison remain the integration owner's verification.
