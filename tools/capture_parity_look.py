"""One held comparison from the saved gameplay camera; no asset writes."""
import unreal as u
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture_room_gallery as gallery
gallery.VIEWS=[{'name':'01-matched-gameplay','caption':'Saved gameplay camera, lighting, exposure and spawns. Player/NPC movement held, HUD hidden; player rotation staged toward boss for the selected look reference. No camera or exposure override.','kind':'gameplay'}]
original_stage=gallery.stage
def stage(world,player,pc):
    delta=gallery.state['boss'].get_actor_location()-player.get_actor_location()
    direction=u.MathLibrary.find_look_at_rotation(player.get_actor_location(),gallery.state['boss'].get_actor_location())
    player.set_actor_rotation(u.Rotator(pitch=0,yaw=direction.yaw,roll=0),False)
    original_stage(world,player,pc)
gallery.stage=stage
