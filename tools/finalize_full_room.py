"""Assemble a local review from fresh receipts and byte-preservation checks."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(json.loads((ROOT/'evidence/full-room/current-run.json').read_text())['out'])
p=argparse.ArgumentParser()
for name in ['gallery','qa','keys','native']:p.add_argument('--'+name,required=True)
args=p.parse_args()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return os.path.relpath(path,OUT).replace('\\','/')
def link(path,label):return '<a href="'+escape(rel(path),quote=True)+'">'+escape(label)+'</a>'
def check_run(path):
    r=read(path/'receipt.json');assert r['passed'],path
    if (path/'host-result.json').exists():assert read(path/'host-result.json')['passed'],path
    return r

folders={key:(ROOT/getattr(args,key)).resolve() for key in ['gallery','qa','keys','native']}
receipts={key:check_run(path) for key,path in folders.items()}
assert len(receipts['gallery']['captures'])==6
assert len(receipts['qa']['cases'])==12
assert len(receipts['qa']['images'])==6
assert receipts['native']['all_frames_decoded']
assert all(receipts['qa']['checks'].values())
assert all(receipts['keys']['checks'].values())

# The user confirmed a separate Grok surface pass and requested a combined
# verification after it finished. Bind every new run to that stable handoff.
snapshot=read(OUT/'combined-validation-start.json')
snapshot_changed=[item['path'] for item in snapshot['files']
                  if not (ROOT/item['path']).is_file() or sha(ROOT/item['path'])!=item['sha256']]
assert not snapshot_changed,{'changed_during_combined_verification':snapshot_changed}
current_assets={f.relative_to(ROOT).as_posix() for f in (ROOT/'TeddyBlueprint/Content/TeddyEncounter').rglob('*.uasset')}
snapshot_assets={item['path'] for item in snapshot['files'] if item['path'].startswith('TeddyBlueprint/Content/TeddyEncounter/')}
assert current_assets==snapshot_assets,{'added':sorted(current_assets-snapshot_assets),'removed':sorted(snapshot_assets-current_assets)}
started=datetime.fromisoformat(snapshot['created_utc'])
for key,folder in folders.items():
    stamp=re.search(r'(\d{8}T\d{6})',folder.name).group(1)
    assert datetime.strptime(stamp,'%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc)>=started.replace(microsecond=0),key
    marker=folder/('invocation.json' if (folder/'invocation.json').exists() else 'authoring.json')
    assert marker.stat().st_mtime>=started.timestamp(),key
surface=read(ROOT/snapshot['surface_receipt'])
assert surface['passed']
combined={'passed':True,'snapshot_created_utc':snapshot['created_utc'],'files_unchanged':len(snapshot['files']),
          'active_asset_set_unchanged':True,'fresh_runs':{k:str(v.relative_to(ROOT)) for k,v in folders.items()},
          'handoff':snapshot['handoff'],'surface_receipt_sha256':sha(ROOT/snapshot['surface_receipt'])}
(OUT/'combined-validation.json').write_text(json.dumps(combined,indent=2))

baseline=read(OUT/'baseline.json')
changed=[];missing=[]
for item in baseline['files']:
    f=ROOT/item['path']
    if not f.is_file():missing.append(item['path'])
    elif sha(f)!=item['sha256']:changed.append(item['path'])
assert not missing,missing
game_changes=[f for f in changed if f.startswith('TeddyBlueprint/Content/')]
surface_changes=['TeddyBlueprint/Content/TeddyEncounter/'+name for name in [
    'Blueprints/BP_Stitchling.uasset','Blueprints/BP_TeddyBoss.uasset',
    'Materials/M_QA_Concrete.uasset','Materials/M_QA_TeddyCloth.uasset','Materials/M_TeddyCloth.uasset']]
assert set(game_changes)==set(['TeddyBlueprint/Content/Maps/TeddyEncounter.umap',*surface_changes]),game_changes
assert not [f for f in changed if f.startswith('Assets/Adapted/')],changed
original_baseline=read(ROOT/'evidence/implementation/20261004-start/baseline-manifest.json')
original_changed=[item['path'] for item in original_baseline['files'] if not (ROOT/item['path']).is_file() or sha(ROOT/item['path'])!=item['sha256']]
assert not original_changed,original_changed
settings=read(ROOT/'tools/project-settings.json');originals={}
for name in ['reference_video','source_archive','teddy_model']:
    path=Path(settings[name]);path=path if path.is_absolute() else ROOT/path
    actual=sha(path);assert actual==settings[name+'_sha256'],name
    originals[name]={'path':str(path),'sha256':actual,'unchanged':True}
preservation={'passed':True,'pre_room_files':len(baseline['files']),'changed_pre_room_files':changed,
              'changed_existing_game_assets':game_changes,'original_baseline_files_unchanged':len(original_baseline['files']),
              'authorized_grok_surface_changes':surface_changes,'combined_state_validation':combined,
              'originals':originals,'archive_sha256':sha(OUT/'before-room.zip')}
(OUT/'preservation.json').write_text(json.dumps(preservation,indent=2))

gallery=folders['gallery'];native=folders['native'];qa=folders['qa']
hero=gallery/'03-architecture-overview.png'
initial=gallery/'01-gameplay-initial.png'
reference=ROOT/'evidence/independent-qa/20261005T034938Z/derived/original-gameplay-10.png'
before=ROOT/'evidence/implementation/20261005T044114-verify_encounter_repair/01-initial-composition.png'
# Truthful evidence layout only: preserve aspect ratio and image colours.
board=Image.new('RGB',(1740,400),(12,18,23));draw=ImageDraw.Draw(board)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',21)
for i,(path,title) in enumerate([(reference,'Original video'),(before,'Before: repaired encounter'),(initial,'After: room gameplay')]):
    im=Image.open(path).convert('RGB');im.thumbnail((560,330))
    x=10+i*580;draw.text((x+8,10),title,font=font,fill=(220,235,238))
    board.paste(im,(x+(560-im.width)//2,50+(330-im.height)//2))
board.save(OUT/'reference-comparison.png')

qa_count=len(receipts['qa']['checks']);keys_count=len(receipts['keys']['checks'])
authorings=[read(f) for f in OUT.glob('authoring*.json')]
last=next(r for r in reversed(authorings) if r.get('decoration_collision_profile_saved'))
kit=read(ROOT/'Assets/Adapted/Room/manifest.json')
caption_names=['Combat view','Maximum separation','Room overview','Rear bulkhead','Pipe services','Electrical bay']
buttons=''.join('<button type="button" data-index="'+str(i)+'">'+escape(name)+'</button>' for i,name in enumerate(caption_names))
slides=[{'src':rel(Path(cap['path'])),'caption':cap['caption']} for cap in receipts['gallery']['captures']]
links=' · '.join([link(qa/'receipt.json','Independent room checks'),link(folders['keys']/'receipt.json','Controls'),
                  link(OUT/'INDEPENDENT_REVIEW.md','Independent visual review'),link(OUT/'ROOM_REPORT.md','Build report'),
                  link(OUT/'preservation.json','Preservation'),link(OUT/'combined-validation.json','Combined version'),link(OUT/'manifest.json','Manifest')])
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Teddy Encounter — industrial chamber</title><style>
:root{color-scheme:dark;font:16px/1.5 system-ui,sans-serif;background:#091014;color:#d8e6e8}body{max-width:1280px;margin:auto;padding:24px}h1{font-size:32px;line-height:1.15;margin:8px 0}p{max-width:1000px}a{color:#83d8e2}button{background:#162a32;color:#d8e6e8;border:1px solid #3c5964;padding:9px 14px;border-radius:5px;cursor:pointer}button[aria-pressed=true]{background:#275a65;border-color:#91d9e4}nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}figure{margin:0}figure img{display:block;width:100%;height:auto;background:black}figcaption{font-size:14px;color:#afc2c8;padding:10px 0 18px}video{width:100%;background:black}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid img{width:100%}.pill{display:inline-block;border:1px solid #3e6364;padding:4px 10px;border-radius:20px;color:#a5d6c9;font-size:14px}section{margin-top:32px}summary{cursor:pointer}li{margin:8px 0}@media(max-width:700px){.grid{grid-template-columns:1fr}body{padding:14px}}
</style><h1>The full industrial chamber</h1><p>Heavy service doors, concrete supports, ventilation, continuous pipework, raised drainage channels and utility bays surround the playable encounter. The near wall and ceiling are cut away for the elevated camera.</p>
<span class="pill">'''+str(qa_count)+''' room checks + '''+str(keys_count)+''' control checks passed</span>
<nav aria-label="Room views">'''+buttons+'''</nav><figure><img id="scene" src="'''+rel(hero)+'''" alt="Full room architectural overview"><figcaption id="caption">'''+escape(slides[2]['caption'])+'''</figcaption></figure>
<p>These are actual Unreal renders at the saved lighting and exposure. Architectural views temporarily reposition the camera for review; gameplay views use the existing combat camera. The stills hold the characters and hide the HUD.</p>
<p>This review includes the completed Grok floor, cloth and decal pass. All fresh checks and captures ran after that handoff; the combined assets remained unchanged throughout verification.</p>
<section><h2>Play and motion</h2><p>Launch '''+link(ROOT/'PLAY.cmd','PLAY.cmd')+''' on this Windows machine, or open '''+link(ROOT/'EDIT.cmd','EDIT.cmd')+'''. WASD moves, mouse aims, left click fires, Space dodges, Escape pauses and F5 restarts.</p>
<video controls preload="metadata" poster="'''+rel(native/'motion-still.png')+'''" src="'''+rel(native/'native-motion.mp4')+'''"></video>
<p>The movie records an ordinary game window at approximately 30 fps. An isolated copy of the saved map drives normal key events and aiming, with normal AI and health. The movie is silent; this is not physical-device testing or a sustained performance benchmark.</p></section>
<section><h2>Reference comparison</h2><img style="width:100%" src="reference-comparison.png" alt="Original video, previous encounter and new room gameplay"><p>The video establishes the elevated view, pale grounded threat, cool light and dark perimeter. The complete industrial layout is a new extension because the reference does not show the whole room.</p></section>
<section><h2>What was checked</h2><p>'''+str(qa_count)+''' independent room checks cover saved boundaries/spawns, '''+str(len(receipts['qa']['capsule_probes']))+''' capsule probes, four wall walks and dashes, twelve camera cases and seventy-two body-visibility rays. Three known-hit controls verify the trace queries. All six edge screenshots were decoded and independently reviewed. '''+str(keys_count)+''' saved-key checks cover movement, firing, dodge, pause and restart.</p>
<p>At maximum opposite-corner separation, the player remains small and dim, though its silhouette is distinguishable. The new floor crack, stain and debris are conspicuous and flatter than the reference wear. The teddy anatomy/motion and exact reference fidelity remain broader limitations. Physical-device play, audio matching, packaged distribution and sustained performance are unverified.</p><p>'''+links+'''</p></section>
<details><summary>Editable art and ownership</summary><p>'''+link(ROOT/'Assets/Adapted/Room/IndustrialRoom_Kit.blend','Blender room kit')+''' · '''+link(ROOT/'Assets/Adapted/Room/manifest.json','10 original meshes and provenance')+''' · '''+link(ROOT/'ROOM_ART_DIRECTION.md','Astra art direction')+''' · '''+link(ROOT/'Assets/Adapted/Arena/ai-provenance.json','Grok surface provenance')+'''</p><p>The room team used one Unreal integrator. The separate user-owned Grok surface pass finished before this combined verification; its work was preserved. Original video, source archive, teddy download, starter and historical BossShot project were preserved.</p></details>
<script>
const slides='''+json.dumps(slides)+''';
function show(index){const s=slides[index];document.getElementById('scene').src=s.src;document.getElementById('caption').textContent=s.caption;document.querySelectorAll('button[data-index]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.index)===index?'true':'false'));}
document.querySelectorAll('button[data-index]').forEach(b=>b.addEventListener('click',()=>show(Number(b.dataset.index))));show(2);
</script></html>'''
(OUT/'review.html').write_text(html,encoding='utf-8')

report=f'''# Full industrial room

Built on 5 October 2026 in `/Game/Maps/TeddyEncounter`, Unreal 5.8.3. Launch `PLAY.cmd`; edit with `EDIT.cmd`.

## Delivered

Three full-height enclosing walls, a low foreground cutaway, sealed rear bulkhead, structural supports, two distinct service sides, fans, cabinets, tanks, continuous pipe runs with supports, drainage grates, restrained warning fixtures and damp floor wear. Perimeter foundations support the equipment. The central fighting area remains clear. There is no overhead slab that could conceal the elevated view; doors/equipment are static scenery.

{last['saved_room_actor_count']} owned room actors use `/Game/TeddyEncounter/Room` and `FullRoomOwned` tags. Ten original modular FBXs contain {kit['total_triangles']:,} triangles in the source kit; repeated placements add instances. The editable Blender source, deterministic generator, material slots, exact dimensions and FBX round-trip checks are in `Assets/Adapted/Room`. The room kit was made locally with installed tools.

The user's separate Grok session completed nine generated floor/plush/decal textures, three existing material rebuilds, four decal materials/actors and material overrides on the two creature Blueprints. That work is preserved, with provenance in `Assets/Adapted/Arena/ai-provenance.json`. The materials use Default Lit with normal/roughness detail: the script's Cloth attempt fell back after a Python enum conversion error. This does not establish that Unreal lacks Cloth shading. This review does not credit those surfaces to the room team or claim a new mesh/rig.

## Fresh verification

All runs below began after the completed Grok handoff. All {len(snapshot['files'])} combined asset/source/config snapshot files and the active encounter asset set stayed unchanged during testing. [Combined validation](combined-validation.json) binds these receipts to [the snapshot](combined-validation-start.json). Earlier passing room checks and interim default-material plates remain historical evidence only.

- Room suite: **{qa_count}/{qa_count}** checks; {len(receipts['qa']['capsule_probes'])} capsule probes, three trace positive controls, four mapped-key wall walks/dashes, twelve framing cases and 72 visibility traces. [Receipt]({rel(qa/'receipt.json')}). Six held edge screenshots are in that folder.
- Saved input suite: **{keys_count}/{keys_count}** checks. [Receipt]({rel(folders['keys']/'receipt.json')}). These route simulated keys through saved mappings; they are not physical keyboard/controller verification.
- Six actual saved-lighting gallery images fully decoded. [Gallery receipt]({rel(gallery/'receipt.json')}). NPCs held/HUD hidden; architectural views are explicitly staged camera positions.
- Ordinary-game motion: [video]({rel(native/'native-motion.mp4')}) and [receipt]({rel(native/'receipt.json')}). Isolated map copy, normal AI/health, input driver, owned client-window capture, clean game exit and all frames decoded. Approximately 30 fps capture is not a performance benchmark. Movie is silent; source audio matching is not claimed.
- [Independent visual review](INDEPENDENT_REVIEW.md) records findings, fixes, inspected views and residual limits.

## Fixes found during review

Corrected Unreal's imported Y-axis direction; joined pipe spans; moved a fan out of a support; grounded door/tank/cabinet bases; softened coarse wall texture and glossy stains; reduced bright rear spill and added local edge fill. Replaced transient collision toggles with saved NoCollision profiles on decoration, with saved readback and a fresh runtime check.

The first QA harness attempts exposed UE 5.8 Python API differences, preserved in their failed receipts. Traces now use the installed documented HitResult-or-None contract plus known-hit positive controls. The right-wall dash fixture originally overlapped a stitchling; its corrected parallel lane is recorded, not counted as a game repair.

## Scope and limits

This is a complete authored chamber around the existing single encounter, not a literal reconstruction of unseen reference architecture. At the widest opposite-corner framing, the player remains small and dim. Grok's crack, rounded stain and pale debris decals read more graphic and conspicuous than the source's subtle worn floor. Simpler teddy anatomy/procedural motion, exact atmospheric fidelity, audio matching, physical-device play, packaged distribution and sustained performance remain outside verified claims. Rendered review is separate from user acceptance.

Six existing game assets changed relative to the pre-room snapshot: the encounter map and five assets from Grok's surface pass (two creature Blueprint material overrides and three materials). Other pre-room game assets, including the player, input and camera assets, and previous adapted source files retain their hashes. All {len(original_baseline['files'])} original baseline files, original video, source ZIP and downloaded teddy are unchanged. [Preservation receipt](preservation.json). `before-room.zip` is a pre-room historical archive, not a safe blanket rollback of the later Grok work.

The requested team comprised Astra art direction/gallery tooling, an environment mesh artist, an independent QA reviewer, and the root integrator as the room team's Unreal writer. When the separate user-owned Grok writer was identified, shared edits stopped until its final handoff. No second Codex session, installer, global configuration or security change was started by the room team.
'''
(OUT/'ROOM_REPORT.md').write_text(report,encoding='utf-8')

files={ROOT/item['path'] for item in snapshot['files']}
for name in ['build_full_room.py','make_industrial_room.py','verify_full_room.py','capture_room_gallery.py','capture_qa_native_motion.py','author_qa_native_motion.py','finalize_full_room.py']:
    files.add(ROOT/'tools'/name)
manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'map':'/Game/Maps/TeddyEncounter',
          'evidence':{k:str(v.relative_to(ROOT)) for k,v in folders.items()},'preservation':preservation,
          'files':[{'path':f.relative_to(ROOT).as_posix(),'size':f.stat().st_size,'sha256':sha(f)} for f in sorted(files) if f.is_file()]}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))

class Links(HTMLParser):
    def __init__(self):super().__init__();self.paths=[]
    def handle_starttag(self,tag,attrs):
        self.paths.extend(v for k,v in attrs if k in ['src','href','poster'] and v and not v.startswith(('http:','https:','#','data:')))
parser=Links();parser.feed(html)
for path in parser.paths:assert (OUT/path).resolve().is_file(),path
for cap in receipts['gallery']['captures']:
    with Image.open(cap['path']) as im:im.load();assert im.size==(1280,720)
for source in [ROOT/'tools'/name for name in ['build_full_room.py','make_industrial_room.py','verify_full_room.py','capture_room_gallery.py','finalize_full_room.py']]:ast.parse(source.read_text(encoding='utf-8-sig'))
script=re.search(r'<script>([\s\S]*?)</script>',html).group(1)
(OUT/'review-script.js').write_text(script,encoding='utf-8')
node=shutil.which('node')
assert node,'Installed Node is required to validate the local review script'
subprocess.run([node,'--check',str(OUT/'review-script.js')],check=True,capture_output=True,text=True)
doc_links=[]
for name in ['ENCOUNTER.md','WORK_STATUS.md']:
    source=ROOT/name
    for target in re.findall(r'\]\(([^)]+)\)',source.read_text(encoding='utf-8')):
        if not target.startswith(('http:','https:','#')):
            assert (source.parent/target.split('#')[0]).is_file(),(name,target)
            doc_links.append([name,target])
validation={'passed':True,'local_html_links_checked':len(parser.paths),'gallery_images_decoded':6,
            'python_syntax_checked':True,'javascript_syntax_checked':True,'documentation_links_checked':len(doc_links),
            'game_changes':game_changes,'checks':qa_count+keys_count}
(OUT/'delivery-validation.json').write_text(json.dumps(validation,indent=2))
print(json.dumps({'out':str(OUT),'validation':validation,'checks':qa_count+keys_count},indent=2))
