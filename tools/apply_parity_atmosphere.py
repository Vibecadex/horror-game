"""Confine luminous haze to the room and retain creatures in perimeter darkness."""
import json, sys, traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import NS,existing,components,compile
from apply_parity_look import spawn,light_settings
P=json.loads((ROOT/'study/parity-atmosphere-settings.json').read_text())
OUT=Path(json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'])
R={'passed':False,'settings':P,'material_camera_key_and_player_light_changes':False}

def main():
    level=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert existing('/Game/Maps/TeddyEncounter');assert level.load_level('/Game/Maps/TeddyEncounter')
    for a in list(actors.get_all_level_actors()):
        if a.get_actor_label().startswith('TE_Parity_FarFog'):
            assert 'ParityOwned' in [str(t) for t in a.tags];assert actors.destroy_actor(a)
    for spec in P['fog']:
        a=spawn(u.LocalFogVolume,spec['name'],spec['location']);a.set_actor_scale3d(u.Vector(spec['scale'],spec['scale'],spec['scale']))
        c=a.get_component_by_class(u.LocalFogVolumeComponent)
        for k,v in {'radial_fog_extinction':spec['density'],'height_fog_extinction':.1,'height_fog_falloff':1.4,'fog_phase_g':.2,'fog_albedo':u.LinearColor(.42,.76,.76,1),'fog_emissive':u.LinearColor(*spec['emission'],1)}.items():c.set_editor_property(k,v)
        assert spec['location'][2]+spec['scale']*500 <= 685,'Fog exceeds room wall height'
    for spec in P.get('fog_lights',[]):
        location=u.Vector(*spec['location']);target=u.Vector(*spec['target'])
        is_rect=spec.get('type')=='rect'
        a=spawn(u.RectLight if is_rect else u.SpotLight,spec['name'],spec['location'],u.MathLibrary.find_look_at_rotation(location,target))
        c=a.get_component_by_class(u.RectLightComponent if is_rect else u.SpotLightComponent)
        if is_rect:
            for k,v in {'mobility':u.ComponentMobility.MOVABLE,'intensity_units':u.LightUnits.CANDELAS,'intensity':float(spec['intensity']),'attenuation_radius':float(spec['radius']),'source_width':float(spec['width']),'source_height':float(spec['height']),'volumetric_scattering_intensity':float(spec['scattering'])}.items():c.set_editor_property(k,v)
            c.set_light_color(u.LinearColor(*spec['color'],1));c.set_cast_shadows(True)
        else:
            light_settings(c,spec['intensity'],spec['color'],spec['radius'],spec['source'],spec['scattering'])
            c.set_editor_property('inner_cone_angle',float(spec['inner']));c.set_editor_property('outer_cone_angle',float(spec['outer']))
        for k,v in {'diffuse_scale':0.,'specular_scale':0.,'indirect_lighting_intensity':0.,'cast_volumetric_shadow':True}.items():c.set_editor_property(k,v)
    for name in ['BP_TeddyBoss','BP_Stitchling','BP_EncounterPlayer']:
        bp=existing(NS+'/Blueprints/'+name)
        for _,(_,c) in components(bp).items():
            if isinstance(c,u.SkeletalMeshComponent):c.set_lighting_channels(True,True,False)
        compile(bp)
    fills=[]
    for a in actors.get_all_level_actors():
        if a.get_actor_label()=='TE_LowMist' and 'height_fog' in P:
            c=a.get_component_by_class(u.ExponentialHeightFogComponent)
            for k,v in P['height_fog'].items():c.set_editor_property(k,v)
        if a.get_actor_label()=='TE_MainTeddy' or a.get_actor_label().startswith('TE_Stitchling'):
            for c in a.get_components_by_class(u.SkeletalMeshComponent):c.set_lighting_channels(True,True,False)
        if a.get_actor_label().startswith('TE_Room_CornerBounce_'):
            spec=P['perimeter_character_fill'];pos=a.get_actor_location()
            if pos.x<0 and P.get('foreground_character_fill'):
                spec=P['foreground_character_fill'];pos.x=spec['x']
            pos.z=spec['height'];a.set_actor_location(pos,False,False)
            c=a.get_component_by_class(u.PointLightComponent);c.set_lighting_channels(False,True,False)
            c.set_intensity(spec['intensity']);c.set_attenuation_radius(spec['radius']);c.set_editor_property('volumetric_scattering_intensity',0.)
            fills.append(a.get_actor_label())
    assert len(fills)==4,fills
    assert level.save_current_level();assert level.load_level('/Game/Maps/TeddyEncounter')
    R['fog_readback']=[];R['fill_readback']=[]
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith('TE_Parity_FarFog') and isinstance(a,u.LocalFogVolume):
            c=a.get_component_by_class(u.LocalFogVolumeComponent)
            R['fog_readback'].append({'label':a.get_actor_label(),'location':str(a.get_actor_location()),'scale':str(a.get_actor_scale3d()),'emission':str(c.get_editor_property('fog_emissive'))})
        if a.get_actor_label() in fills:
            c=a.get_component_by_class(u.PointLightComponent);ch=c.get_editor_property('lighting_channels')
            assert not ch.channel0 and ch.channel1 and not ch.channel2
            R['fill_readback'].append({'label':a.get_actor_label(),'channels':str(ch),'intensity':c.get_editor_property('intensity')})
    assert len(R['fog_readback'])==len(P['fog']);assert len(R['fill_readback'])==4
    R['fog_light_count']=sum(1 for a in actors.get_all_level_actors() if a.get_actor_label().startswith('TE_Parity_FarFog') and isinstance(a,u.Light))
    assert R['fog_light_count']==len(P.get('fog_lights',[]))
    R['passed']=True

if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/(P['revision']+'-authoring.json')).write_text(json.dumps(R,indent=2))
