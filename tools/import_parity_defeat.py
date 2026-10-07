"""Import a separate grounded collapse and replace only two saved death bindings."""
import hashlib, json, sys, traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import NS,A,L,own,existing,save,compile
OUT=ROOT/json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'];assert OUT.is_dir(),f'Run directory missing: {OUT}'
SOURCE=ROOT/'Assets/Adapted/Parity/DefeatGrounded/Teddy_DefeatGrounded.fbx'
DEST=NS+'/Parity/Animation/A_Teddy_DefeatGrounded';OLD=NS+'/Teddy/Defeat/A_Teddy_Defeat'
R={'passed':False,'source':str(SOURCE),'destination':DEST,'bindings':[]}

def hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'TeddyBlueprint/Content/TeddyEncounter/Teddy').rglob('*.uasset')}

def pins(bp):
    out=[]
    for graph in L.list_graphs(bp):
        for n in u.BlueprintGraphEditor.get_graph_editor(graph).list_all_nodes():
            p=n.find_input_pin('NewAnimToPlay')
            if p.is_valid() and not p.list_connected_pins():out.append((n,p,p.get_pin_value()))
    return out

def main():
    before=hashes();assert before
    manifest=json.loads((SOURCE.parent/'manifest.json').read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==manifest['fbx_sha256']
    level=u.get_editor_subsystem(u.LevelEditorSubsystem);assert level.load_level('/Game/Maps/TeddyEncounter')
    skeleton=existing(NS+'/Teddy/Idle/SK_Teddy_Skeleton');assert skeleton
    selected=[]
    for name in ['BP_TeddyBoss','BP_Stitchling']:
        bp=existing(NS+'/Blueprints/'+name)
        choices=[(n,p,v) for n,p,v in pins(bp) if OLD in v or DEST in v]
        expected=1 if name=='BP_TeddyBoss' else 2
        assert len(choices)==expected,(name,[(n.get_name(),v) for n,p,v in pins(bp)])
        selected.append((bp,choices))
    clip=existing(DEST)
    if not clip:
        u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
        opt=u.FbxImportUI()
        for k,v in {'automated_import_should_detect_type':False,'import_as_skeletal':True,'import_mesh':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,'import_animations':True,'import_materials':False,'import_textures':False,'create_physics_asset':False,'skeleton':skeleton,'override_animation_name':'A_Teddy_DefeatGrounded'}.items():opt.set_editor_property(k,v)
        for data in [opt.skeletal_mesh_import_data,opt.anim_sequence_import_data]:
            for k in ['convert_scene','convert_scene_unit','force_front_x_axis']:data.set_editor_property(k,True)
        data=opt.anim_sequence_import_data
        data.set_editor_property('use_default_sample_rate',False);data.set_editor_property('custom_sample_rate',60)
        data.set_editor_property('import_custom_attribute',False);data.set_editor_property('add_curve_metadata_to_skeleton',False)
        task=u.AssetImportTask();task.filename=str(SOURCE);task.destination_path=DEST.rsplit('/',1)[0];task.destination_name='A_Teddy_DefeatGrounded';task.automated=True;task.save=False;task.options=opt
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        assert len(task.imported_object_paths)==1,list(task.imported_object_paths)
        clip=own(A.load_asset(task.imported_object_paths[0]));assert clip.get_path_name().split('.')[0]==DEST;assert isinstance(clip,u.AnimSequence)
        save(clip)
    assert clip.get_editor_property('skeleton')==skeleton
    assert abs(clip.get_play_length()-manifest['duration_seconds'])<.025
    for bp,choices in selected:
        changed={n.get_name() for n,p,old in choices}
        other_before={node.get_name():value for node,pin,value in pins(bp) if node.get_name() not in changed}
        for n,p,old in choices:assert p.set_pin_value(DEST)
        compile(bp)
        current=pins(bp);other_after={node.get_name():value for node,pin,value in current if node.get_name() not in changed}
        assert other_before==other_after,'Unrelated animation binding changed'
        found=[value for node,pin,value in current if DEST in value];assert len(found)==len(choices)
        R['bindings'].append({'blueprint':bp.get_path_name(),'nodes':[n.get_name() for n,p,old in choices],'before':[old for n,p,old in choices],'after':found,'other_animation_bindings_unchanged':True})
    assert level.save_current_level();assert level.load_level('/Game/Maps/TeddyEncounter')
    after=hashes();assert after==before,'Original Teddy assets changed'
    R.update(passed=True,length=clip.get_play_length(),skeleton=skeleton.get_path_name(),original_asset_count=len(before),original_asset_hashes_unchanged=True,source_sha256=manifest['fbx_sha256'],original_hashes=before)

if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/'defeat-grounded-import.json').write_text(json.dumps(R,indent=2))
