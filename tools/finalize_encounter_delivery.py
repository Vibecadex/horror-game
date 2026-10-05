"""Assemble review artifacts from verified runs without replacing their evidence."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for name in ['capture','record','native','main','edges','camera']:p.add_argument('--'+name,required=True)
args=p.parse_args();runs={k:Path(v).resolve() for k,v in vars(args).items()}
receipts={k:json.loads((v/'receipt.json').read_text()) for k,v in runs.items()}
assert all(r['passed'] for r in receipts.values())
out=ROOT/'evidence/delivery';out.mkdir(exist_ok=True)
assert not (out/'manifest.json').exists()
subprocess.run(['python',str(ROOT/'tools/make_encounter_comparisons.py'),str(runs['capture']),str(runs['record'])],cwd=ROOT,check=True)
def copy(source,name):
    assert not (out/name).exists();shutil.copyfile(source,out/name)
copy(runs['record']/'TeddyEncounter-gameplay.mp4','TeddyEncounter-gameplay.mp4')
copy(runs['capture']/'position-01.png','gameplay-still.png')
copy(runs['native']/'standalone.png','standalone-hud.png')
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(runs['native']/'standalone-audio.wav'),'-ac','2','-c:a','pcm_s16le',str(out/'native-game-audio.wav')],check=True)
encoded=json.loads((runs['record']/'encoded.json').read_text());perf=json.loads((runs['native']/'performance-audio.json').read_text());preservation=json.loads((ROOT/'evidence/implementation/preservation-audit.json').read_text());assert preservation['passed']
count_main=len(receipts['main']['checks']);count_edges=len(receipts['edges']['checks']);count_camera=len(receipts['camera']['cases'])
def link(key):return '../implementation/'+runs[key].name+'/receipt.json'
review=f'''# Teddy Encounter review

[Play guide and controls](../../ENCOUNTER.md) · [Offline visual viewer](review.html) · [Gameplay movie](TeddyEncounter-gameplay.mp4)

The saved encounter uses `/Game/Maps/TeddyEncounter` in Unreal 5.8.3. The movie shows approach, independent aim, a dodged strike, damage, moving fire, animated boss defeat, pause/resume and restart. It uses normal saved Blueprint gameplay driven through Enhanced Input; there are no staging teleports, health edits or AI freezes after its initial loading pause.

The movie is **silent** because this offscreen PIE capture route returned empty audio. That empty track is omitted. The ordinary `-game` process separately produced nonzero sound: [native game audio](native-game-audio.wav), a stereo downmix of the preserved master recording. Sound design is proposed original synthesis; source reference audio was not auditioned.

The source recording contains {encoded['source_frames']} unique captured frames at 1014×550, about {1/encoded['capture_interval_median_seconds']:.1f} captures/second, encoded into a {float(encoded['metadata']['format']['duration']):.2f}-second 30 fps container using frame duplication. It is actual runtime output, not an animation render or a claim of 30 unique captures/second. Request-time telemetry is contextual, not exact rendered-frame identity.

## Comparison stills

[Reference 5 seconds](comparison-05.png) · [Reference 10 seconds](comparison-10.png) · [Reference 16 seconds](comparison-16.png) · [Gameplay sequence](gameplay-contact-sheet.png)

The references use the recorded upright crop `[76,0,700,384]`; social overlays are covered by explicit rectangles rather than reconstructed. [comparison-method.json](comparison-method.json) records all masks. The game side uses 1280×720 held gameplay plates, resized without changing aspect ratio. NPC movement and the player are staged for composition, the world is paused, and the HUD is hidden only for these plates. Camera/pawn state remains held until CRC validation and full pixel decoding complete. These plates establish a reviewable composition, not physical input or dynamic frame identity. Ordinary `Shot` captures in the gameplay movie retain the HUD and normal rendering.

The main framing error is corrected: an elevated -51-degree view tracks the player/boss pair and widens at greater separation. The pale teddy, small human, crawling threats, cool floor lighting, dark perimeter, red practicals and cyan aim/fire feedback now share the combat composition. A late edge review also corrected foreground clipping and the rifle's reversed hand attachment.

The three largest remaining visual differences are:

1. **Creature surface and anatomy:** the requested teddy substitution is unmistakable, but its cloth and silhouette remain smoother and simpler than the reference's irregular creature. Bulk, welded smoothing, a weighted rig and grounded motion improved the downloaded base; this is not a fidelity-equivalent replacement.
2. **Environment:** the floor has worn texture and hairline cracks, but its slab rhythm and straight containment walls remain more regular than the source's broken, mottled ground. Long-distance camera widening reveals more arena architecture than the source frames.
3. **Motion and effects:** foot-targeted walking/crawling, anticipation, hit response and a grounded fall are present; turning and procedural deformation remain less nuanced than the source. The attack circle is a proposed gameplay aid, brighter and more explicit than anything recoverable from the obscured source HUD.

## Verification

| Evidence | Result and scope |
| --- | --- |
| [Main encounter]({link('main')}) | {count_main}/{count_main} checks: possession, no-input baseline, mapped movement, aiming while moving, attributed fire/damage, dodge, telegraph, defeat, pause and two restarts |
| [Collision and input edges]({link('edges')}) | {count_edges}/{count_edges}: wall/dash collision, cursor aiming, rifle direction, invulnerability, actual strike evasion, player defeat/input suppression and restart |
| [Camera bounds]({link('camera')}) | {count_camera}/{count_camera} staged edge/diagonal compositions; conservative player/boss bounds, plus three actual corner screenshots |
| [Held image proof]({link('capture')}) | Three fresh 1280×720 PNGs; all CRCs and full pixel decode; held state through completion |
| [Continuous play]({link('record')}) | Normal saved encounter, all source PNGs and final MP4 decoded; boss and minions defeated; restart restores 100/300 health |
| [Ordinary game]({link('native')}) | Saved Blueprints executed under `-game`; native 1280×720 PNG fully decoded before process exit; nonzero audio; clean exit |
| [Preservation](../implementation/preservation-audit.json) | {preservation['unchanged_count']}/{preservation['baseline_files_checked']} archived baseline files unchanged; source video, source ZIP and original GLB hashes unchanged |

The ordinary game's CSV profiler recorded {perf['metrics']['FrameTime']['samples']:,} frames over about five seconds, following three game seconds of warmup, at **1280×720** on **RTX 5080 / Ryzen 9 9900X**. Median frame time was **{perf['metrics']['FrameTime']['median_ms']:.2f} ms**, p95 **{perf['metrics']['FrameTime']['p95_ms']:.2f} ms**; median GPU time was **{perf['metrics']['GPUTime']['median_ms']:.2f} ms**. [Full profile and conditions](../implementation/{runs['native'].name}/performance-audio.json). This is a short offscreen Development run with a warm shader cache, not a packaged-build or sustained-performance benchmark. The 1014×550 editor capture timing is not substituted for this measurement.

All controls above are automated action/cursor evidence. Physical-device behavior, gamepad support, exact visual fidelity and user acceptance are unverified. The isolated starter's earlier fire-attribution gap remains preserved; these encounter-specific fire/damage checks are independent. Some earlier editor runs returned 0xC0000005 after normal shutdown logs and completed images; those failures remain recorded. The final results do not establish that the intermittent editor shutdown issue is permanently resolved.

Editable Blender files, FBXs, textures, WAVs and source/license evidence are linked from [ENCOUNTER.md](../../ENCOUNTER.md). No original or baseline was replaced. [manifest.json](manifest.json) records delivery and final owned-asset hashes.
'''
(out/'README.md').write_text(review,encoding='utf-8')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Teddy Encounter review</title><style>body{margin:0;background:#071015;color:#c3d0d2;font:16px/1.6 "Segoe UI",sans-serif}main{max-width:1120px;margin:auto;padding:36px 24px}h1{font-size:36px;color:#edf3f4;margin-bottom:0}h2{margin-top:38px}a{color:#80cbd0}video,img{display:block;width:100%;height:auto;background:#000;border:1px solid #23363c;border-radius:5px}p{max-width:850px}figcaption{font-size:14px;color:#9cafb5;margin:8px 0 25px}figure{margin:25px 0}audio{width:100%;max-width:600px}.meta{color:#82bcc1;font-size:14px}</style><main><p class="meta">UNREAL 5.8.3 · SAVED BLUEPRINT ENCOUNTER</p><h1>Teddy Encounter</h1><p>Elevated combat framing, an animated teddy and three surrounding threats. Move, aim, fire, dodge, survive and restart.</p><video controls preload="metadata" poster="gameplay-still.png" src="TeddyEncounter-gameplay.mp4"></video><p class="meta">Actual input-driven gameplay. Silent offscreen editor capture; approximately 9 unique captures per second.</p><p><a href="../../ENCOUNTER.md">Play guide and editable assets</a> · <a href="README.md">Verification and limitations</a> · <a href="TeddyEncounter-gameplay.mp4">Open movie</a></p><h2>Reference comparisons</h2><p>Social overlays are masked. The game plates hold staged positions for visual review. The teddy substitution is intentional; the source creature has more irregular surface detail.</p>'''
for sec in [5,10,16]:html+=f'<figure><a href="comparison-{sec:02}.png"><img src="comparison-{sec:02}.png" alt="Reference at {sec} seconds beside the held Teddy Encounter gameplay view"></a><figcaption>Reference {sec} seconds / actual held gameplay view</figcaption></figure>'
html+='''<h2>Ordinary-game audio sample</h2><p>Proposed original ambience and impacts recorded separately from the ordinary game. This is not the reference soundtrack or a dubbed movie track.</p><audio controls src="native-game-audio.wav"></audio><p class="meta">Automated behavior is verified. Physical devices and user acceptance remain separate review steps.</p></main></html>'''
(out/'review.html').write_text(html,encoding='utf-8')
def digest(path):return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
owned=list((ROOT/'TeddyBlueprint/Content/TeddyEncounter').rglob('*.uasset'))+[ROOT/'TeddyBlueprint/Content/Maps/TeddyEncounter.umap']
editable=[x for x in (ROOT/'Assets/Adapted').rglob('*') if x.is_file() and x.suffix!='.blend1']
manifest={'passed':True,'runs':{k:v.relative_to(ROOT).as_posix() for k,v in runs.items()},'delivery':[digest(x) for x in out.iterdir() if x.is_file()],'owned_unreal_assets':[digest(x) for x in owned],'editable_assets':[digest(x) for x in editable],'source_originals':preservation['originals'],'user_accepted':False,'physical_device_verified':False}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(str(out))
