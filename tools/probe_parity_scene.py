"""Read saved scene/component state and transient API values; never save assets."""
from pathlib import Path
import json,sys,unreal as u
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import existing,components
OUT=Path(json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'])
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level('/Game/Maps/TeddyEncounter')
r={'actors':[],'blueprints':{},'material_property':{},'asset_writes':False}
for a in A.get_all_level_actors():
    name=a.get_actor_label()
    if name.startswith('TE_') and (a.get_component_by_class(u.LightComponent) or 'Fog' in name or name in ['TE_LowMist','TE_ArenaFloor','TE_MainTeddy']):
        d={'label':name,'class':a.get_class().get_name(),'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation()),'scale':str(a.get_actor_scale3d()),'components':[]}
        for c in a.get_components_by_class(u.ActorComponent):
            cd={'name':c.get_name(),'class':c.get_class().get_name()}
            for key in ['intensity','intensity_units','light_color','use_inverse_squared_falloff','light_falloff_exponent','attenuation_radius','source_radius','cast_shadows','volumetric_scattering_intensity','fog_density','fog_height_falloff','volumetric_fog_scattering_distribution','volumetric_fog_albedo','volumetric_fog_extinction_scale','fog_inscattering_luminance','static_mesh','skeletal_mesh_asset','relative_location','relative_rotation','relative_scale3d']:
                try:cd[key]=str(c.get_editor_property(key))
                except Exception:pass
            if len(cd)>2:d['components'].append(cd)
        r['actors'].append(d)
for name in ['BP_Player','BP_TeddyBoss','BP_Stitchling']:
    bp=existing('/Game/TeddyEncounter/Blueprints/'+name)
    if not bp:continue
    cs=[]
    for n,(_,c) in components(bp).items():
        cd={'name':n,'class':c.get_class().get_name()}
        for key in ['skeletal_mesh_asset','anim_class','relative_location','relative_rotation','relative_scale3d','override_materials','attach_parent']:
            try:cd[key]=str(c.get_editor_property(key))
            except Exception:pass
        cs.append(cd)
    r['blueprints'][name]=cs
for key in [x for x in dir(u.MaterialProperty) if x.startswith('MP_')]:r['material_property'][key]=str(getattr(u.MaterialProperty,key))
for name,f in [('ctor16',lambda:u.MaterialProperty(16)),('cast16',lambda:u.MaterialProperty.cast(16)),('enumvalue',lambda:u.MaterialProperty.MP_SUBSURFACE_COLOR.value)]:
    try:r['material_property'][name]=str(f())
    except Exception as e:r['material_property'][name]=str(e)
r['local_fog_class']=str(getattr(u,'LocalFogVolume',None))
(OUT/'scene-before.json').write_text(json.dumps(r,indent=2))
print('PARITY_SCENE_PROBE_COMPLETE')
