"""Publish a local, source-linked chamber comparison after validation receipts pass."""
import json,html,hashlib,os
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
OUT=(ROOT/Path(json.loads((ROOT/'evidence/chamber/current-run.json').read_text())['out'])).resolve()
def rel(p):return quote(Path(os.path.relpath(p,OUT)).as_posix(),safe='/.-_')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    inputs=load(OUT/'delivery-inputs.json');paths={k:(ROOT/v).resolve() for k,v in inputs.items()}
    for p in paths.values():assert p.is_relative_to(ROOT) and p.exists(),p
    reports={k:load(p/'receipt.json') for k,p in paths.items() if k in ['capture','chamber_qa','room_qa','motion','gameplay']}
    for k,v in reports.items():assert v['passed'],k
    preservation=load(OUT/'final-preservation.json');assert preservation['passed']
    views=[]
    for direction,name in [('front','01-chamber-front.png'),('reverse','02-chamber-reverse.png')]:
        views.append({'name':direction.title(),'reference':rel(ROOT/'study/visuals'/('chamber-target-'+direction+'.png')),
                      'candidate':rel(paths['capture']/name),'baseline':rel(ROOT/'evidence/implementation/20261005T095951-capture_chamber_views'/name)})
    checks={k:{'passed':len([v for v in reports[k]['checks'].values() if v]),'total':len(reports[k]['checks'])} for k in ['chamber_qa','room_qa']}
    data={'views':views,'checks':checks,'references_are_concepts':True,'architectural_cameras_are_staged':True,'physical_device_verified':False,
          'exact_reference_parity':False,'acceptance':'Awaiting user visual review','preservation':preservation,
          'inputs':inputs,'settings':load(ROOT/'study/chamber-settings.json')}
    (OUT/'delivery.json').write_text(json.dumps(data,indent=2))
    evidence_links=''.join(f'<li><a href="{rel(p / "receipt.json")}">{html.escape(k.replace("_"," ").title())} receipt</a></li>' for k,p in paths.items() if k in reports)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Teddy Encounter — chamber comparison</title><style>
