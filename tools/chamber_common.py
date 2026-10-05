"""Shared bounded chamber authoring helpers; import has no scene mutation."""
import json,sys
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from encounter_authoring import A,L,M,NS,own,save,existing,asset,Graph,components,component,compile
from apply_parity_look import node,link,bind,scalar,rgb,mul,blend,channel,add
OUT=(ROOT/Path(json.loads((ROOT/'evidence/chamber/current-run.json').read_text())['out'])).resolve()
P=json.loads((ROOT/'study/chamber-settings.json').read_text())
MAP='/Game/Maps/TeddyEncounter';DEST=NS+'/Chamber'
LEVEL=u.get_editor_subsystem(u.LevelEditorSubsystem);ACTORS=u.get_editor_subsystem(u.EditorActorSubsystem)
def newmat(name):
    m=asset('Chamber/Materials/M_Chamber_'+name,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m);return m
def spawn(cls,name,loc,rot=None):
    a=ACTORS.spawn_actor_from_class(cls,u.Vector(*loc),rot or u.Rotator(),transient=False);assert a
    a.set_actor_label('TE_Chamber_'+name);a.set_editor_property('tags',['TeddyEncounterOwned','ChamberOwned'])
    a.set_folder_path('TeddyEncounter/Chamber');return a
def begin():
    assert (OUT/'baseline.json').is_file();assert LEVEL.load_level(MAP)
def finish():assert LEVEL.save_current_level();assert LEVEL.load_level(MAP)
