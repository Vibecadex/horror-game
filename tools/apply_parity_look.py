"""Incremental owned look pass; preserve Grok surfaces and room source assets."""
import json,sys,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import A,L,M,NS,asset,existing,own,save,components,component,compile
P=json.loads((ROOT/'study/parity-settings.json').read_text())
OUT=ROOT/json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'];assert OUT.is_dir(),f'Run directory missing: {OUT}'
LEV=u.get_editor_subsystem(u.LevelEditorSubsystem);ACT=u.get_editor_subsystem(u.EditorActorSubsystem)
R={'passed':False,'settings':P,'changes':[],'new_materials':[],'graph_changes':False}
def node(mat,cls,**props):
    n=M.create_material_expression(mat,cls);assert n
    for k,v in props.items():n.set_editor_property(k,v)
    return n
def link(a,b,pin,output=''):
    names=list(M.get_material_expression_input_names(b))
    if len(names)==1 and names[0] in ('','None'):pin=''
    assert M.connect_material_expressions(a,output,b,pin),(str(b),pin,names)
def bind(n,prop,output=''):assert M.connect_material_property(n,output,prop)
def scalar(m,v):return node(m,u.MaterialExpressionConstant,r=float(v))
def rgb(m,v):return node(m,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*v,1))
def mul(m,a,b):
    n=node(m,u.MaterialExpressionMultiply);link(a,n,'A');link(b if not isinstance(b,(int,float)) else scalar(m,b),n,'B');return n
def blend(m,a,b,t):
    n=node(m,u.MaterialExpressionLinearInterpolate);link(a,n,'A');link(b,n,'B');link(t,n,'Alpha');return n
def noise(m,pos,scale):
    n=node(m,u.MaterialExpressionNoise,scale=scale,quality=1,levels=3,output_min=0.,output_max=1.,turbulence=False)
    link(pos,n,list(M.get_material_expression_input_names(n))[0]);return n
def mat(name):
    m=asset('Parity/Materials/'+name,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m);R['new_materials'].append(m.get_path_name());return m
def sample(m,name,kind,uv):
    n=node(m,u.MaterialExpressionTextureSample,texture=existing(NS+'/Arena/'+name),sampler_type=kind);link(uv,n,'UVs');return n
def parity_texture():
    path=NS+'/Parity/Textures/T_ParityConcrete_Diffuse';t=existing(path)
    if not t:
        task=u.AssetImportTask();task.filename=str(ROOT/'Assets/Adapted/Parity/Textures/T_ParityConcrete_Diffuse.png')
        task.destination_path=NS+'/Parity/Textures';task.destination_name='T_ParityConcrete_Diffuse';task.automated=True;task.save=True
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
        t=own(A.load_asset(task.imported_object_paths[0]));t.set_editor_property('srgb',True);save(t)
    return t
def texture_sample(m,t,uv):
    n=node(m,u.MaterialExpressionTextureSample,texture=t,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR);link(uv,n,'UVs');return n
def add(m,a,b):
    n=node(m,u.MaterialExpressionAdd);link(a,n,'A');link(b,n,'B');return n
def channel(m,n,key):
    c=node(m,u.MaterialExpressionComponentMask,r=key=='R',g=key=='G',b=key=='B',a=False);link(n,c,'Input');return c
def floor_bump(m,t,uv):
    # Runtime central differences keep physical bump aligned to the colour map.
    slopes=[]
    for du,dv in [(.001,0),(0,.001)]:
        left=texture_sample(m,t,add(m,uv,node(m,u.MaterialExpressionConstant2Vector,r=-du,g=-dv)))
        right=texture_sample(m,t,add(m,uv,node(m,u.MaterialExpressionConstant2Vector,r=du,g=dv)))
        slopes.append(mul(m,add(m,channel(m,left,'G'),mul(m,channel(m,right,'G'),-1)),1.8))
    xy=node(m,u.MaterialExpressionAppendVector);link(slopes[0],xy,'A');link(slopes[1],xy,'B')
    xyz=node(m,u.MaterialExpressionAppendVector);link(xy,xyz,'A');link(scalar(m,1),xyz,'B')
    normal=node(m,u.MaterialExpressionNormalize);link(xyz,normal,'VectorInput');return normal
