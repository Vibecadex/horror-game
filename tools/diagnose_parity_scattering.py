"""PIE-only scattering calibration; same saved room, no asset writes."""
import sys
from pathlib import Path
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture_parity_look as comparison
g=comparison.gallery
g.VIEWS=[{'name':f'{i+1:02d}-{kind}-vsi-{value:02d}','kind':'gameplay' if kind=='close' else 'gameplay-staged','value':value,'caption':f'DIAGNOSTIC: scattering intensity {value} in PIE; saved geometry/camera/exposure unchanged.'} for i,(kind,value) in enumerate([('close',8),('close',25),('close',75),('wide',8),('wide',25),('wide',75)])]
g.report['method']='PIE-only fog-light scattering calibration. Not all plates represent saved settings; no asset writes.'
original=g.stage
def stage(world,player,pc):
    original(world,player,pc)
    light=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Light) if a.get_actor_label()=='TE_Parity_FarFog_Light')
    light.get_component_by_class(u.LightComponent).set_editor_property('volumetric_scattering_intensity',float(g.VIEWS[g.state['index']]['value']))
g.stage=stage
