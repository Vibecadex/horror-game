import unreal as u,sys,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False,'assets':[],'blueprints':[]}
try:
    material=existing(NS+'/Materials/M_TeddyCloth');material.set_editor_property('used_with_skeletal_mesh',True);M.recompile_material(material);save(material)
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);assert lev.load_level('/Game/Maps/TeddyEncounter')
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();r['map']=world.get_path_name();r['game_mode']=str(world.get_world_settings().default_game_mode)
    for path in A.list_assets(NS,True,False):
        obj=existing(path);r['assets'].append({'path':path,'class':obj.get_class().get_name()})
        if isinstance(obj,u.Blueprint):compile(obj);r['blueprints'].append(path)
    allactors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors();r['actors']=len(allactors)
    r['named_encounter_actors']=[a.get_actor_label() for a in allactors if a.get_actor_label() in ['TE_MainTeddy','TE_CombatView'] or a.get_actor_label().startswith('TE_Stitchling')]
    assert len(r['named_encounter_actors'])==5
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True);assert lev.load_level('/Game/Maps/TeddyEncounter');r['reopened']=True;r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/final-asset-audit.json').write_text(json.dumps(r,indent=2))
