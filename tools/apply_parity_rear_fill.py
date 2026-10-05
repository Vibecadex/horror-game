"""Close the rear-centre character-light gap without altering fog or surfaces."""
import hashlib,json,shutil,sys,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from apply_parity_look import spawn,light_settings
OUT=Path(json.loads((ROOT/'evidence/parity/current-run.json').read_text())['out'])
SPEC=json.loads((ROOT/'study/parity-atmosphere-settings.json').read_text())['rear_center_character_fill']
LABEL='TE_Parity_RearCenterCharacterFill'
R={'passed':False,'purpose':'Repair independently observed rear-centre character contrast gap','settings':SPEC,'material_camera_fog_key_and_gameplay_changes':False}

def main():
    source=ROOT/'TeddyBlueprint/Content/Maps/TeddyEncounter.umap'
    backup=OUT/'before-rear-readability.umap'
    if not backup.exists():
        shutil.copy2(source,backup)
        assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    R['before_map_backup']=str(backup)
    level=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert level.load_level('/Game/Maps/TeddyEncounter')
    found=[a for a in actors.get_all_level_actors() if a.get_actor_label()==LABEL]
    assert len(found)<=1
    if found:
        actor=found[0];assert isinstance(actor,u.PointLight) and 'ParityOwned' in [str(t) for t in actor.tags]
        actor.set_actor_location(u.Vector(*SPEC['location']),False,False)
    else:actor=spawn(u.PointLight,'RearCenterCharacterFill',SPEC['location'])
    light=actor.get_component_by_class(u.PointLightComponent)
    light_settings(light,SPEC['intensity'],SPEC['color'],SPEC['radius'],SPEC['source'],0.)
    light.set_lighting_channels(False,True,False)
    light.set_editor_property('indirect_lighting_intensity',0.)
    light.set_editor_property('specular_scale',0.)
    assert level.save_current_level();assert level.load_level('/Game/Maps/TeddyEncounter')
    actor=next(a for a in actors.get_all_level_actors() if a.get_actor_label()==LABEL)
    light=actor.get_component_by_class(u.PointLightComponent);channels=light.get_editor_property('lighting_channels')
    assert not channels.channel0 and channels.channel1 and not channels.channel2
    for key,value in [('intensity',SPEC['intensity']),('attenuation_radius',SPEC['radius']),('source_radius',SPEC['source']),('volumetric_scattering_intensity',0.),('indirect_lighting_intensity',0.),('specular_scale',0.)]:
        assert abs(light.get_editor_property(key)-value)<.01,key
    assert (actor.get_actor_location()-u.Vector(*SPEC['location'])).length()<.01
    R.update(passed=True,label=LABEL,lighting_channels=str(channels),map_sha256=hashlib.sha256(source.read_bytes()).hexdigest())

if __name__=='__main__':
    try:main()
    except Exception:R['error']=traceback.format_exc();raise
    finally:(OUT/('rear-fill-'+str(SPEC['intensity'])+'-authoring.json')).write_text(json.dumps(R,indent=2))
