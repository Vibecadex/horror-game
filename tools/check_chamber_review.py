"""Check local delivery links and decoded evidence, without opening Unreal."""
import hashlib,json,subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=(ROOT/Path(json.loads((ROOT/'evidence/chamber/current-run.json').read_text())['out'])).resolve()

class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[];self.scripts=[];self.inscript=False
    def handle_starttag(self,tag,attrs):
        self.inscript=tag=='script' or self.inscript
        self.urls.extend(v for k,v in attrs if k in ('href','src','poster') and v)
    def handle_endtag(self,tag):
        if tag=='script':self.inscript=False
    def handle_data(self,data):
        if self.inscript:self.scripts.append(data)

def main():
    text=(OUT/'review.html').read_text(encoding='utf-8');p=Links();p.feed(text)
    data=json.loads((OUT/'delivery.json').read_text());r={'passed':False,'links':[],'images':[]}
    paths=set()
    for url in p.urls:
        parts=urlsplit(url)
        if parts.scheme or not parts.path:continue
        file=(OUT/unquote(parts.path)).resolve()
        assert file.is_relative_to(ROOT) and file.is_file(),url
        paths.add(file);r['links'].append({'url':url,'exists':True})
    for view in data['views']:
        for key in ['reference','candidate','baseline']:
            file=(OUT/unquote(view[key])).resolve();assert file.is_relative_to(ROOT) and file.is_file()
            paths.add(file)
    for file in sorted(paths):
        if file.suffix.lower() not in ['.png','.jpg','.jpeg']:continue
        with Image.open(file) as im:im.load();size=list(im.size)
        r['images'].append({'path':str(file),'size':size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    javascript=OUT/'review-script.js';javascript.write_text('\n'.join(p.scripts),encoding='utf-8')
    check=subprocess.run(['node','--check',str(javascript)],capture_output=True,text=True)
    r['javascript_syntax_passed']=check.returncode==0
    assert check.returncode==0,check.stderr
    r['counts']={'static_links':len(r['links']),'decoded_images':len(r['images'])}
    r['method']='Local file/link existence, Pillow decode and installed Node syntax check; no claim of a browser interaction test.'
    r['passed']=True;(OUT/'review-integrity.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({'passed':r['passed'],**r['counts'],'javascript_syntax_passed':True}))

if __name__=='__main__':main()
