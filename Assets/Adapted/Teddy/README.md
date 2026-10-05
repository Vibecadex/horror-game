# Adapted encounter teddy

The original GLB and its recorded CC0 source evidence remain in `Assets/ThirdParty/HorrorTeddyBear`. These files are separate adaptations for `/Game/TeddyEncounter/Teddy`.

`Teddy_Encounter.blend` is the editable source. It contains the widened, welded and smoothed mesh, 16-bone weighted skeleton and six actions. Individual FBXs preserve idle, walk, crawl, attack, hit and defeat. `Teddy_BaseColor.png` derives from the original embedded texture; Unreal's owned cloth material adds desaturation and brightness tuning.

`adaptation.json` describes the first export and is retained as historical evidence. The later `motion-refinement.json` supersedes its walk timing and ground-contact notes: walk and crawl use 37 sampled frames over 1.2 seconds, baked foot targets and skinned-surface height correction. Boss world speed is 105 cm/s; the 0.35-scale stitchlings use 55 cm/s and a compressed crawl silhouette. The defeat clip is also corrected against the floor.

Unreal pose samples and actual continuous combat were inspected. Walking feet move, the anticipation precedes damage, and the fallen boss remains grounded after collision is disabled. This is procedural animation with visible limitations in turning and deformation, not motion capture or final art acceptance.

Authoring: `tools/adapt_teddy.py`, `tools/refine_teddy_motion.py`, `tools/import_encounter_art.py`. Reimport replaces only owned assets and requires `TEDDY_REIMPORT_OWNED=1`; inspect material assignments and skeletal-mesh usage flags afterwards. Earlier mesh versions and the original source are preserved in the implementation evidence and `.blend1` backup.
