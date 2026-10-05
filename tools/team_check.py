"""Read-only prerequisites and checkout integrity. No installs or engine launch."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from project_settings import load_settings

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    if not path.is_file():
        return None
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-handoff", action="store_true",
                        help="Hash Content against initial handoff, before intentional edits.")
    args = parser.parse_args()
    settings = load_settings(ROOT)
    checks = []

    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("python", sys.version_info >= (3, 11), sys.version.split()[0])
    for name, command in [("git", ["git", "--version"]), ("git_lfs", ["git", "lfs", "version"])]:
        if not shutil.which(command[0]):
            check(name, False, "Install Git with Git LFS yourself, then reopen the terminal.")
            continue
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        check(name, result.returncode == 0, (result.stdout or result.stderr).strip())
    engine = Path(settings["engine_root"])
    executable = engine / "Engine/Binaries/Win64/UnrealEditor.exe"
    check("editor", executable.is_file(), str(executable))
    version_file = engine / "Engine/Build/Build.version"
    if version_file.is_file():
        # Installed engine metadata, not generated project output.
        version = json.loads(version_file.read_text(encoding="utf-8-sig"))
        number = tuple(version.get(k) for k in ("MajorVersion", "MinorVersion", "PatchVersion"))
        check("engine_version", number == (5, 8, 3), ".".join(map(str, number)))
    else:
        check("engine_version", False, "UE5.8.3 metadata missing; set TEDDY_ENGINE_ROOT.")
    project_path = ROOT / settings["project"]
    project = json.loads(project_path.read_text(encoding="utf-8-sig")) if project_path.is_file() else {}
    enabled = {p["Name"] for p in project.get("Plugins", []) if p.get("Enabled")}
    check("blueprint_project", bool(project) and not project.get("Modules"), str(project_path))
    check("editor_plugins", {"PythonScriptPlugin", "EditorScriptingUtilities"} <= enabled,
          "Built-in editor Python and scripting plugins.")
    files = json.loads((ROOT / "evidence/team-handoff/content-sha256.json").read_text())["files"]
    missing = [name for name in files if not (ROOT / name).is_file()]
    check("complete_content", not missing, {"expected": len(files), "missing": missing})
    if args.verify_handoff:
        drift = [name for name, expected in files.items() if digest(ROOT / name) != expected]
        check("handoff_hashes", not drift, {"changed_missing_or_LFS_pointer": drift,
              "method": "Byte hashes only; no asset parsing"})
    else:
        pointers = [name for name in files if (ROOT / name).is_file() and (ROOT / name).stat().st_size < 256]
        check("content_hydrated", not pointers, {"possible_LFS_pointers": pointers, "fix": "git lfs pull"})
    for key in ("reference_video", "source_archive", "teddy_model"):
        path = ROOT / settings[key]
        check(key, digest(path) == settings[key + "_sha256"], str(path))
    for name in ["study/brief/index.html", "study/visuals/chamber-target-front.png",
                 "study/visuals/chamber-target-reverse.png", "evidence/chamber-qa/final/INDEPENDENT_REVIEW.md",
                 "evidence/chamber/20261005T095028Z/review.html"]:
        check("handoff_document", (ROOT / name).is_file(), name)
    passed = all(c["passed"] for c in checks)
    print(json.dumps({"passed": passed, "root": str(ROOT), "checks": checks,
                     "engine_started": False, "installs_performed": False,
                     "note": "File/prerequisite check, not a fresh gameplay or visual parity test."}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
