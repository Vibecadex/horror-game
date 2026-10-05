"""Assemble local review from actual captures/receipts; never fabricate acceptance."""
import argparse,html,json,os
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'])
def url(p):return quote(os.path.relpath(p,OUT).replace('\\','/'),safe='/.-_')
def link(p,label):return '<a href="'+url(p)+'">'+html.escape(label)+'</a>'
def img(p,caption):return '<figure><a href="'+url(p)+'"><img loading="lazy" src="'+url(p)+'" alt="'+html.escape(caption,quote=True)+'"></a><figcaption>'+html.escape(caption)+'</figcaption></figure>'
def receipt(p):
    r=json.loads((p/'receipt.json').read_text());assert r['passed'],p
    return r
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--captures',required=True,type=Path);ap.add_argument('--motion',required=True,type=Path)
    ap.add_argument('--room',required=True,type=Path);ap.add_argument('--runtime',required=True,type=Path);ap.add_argument('--keys',required=True,type=Path)
    ap.add_argument('--independent-review',required=True,type=Path);args=ap.parse_args()
    captures,motion,room,runtime,keys=[getattr(args,n).resolve() for n in ['captures','motion','room','runtime','keys']]
    cr,mr,rr,ar,kr=[receipt(p) for p in [captures,motion,room,runtime,keys]]
    assert mr['all_frames_decoded'];assert args.independent_review.is_file()
    preservation=json.loads((OUT/'final-preservation.json').read_text());assert preservation['passed']
    rear=ROOT/'evidence/implementation/20261005T092532-capture_parity_rear_visibility'
    rear_receipt=receipt(rear);assert len(rear_receipt['captures'])==3
    target=ROOT/'study/visuals/direction-close-best.jpg';concept=ROOT/'study/visuals/parity-expanded-reference.png';candidate=captures/'01-matched-gameplay.png'
    movie=motion/'native-motion.mp4';assert all(p.is_file() for p in [target,concept,candidate,movie])
    counts={n:len(r['checks']) for n,r in [('room',rr),('animation_and_death',ar),('keys',kr)]}
    assert all(all(r['checks'].values()) for r in [rr,ar,kr])
    data={'reference':str(target),'concept':str(concept),'captures':str(captures),'motion':str(movie),'rear_visibility':str(rear),'checks':counts,'independent_review':str(args.independent_review.resolve()),'preservation':str(OUT/'final-preservation.json'),'play':'PLAY.cmd','visual_acceptance':'See independent review; user acceptance is separate.'}
    (OUT/'delivery.json').write_text(json.dumps(data,indent=2))
    css='''*{box-sizing:border-box}body{margin:0;background:#0c1214;color:#d9e6e4;font:16px/1.55 system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:32px}h1{font-size:38px;letter-spacing:-1px;margin:4px 0}h2{margin-top:40px;font-size:24px}p{max-width:1000px;color:#b1c3c3}a{color:#87d8cc}nav{display:flex;gap:20px;flex-wrap:wrap;margin:22px 0}figure{margin:0}img,video{display:block;width:100%;height:auto;background:#050808;border:1px solid #294044}figcaption{font-size:13px;padding:9px 0 18px;color:#93abad}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.compare{position:relative;aspect-ratio:16/9;overflow:hidden;background:black}.compare img{position:absolute;inset:0;width:100%;height:100%;border:0}.compare .over{clip-path:inset(0 50% 0 0)}.labels{display:flex;justify-content:space-between;font-size:13px}input[type=range]{width:100%;accent-color:#86d8cb}table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #294044;padding:10px}small{color:#93abad}.tag{color:#86d8cb;text-transform:uppercase;letter-spacing:2px;font-size:12px}@media(max-width:760px){main{padding:18px}.grid{grid-template-columns:1fr}h1{font-size:29px}}'''
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Teddy Encounter — reference and Unreal review</title><style>'+css+'</style><main>',
      '<div class="tag">Teddy Encounter · Unreal 5.8.3</div><h1>From reference to playable room</h1>',
      '<p>The selected look expanded into an industrial containment chamber: fractured concrete, a stitched cloth creature, a small moving player light, teal depth and dark service bays.</p>',
      '<nav>'+link(ROOT/'PLAY.cmd','PLAY.cmd')+link(ROOT/'ENCOUNTER.md','Controls')+link(args.independent_review.resolve(),'Independent QA')+link(OUT/'final-preservation.json','Preservation receipt')+'</nav>',
      '<h2>Reference and saved Unreal render</h2><p>Both original images are displayed at the same aspect ratio, without colour correction or warping. The Unreal still holds movement, hides HUD and stages the player aim; it uses the saved gameplay camera, lighting and materials. The animation pose differs.</p>',
      '<div class="compare"><img src="'+url(target)+'" alt="User-selected reference"><img id="actual" class="over" src="'+url(candidate)+'" alt="Actual saved Unreal comparison"></div>',
      '<label for="wipe" class="labels"><span>Actual Unreal</span><span>Selected reference</span></label><input id="wipe" type="range" min="0" max="100" value="50" aria-label="Compare actual Unreal and selected reference">',
      '<div class="grid">'+img(candidate,'Actual Unreal — saved gameplay composition')+img(target,'Selected reference — art direction image, not runtime')+'</div>',
      '<h2>Moving gameplay</h2><video controls preload="metadata" poster="'+url(motion/'motion-still.png')+'"><source src="'+url(movie)+'" type="video/mp4"></video>',
      '<p>Native game-window capture at 1280×720. A separate QA copy of the encounter drives movement, dash, aim and firing through saved input routes. AI, health and gameplay are unchanged. The movie is silent; this is automated input evidence, not physical keyboard or mouse testing.</p>',
      '<h2>The full room</h2><div class="grid">']
    for entry in cr['captures'][1:]:parts.append(img(Path(entry['path']),entry['caption']))
    parts+=['</div><h2>Rear-centre visibility repair</h2><p>Independent review found the player blending into the rear haze. A small local fill restores the silhouette. These are staged coverage views with the saved gameplay camera; the reference-matched opening composition stays unchanged.</p><div class="grid">'+img(room/'room-case-03.png','Before — low contrast at the rear centre')+img(rear/'rear-center-1300.png','After — head, shoulders and weapon remain visible through the haze')+'</div>',
      '<p>'+link(rear/'receipt.json','Three-position visibility capture receipt')+' · '+link(OUT/'rear-readability-checkpoint-change.json','Bounded map correction record')+'</p>',
      '<h2>Expanded concept</h2>'+img(concept,'AI-generated expansion board — proposed art direction, not an Unreal capture'),
      '<p>'+link(ROOT/'study/visuals/parity-expansion-prompt.txt','Generation prompt')+' · '+link(ROOT/'study/PARITY_ART_DIRECTION.md','Astra art direction')+' · '+link(ROOT/'study/PARITY_ASSET_MANIFEST.md','Editable assets and provenance')+'</p>',
      '<h2>Verification</h2><table><tr><th>Check</th><th>Result</th><th>Evidence</th></tr>']
    for label,p,r in [('Room, bounds and movement',room,rr),('Skin, clips and saved death routes',runtime,ar),('Saved key mappings and controls',keys,kr)]:
        parts.append('<tr><td>'+label+'</td><td>'+str(len(r['checks']))+'/'+str(len(r['checks']))+' passed</td><td>'+link(p/'receipt.json','Receipt')+'</td></tr>')
    parts+=['<tr><td>Native movie</td><td>All frames decoded</td><td>'+link(motion/'receipt.json','Receipt')+'</td></tr>',
      '<tr><td>Preservation</td><td>'+str(preservation['original_baseline_files'])+' original files and all source anchors unchanged</td><td>'+link(OUT/'final-preservation.json','Receipt')+'</td></tr></table>',
      '<p>Functional results, rendered fidelity and user acceptance are separate. Read the independent review for remaining visible differences. Original download, video, starter, native experiment and earlier variants remain preserved.</p>',
      '</main><script>const wipe=document.getElementById("wipe"), actual=document.getElementById("actual");wipe.addEventListener("input",()=>actual.style.clipPath="inset(0 "+(100-wipe.value)+"% 0 0)");</script></html>']
    (OUT/'review.html').write_text('\n'.join(parts),encoding='utf-8')
    print(json.dumps({'review':str(OUT/'review.html'),'counts':counts,'links_are_local':True}))
if __name__=='__main__':main()
