"""Copy the installed Epic Blueprint Twin Stick template to a fresh local candidate.

Never modifies the installed engine, the native BossShot experiment, or an existing candidate.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path(json.loads((ROOT / "tools/project-settings.json").read_text(encoding="utf-8-sig"))["engine_root"])
TARGET = ROOT / "TeddyBlueprint"


def main():
    if TARGET.exists():
        raise RuntimeError(f"Preserving existing candidate: {TARGET}")
    template = ENGINE / "Templates/TP_TopDownBP"
    resources = ENGINE / "Templates/TemplateResources"
    pairs = [(template / "Content", TARGET / "Content")]
    for quality, name in [("High", "Characters"), ("High", "LevelPrototyping"),
                          ("High", "Input"), ("Standard", "Cursor"), ("Standard", "Variant_TwinStick")]:
        pairs.append((resources / quality / name / "Content", TARGET / "Content" / name))
    for name in ("__ExternalActors__", "__ExternalObjects__"):
        pairs.append((resources / "Standard/Variant_TwinStick" / name,
                      TARGET / "Content" / name / "Variant_TwinStick"))
    manifest = []
    for source, destination in pairs:
        for path in source.rglob("*"):
            if path.is_file():
                target = destination / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                manifest.append({"source": str(path), "destination": str(target.relative_to(ROOT)),
                                 "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    (TARGET / "Config").mkdir(exist_ok=True)
    for name in ("DefaultEngine.ini", "DefaultGame.ini", "DefaultInput.ini"):
        source = template / "Config" / name
        value = source.read_text(encoding="utf-8-sig").replace("TP_TopDownBP", "TeddyBlueprint")
        value = value.replace("/Game/TopDown/Lvl_TopDown.Lvl_TopDown",
                              "/Game/Variant_TwinStick/LVL_TwinStick.LVL_TwinStick")
        value = value.replace("/Game/TopDown/Blueprints/BP_TopDownGameMode.BP_TopDownGameMode_C",
                              "/Game/Variant_TwinStick/Blueprints/BP_TwinStickGameMode.BP_TwinStickGameMode_C")
        (TARGET / "Config" / name).write_text(value, encoding="utf-8")
    project = json.loads((template / "TP_TopDownBP.uproject").read_text())
    project.update(EngineAssociation="5.8", Description="Blueprint-only encounter workspace; Epic Twin Stick starter.")
    project["Plugins"].extend([
        {"Name": "PythonScriptPlugin", "Enabled": True, "TargetAllowList": ["Editor"]},
        {"Name": "EditorScriptingUtilities", "Enabled": True, "TargetAllowList": ["Editor"]}])
    (TARGET / "TeddyBlueprint.uproject").write_text(json.dumps(project, indent=2), encoding="utf-8")
    evidence = ROOT / "evidence/setup/blueprint-candidate"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "template-provenance.json").write_text(json.dumps({
        "engine": str(ENGINE), "source": "Installed Epic Top Down Blueprint Twin Stick variant",
        "license": "Unreal Engine template content; subject to applicable Epic license, not CC0",
        "files": manifest, "project_has_native_module": False,
        "original_native_project_preserved": True}, indent=2), encoding="utf-8")
    print(f"Prepared {TARGET}; {len(manifest)} copied template assets.")


if __name__ == "__main__":
    main()
