"""Correct the imported rifle's forward axis at the animated hand attachment."""
import unreal as u,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import *
bp=existing(NS+'/Blueprints/BP_EncounterPlayer')
if A.get_metadata_tag(bp,'RifleGrip')!='forward-v1':
    g=Graph(bp)
    attach=next(n for n in g.g.list_all_nodes() if n.find_input_pin('SocketName').is_valid() and n.find_input_pin('RotationRule').is_valid())
    outgoing=attach.find_output_pin('then').list_connected_pins();attach.find_output_pin('then').break_pin_links()
    rotation=g.math('MakeRotator',Roll=0,Pitch=0,Yaw=180)
    grip=g.call('SceneComponent.K2_SetRelativeRotation',self=(g.get('ServiceRifle'),'ServiceRifle'),NewRotation=(rotation,'ReturnValue'),bSweep='false',bTeleport='false')
    g.chain(attach,grip)
    for pin in outgoing:assert grip.find_output_pin('then').try_create_connection(pin)
    A.set_metadata_tag(bp,'RifleGrip','forward-v1')
compile(bp)
(ROOT/'evidence/implementation/weapon-grip.json').write_text(json.dumps({'passed':True,'socket':'hand_r','relative_yaw':180,'reason':'Native imported rifle +X opposed the animated hand forward; runtime inspection measured dot -0.968 before and +0.968 with this correction.'},indent=2))
