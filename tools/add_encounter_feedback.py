import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False}
try:
    sounds={}
    for name in ['Rifle','Slam','ClothHit','RoomTone']:
        sound=existing(NS+'/Audio/'+name)
        if not sound:
            task=u.AssetImportTask();task.filename=str(ROOT/'Assets/Adapted/Audio'/(name+'.wav'));task.destination_path=NS+'/Audio';task.destination_name=name;task.automated=True;task.save=True
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths;sound=own(A.load_asset(task.imported_object_paths[0]))
        if name=='RoomTone':sound.set_editor_property('looping',True)
        save(sound);sounds[name]=sound
    pawn=existing(NS+'/Blueprints/BP_EncounterPlayer');assert A.get_metadata_tag(pawn,'FeedbackAuthored')!='v1'
    muzzle=component(pawn,'MuzzleFlash',u.StaticMeshComponent,'CapsuleComponent');muzzle.set_editor_property('static_mesh',u.load_asset('/Engine/BasicShapes/Sphere'));muzzle.set_editor_property('override_materials',[existing(NS+'/Materials/M_Muzzle')]);muzzle.set_editor_property('relative_location',u.Vector(83,0,30));muzzle.set_editor_property('relative_scale3d',u.Vector(.22,.08,.08));muzzle.set_editor_property('visible',False);muzzle.set_editor_property('cast_shadow',False);muzzle.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    g=Graph(pawn);spawn=next(n for n in g.g.list_all_nodes() if n.get_class().get_name()=='K2Node_SpawnActorFromClass');old=spawn.find_output_pin('then').list_connected_pins();spawn.find_output_pin('then').break_pin_links()
    loc=g.call('Actor.K2_GetActorLocation');sound=g.call('GameplayStatics.PlaySoundAtLocation',Sound=sounds['Rifle'].get_path_name(),Location=(loc,'ReturnValue'),VolumeMultiplier='.26')
    show=g.call('SceneComponent.SetVisibility',self=(g.get('MuzzleFlash'),'MuzzleFlash'),bNewVisibility='true');delay=g.call('KismetSystemLibrary.Delay',Duration='.05');hide=g.call('SceneComponent.SetVisibility',self=(g.get('MuzzleFlash'),'MuzzleFlash'),bNewVisibility='false');g.chain(spawn,sound,show,delay,hide)
    for pin in old:assert hide.find_output_pin('then').try_create_connection(pin)
    # Hide the laser after player defeat, alongside the existing saved death sequence.
    death=next(n for n in g.g.list_all_nodes() if n.find_input_pin('NewAnimToPlay').is_valid() and 'MM_Death' in str(n.find_input_pin('NewAnimToPlay').get_pin_value()))
    hideaim=g.call('SceneComponent.SetVisibility',self=(g.get('AimGuide'),'AimGuide'),bNewVisibility='false');g.chain(death,hideaim)
    compile(pawn);A.set_metadata_tag(pawn,'FeedbackAuthored','v1');save(pawn)
    for name in ['BP_TeddyBoss','BP_Stitchling']:
        bp=existing(NS+'/Blueprints/'+name);g=Graph(bp)
        for n in list(g.g.list_all_nodes()):
            if n.get_class().get_name()=='K2Node_VariableSet' and str(L.get_node_title(n))=='Set Attacks':
                old=n.find_output_pin('then').list_connected_pins();n.find_output_pin('then').break_pin_links();loc=g.call('Actor.K2_GetActorLocation');slam=g.call('GameplayStatics.PlaySoundAtLocation',Sound=sounds['Slam'].get_path_name(),Location=(loc,'ReturnValue'),VolumeMultiplier='.5' if name=='BP_TeddyBoss' else '.18');g.chain(n,slam)
                for p in old:assert slam.find_output_pin('then').try_create_connection(p)
        compile(bp)
    camera=existing(NS+'/Blueprints/BP_CombatCamera');amb=component(camera,'RoomTone',u.AudioComponent);amb.set_editor_property('sound',sounds['RoomTone']);amb.set_editor_property('volume_multiplier',.5);amb.set_editor_property('auto_activate',True);compile(camera)
    r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/feedback-build.json').write_text(json.dumps(r,indent=2))
