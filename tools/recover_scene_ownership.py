"""Recover our new empty map after the first scene script failed before its final save.
The map was absent in the pre-run inventory and baseline; this is not adoption of an external asset.
"""
from pathlib import Path
import json,hashlib,shutil
import unreal as u
R=Path(__file__).resolve().parents[1];p=R/'TeddyBlueprint/Content/Maps/TeddyEncounter.umap'
manifest=json.loads((R/'evidence/implementation/20261004-start/baseline-manifest.json').read_text())
assert not any(x['path']==p.relative_to(R).as_posix() for x in manifest['files'])
assert p.stat().st_size==6397,'Only the exact empty map created by our failed initial scene run is eligible'
backup=R/'evidence/implementation/scene-before-metadata.umap';assert not backup.exists();shutil.copy2(p,backup)
lev=u.get_editor_subsystem(u.LevelEditorSubsystem);assert lev.load_level('/Game/Maps/TeddyEncounter')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
assert all(a.get_class().get_name() in ['WorldSettings','Brush','LevelScriptActor','WorldDataLayers'] for a in actors),[a.get_class().get_name() for a in actors]
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.EditorAssetLibrary.set_metadata_tag(w,'TeddyEncounter.Owner','encounter-20261004')
assert u.EditorAssetLibrary.save_loaded_asset(w,False)
(R/'evidence/implementation/scene-ownership-recovery.json').write_text(json.dumps({'reason':__doc__,'before_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'actors':[a.get_class().get_name() for a in actors],'source_run':'evidence/editor-runs/20261004T203947-d49316'},indent=2))
