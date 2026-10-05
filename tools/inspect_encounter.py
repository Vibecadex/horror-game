"""Read-only starter graph/component inventory plus an isolated evidence map."""
import json, traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/implementation/starter-inventory.json'
L=u.BlueprintEditorLibrary
A=u.EditorAssetLibrary
report={'blueprints':{},'api':{}}
def props(obj,names):
    result={}
    for n in names:
        try: result[n]=str(obj.get_editor_property(n))
        except Exception: pass
    return result
try:
    for path in A.list_assets('/Game/Variant_TwinStick',True):
        bp=A.load_asset(path)
        if not isinstance(bp,u.Blueprint): continue
        item={'parent':str(L.get_blueprint_parent_class(bp)),'graphs':{},'components':[]}
        cdo=u.get_default_object(L.generated_class(bp))
        item['defaults']=props(cdo,['default_pawn_class','player_controller_class','hud_class','MaxHealth','Health','ProjectileClass','DashCooldown','DashSpeed','EnemyClass','show_mouse_cursor'])
        for gr in L.list_graphs(bp):
            ge=u.BlueprintGraphEditor.get_graph_editor(gr)
            nodes=[]
            for node in ge.list_all_nodes():
                pins=[]
                for p in node.list_input_pins()+node.list_output_pins():
                    pins.append({'name':str(p.get_pin_name()),'dir':str(p.get_pin_direction()),'type':p.get_pin_type_display_string(),'value':p.get_pin_value(),'links':[(q.get_owning_node().get_name(),str(q.get_pin_name())) for q in p.list_connected_pins()]})
                nodes.append({'id':node.get_name(),'class':node.get_class().get_name(),'title':str(L.get_node_title(node)) if hasattr(L,'get_node_title') else '', 'pins':pins})
            item['graphs'][gr.get_name()]=nodes
        sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
        for h in sub.k2_gather_subobject_data_for_blueprint(bp):
            d=u.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            o=u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
            if o:
                item['components'].append({'name':o.get_name(),'class':o.get_class().get_name(),'properties':props(o,['relative_location','relative_rotation','relative_scale3d','static_mesh','skeletal_mesh_asset','anim_class','animation_mode','target_arm_length','field_of_view','enable_camera_lag','max_walk_speed','jump_z_velocity','material_overrides'])})
        report['blueprints'][path]=item
    for name in ['BlueprintEditorLibrary','BlueprintGraphEditor','AutomationLibrary','SubobjectDataSubsystem','SubobjectDataBlueprintFunctionLibrary','InputMappingContext','EditorAssetLibrary']:
        cls=getattr(u,name)
        report['api'][name]={n:str(getattr(cls,n).__doc__) for n in dir(cls) if any(t in n for t in ['variable','title','action','node','shader','loading','subobject','map_key','consolidate','replace'])}
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem)
    target='/Game/SetupValidation/Evidence_20261004/StarterEvidence'
    assert not A.does_asset_exist(target), 'Fresh namespace required'
    assert lev.new_level_from_template(target,'/Game/Variant_TwinStick/LVL_TwinStick')
    assert lev.load_level(target)
    report['map']=target
    report['actors']=[{'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':str(a.get_actor_location())} for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()]
    assert lev.save_current_level()
    assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,False)
    report['passed']=True
except Exception:
    report['error']=traceback.format_exc()
    raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,default=str))
