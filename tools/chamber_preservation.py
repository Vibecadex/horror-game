"""Byte-only validation of chamber delivery, original assets and reference copies."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from parity_preservation import active,digest,ROOT
OUT=(ROOT/Path(json.loads((ROOT/'evidence/chamber/current-run.json').read_text())['out'])).resolve()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['snapshot','verify']);ap.add_argument('--name',default='final-validation-baseline.json');args=ap.parse_args()
    assert Path(args.name).name==args.name and args.name.endswith('.json')
    checkpoint=OUT/args.name
    if args.mode=='snapshot':
        assert not checkpoint.exists();record={'utc':datetime.now(timezone.utc).isoformat(),'method':'Byte hashes only','assets':active()}
        checkpoint.write_text(json.dumps(record,indent=2));print(json.dumps({'snapshot':str(checkpoint),'assets':len(record['assets'])}));return
    before=json.loads((OUT/'baseline.json').read_text());now=active();baseline=json.loads(checkpoint.read_text())['assets']
    r={'passed':False,'utc':datetime.now(timezone.utc).isoformat(),'method':'Byte hashes only, no binary asset inspection','validation_snapshot':str(checkpoint),'active_assets':len(now),
       'validation_drift':[p for p in sorted(set(baseline)|set(now)) if now.get(p)!=baseline.get(p)],
       'preexisting_changed':[e['path'] for e in before['files'] if e['path'].endswith(('.uasset','.umap')) and now.get(e['path'])!=e['sha256']],
       'new_assets':sorted(set(now)-{e['path'] for e in before['files']}),'original_failures':[],'sources':[]}
    original=json.loads((ROOT/'evidence/implementation/20261004-start/baseline-manifest.json').read_text());r['original_files']=len(original['files'])
    for row in original['files']:
        p=(ROOT/row['path']).resolve();assert p.is_relative_to(ROOT)
        if not p.is_file() or digest(p)!=row['sha256']:r['original_failures'].append(row['path'])
    settings=json.loads((ROOT/'tools/project-settings.json').read_text())
    for name in ['reference_video','source_archive','teddy_model']:
        p=Path(settings[name]);p=p if p.is_absolute() else ROOT/p;actual=digest(p)
        r['sources'].append({'name':name,'path':str(p),'sha256':actual,'unchanged':actual==settings[name+'_sha256']})
    for row in before['references']:
        r['sources'].append({'name':Path(row['copy']).name,'sha256':digest(Path(row['copy'])),'unchanged':digest(Path(row['copy']))==row['sha256'] and digest(Path(row['source']))==row['sha256']})
    close=ROOT/'study/visuals/direction-close-best.jpg';r['sources'].append({'name':close.name,'sha256':digest(close),'unchanged':digest(close)=='93fbe5a65dd56b5015bdd951fbefa5d1a3d60951688a00d28b33343a721107a8'})
    r['config_and_launcher_unchanged']=all(digest(ROOT/e['path'])==e['sha256'] for e in before['files'] if e['path'].endswith('.ini') or e['path']=='tools/astra_setup.py')
    r['passed']=not r['validation_drift'] and not r['original_failures'] and r['preexisting_changed']==['TeddyBlueprint/Content/Maps/TeddyEncounter.umap'] and r['config_and_launcher_unchanged'] and all(s['unchanged'] for s in r['sources'])
    (OUT/'final-preservation.json').write_text(json.dumps(r,indent=2));(OUT/'final-active-assets.json').write_text(json.dumps(now,indent=2));print(json.dumps(r,indent=2));assert r['passed']
if __name__=='__main__':main()
