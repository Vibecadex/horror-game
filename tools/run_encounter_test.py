"""Run one bounded full-editor Python test, never another Codex session."""
import sys, os, json
from pathlib import Path
from datetime import datetime, timezone
import astra_setup as s
s.require_editor_closed()
script=Path(sys.argv[1]).resolve()
assert script.is_relative_to(s.ROOT) and script.is_file()
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
out=s.ROOT/'evidence/implementation'/f'{stamp}-{script.stem}'
out.mkdir(parents=True,exist_ok=False)
env=dict(s.tool_environment(),TEDDY_TEST_DIR=str(out))
engine=Path(s.SETTINGS['engine_root'])/'Engine/Binaries/Win64/UnrealEditor.exe'
args=[str(engine),str(s.ROOT/s.SETTINGS['project']),f'-ExecutePythonScript={script}','-RenderOffscreen','-ResX=1280','-ResY=720','-unattended','-nosplash','-nop4','-NoSound',f'-abslog={out / "engine.log"}',*s.unreal_local_arguments()]
if os.environ.get('TEDDY_TEST_AUDIO')=='1':
    args.remove('-NoSound')
    # An offscreen editor never has desktop focus. Capture its otherwise-muted audio
    # through a process-only ini override; project and global settings are untouched.
    args.append('-ini:Engine:[Audio]:UnfocusedVolumeMultiplier=1.0')
print(str(out),flush=True)
s.write_json(out/'invocation.json',{'arguments':args,'script_sha256':s.sha256(script)})
try:
    host=s.run_logged(args,out/'process.log',timeout=int(os.environ.get('TEDDY_TEST_TIMEOUT','420')),env=env)
    s.write_json(out/'host-result.json',host)
except Exception as error:
    s.write_json(out/'host-result.json',{'passed':False,'error':str(error)})
    raise
r=json.loads((out/'receipt.json').read_text())
print(json.dumps({k:v for k,v in r.items() if k not in ['frames','actors','phases','shots','samples','captures','images','encoding','events','cases']},indent=2))
if not r.get('passed'): sys.exit(1)
