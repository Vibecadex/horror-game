"""Unreal editor-only GLB import check; uses owned, isolated setup content."""
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

import unreal

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / "tools/project-settings.json").read_text(encoding="utf-8-sig"))
SOURCE = ROOT / SETTINGS["teddy_model"]
SOURCE_HASH = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if SOURCE_HASH != SETTINGS["teddy_model_sha256"]:
    raise RuntimeError("Original teddy source hash changed")
REPORT = Path(os.environ["BOSSSHOT_SETUP_REPORT"]).resolve()
if not REPORT.is_relative_to((ROOT / "evidence/setup").resolve()):
    raise RuntimeError("Setup report path escapes the workspace evidence directory")
DESTINATION = "/Game/SetupValidation/HorrorTeddy_" + SOURCE_HASH[:8]
TAG = "BossShot.SetupSourceSha256"
report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "passed": False,
          "source_sha256": SOURCE_HASH, "destination": DESTINATION, "assets": [],
          "rigged": False, "animated": False, "final_art_accepted": False, "preserved_incomplete_destinations": []}


def complete_owned_assets(objects):
    if any(obj is None or unreal.EditorAssetLibrary.get_metadata_tag(obj, TAG) != SOURCE_HASH for obj in objects):
        return False
    meshes = [obj for obj in objects if isinstance(obj, unreal.StaticMesh)]
    if not meshes or not any(isinstance(obj, unreal.Texture) for obj in objects):
        return False
    if not any(isinstance(obj, unreal.MaterialInterface) for obj in objects):
        return False
    return all(mesh.get_editor_property("static_materials") and
               all(slot.get_editor_property("material_interface") is not None
                   for slot in mesh.get_editor_property("static_materials")) for mesh in meshes)

try:
    base_destination = DESTINATION
    # An interrupted import may have saved files before their ownership tags.
    # Preserve every such folder and use a fresh namespace instead of deleting it.
    for retry in range(100):
        DESTINATION = base_destination + ("_retry_%02d" % retry if retry else "")
        existing = unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=True, include_folder=False)
        if not existing:
            break
        objects = [unreal.EditorAssetLibrary.load_asset(path) for path in existing]
        if complete_owned_assets(objects):
            break
        report["preserved_incomplete_destinations"].append(DESTINATION)
    else:
        raise RuntimeError("No free isolated setup namespace; existing assets were preserved")
    report["destination"] = DESTINATION
    if existing:
        report["operation"] = "reopened_owned_assets"
    else:
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(SOURCE))
        task.set_editor_property("destination_path", DESTINATION)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", True)
        task.set_editor_property("async_", False)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        objects = list(task.get_objects())
        if not objects:
            raise RuntimeError("Unreal returned no imported objects")
        for obj in objects:
            if not obj.get_path_name().startswith(DESTINATION + "/"):
                raise RuntimeError("Importer created an object outside the isolated setup destination")
            unreal.EditorAssetLibrary.set_metadata_tag(obj, TAG, SOURCE_HASH)
            if not unreal.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False):
                raise RuntimeError("Could not save imported asset " + obj.get_path_name())
        report["operation"] = "imported_and_saved"
    meshes = [obj for obj in objects if isinstance(obj, unreal.StaticMesh)]
    textures = [obj for obj in objects if isinstance(obj, unreal.Texture)]
    materials = [obj for obj in objects if isinstance(obj, unreal.MaterialInterface)]
    if not meshes or not textures or not materials:
        raise RuntimeError("Expected a static mesh, material and texture from the teddy GLB")
    for mesh in meshes:
        slots = mesh.get_editor_property("static_materials")
        if not slots or any(slot.get_editor_property("material_interface") is None for slot in slots):
            raise RuntimeError("Imported mesh has missing material assignments")
    report.update({"meshes": len(meshes), "materials": len(materials), "textures": len(textures),
                   "assets": [{"path": obj.get_path_name(), "class": obj.get_class().get_name()} for obj in objects],
                   "passed": True})
    unreal.log("BOSSSHOT_SETUP_IMPORT_PASSED " + json.dumps(report))
except Exception as exc:
    report["error"] = str(exc)
    raise
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
