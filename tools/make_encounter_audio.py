"""Proposed original synthetic sounds, not a match to the unauditioned reference audio."""
from pathlib import Path
import math,random,wave,array,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Assets/Adapted/Audio';OUT.mkdir(exist_ok=True,parents=True);rate=48000
rng=random.Random(74);entries=[]
for name,length in [('Rifle',.19),('Slam',.8),('ClothHit',.22),('RoomTone',16.)]:
    samples=array.array('h');low=0;phase=0
    for i in range(int(length*rate)):
        t=i/rate;noise=rng.uniform(-1,1);low=.965*low+.035*noise
        if name=='Rifle':value=(noise*.5+math.sin(2*math.pi*(180*t+290*t*math.exp(-t*45)))*.45)*math.exp(-t*28)
        elif name=='Slam':value=(low*2.5+math.sin(2*math.pi*(43*t+28*t*math.exp(-t*5)))*.6)*math.exp(-t*5)
        elif name=='ClothHit':value=(noise-low)*.35*math.exp(-t*24)+low*math.exp(-t*8)
        else:value=.19*low+.032*math.sin(2*math.pi*41*t)*(1+.3*math.sin(2*math.pi*t/8))+.012*math.sin(2*math.pi*67*t)
        fade=min(t/.002,1.,(length-t)/.006) if name!='RoomTone' else min(t/.4,1.,(length-t)/.4)
        samples.append(int(max(-.95,min(.95,value*fade))*32767))
    path=OUT/(name+'.wav')
    with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(samples.tobytes())
    entries.append({'name':name,'seconds':length,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(OUT/'provenance.json').write_text(json.dumps({'origin':'Original locally synthesized, deterministic seed 74','reference_audio_auditioned':False,'sound_design':'Proposed original encounter audio','rate':rate,'assets':entries},indent=2))
