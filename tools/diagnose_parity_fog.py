"""Transient luminance sweep; diagnostic images are not saved-game evidence."""
import sys
from pathlib import Path
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture_parity_look as comparison
g=comparison.gallery
g.VIEWS=[{'name':f'fog-luminance-{v:02d}','kind':'gameplay','caption':f'DIAGNOSTIC ONLY: far local fog emissive (.225,1,1)*{v} in transient PIE; saved camera and all other lighting retained.','value':v} for v in [5,20,60]]
g.report['method']='Transient fog-emission sweep; no saved asset changes. Held matched gameplay composition.'
original_stage=g.stage
def stage(world,player,pc):
    original_stage(world,player,pc)
    fog=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.LocalFogVolume) if a.get_actor_label()=='TE_Parity_FarFog')
    c=fog.get_component_by_class(u.LocalFogVolumeComponent);value=g.VIEWS[g.state['index']]['value']
    c.set_fog_emissive(u.LinearColor(value*.225,value,value,1))
    g.report['fog_volume']={'location':str(fog.get_actor_location()),'scale':str(fog.get_actor_scale3d()),'radial':c.get_editor_property('radial_fog_extinction'),'height':c.get_editor_property('height_fog_extinction')}
    g.report['console_values']={k:u.SystemLibrary.get_console_variable_int_value(k) for k in ['r.LocalFogVolume','r.SupportLocalFogVolumes','r.LocalFogVolume.RenderIntoVolumetricFog','r.VolumetricFog']}
g.stage=stage
