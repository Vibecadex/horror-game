# Damaged concrete floor kit

Original local geometry for the selected `study/visuals/direction-close-best.jpg` direction. The reference and existing AI surface maps were not modified or sampled into these exports.

`ParityFloor_Kit.blend` is the editable master. Six FBXs contain 25,394 unique triangles. `manifest.json` records dimensions, hashes, material slots, six successful FBX round trips and 45 suggested placements. `kit-overview.png` and `fracture-depth-detail.png` are Blender geometry reviews, not Unreal parity evidence.

Import as separate static meshes in a new owned namespace. Match materials by the names **Concrete**, **Aggregate**, **Dark**, because an importer may omit unused slots. Use the same world-aligned floor material for Concrete as the arena floor; otherwise the shallow plates can look like pasted patches. Aggregate is slightly lighter, rough fractured concrete. Dark is a narrow recessed crack bottom, not a broad backing sheet.

The source uses metres and FBX converts to centimetres. Mesh origins lie on local Z=0. Place on the measured floor surface, currently world Z=-5 cm, without upward Z scaling. Every mesh is decorative: NoCollision and actor collision disabled. Interior meshes reach at most 3.83 cm above the floor; EdgeSpall reaches 10.53 cm and belongs only near the perimeter. Recommended transforms use Unreal Rotator(pitch, yaw, roll).

FractureField_A has actual shallow cracked plates. Use sparingly and review its silhouette with the shared floor material. FractureField_B contains branching hairline ribbons and discontinuous edge lips without a backing sheet. Alternate the two rubble patterns and micro-chips with varied yaw and XY scale. Hide superseded oversized graphical decals when judging this kit. Check feet, shadows and aiming visibility in actual gameplay after import.

Regenerate with the installed Blender and `tools/make_parity_floor.py`. The script refuses an unowned destination. No Unreal process or original asset is modified by the generator.
