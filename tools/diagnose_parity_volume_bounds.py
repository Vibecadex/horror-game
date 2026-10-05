"""Transient gameplay/edge lighting test; never saves a map or asset."""
import sys
from pathlib import Path
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture_parity_look as comparison
g=comparison.gallery
g.VIEWS=[{'name':'01-initial','kind':'gameplay','caption':'DIAGNOSTIC: lowered far fog cap and localized perimeter fills, saved gameplay camera.'},
         {'name':'02-wide','kind':'gameplay-staged','caption':'DIAGNOSTIC: opposite-corner separation, same staged lighting.'},
         {'name':'03-room','kind':'architecture','caption':'DIAGNOSTIC: elevated room coverage, temporary camera and fog/fills.','location':(-4300,-2300,4100),'target':(0,0,180),'fov':53}]
g.report['method']='Transient volume-bounds and peripheral readability study. Asset writes false. This is not the saved game.'
original=g.stage
def stage(world,player,pc):
    original(world,player,pc)
    for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor):
        if a.get_actor_label()=='TE_Parity_FarFog':
            a.set_actor_location(u.Vector(1400,150,-600),False,False)
            c=a.get_component_by_class(u.LocalFogVolumeComponent);c.set_fog_emissive(u.LinearColor(19.25,55,53.35,1))
        if a.get_actor_label().startswith('TE_Room_CornerBounce_'):
            pos=a.get_actor_location();pos.z=600;a.set_actor_location(pos,False,False)
            c=a.get_component_by_class(u.PointLightComponent);c.set_intensity(14000);c.set_attenuation_radius(950)
g.stage=stage
