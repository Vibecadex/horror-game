"""Held saved-camera rear-centre coverage; no assets saved, not an input test."""
import sys
from pathlib import Path
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture_room_gallery as gallery

gallery.VIEWS=[{'name':'rear-center-'+str(x),'caption':'Saved gameplay lighting/camera, player staged at ('+str(x)+', 0), boss held at original spawn. Visibility coverage only.','kind':'rear-visibility','player_x':x} for x in [1000,1300,1400]]
original_stage=gallery.stage

def stage(world,player,pc):
    x=gallery.VIEWS[gallery.state['index']]['player_x']
    player.set_actor_location(u.Vector(x,0,85),False,False)
    boss=gallery.state['boss'];direction=boss.get_actor_location()-player.get_actor_location()
    length=max(1.,direction.length())
    player.call_method('TouchAim',(direction.x/length,direction.y/length))
    rotation=u.MathLibrary.find_look_at_rotation(player.get_actor_location(),boss.get_actor_location())
    player.set_actor_rotation(u.Rotator(yaw=rotation.yaw),False)
    original_stage(world,player,pc)

gallery.stage=stage
