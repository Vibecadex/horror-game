import sys,json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
mat=existing(NS+'/Materials/M_TeddyCloth');base=M.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR);base.set_editor_property('const_b',1.7);M.recompile_material(mat);save(mat)
pawn=existing(NS+'/Blueprints/BP_EncounterPlayer');r={}
for name,(_,c) in components(pawn).items():
    if name=='ServiceRifle_GEN_VARIABLE':
        r['rifle_bounds']=str(c.static_mesh.get_bounds())
if A.get_metadata_tag(pawn,'RifleAttachment')!='hand_r':
    g=Graph(pawn);begin=next(n for n in g.g.list_all_nodes() if str(L.get_node_title(n))=='Event BeginPlay');links=begin.find_output_pin('then').list_connected_pins();begin.find_output_pin('then').break_pin_links()
    attach=g.call('SceneComponent.K2_AttachToComponent',self=(g.get('ServiceRifle'),'ServiceRifle'),Parent=(g.get('Mesh'),'Mesh'),SocketName='hand_r',LocationRule='SnapToTarget',RotationRule='SnapToTarget',ScaleRule='KeepRelative',bWeldSimulatedBodies='false');g.chain(begin,attach)
    for p in links:assert attach.find_output_pin('then').try_create_connection(p)
    A.set_metadata_tag(pawn,'RifleAttachment','hand_r')
compile(pawn)
lev=u.get_editor_subsystem(u.LevelEditorSubsystem);assert lev.load_level('/Game/Maps/TeddyEncounter')
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label()=='TE_FaceFill':a.point_light_component.set_editor_property('intensity',10000.)
    if a.get_actor_label()=='TE_Exposure':
        pp=a.settings;pp.set_editor_property('auto_exposure_bias',3.8);a.set_editor_property('settings',pp)
    if a.get_actor_label()=='TE_LowMist':a.get_component_by_class(u.ExponentialHeightFogComponent).set_editor_property('fog_density',.019)
assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(ROOT/'evidence/implementation/material-polish.json').write_text(json.dumps(r,indent=2))
