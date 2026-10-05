import sys,json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/TeddyEncounter')
r={'actors':[],'material':{}}
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    c=a.get_component_by_class(u.LightComponent)
    if c:
        item={'name':a.get_actor_label(),'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation())}
        for k in ['intensity','light_color','intensity_units','mobility','visible','affects_world','cast_shadows','attenuation_radius','source_radius','use_inverse_squared_falloff']:
            try:item[k]=str(c.get_editor_property(k))
            except:pass
        r['actors'].append(item)
    if isinstance(a,u.PostProcessVolume):
        pp=a.settings;r['pp']={k:str(pp.get_editor_property(k)) for k in ['auto_exposure_method','auto_exposure_bias','camera_iso','camera_shutter_speed','depth_of_field_fstop','auto_exposure_apply_physical_camera_exposure','override_auto_exposure_bias','override_camera_iso','override_camera_shutter_speed','override_depth_of_field_fstop']}
    if a.get_actor_label()=='TE_MainTeddy':r['teddy_materials']=[str(x) for x in a.get_component_by_class(u.SkeletalMeshComponent).get_materials()]
mat=existing(NS+'/Materials/M_TeddyCloth')
r['material']['doc']=u.MaterialEditingLibrary.get_material_property_input_node.__doc__
for p in [u.MaterialProperty.MP_BASE_COLOR,u.MaterialProperty.MP_ROUGHNESS]:
    r['material'][str(p)]=str(M.get_material_property_input_node(mat,p))
(ROOT/'evidence/implementation/render-state.json').write_text(json.dumps(r,indent=2))
