import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False,'before':{},'actors':{}}
try:
    for name in ['BP_TeddyBoss','BP_Stitchling','BP_EncounterPlayer']:
        bp=existing(NS+'/Blueprints/'+name);r['before'][name]={}
        for label,(_,c) in components(bp).items():
            if isinstance(c,u.StaticMeshComponent):
                r['before'][name][label]={k:str(c.get_editor_property(k)) for k in ['static_mesh','relative_location','relative_scale3d','override_materials']}
                if 'AttackWarning' in label:
                    c.set_editor_property('static_mesh',existing(NS+'/Arena/AttackRing'));c.set_editor_property('override_materials',[existing(NS+'/Materials/M_AttackWarning')]);c.set_editor_property('relative_location',u.Vector(0,0,-156 if name=='BP_Stitchling' else -226));c.set_editor_property('relative_scale3d',u.Vector(1.25,1.25,1) if name=='BP_Stitchling' else u.Vector(1,1,1));c.set_editor_property('visible',False)
        compile(bp)
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);assert lev.load_level('/Game/Maps/TeddyEncounter')
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label()=='TE_MainTeddy' or a.get_actor_label().startswith('TE_Stitchling'):
            r['actors'][a.get_actor_label()]={}
            for c in a.get_components_by_class(u.StaticMeshComponent):
                r['actors'][a.get_actor_label()][c.get_name()]={k:str(c.get_editor_property(k)) for k in ['static_mesh','relative_location','relative_scale3d','override_materials']}
                if 'AttackWarning' in c.get_name():
                    c.set_editor_property('static_mesh',existing(NS+'/Arena/AttackRing'));c.set_editor_property('override_materials',[existing(NS+'/Materials/M_AttackWarning')]);c.set_editor_property('relative_location',u.Vector(0,0,-156 if 'Stitchling' in a.get_actor_label() else -226));c.set_editor_property('relative_scale3d',u.Vector(1.25,1.25,1) if 'Stitchling' in a.get_actor_label() else u.Vector(1,1,1));c.set_editor_property('visible',False)
    assert lev.save_current_level();assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True);r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/component-repair.json').write_text(json.dumps(r,indent=2))
