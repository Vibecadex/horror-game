"""Reveal the chamber's layered wall surfaces using local directional washes."""
import traceback,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chamber_common import *
R={'passed':False,'settings':P['room_lights'],'gameplay_and_key_light_changed':False}
def main():
    begin()
    if 'key_outer_cone' in P:
        key=next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label()=='TE_Parity_Key')
        key.get_component_by_class(u.SpotLightComponent).set_editor_property('outer_cone_angle',float(P['key_outer_cone']))
        R['key_outer_cone_only_changed']=P['key_outer_cone'];R['gameplay_and_key_light_changed']='Only key outer cone; gameplay unchanged'
    surfaces=[]
    for a in ACTORS.get_all_level_actors():
        if a.get_actor_label().startswith(('TE_Room_','TE_Parity_RoomExt_','TE_Chamber_')):
            if {'RoomFloorDetail','ChamberFloorOwned','ChamberSlabsOwned','ChamberCrustOwned','ChamberMorphologyOwned'} & {str(t) for t in a.tags}:continue
            for c in a.get_components_by_class(u.StaticMeshComponent):
                c.set_lighting_channels(True,False,True);surfaces.append(a.get_actor_label()+':'+c.get_name())
    # Persist component defaults as well as placed-instance channels.
    bp=existing(DEST+'/Blueprints/BP_ChamberCutaway')
    if bp:
        for _,(_,c) in components(bp).items():
            if isinstance(c,u.StaticMeshComponent):c.set_lighting_channels(True,False,True)
        compile(bp)
    R['channel2_environment_components']=surfaces
    if 'rear_fog_scattering' in P:
        foglight=next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label()=='TE_Parity_FarFog_Light')
        assert 'ParityOwned' in [str(t) for t in foglight.tags]
        fog=foglight.get_component_by_class(u.LightComponent)
        R['rear_fog_before']={'scattering':float(fog.get_editor_property('volumetric_scattering_intensity')),'intensity':float(fog.get_editor_property('intensity')),'diffuse_scale':float(fog.get_editor_property('diffuse_scale'))}
        fog.set_editor_property('volumetric_scattering_intensity',float(P['rear_fog_scattering']))
        R['rear_fog_scattering']=P['rear_fog_scattering']
        if 'overhead_mist' in P:
            spec=P['overhead_mist']
            foglight.set_actor_location(u.Vector(*spec['location']),False,False)
            foglight.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*spec['location']),u.Vector(*spec['target'])),False)
            for prop,key in (('intensity','intensity'),('attenuation_radius','radius'),('source_width','width'),('source_height','height'),('volumetric_scattering_intensity','scattering')):fog.set_editor_property(prop,float(spec[key]))
            fog.set_editor_property('diffuse_scale',0.);fog.set_editor_property('specular_scale',0.)
            R['overhead_mist']=spec
    if 'height_fog' in P:
        mist=next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label()=='TE_LowMist')
        hc=mist.get_component_by_class(u.ExponentialHeightFogComponent)
        R['height_fog_before']={k:float(hc.get_editor_property(k)) for k in P['height_fog']}
        R['height_fog_inscattering_left_unchanged']=str(hc.get_editor_property('fog_inscattering_luminance'))
        for k,v in P['height_fog'].items():hc.set_editor_property(k,float(v))
        R['height_fog']=P['height_fog']
    if 'reverse_overhead' in P:
        s=P['reverse_overhead']
        def tune(c):
            c.set_editor_property('relative_location',u.Vector(*s['location']))
            c.set_editor_property('relative_rotation',u.MathLibrary.find_look_at_rotation(u.Vector(*s['location']),u.Vector(*s['target'])))
            for prop,key in (('intensity','intensity'),('attenuation_radius','radius'),('inner_cone_angle','inner'),('outer_cone_angle','outer'),('source_radius','source'),('volumetric_scattering_intensity','scattering')):c.set_editor_property(prop,float(s[key]))
            c.set_editor_property('intensity_units',u.LightUnits.CANDELAS);c.set_editor_property('indirect_lighting_intensity',0.)
            c.set_light_color(u.LinearColor(*s['color'],1));c.set_lighting_channels(False,False,True);c.set_cast_shadows(True)
        bp=existing(DEST+'/Blueprints/BP_ChamberCutaway');pool=component(bp,'ReverseOverheadPool',u.SpotLightComponent,parent='ChamberRoot');tune(pool);compile(bp)
        owner=next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label()=='TE_Chamber_FrontCutaway')
        inst=next(c for c in owner.get_components_by_class(u.SpotLightComponent) if c.get_name()=='ReverseOverheadPool');tune(inst)
        R['reverse_overhead']=s
    if 'front_floor_return' in P:
        s=P['front_floor_return'];label='TE_Chamber_FrontFloorReturn'
        for a in list(ACTORS.get_all_level_actors()):
            if a.get_actor_label()==label:assert 'ChamberOwned' in [str(t) for t in a.tags];assert ACTORS.destroy_actor(a)
        a=spawn(u.SpotLight,'FrontFloorReturn',s['location'],u.MathLibrary.find_look_at_rotation(u.Vector(*s['location']),u.Vector(*s['target'])))
        c=a.get_component_by_class(u.SpotLightComponent)
        for k,v in {'mobility':u.ComponentMobility.MOVABLE,'intensity_units':u.LightUnits.CANDELAS,'intensity':float(s['intensity']),'attenuation_radius':float(s['radius']),'inner_cone_angle':float(s['inner']),'outer_cone_angle':float(s['outer']),'source_radius':float(s['source']),'volumetric_scattering_intensity':float(s.get('scattering',.4)),'indirect_lighting_intensity':0.,'specular_scale':.1}.items():c.set_editor_property(k,v)
        c.set_light_color(u.LinearColor(*s['color'],1));c.set_cast_shadows(True);c.set_lighting_channels(True,False,False)
        R['front_floor_return']=s
    planned={'TE_Chamber_'+s['name'] for s in P['room_lights']}
    for a in list(ACTORS.get_all_level_actors()):
        if a.get_actor_label() in planned:
            assert 'ChamberOwned' in [str(t) for t in a.tags];assert ACTORS.destroy_actor(a)
    for s in P['room_lights']:
        a=spawn(u.RectLight,s['name'],s['location'],u.MathLibrary.find_look_at_rotation(u.Vector(*s['location']),u.Vector(*s['target'])))
        c=a.get_component_by_class(u.RectLightComponent)
        for k,v in {'mobility':u.ComponentMobility.MOVABLE,'intensity_units':u.LightUnits.CANDELAS,'intensity':float(s['intensity']),'attenuation_radius':float(s['radius']),'source_width':float(s['width']),'source_height':float(s['height']),'volumetric_scattering_intensity':0.,'indirect_lighting_intensity':0.,'specular_scale':float(s.get('specular',.45))}.items():c.set_editor_property(k,v)
        c.set_light_color(u.LinearColor(*s['color'],1));c.set_cast_shadows(True);c.set_lighting_channels(False,False,True)
    finish()
    got=[a for a in ACTORS.get_all_level_actors() if a.get_actor_label() in planned];assert len(got)==len(planned)
    R['readback']=[{'label':a.get_actor_label(),'intensity':a.get_component_by_class(u.RectLightComponent).get_editor_property('intensity')} for a in got];R['passed']=True
if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/(P['revision']+'-lighting.json')).write_text(json.dumps(R,indent=2))