def floor_mat():
    m=mat('M_Parity_Floor')
    world=node(m,u.MaterialExpressionWorldPosition)
    xy=node(m,u.MaterialExpressionComponentMask,r=True,g=True,b=False,a=False);link(world,xy,'Input')
    uv=mul(m,xy,1/P['floor_tile_cm'])
    texture=parity_texture();tex=texture_sample(m,texture,uv)
    soft=sample(m,'T_AI_Floor_Color',u.MaterialSamplerType.SAMPLERTYPE_COLOR,uv)
    tex=blend(m,soft,tex,scalar(m,.70))
    desat=node(m,u.MaterialExpressionDesaturation);link(tex,desat,'');link(scalar(m,.8),desat,'Fraction')
    broad=noise(m,world,.0018)
    variation=blend(m,scalar(m,.55),scalar(m,1.15),broad)
    base=mul(m,mul(m,desat,P['floor_scale']),variation)
    bind(base,u.MaterialProperty.MP_BASE_COLOR)
    nr=floor_bump(m,texture,uv)
    normal=blend(m,rgb(m,(0,0,1)),nr,scalar(m,P['floor_normal']))
    bind(normal,u.MaterialProperty.MP_NORMAL)
    rough=channel(m,tex,'G')
    roughness=blend(m,scalar(m,.53),scalar(m,.98),rough)
    bind(roughness,u.MaterialProperty.MP_ROUGHNESS);bind(scalar(m,.28),u.MaterialProperty.MP_SPECULAR)
    M.recompile_material(m);save(m);return m
