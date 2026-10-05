# Weighted teddy seam adaptation

`Teddy_Parity.blend` is a separate editable adaptation of `Assets/Adapted/Teddy/Teddy_Encounter.blend`. It adds a dark irregular crown seam, 13 crown stitch bridges and five upper-back stitch bridges. The source file remains unchanged.

Import **Teddy_Parity.fbx** as a NEW SkeletalMesh on the existing encounter teddy Skeleton. Turn animation, material and texture importing off, retain the original physics asset and runtime animation clips, and map slots by name: **Material_0** gets the tuned teddy cloth, **SeamDark** is a rough near-black seam, **StitchThread** is worn desaturated tan. No new skeleton or runtime Blueprint is required by this asset.

The six `Teddy_Parity_<clip>.fbx` files are preservation exports of the existing motions with the added geometry. The original clips can remain in use. No source bind bone, body vertex, polygon, UV or skin weight changed. Added vertices inherit nearby body skin weights through barycentric interpolation; only the existing head and spine bones affect them.

`manifest.json` records the unchanged source hash, exact 16-bone hierarchy, 18 successful start/middle/end pose comparisons across six clips and a successful skin-FBX readback. The addition is 3,764 triangles, making 25,724 total. Thread diameters are about 1.5-2.1 cm at the full-size boss. `stitch-crown-detail.png` and `teddy-parity-overview.png` show geometry with the source material in a Blender studio; they do not establish the final Unreal cloth appearance.

Regenerate with installed Blender and `tools/make_parity_teddy.py`. Unreal skeleton assignment, material overrides and animated contact still require a saved import and gameplay capture by the integration owner.
