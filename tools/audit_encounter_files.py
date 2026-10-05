"""Read-only preservation audit against the implementation-start archive manifest."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];baseline=json.loads((ROOT/'evidence/implementation/20261004-start/baseline-manifest.json').read_text());settings=json.loads((ROOT/'tools/project-settings.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
changed=[];missing=[];same=[]
for item in baseline['files']:
    path=ROOT/item['path']
    if not path.exists():missing.append(item['path'])
    elif sha(path)!=item['sha256']:changed.append(item['path'])
    else:same.append(item['path'])
originals={}
for name in ['reference_video','source_archive','teddy_model']:
    path=Path(settings[name]);path=path if path.is_absolute() else ROOT/path
    actual=sha(path);originals[name]={'path':str(path),'sha256':actual,'unchanged':actual==settings[name+'_sha256']}
protected=[p for p in changed+missing if p.startswith('BossShot/') or p.startswith('TeddyBlueprint/Content/')]
r={'passed':not protected and all(x['unchanged'] for x in originals.values()),'baseline_files_checked':len(baseline['files']),'unchanged_count':len(same),'changed':changed,'missing':missing,'protected_content_changes':protected,'originals':originals,'baseline_archive_sha256':sha(Path(baseline['archive']))}
(ROOT/'evidence/implementation/preservation-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if not r['passed']:raise SystemExit(1)
