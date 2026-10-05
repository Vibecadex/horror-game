"""Preserve the completed combined room before the authorized parity art pass."""
from datetime import datetime, timezone
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/parity'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT.mkdir(parents=True,exist_ok=False)
files=set(ROOT.glob('*.md'))|set(ROOT.glob('*.cmd'))
for folder in ['tools','TeddyBlueprint/Config','TeddyBlueprint/Content/TeddyEncounter','TeddyBlueprint/Content/Maps','Assets/Adapted/Teddy','Assets/Adapted/Arena','Assets/Adapted/Room']:
    files.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'parity' not in p.name.lower())
files.add(ROOT/'study/visuals/direction-close-best.jpg')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
items=[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]
archive=OUT/'before-parity.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for item in items:z.write(ROOT/item['path'],item['path'])
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for item in items:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
report={'passed':True,'created_utc':datetime.now(timezone.utc).isoformat(),'files':items,'archive_sha256':sha(archive),'purpose':'Preserve all combined Grok/full-room assets before new owned Parity assets and deliberate map/Blueprint updates. No binary content interpreted.'}
(OUT/'baseline.json').write_text(json.dumps(report,indent=2))
(ROOT/'evidence/parity/current-run.json').write_text(json.dumps({'out':str(OUT)},indent=2))
print(json.dumps({'out':str(OUT),'files':len(items),'archive_bytes':archive.stat().st_size,'passed':True}))
