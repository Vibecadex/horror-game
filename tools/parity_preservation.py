"""Hash-only preservation and verification manifests; no Unreal asset parsing."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'];assert OUT.is_dir(),f'Run directory missing: {OUT}'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def active():
    paths=list((ROOT/'TeddyBlueprint/Content/TeddyEncounter').rglob('*.uasset'))
    paths+=[ROOT/'TeddyBlueprint/Content/Maps/TeddyEncounter.umap']
    external=ROOT/'TeddyBlueprint/Content/__ExternalActors__/Maps/TeddyEncounter'
    if external.exists():paths+=list(external.rglob('*.uasset'))
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(set(paths))}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['snapshot','verify'])
    ap.add_argument('--baseline-name',default='validation-baseline.json',help='Distinct checkpoint after an intentional authoring correction; earlier snapshots are preserved.')
    args=ap.parse_args()
    assert Path(args.baseline_name).name==args.baseline_name and args.baseline_name.endswith('.json')
    path=OUT/args.baseline_name
    if args.mode=='snapshot':
        assert not path.exists(),'Preserve existing validation snapshot; do not overwrite it'
        record={'created_utc':datetime.now(timezone.utc).isoformat(),'method':'Byte hashes only, no binary asset inspection','assets':active()}
        path.write_text(json.dumps(record,indent=2));print(json.dumps({'snapshot':str(path),'assets':len(record['assets'])}));return
    baseline=json.loads(path.read_text());now=active();changed=[k for k,v in baseline['assets'].items() if now.get(k)!=v];added=sorted(set(now)-set(baseline['assets']))
    original=json.loads((ROOT/'evidence/implementation/20261004-start/baseline-manifest.json').read_text())
    failures=[]
    for entry in original['files']:
        p=(ROOT/entry['path']).resolve();assert p.is_relative_to(ROOT)
        if not p.is_file() or digest(p)!=entry['sha256']:failures.append(entry['path'])
    settings=json.loads((ROOT/'tools/project-settings.json').read_text());sources=[]
    for name in ['reference_video','source_archive','teddy_model']:
        p=Path(settings[name]);p=p if p.is_absolute() else ROOT/p
        actual=digest(p);expected=settings[name+'_sha256'];sources.append({'name':name,'path':str(p),'sha256':actual,'unchanged':actual==expected})
    reference=ROOT/'study/visuals/direction-close-best.jpg'
    sources.append({'name':'selected_reference','path':str(reference),'sha256':digest(reference),'unchanged':digest(reference)=='93fbe5a65dd56b5015bdd951fbefa5d1a3d60951688a00d28b33343a721107a8'})
    r={'passed':not changed and not added and not failures and all(s['unchanged'] for s in sources),'validation_baseline':str(path),'checked_utc':datetime.now(timezone.utc).isoformat(),'active_assets':len(now),'active_changed_during_validation':changed,'active_added_during_validation':added,'original_baseline_files':len(original['files']),'original_baseline_failures':failures,'sources':sources,'method':'Byte hashes only; separate SetupValidation capture-map assets are outside the playable encounter snapshot.'}
    (OUT/'final-preservation.json').write_text(json.dumps(r,indent=2));(OUT/'final-active-assets.json').write_text(json.dumps(now,indent=2));print(json.dumps(r,indent=2));assert r['passed']
if __name__=='__main__':main()
