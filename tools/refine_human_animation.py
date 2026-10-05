import sys,json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
r={'passed':False,'samples':[],'nodes':[]}
try:
    bs=duplicate('/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run','Player/BS_RifleLocomotion')
    samples=bs.get_editor_property('sample_data');idle=A.load_asset('/Game/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS')
    for sample in samples:
        old=sample.get_editor_property('animation');name=old.get_name();candidate=name.replace('Unarmed','Rifle').replace('Run','Jog')
        folder='Walk' if 'Walk' in candidate else 'Jog'
        anim=A.load_asset('/Game/Characters/Mannequins/Anims/Rifle/'+folder+'/'+candidate) if any(x in candidate for x in ['Walk','Jog']) else idle
        if not anim:anim=idle
        sample.set_editor_property('animation',anim);r['samples'].append([old.get_path_name(),anim.get_path_name()])
    bs.set_editor_property('sample_data',samples);save(bs)
    abp=duplicate('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed','Player/ABP_EncounterRifle')
    for gr in L.list_graphs(abp):
        for n in u.BlueprintGraphEditor.get_graph_editor(gr).list_all_nodes():
            if n.get_class().get_name()=='AnimGraphNode_BlendSpacePlayer':
                node=n.get_editor_property('node');node.set_editor_property('blend_space',bs);n.set_editor_property('node',node);r['nodes'].append(n.get_name())
            if gr.get_name()=='Idle' and n.get_class().get_name()=='AnimGraphNode_SequencePlayer':
                node=n.get_editor_property('node');node.set_editor_property('sequence',idle);n.set_editor_property('node',node);r['nodes'].append(n.get_name())
    compile(abp)
    pawn=existing(NS+'/Blueprints/BP_EncounterPlayer')
    for _,c in components(pawn).values():
        if isinstance(c,u.SkeletalMeshComponent):c.set_anim_instance_class(L.generated_class(abp))
        if c.get_name()=='ServiceRifle_GEN_VARIABLE':c.set_editor_property('relative_location',u.Vector(17,43,123));c.set_editor_property('relative_rotation',u.Rotator(yaw=90))
    compile(pawn);r['passed']=True
except Exception:r['error']=traceback.format_exc();raise
finally:(ROOT/'evidence/implementation/human-animation.json').write_text(json.dumps(r,indent=2))
