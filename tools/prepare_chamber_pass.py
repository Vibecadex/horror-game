"""Preserve exact current playable files and the two selected chamber references."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/chamber'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=BASE/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out.mkdir(parents=True,exist_ok=False)
    refs=[]
    for source,name in [('codex-clipboard-dafd68c7-909c-4849-872b-5707e8477e31.png','chamber-target-front.png'),('codex-clipboard-bda9ece1-a641-46f8-995d-8603600a6c40.png','chamber-target-reverse.png')]:
        source=Path('C:/Users/4elut/AppData/Local/Temp')/source;dest=ROOT/'study/visuals'/name
        assert source.is_file()
        if dest.exists():assert sha(source)==sha(dest)
        else:shutil.copy2(source,dest)
        refs.append({'source':str(source),'copy':str(dest),'sha256':sha(dest)})
    files=list((ROOT/'TeddyBlueprint/Content/TeddyEncounter').rglob('*.uasset'))
    files+=[ROOT/'TeddyBlueprint/Content/Maps/TeddyEncounter.umap']
    files+=list((ROOT/'TeddyBlueprint/Config').rglob('*.ini'))
    files+=[ROOT/'WORK_STATUS.md',ROOT/'ENCOUNTER.md',ROOT/'tools/astra_setup.py']
    rows=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(files))]
    archive=out/'before-chamber.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for r in rows:z.write(ROOT/r['path'],r['path'])
    with zipfile.ZipFile(archive) as z:
        for r in rows:assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
    previous=json.loads((ROOT/'evidence/parity/20261005T070301Z/final-active-assets.json').read_text())
    drift=[r['path'] for r in rows if r['path'] in previous and r['sha256']!=previous[r['path']]]
    result={'out':str(out),'passed':True,'archive':str(archive),'files':rows,'references':refs,'changes_since_last_handoff':drift,'method':'Exact byte copies and hashes; no semantic asset parsing.'}
    (out/'baseline.json').write_text(json.dumps(result,indent=2));(BASE/'current-run.json').write_text(json.dumps({'out':out.relative_to(ROOT).as_posix()},indent=2))
    print(json.dumps({'out':str(out),'files':len(rows),'references':refs,'changes_since_last_handoff':drift},indent=2))
if __name__=='__main__':main()
