"""Runs inside Unreal's installed Python editor plugin; no native project module."""
from pathlib import Path
import json
import os
import traceback
import unreal

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("TEDDY_INSPECTION_REPORT", str(ROOT / "evidence/setup/blueprint-candidate/inspection.json")))
report = {"passed": False, "blueprints": [], "maps": [], "input_mappings": []}
try:
    assets = unreal.EditorAssetLibrary.list_assets("/Game/Variant_TwinStick", recursive=True)
    for path in assets:
        obj = unreal.EditorAssetLibrary.load_asset(path)
        if obj is None:
            raise RuntimeError(f"Could not load {path}")
        if isinstance(obj, unreal.Blueprint):
            compiled = unreal.BlueprintEditorLibrary.compile_blueprint(obj)
            generated = unreal.BlueprintEditorLibrary.generated_class(obj)
            report["blueprints"].append({"asset": path, "compiled": compiled,
                                         "generated_class": str(generated),
                                         "parent": str(unreal.BlueprintEditorLibrary.get_blueprint_parent_class(obj))})
            if compiled is False or generated is None:
                raise RuntimeError(f"Blueprint failed compilation: {path}")
        elif isinstance(obj, unreal.InputMappingContext):
            mappings = []
            for entry in obj.get_editor_property("default_key_mappings").get_editor_property("mappings"):
                mappings.append({"action": entry.get_editor_property("action").get_path_name(),
                                 "key": str(unreal.InputLibrary.key_get_display_name(entry.get_editor_property("key")))})
            report["input_mappings"].append({"asset": path, "mappings": mappings})
    world = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Variant_TwinStick/LVL_TwinStick")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    report["maps"].append({"loaded": world, "actor_count": len(actors),
                            "actors": [{"name": a.get_actor_label(), "class": a.get_class().get_path_name()}
                                       for a in actors]})
    if not world or len(actors) < 10:
        raise RuntimeError("Template level did not load its world content")
    report["api"] = {name: [x for x in dir(getattr(unreal, name)) if not x.startswith("_")]
                       for name in ("BlueprintEditorLibrary", "BlueprintGraphEditor", "EditorLevelLibrary", "AutomationLibrary",
                                    "EnhancedInputLocalPlayerSubsystem", "EditorActorSubsystem") if hasattr(unreal, name)}
    report["passed"] = True
except Exception:
    report["error"] = traceback.format_exc()
    unreal.log_error(report["error"])
finally:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
if not report["passed"]:
    raise RuntimeError(report.get("error", "Candidate inspection failed"))