:root{color-scheme:dark;font:16px/1.5 system-ui;background:#0a1114;color:#dce8e7}body{max-width:1540px;margin:0 auto;padding:32px}h1{font-size:clamp(28px,4vw,48px);line-height:1.1;margin:8px 0 18px}h2{font-size:22px;margin-top:36px}p{max-width:1000px;color:#adc1c2}a{color:#8edad3}button{font:inherit;color:inherit;border:1px solid #426066;background:#17272c;border-radius:7px;padding:9px 18px;cursor:pointer}button[aria-pressed=true]{background:#a1d6ce;color:#0c2222}.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:24px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#050708;border:1px solid #263c40;border-radius:8px;overflow:hidden}figure img{width:100%;aspect-ratio:3/2;object-fit:contain;display:block}figcaption{padding:12px 16px;color:#bcd0cf}video{width:min(100%,1280px);background:black;border-radius:8px}.evidence{display:flex;gap:20px;flex-wrap:wrap}.badge{display:inline-block;border:1px solid #355b60;border-radius:30px;padding:5px 12px;color:#a7d6d0}.note{border-left:3px solid #d4ac67;padding:0 18px}details{margin:20px 0;padding:16px;background:#122025;border-radius:8px}ul{padding-left:22px}@media(max-width:850px){body{padding:20px}.pair{grid-template-columns:1fr}}
</style><body><span class="badge">UNREAL 5.8.3 · SAVED PLAYABLE CHAMBER</span><h1>The chamber, from both directions</h1>
<p>Wide B-3 bulkhead, a complete reverse wall with two service bays, weathered machinery, lower drains, broad broken concrete plates and controlled teal lighting. The environment remains part of the playable Teddy Encounter.</p>
<div class="toolbar"><button data-index="0" aria-pressed="true">Front chamber</button><button data-index="1" aria-pressed="false">Reverse chamber</button><label><input id="baseline" type="checkbox"> Show pre-pass room</label></div>
<div class="pair"><figure><a id="refLink"><img id="ref" alt="Supplied chamber concept reference"></a><figcaption id="refCap"></figcaption></figure><figure><a id="gameLink"><img id="game" alt="Actual Unreal chamber capture"></a><figcaption id="gameCap"></figcaption></figure></div>
<p>These are direct native 1920×1280 Unreal captures at comparison cameras. Images are fitted proportionally, with no warping or painted correction. The old baseline uses the earlier camera; its checkbox documents missing architecture, not a pixel-aligned test. Normal gameplay retains its original adaptive camera.</p>
<h2>Moving gameplay</h2><video controls preload="metadata" poster="__POSTER__"><source src="__VIDEO__" type="video/mp4"></video>
<p>Native game-window capture from an isolated QA copy using the saved encounter and simulated input. Normal AI and health remain enabled. This take ends in player defeat and shows the F5 restart prompt; it does not demonstrate a boss defeat. The movie is silent and does not establish physical-device or audio matching.</p>
<div class="evidence"><span class="badge">__CHAMBER__ chamber checks</span><span class="badge">__ROOM__ room checks</span><span class="badge">555 original files preserved</span></div>
<h2>Visual assessment</h2><p class="note">The defining room structures are now present and independently inspected. Exact reference parity is not established: the floor still has more localized fracture patches and fine grain, wall panels are more regular, overhead haze is weaker and service recesses are darker. Functional checks are separate from visual acceptance.</p>
<p><a href="__QA__">Independent visual review</a> · <a href="../../../PLAY.cmd">Play saved encounter</a> · <a href="../../../EDIT.cmd">Open editable level</a> · <a href="../../../ENCOUNTER.md">Controls and handoff</a></p>
<details><summary>Evidence and editable sources</summary><ul>__RECEIPTS__<li><a href="final-preservation.json">Final preservation receipt</a></li><li><a href="delivery.json">Delivery settings and evidence paths</a></li><li><a href="../../../study/CHAMBER_PARITY_BRIEF.md">Astra art direction</a></li><li><a href="../../../Assets/Adapted/ChamberParity/manifest.json">Editable chamber kit</a></li><li><a href="../../../Assets/Adapted/ChamberParity/FloorNormalsV2/manifest.json">Editable corrected connected floor kit</a></li><li><a href="../../../Assets/Adapted/ChamberParity/SlabsNormalsV2/manifest.json">Editable corrected sparse fragments</a></li><li><a href="../../../Assets/Adapted/ChamberParity/CrustNormalsV2/manifest.json">Editable broken concrete plates</a></li><li><a href="../../../Assets/Adapted/ChamberParity/WallSurface/T_ChamberWall_Albedo.png">Generated wall albedo</a> · <a href="../../../Assets/Adapted/ChamberParity/WallSurface/prompt.txt">exact prompt</a> · <a href="../../../Assets/Adapted/ChamberParity/WallSurface/manifest.json">built-in imagegen provenance</a></li></ul></details>
<script>const views=__VIEWS__;let selected=0;function render(){let v=views[selected],old=document.querySelector('#baseline').checked;document.querySelector('#ref').src=v.reference;document.querySelector('#refLink').href=v.reference;document.querySelector('#game').src=old?v.baseline:v.candidate;document.querySelector('#gameLink').href=old?v.baseline:v.candidate;document.querySelector('#refCap').textContent=v.name+' — supplied concept';document.querySelector('#gameCap').textContent=v.name+(old?' — original pre-pass room':' — saved Unreal chamber');document.querySelectorAll('[data-index]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.index)===selected));}document.querySelectorAll('[data-index]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.index);render()});document.querySelector('#baseline').onchange=render;render();</script></body></html>'''
    replacements={'__POSTER__':rel(paths['motion']/'motion-still.png'),'__VIDEO__':rel(paths['motion']/'native-motion.mp4'),'__QA__':rel(paths['visual_review']),
        '__CHAMBER__':f"{checks['chamber_qa']['passed']}/{checks['chamber_qa']['total']}",'__ROOM__':f"{checks['room_qa']['passed']}/{checks['room_qa']['total']}",'__RECEIPTS__':evidence_links,'__VIEWS__':json.dumps(views)}
    for a,b in replacements.items():page=page.replace(a,b)
    (OUT/'review.html').write_text(page,encoding='utf-8');print(json.dumps({'review':str(OUT/'review.html'),'checks':checks}))
if __name__=='__main__':main()