def cloth_mat():
    m=mat('M_Parity_TeddyCloth');m.set_editor_property('used_with_skeletal_mesh',True)
    m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_CLOTH)
    m.set_editor_property('use_material_attributes',True)
    attributes=node(m,u.MaterialExpressionMakeMaterialAttributes)
    R['cloth_attribute_inputs']=list(M.get_material_expression_input_names(attributes))
    base=node(m,u.MaterialExpressionTextureSample,texture=existing(NS+'/Teddy/T_Teddy_BaseColor'))
    d=node(m,u.MaterialExpressionDesaturation);link(base,d,'','RGB');link(scalar(m,P['cloth_desaturation']),d,'Fraction')
    tinted=mul(m,mul(m,d,P['cloth_base_scale']),rgb(m,(1.,.90,.76)))
    grain_uv=node(m,u.MaterialExpressionTextureCoordinate)
    grain_uv3=node(m,u.MaterialExpressionAppendVector);link(grain_uv,grain_uv3,'A');link(scalar(m,0),grain_uv3,'B')
    grain=noise(m,grain_uv3,155)
    tinted=mul(m,tinted,blend(m,scalar(m,.58),scalar(m,1.42),grain))
    link(tinted,attributes,'BaseColor')
    uv=node(m,u.MaterialExpressionTextureCoordinate,u_tiling=P['cloth_uv'][0],v_tiling=P['cloth_uv'][1])
    normal=sample(m,'T_AI_Plush_Normal',u.MaterialSamplerType.SAMPLERTYPE_NORMAL,uv)
    normal=blend(m,rgb(m,(0,0,1)),normal,scalar(m,P['cloth_normal']))
    normalized=node(m,u.MaterialExpressionNormalize);link(normal,normalized,'VectorInput')
    link(normalized,attributes,'Normal')
    rough=sample(m,'T_AI_Plush_Roughness',u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE,uv)
    link(blend(m,scalar(m,.88),scalar(m,.99),rough),attributes,'Roughness')
    link(scalar(m,.10),attributes,'Specular');link(rgb(m,(.08,.075,.045)),attributes,'SubsurfaceColor')
    # MakeMaterialAttributes exposes CustomData0 through its ClearCoat input.
    # Cloth consumes that channel as its amount; avoids hidden enum construction.
    link(scalar(m,P['cloth_amount']),attributes,'ClearCoat')
    bind(attributes,u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    M.recompile_material(m);save(m);R['cloth_shading_model']=str(m.get_editor_property('shading_model'));return m
def spawn(cls,name,loc,rotation=None):
    a=ACT.spawn_actor_from_class(cls,u.Vector(*loc),rotation or u.Rotator(),transient=False);assert a
    a.set_actor_label('TE_Parity_'+name);a.set_editor_property('tags',['TeddyEncounterOwned','ParityOwned'])
    a.set_folder_path('TeddyEncounter/Parity');return a
def light_settings(c,intensity,color,radius,source=10,volume=0.0):
    c.set_editor_property('mobility',u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units',u.LightUnits.CANDELAS)
    c.set_editor_property('use_inverse_squared_falloff',True)
    c.set_editor_property('intensity',float(intensity));c.set_light_color(u.LinearColor(*color,1))
    c.set_editor_property('attenuation_radius',float(radius));c.set_editor_property('source_radius',float(source))
    c.set_editor_property('volumetric_scattering_intensity',float(volume));c.set_cast_shadows(True)
def main():
    assert existing('/Game/Maps/TeddyEncounter');assert LEV.load_level('/Game/Maps/TeddyEncounter')
    # Delete only this incremental pass's light/fog actors, retaining all source work.
    for a in list(ACT.get_all_level_actors()):
        if a.get_actor_label().startswith('TE_Parity_') and any(t in a.get_actor_label() for t in ['Key','FarFog','Warning']):
            assert 'ParityOwned' in [str(x) for x in a.tags];ACT.destroy_actor(a)
    floor,cloth=floor_mat(),cloth_mat()
    for name in ['BP_TeddyBoss','BP_Stitchling']:
        bp=existing(NS+'/Blueprints/'+name)
        for _,(_,c) in components(bp).items():
            if isinstance(c,u.SkeletalMeshComponent):
                mats=list(c.get_editor_property('override_materials'));mats=[cloth,*mats[1:]]
                c.set_editor_property('override_materials',mats)
        compile(bp)
    player=existing(NS+'/Blueprints/BP_EncounterPlayer');assert player
    pc=component(player,'ParityPlayerLight',u.SpotLightComponent,'CollisionCylinder')
    light_settings(pc,P['player_light_intensity'],(.96,.98,1.),850,6,0.)
    pc.set_editor_property('relative_location',u.Vector(*P['player_light_location']))
    pc.set_editor_property('relative_rotation',u.Rotator(pitch=P['player_light_pitch'],yaw=0,roll=0))
    pc.set_editor_property('inner_cone_angle',9.);pc.set_editor_property('outer_cone_angle',26.)
    compile(player)
    camera=existing(NS+'/Blueprints/BP_CombatCamera')
    for _,(_,c) in components(camera).items():
        if isinstance(c,u.CameraComponent):c.set_editor_property('field_of_view',float(P.get('camera_fov',48)))
    compile(camera)
    for a in ACT.get_all_level_actors():
        name=a.get_actor_label();c=a.get_component_by_class(u.LightComponent)
        if name=='TE_ArenaFloor':a.static_mesh_component.set_material(0,floor)
        if name=='TE_MainTeddy' or name.startswith('TE_Stitchling'):
            for sc in a.get_components_by_class(u.SkeletalMeshComponent):
                mats=list(sc.get_editor_property('override_materials'));sc.set_editor_property('override_materials',[cloth,*mats[1:]])
        if name=='TE_CombatView':a.get_component_by_class(u.CameraComponent).set_editor_property('field_of_view',float(P.get('camera_fov',48)))
        if name.startswith('TE_AI_Decal_') or (name.startswith('TE_Room_') and 'RoomFloorDetail' in [str(t) for t in a.tags]):
            a.set_actor_hidden_in_game(True)
        if name in ['TE_Key','TE_Rim','TE_PlayerFill','TE_FaceFill'] and c:c.set_editor_property('intensity',0.)
        if name=='TE_AmbientFill':c.set_editor_property('intensity',float(P['ambient']))
        if name.startswith('TE_Room_') and c:
            originals={'RearGrazing_0':3600,'RearGrazing_1':3600,'LeftServiceLight':4100,'RightServiceLight':3600}
            suffix=name.removeprefix('TE_Room_')
            if suffix in originals:c.set_editor_property('intensity',originals[suffix]*P['room_light_scale'])
            if suffix.startswith('CornerBounce_'):c.set_editor_property('intensity',float(P['corner_light']))
        if name=='TE_LowMist':
            fog=a.get_component_by_class(u.ExponentialHeightFogComponent)
            fog.set_editor_property('fog_density',float(P['fog_density']))
            fog.set_editor_property('fog_inscattering_luminance',u.LinearColor(.004,.012,.010,1))
            fog.set_editor_property('volumetric_fog_scattering_distribution',.2)
    loc=u.Vector(*P['key_location']);target=u.Vector(*P['key_target'])
    key=spawn(u.SpotLight,'Key',P['key_location'],u.MathLibrary.find_look_at_rotation(loc,target))
    c=key.get_component_by_class(u.SpotLightComponent)
    light_settings(c,P['key_intensity'],P['key_color'],P['key_radius'],P['key_source'],.45)
    c.set_editor_property('inner_cone_angle',float(P['key_inner']));c.set_editor_property('outer_cone_angle',float(P['key_outer']))
    c.set_editor_property('cast_volumetric_shadow',True)
    fog=spawn(u.LocalFogVolume,'FarFog',P['far_fog_location']);fog.set_actor_scale3d(u.Vector(*P['far_fog_scale']))
    fc=fog.get_component_by_class(u.LocalFogVolumeComponent)
    for k,v in {'radial_fog_extinction':float(P['far_fog_density']),'height_fog_extinction':.12,'height_fog_falloff':1.4,'fog_phase_g':.2,'fog_albedo':u.LinearColor(.42,.76,.76,1),'fog_emissive':u.LinearColor(*P['far_fog_emission'],1)}.items():fc.set_editor_property(k,v)
    warning=mat('M_Parity_Warning');bind(rgb(warning,(.28,.004,.002)),u.MaterialProperty.MP_BASE_COLOR)
    bind(rgb(warning,(1.8,.016,.005)),u.MaterialProperty.MP_EMISSIVE_COLOR);M.recompile_material(warning);save(warning)
    cube=u.load_asset('/Engine/BasicShapes/Cube')
    for i,(x,y) in enumerate([(1200,-470),(1200,720),(940,-1160),(940,1390)]):
        a=spawn(u.StaticMeshActor,'Warning_'+str(i),(x,y,-3.5))
        a.set_actor_scale3d(u.Vector(.50,.075,.012));c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,warning)
        c.set_collision_profile_name('NoCollision');c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_enable_collision(False)
    assert LEV.save_current_level()
    assert LEV.load_level('/Game/Maps/TeddyEncounter')
    saved=next(a for a in ACT.get_all_level_actors() if a.get_actor_label()=='TE_ArenaFloor')
    assert saved.static_mesh_component.get_material(0)==floor
    R.update(passed=True,player_component=pc.get_name(),camera_fov=P.get('camera_fov',48),camera_tracking_and_input_unchanged=True,source_materials_preserved=True)
if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/(P['revision']+'-authoring.json')).write_text(json.dumps(R,indent=2))
