# Crown seam V2

This separate revision turns the seam route approximately 90 degrees in source XY so it crosses the crown in the saved gameplay view. The dark seam is 2.4 cm across, with 13 irregular thread bridges. The previous crossing upper-back continuation is absent. The original adapted teddy and V1 exports remain unchanged.

Import **Teddy_ParityV2.fbx** as a new SkeletalMesh using the existing encounter teddy Skeleton. Keep animation, texture and material importing off. Retain the original runtime clips and physics asset. Material slots remain **Material_0**, **SeamDark**, **StitchThread**. Use the tuned cloth, near-black rough seam and visible worn thread materials respectively.

The new mesh contains 24,698 triangles, including 2,738 added triangles. `manifest.json` records the exact unchanged body vertices, polygons, UVs and weights; 18 successful pose comparisons across six original clips; and a successful FBX readback preserving all 16 bone names and parents. The source file hash is unchanged, and the seven V1 FBXs still match their V1 manifest hashes.

`Teddy_ParityV2.blend` is the editable master. The six animation FBXs preserve the same motions with the new seam. `stitch-crown-detail.png` is a Blender studio view from approximately the gameplay viewing direction; it proves visible geometry, not the final Unreal lighting or cloth appearance. Root integration must reopen the new skin and inspect its actual animated gameplay capture.

Regenerate with the installed Blender and `tools/make_parity_teddy_v2.py`. That script writes only this owned V2 output directory and never launches Unreal.
