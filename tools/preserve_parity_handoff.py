"""Byte-for-byte preservation of the completed external surface handoff."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,zipfile
import astra_setup as setup
ROOT=setup.ROOT
setup.require_editor_closed()
OUT=Path(json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'])/'external-handoff'
OUT.mkdir(exist_ok=False)
files=set()
for directory in ['TeddyBlueprint/Content/TeddyEncounter','TeddyBlueprint/Content/Maps','Assets/Adapted/Parity/Surfaces']:
    files.update(p for p in (ROOT/directory).rglob('*') if p.is_file())
files.update(ROOT/p for p in ['WORK_STATUS.md','study/LIVE_BRIEF.md','study/parity-settings.json','study/assets/comfy-provenance.json','tools/apply_comfy_surfaces.py','evidence/implementation/comfy-surfaces.json'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]
with zipfile.ZipFile(OUT/'before-combined.zip','x',zipfile.ZIP_DEFLATED) as z:
    for entry in entries:z.write(ROOT/entry['path'],entry['path'])
with zipfile.ZipFile(OUT/'before-combined.zip') as z:
    assert z.testzip() is None
    for entry in entries:
        assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
        assert sha(ROOT/entry['path'])==entry['sha256'],'Concurrent file write: '+entry['path']
setup.require_editor_closed()
(OUT/'manifest.json').write_text(json.dumps({'passed':True,'created_utc':datetime.now(timezone.utc).isoformat(),'files':entries,'source_handoff':'study/LIVE_BRIEF.md','external_final_capture':'20261005T073350-capture_parity_look','external_recording_passed':False,'binary_contents_interpreted':False},indent=2))
print(json.dumps({'passed':True,'files':len(entries),'out':str(OUT)}))
