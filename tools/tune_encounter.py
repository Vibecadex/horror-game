import unreal as u
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];lev=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert lev.load_level('/Game/Maps/TeddyEncounter')
changes=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label()=='TE_Exposure':
        pp=a.get_editor_property('settings')
        for k,v in {'auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_bias':3.5,'camera_iso':100.,'camera_shutter_speed':60.,'depth_of_field_fstop':4.}.items():
            pp.set_editor_property('override_'+k,True);pp.set_editor_property(k,v)
        a.set_editor_property('settings',pp);changes.append('Manual physical exposure ISO100, 1/60s, f4, bias +3.5 EV')
    if isinstance(a,u.PointLight) and a.get_actor_label() in ['TE_Key','TE_Rim','TE_PlayerFill']:
        c=a.point_light_component;c.set_attenuation_radius(2900);c.set_source_radius(110);c.set_editor_property('volumetric_scattering_intensity',.18)
    if isinstance(a,u.ExponentialHeightFog):
        c=a.get_component_by_class(u.ExponentialHeightFogComponent);c.set_editor_property('fog_density',.008)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
if not any(a.get_actor_label()=='TE_AmbientFill' for a in actors.get_all_level_actors()):
    a=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,1000),u.Rotator(pitch=-65,yaw=15),transient=False);a.set_actor_label('TE_AmbientFill');a.set_editor_property('tags',['TeddyEncounterOwned'])
    c=a.get_component_by_class(u.DirectionalLightComponent);c.set_light_color(u.LinearColor(.18,.34,.45,1));c.set_intensity(.8);c.set_editor_property('light_source_angle',8.)
assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(ROOT/'evidence/implementation/exposure-tuning.json').write_text(json.dumps(changes,indent=2))
