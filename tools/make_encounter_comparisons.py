"""Transparent crops/masks and labelled reference comparisons; no generated imagery."""
from pathlib import Path
import json,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parents[1];capture=Path(sys.argv[1]).resolve();record=Path(sys.argv[2]).resolve();OUT=ROOT/'evidence/delivery';OUT.mkdir(exist_ok=True)
font=ROOT/'.tool-cache/fonts/ReviewSans.ttf';font.parent.mkdir(exist_ok=True,parents=True)
if not font.exists():shutil.copyfile('C:/Windows/Fonts/segoeui.ttf',font)
labelsfont='.tool-cache/fonts/ReviewSans.ttf'
masks=[(0,10,43,40),(482,9,211,40),(0,235,275,68),(302,267,398,42),(0,320,700,64)]
def run(args):subprocess.run(['ffmpeg','-v','error','-xerror',*args],cwd=ROOT,check=True)
for i,sec in enumerate([5,10,16]):
    src=ROOT/'evidence/reference-video'/f'upright-{sec:02}.png';target=capture/f'position-{i+1:02}.png';out=OUT/f'comparison-{sec:02}.png';assert not out.exists()
    filters='crop=700:384:76:0'+''.join(f',drawbox=x={x}:y={y}:w={w}:h={h}:color=0x0c1b22:t=fill' for x,y,w,h in masks)
    left=filters+",pad=700:440:0:36:color=0x050b0f,drawtext=fontfile="+labelsfont+":text='REFERENCE / "+str(sec)+" seconds / overlays masked':x=15:y=10:fontsize=16:fontcolor=0x9aafb5"
    right="scale=700:-2,pad=700:440:0:36:color=0x050b0f,drawtext=fontfile="+labelsfont+":text='TEDDY ENCOUNTER / held gameplay view':x=15:y=10:fontsize=16:fontcolor=0x9aafb5"
    run(['-i',str(src),'-i',str(target),'-filter_complex',f'[0:v]{left}[l];[1:v]{right}[r];[l][r]hstack=inputs=2','-frames:v','1',str(out)])
run(['-i',str(record/'TeddyEncounter-gameplay.mp4'),'-vf',"fps=9/20,scale=400:-2,tile=3x3:padding=5:margin=5:color=0x050b0f",'-frames:v','1',str(OUT/'gameplay-contact-sheet.png')])
(OUT/'comparison-method.json').write_text(json.dumps({'capture':str(capture),'recording':str(record),'source_crop':[76,0,700,384],'source_overlay_masks_xywh':masks,'target_resize':'700 pixels wide, original aspect ratio retained','comparison':'Visual review of composition, lighting, scale and floor contact; source overlays remain masked, never inpainted. Not a pixel fidelity score or user acceptance.'},indent=2))
print(str(OUT))
