import astra_setup as setup,sys,os,json,subprocess,time,traceback
from pathlib import Path
from datetime import datetime,timezone
from png_evidence import decode_png
setup.require_editor_closed();out=setup.ROOT/'evidence/implementation'/('native-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'));out.mkdir()
env=dict(setup.tool_environment(),TEDDY_STANDALONE_DIR=str(out));print(str(out),flush=True)
subprocess.run([sys.executable,str(setup.ROOT/'tools/astra_setup.py'),'editor-script','tools/author_standalone_evidence.py'],env=env,cwd=setup.ROOT,check=True)
author=json.loads((out/'authoring.json').read_text());assert author['passed']
engine=Path(setup.SETTINGS['engine_root'])/'Engine/Binaries/Win64/UnrealEditor.exe'
args=[str(engine),str(setup.ROOT/setup.SETTINGS['project']),author['map'],'-game','-RenderOffscreen','-windowed','-ResX=1280','-ResY=720','-unattended','-nosplash','-nop4','-csvGpuStats','-ini:Engine:[Audio]:UnfocusedVolumeMultiplier=1.0',f'-abslog={out/"engine.log"}',*setup.unreal_local_arguments()]
setup.write_json(out/'invocation.json',{'arguments':args});r={'passed':False,'authoring':author,'resolution':[1280,720],'ordinary_game_process':True}
profile_dir=setup.ROOT/'.tool-cache/unreal-user/Saved/Profiling/CSV';old_profiles=set(profile_dir.glob('*.csv'))
with (out/'process.log').open('w') as log:
    p=subprocess.Popen(args,env=env,cwd=setup.ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));started=time.monotonic()
    try:
        while p.poll() is None:
            if (out/'standalone.png').exists() and 'image' not in r:
                try:r['image']=decode_png(out/'standalone.png');r['image_complete_before_process_exit']=p.poll() is None;r['complete_wall_seconds']=time.monotonic()-started
                except Exception:pass
            if time.monotonic()-started>100:raise RuntimeError('Standalone timeout')
            time.sleep(.1)
        r['exit_code']=p.returncode;r['passed']=p.returncode==0 and bool(r.get('image_complete_before_process_exit')) and 'TEDDY_STANDALONE_SAVED_BLUEPRINTS_EXECUTED' in (out/'engine.log').read_text(errors='replace')
    except Exception:r['error']=traceback.format_exc();p.terminate();p.wait(timeout=15)
setup.write_json(out/'receipt.json',r)
new_profiles=set(profile_dir.glob('*.csv'))-old_profiles
if r['passed'] and len(new_profiles)==1:
    subprocess.run([sys.executable,str(setup.ROOT/'tools/summarize_standalone_evidence.py'),str(out),str(new_profiles.pop())],cwd=setup.ROOT,check=True)
print(json.dumps({k:v for k,v in r.items() if k!='image'},indent=2));raise SystemExit(0 if r['passed'] else 1)
