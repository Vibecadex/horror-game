"""Archive the repaired encounter before the authorized room extension."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/full-room' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT.mkdir(parents=True, exist_ok=False)
files = set(ROOT.glob('*.md')) | set(ROOT.glob('*.cmd'))
for folder in ['tools', 'Assets/Adapted', 'TeddyBlueprint/Content/TeddyEncounter', 'TeddyBlueprint/Content/Maps']:
    files.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

items = [{'path': p.relative_to(ROOT).as_posix(), 'size': p.stat().st_size, 'sha256': sha(p)} for p in sorted(files)]
archive = OUT/'before-room.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for item in items:
        z.write(ROOT/item['path'], item['path'])
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for item in items:
        assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256']
report = {'passed': True, 'created_utc': datetime.now(timezone.utc).isoformat(), 'files': items,
          'archive': str(archive), 'archive_sha256': sha(archive),
          'purpose': 'Byte-preserving rollback snapshot; no binary assets interpreted.'}
(OUT/'baseline.json').write_text(json.dumps(report, indent=2))
(ROOT/'evidence/full-room/current-run.json').write_text(json.dumps({'out': OUT.relative_to(ROOT).as_posix()}, indent=2))
print(json.dumps({'out': str(OUT), 'files': len(items), 'archive_bytes': archive.stat().st_size, 'passed': True}))
