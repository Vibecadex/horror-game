"""One-command Astra launch and bounded, evidence-backed workstation checks."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import tomllib
import uuid
import zipfile
from project_settings import load_settings

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = load_settings(ROOT)
EVIDENCE = ROOT / "evidence/setup"
HIDDEN = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


def sha256(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def tool(name):
    if name == "codex.exe" and SETTINGS.get("codex_executable"):
        executable = ROOT / SETTINGS["codex_executable"]
        if not executable.is_file():
            raise RuntimeError("The prepared Codex CLI is missing. Read START_HERE.md for the user-run install command.")
        return str(executable)
    result = shutil.which(name)
    if not result:
        raise RuntimeError(f"Required tool is missing from PATH: {name}")
    return result


def capture(args, timeout=30):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=HIDDEN)
    if result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} failed ({result.returncode}): "
                           + (result.stderr or result.stdout)[-1800:])
    return (result.stdout + result.stderr).strip()


def tool_environment():
    cache = ROOT / ".tool-cache"
    for name in ("temp", "dotnet", "nuget", "unreal-user", "derived-data"):
        (cache / name).mkdir(parents=True, exist_ok=True)
    return dict(os.environ, TMP=str(cache / "temp"), TEMP=str(cache / "temp"),
                DOTNET_CLI_HOME=str(cache / "dotnet"), NUGET_PACKAGES=str(cache / "nuget"))


def cli_environment():
    environment = tool_environment()
    if environment.get("TERM", "").lower() in ("", "dumb"):
        environment["TERM"] = "xterm-256color"
    # Keep shell version checks on the same CLI as the actual implementation run.
    environment["PATH"] = str(Path(tool("codex.exe")).parent) + os.pathsep + environment.get("PATH", "")
    environment["CODEX_MANAGED_BY_NPM"] = "1"
    environment["CODEX_MANAGED_PACKAGE_ROOT"] = str(ROOT / ".tool-cache/codex-cli/node_modules/@openai/codex")
    return environment


def codex_version_check():
    executable = tool("codex.exe")
    version = capture([executable, "--version"]).splitlines()[0]
    expected = SETTINGS.get("codex_version")
    if expected and version != f"codex-cli {expected}":
        raise RuntimeError(f"Prepared Codex version mismatch: expected {expected}, got {version}")
    return {"path": executable, "version": version}


def unreal_cache_paths():
    if SETTINGS.get("workflow") == "unreal_blueprint_5_8":
        return []
    # UE 5.8's initial UBT trace path is fixed to its own Windows cache folder.
    # Add only that folder for this invocation; never add the source-reference folder.
    return [Path(SETTINGS["unreal_build_cache"])]


def cache_config_argument():
    # --add-dir creates split root sets that this Windows unelevated CLI cannot
    # enforce. Use its documented unified writable_roots setting instead.
    config_directory = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config_file = config_directory / "config.toml"
    configured = []
    if config_file.is_file():
        config = tomllib.loads(config_file.read_text(encoding="utf-8-sig"))
        configured = config.get("sandbox_workspace_write", {}).get("writable_roots", [])
    roots = list(dict.fromkeys([Path(p).as_posix() for p in configured] +
                              [p.as_posix() for p in unreal_cache_paths()]))
    return "sandbox_workspace_write.writable_roots=" + json.dumps(roots)


def unreal_local_arguments():
    cache = ROOT / ".tool-cache"
    return ["-DDC=InstalledNoZenLocalFallback", f"-LocalDataCachePath={cache / 'derived-data'}",
            f"-UserDir={cache / 'unreal-user'}"]


def run_logged(args, log, timeout=900, env=None):
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                   env=env, creationflags=HIDDEN)
        try:
            code = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Stop only the process tree created by this invocation.
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=HIDDEN)
            else:
                process.terminate()
            process.wait(timeout=30)
            raise RuntimeError(f"Stopped timed-out/interrupted check. See {log}")
    if code:
        raise RuntimeError(f"Check failed with exit {code}. See {log}")
    return {"passed": True, "exit_code": code, "log": str(log)}


def require_file(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Required file is missing or empty: {path}")
    return path


def inspect_glb(path):
    data = Path(path).read_bytes()
    if len(data) < 20:
        raise RuntimeError("The teddy GLB is truncated")
    magic, version, size, chunk_size, chunk_type = struct.unpack_from("<4sIIII", data)
    if magic != b"glTF" or version != 2 or size != len(data) or chunk_type != 0x4E4F534A:
        raise RuntimeError("The teddy file is not a valid GLB 2 container")
    scene = json.loads(data[20:20 + chunk_size])
    if not scene.get("meshes") or not scene.get("images"):
        raise RuntimeError("The teddy GLB has no mesh or texture")
    return {"meshes": len(scene["meshes"]), "images": len(scene["images"]),
            "skeletons": len(scene.get("skins", [])), "animations": len(scene.get("animations", []))}


def quick_check():
    checks = []

    def check(name, action):
        try:
            value = action()
            checks.append({"name": name, "passed": True, "detail": value})
        except Exception as exc:
            checks.append({"name": name, "passed": False, "detail": str(exc)})

    check("codex.exe", codex_version_check)
    for name, args in [("pwsh.exe", ["--version"]),
                       ("node.exe", ["--version"]), ("ffmpeg.exe", ["-version"]),
                       ("ffprobe.exe", ["-version"]), ("blender.exe", ["--version"])]:
        check(name, lambda name=name, args=args: {
            "path": tool(name), "version": capture([tool(name), *args]).splitlines()[0]})
    check("python", lambda: {"path": sys.executable, "version": sys.version.split()[0]})
    check("context7_runner", lambda: tool("npx.cmd"))
    check("codex_sign_in", lambda: capture([tool("codex.exe"), "login", "status"]))

    def check_project():
        project = json.loads(require_file(ROOT / SETTINGS["project"]).read_text(encoding="utf-8-sig"))
        enabled = {p["Name"] for p in project.get("Plugins", []) if p.get("Enabled")}
        for name in ("PythonScriptPlugin", "EditorScriptingUtilities"):
            if name not in enabled:
                raise RuntimeError(f"Project plugin is not enabled: {name}")
        if SETTINGS.get("workflow") == "unreal_blueprint_5_8" and project.get("Modules"):
            raise RuntimeError("The prepared Blueprint workflow must not depend on a native project module")
        return {"path": str(ROOT / SETTINGS["project"]), "engine": project["EngineAssociation"],
                "native_modules": len(project.get("Modules", []))}
    check("unreal_project", check_project)
    engine = Path(SETTINGS["engine_root"])
    for relative in ["Engine/Binaries/Win64/UnrealEditor.exe", "Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
                     "Engine/Source/Editor/BlueprintEditorLibrary/Private/BlueprintEditorLibrary/BlueprintGraphEditor.h",
                     "Engine/Plugins/Experimental/PythonScriptPlugin/PythonScriptPlugin.uplugin",
                     "Engine/Plugins/Editor/EditorScriptingUtilities/EditorScriptingUtilities.uplugin"]:
        check(Path(relative).name, lambda relative=relative: str(require_file(engine / relative)))
    check("engine_version", lambda: json.loads((engine / "Engine/Build/Build.version").read_text(encoding="utf-8-sig")))

    def compiler():
        vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
        installation = capture([str(require_file(vswhere)), "-latest", "-products", "*", "-requires",
                                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"])
        if not installation:
            raise RuntimeError("Visual Studio C++ Build Tools are not installed")
        compilers = sorted((Path(installation) / "VC/Tools/MSVC").glob("*/bin/Hostx64/x64/cl.exe"))
        sdk = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits/10/Include"
        sdks = [p.parent.parent for p in sdk.glob("*/um/Windows.h")]
        if not compilers or not sdks:
            raise RuntimeError("MSVC compiler or Windows SDK headers are missing")
        return {"compiler": str(compilers[-1]), "windows_sdk": str(sorted(sdks)[-1])}
    # The preserved native experiment uses MSVC; the selected Blueprint workflow does not.
    if SETTINGS.get("workflow") != "unreal_blueprint_5_8":
        check("cpp_toolchain", compiler)

    for name in ("reference_video", "source_archive", "teddy_model"):
        def verify_hash(name=name):
            path = ROOT / SETTINGS[name]
            actual = sha256(require_file(path))
            if actual != SETTINGS[name + "_sha256"]:
                raise RuntimeError(f"Original input hash changed: {path}. Inspect the change before updating settings.")
            return {"path": str(path), "sha256": actual}
        check(name, verify_hash)
    for relative in ["AGENTS.md", "MASTER_PROMPT.md", "RUN_ASTRA.md", "REFERENCE_BRIEF.md", "WORK_STATUS.md",
                     "tools/verify_blueprint_authoring.py", "tools/verify_blueprint_runtime.py",
                     "tools/BLUEPRINT_WORKFLOW.md", "tools/verify_setup_import.py", *SETTINGS["reference_images"]]:
        check(relative, lambda relative=relative: str(require_file(ROOT / relative)))
    check("teddy_mesh", lambda: inspect_glb(ROOT / SETTINGS["teddy_model"]))

    def reference_probe():
        raw = capture([tool("ffprobe.exe"), "-v", "error", "-show_entries",
                       "format=duration:stream=codec_type,width,height", "-of", "json", SETTINGS["reference_video"]])
        info = json.loads(raw)
        if not any(s.get("codec_type") == "video" for s in info.get("streams", [])):
            raise RuntimeError("No decodable video stream")
        return info
    check("reference_video_decode", reference_probe)

    def disk():
        free = shutil.disk_usage(ROOT).free
        if free < 10 * 1024**3:
            raise RuntimeError("Less than 10 GiB free for build and capture work")
        return {"free_gib": round(free / 1024**3, 1)}
    check("working_space", disk)
    result = {"checked_at_utc": utc(), "ready": all(c["passed"] for c in checks),
              "model": SETTINGS["model"], "reasoning_effort": SETTINGS["reasoning_effort"], "checks": checks,
              "implementation_complete": False,
              "notes": ["The teddy still needs visual refinement, rigging and animation.",
                        "Source audio has not been auditioned.",
                        "The user-authorized launcher uses Full Access and never asks for routine command approval."]}
    write_json(EVIDENCE / "latest-check.json", result)
    return result


def print_check(result):
    for item in result["checks"]:
        if not item["passed"]:
            print(f"MISSING: {item['name']}: {item['detail']}")
    print(f"Quick prerequisites {'READY' if result['ready'] else 'NEED ATTENTION'}: "
          f"{sum(c['passed'] for c in result['checks'])}/{len(result['checks'])} checks passed.")
    print(f"Details: {EVIDENCE / 'latest-check.json'}")
    receipt = EVIDENCE / "latest-verification.json"
    if receipt.is_file():
        previous = json.loads(receipt.read_text(encoding="utf-8"))
        state = 'PASSED' if previous.get('ready') else 'DID NOT PASS'
        print(f"Last full verification: {state} ({previous.get('finished_at_utc', 'time unknown')}).")
        if not previous.get("ready"):
            print(f"Implementation launch is not verified. Read {ROOT / 'SETUP_STATUS.md'}.")
    else:
        print("Full authoring/import/render/Astra verification has not yet completed.")


def require_launch_verification():
    receipt = EVIDENCE / "latest-verification.json"
    result = json.loads(receipt.read_text(encoding="utf-8")) if receipt.is_file() else {}
    if (not result.get("ready") or result.get("project") != SETTINGS["project"] or
            result.get("workflow") != SETTINGS.get("workflow")):
        raise RuntimeError("The selected project's implementation launcher is not yet verified. Read SETUP_STATUS.md "
                           "and rerun the full validator after resolving its reported failure. "
                           "No model implementation request was sent.")


def launch_arguments(resume_session=None):
    if resume_session is not None:
        resume_session = str(uuid.UUID(resume_session))
    prompt = ("Execute RUN_ASTRA.md in this workspace. Read MASTER_PROMPT.md, REFERENCE_BRIEF.md and WORK_STATUS.md, "
              "inspect the three attached gameplay references, and begin the corrected Unreal teddy encounter. "
              "The target is elevated combat framing, not the historical low-angle BossArena. "
              "Use existing setup evidence and continue through rendering, comparison, controls, animation and verification. "
              "Preserve originals and the baseline. Do not recursively run START_ASTRA.cmd. "
              "The user authorizes needed local command permissions for this encounter without repeated approval prompts. "
              "For dependency installations or updates, provide the exact commands for the user to run; do not run them yourself.")
    args = [tool("codex.exe")]
    if resume_session:
        args.append("resume")
        prompt = ("Resume the existing encounter implementation from this saved session and inspect actual current files. "
                  "The pause was for a CLI update and permission change, not cancellation of the task. "
                  "Preserve completed work and continue the unfinished steps in RUN_ASTRA.md. "
                  "The user explicitly authorizes necessary local command permissions without repeated yes prompts. "
                  "Full Access is configured for this launcher only. Preserve Windows protection and the project boundaries in AGENTS.md. "
                  "For dependency installations or updates, hand the exact commands to the user instead of executing them. "
                  "Reuse installed tools for documentation where available. Do not start another Codex or START_ASTRA session. "
                  "Keep WORK_STATUS.md current and continue through the encounter's evidence and visual verification milestones.")
    args.extend(["--cd", str(ROOT), "--model", SETTINGS["model"],
            "--config", f'model_reasoning_effort="{SETTINGS["reasoning_effort"]}"',
            "--sandbox", "danger-full-access", "--ask-for-approval", "never", "--search"])
    if not os.environ.get("CODEX_WINDOWS_REGISTERED_CORE"):
        # This desktop-only bridge cannot start in a standalone terminal without its host.
        args.extend(["--config", "mcp_servers.node_repl.enabled=false"])
    if unreal_cache_paths():
        args.extend(["--config", cache_config_argument()])
    if resume_session:
        return [*args, "--", resume_session, prompt]
    for image in SETTINGS["reference_images"]:
        args.extend(["--image", str(ROOT / image)])
    return [*args, "--", prompt]


def open_project(mode, baseline=False, dry_run=False):
    chosen = SETTINGS["baseline_map"] if baseline else SETTINGS["target_map"]

    def level_file(level):
        return (ROOT / SETTINGS["project"]).parent / "Content" / (level.removeprefix("/Game/") + ".umap")

    if not level_file(chosen).is_file() and not baseline:
        print("TeddyEncounter has not been built yet. Opening the prepared Twin Stick starter.", flush=True)
        chosen = SETTINGS["baseline_map"]
    require_file(level_file(chosen))
    executable = require_file(Path(SETTINGS["engine_root"]) / "Engine/Binaries/Win64/UnrealEditor.exe")
    project = require_file(ROOT / SETTINGS["project"])
    arguments = [str(executable), str(project), chosen, "-nosplash", *unreal_local_arguments()]
    if mode == "play":
        arguments.extend(["-game", "-windowed", "-ResX=1600", "-ResY=900"])
    if dry_run:
        print(json.dumps({"level": chosen, "mode": mode, "arguments": arguments}, indent=2))
        return 0
    require_editor_closed()
    process = subprocess.Popen(arguments, cwd=ROOT, env=tool_environment())
    print(f"Opened {chosen} ({mode}), process {process.pid}.")
    return 0


def run_editor_script(script, render=False):
    script = (ROOT / script).resolve()
    if not script.is_relative_to(ROOT):
        raise RuntimeError("Editor scripts must be saved inside this project")
    require_file(script)
    require_editor_closed()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    directory = ROOT / "evidence/editor-runs" / stamp
    directory.mkdir(parents=True, exist_ok=False)
    args = [str(Path(SETTINGS["engine_root"]) / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"),
            str(ROOT / SETTINGS["project"]), "-run=pythonscript", f"-script={script}",
            "-unattended", "-nosplash", "-nop4", "-NoSound", *unreal_local_arguments(),
            "-RenderOffscreen" if render else "-nullrhi"]
    print(f"Running Unreal script: {script}\nLog: {directory / 'editor.log'}", flush=True)
    result = run_logged(args, directory / "editor.log", env=tool_environment())
    write_json(directory / "process-result.json", {**result, "script": str(script),
               "script_outputs_require_inspection": True})
    return 0


@contextmanager
def launch_lock():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / "astra-run.lock"
    handle = path.open("a+b")
    if path.stat().st_size == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    import msvcrt
    try:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        handle.close()
        raise RuntimeError("Another Astra launcher or full setup verification is already using this project.") from exc
    try:
        yield
    finally:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        handle.close()


def snapshot(directory):
    destination = directory / "baseline-source-and-content.zip"
    files = []
    for project in (SETTINGS["project"], SETTINGS["legacy_project"]):
        for folder in ("Source", "Config", "Content"):
            files.extend(p for p in ((ROOT / project).parent / folder).rglob("*")
                         if p.is_file() and "__pycache__" not in p.parts)
    files.extend(ROOT / rel for rel in [SETTINGS["project"], "MASTER_PROMPT.md", "REFERENCE_BRIEF.md"])
    manifest = []
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            rel = path.relative_to(ROOT).as_posix()
            archive.write(path, rel)
            manifest.append({"path": rel, "sha256": sha256(path), "bytes": path.stat().st_size})
    result = {"archive": str(destination), "sha256": sha256(destination), "files": manifest,
              "excludes": ["Binaries", "Intermediate", "Saved", "external originals (retained in place)"]}
    write_json(directory / "baseline-manifest.json", result)
    return {"archive": str(destination), "sha256": result["sha256"], "file_count": len(manifest)}


def require_editor_closed():
    # Process enumeration works in the restricted CLI token; WMI/CIM does not.
    # Conservatively refuse any editor process because its project is not visible here.
    script = ("$editors = @(Get-Process -Name UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue); "
              "if ($editors.Count) { $editors | Select-Object Id,ProcessName | ConvertTo-Json -Compress }; exit 0")
    active = capture([tool("pwsh.exe"), "-NoProfile", "-Command", script])
    if active:
        raise RuntimeError("Close existing Unreal editor/game instances before opening or authoring this project; "
                           "existing processes will not be stopped: " + active)


def engine_probe(directory, render_runtime=False):
    directory = Path(directory).resolve()
    if not directory.is_relative_to(EVIDENCE.resolve()):
        raise RuntimeError("Probe output must remain under this project's evidence/setup folder")
    directory.mkdir(parents=True, exist_ok=False)
    result = {"checked_at_utc": utc(), "passed": False, "project": SETTINGS["project"],
              "workflow": SETTINGS["workflow"], "native_compilation_required": False}
    try:
        require_editor_closed()
        descriptor = json.loads((ROOT / SETTINGS["project"]).read_text())
        if descriptor.get("Modules"):
            raise RuntimeError("Blueprint setup unexpectedly contains a native project module")
        proof_id = uuid.uuid4().hex[:12]
        env = dict(tool_environment(), TEDDY_PROOF_ID=proof_id,
                   TEDDY_INSPECTION_REPORT=str(directory / "blueprints.json"),
                   TEDDY_AUTHORING_REPORT=str(directory / "authoring.json"),
                   BOSSSHOT_SETUP_REPORT=str(directory / "unreal-import.json"))
        common = [str(Path(SETTINGS["engine_root"]) / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"),
                  str(ROOT / SETTINGS["project"]), "-run=pythonscript", "-unattended", "-nullrhi",
                  "-nosplash", "-nop4", "-NoSound", *unreal_local_arguments()]
        for script, report_name in [("inspect_blueprint_candidate.py", "blueprints"),
                                    ("verify_setup_import.py", "unreal-import"),
                                    ("verify_blueprint_authoring.py", "authoring")]:
            run_logged([*common, f"-script={ROOT / 'tools' / script}"], directory / (report_name + ".log"), env=env)
            report = json.loads(require_file(directory / (report_name + ".json")).read_text(encoding="utf-8-sig"))
            if not report.get("passed"):
                raise RuntimeError(f"Blueprint setup step failed: {report_name}")
            result[report_name] = ({"passed": True, "report": str(directory / "blueprints.json"),
                                    "compiled_blueprints": len(report["blueprints"]),
                                    "level_actors": report["maps"][0]["actor_count"]}
                                   if report_name == "blueprints" else report)
        if result["unreal-import"]["source_sha256"] != SETTINGS["teddy_model_sha256"]:
            raise RuntimeError("The imported teddy did not match the original source")
        result["blueprint_authoring_verified"] = True
        if render_runtime:
            result["runtime"] = verify_runtime(directory / "runtime", env)
            result["standalone"] = verify_standalone(directory, result["authoring"], env)
        result["passed"] = True
        return result
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        write_json(directory / "engine-probe.json", result)


def verify_runtime(directory, env):
    directory.mkdir(parents=True, exist_ok=False)
    env = dict(env, TEDDY_RUNTIME_REPORT=str(directory / "runtime.json"))
    engine = Path(SETTINGS["engine_root"]) / "Engine/Binaries/Win64/UnrealEditor.exe"
    args = [str(engine), str(ROOT / SETTINGS["project"]),
            f"-ExecutePythonScript={ROOT / 'tools/verify_blueprint_runtime.py'}", "-RenderOffscreen",
            "-ResX=1280", "-ResY=720", "-unattended", "-nosplash", "-nop4", "-NoSound",
            f"-abslog={directory / 'runtime-engine.log'}", *unreal_local_arguments()]
    run_logged(args, directory / "runtime-process.log", timeout=240, env=env)
    report = json.loads(require_file(directory / "runtime.json").read_text(encoding="utf-8-sig"))
    if not report.get("passed") or not report.get("checks") or not all(report["checks"].values()):
        raise RuntimeError(f"Blueprint runtime check failed: {directory / 'runtime.json'}")
    text = (directory / "runtime-engine.log").read_text(encoding="utf-8", errors="replace")
    if "TEDDY_BLUEPRINT_RUNTIME_AUTHORING_OK" not in text:
        raise RuntimeError("The saved authored graph's runtime marker is missing")
    dimensions = []
    for value in report["images"]:
        path = require_file(value).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise RuntimeError("Runtime capture came from another verification run")
        data = path.read_bytes()
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError("Runtime capture is not a valid PNG")
        dimensions.append(dict(zip(("width", "height"), struct.unpack_from(">II", data, 16))))
    if len(dimensions) != 3 or any(d != {"width": 1280, "height": 720} for d in dimensions):
        raise RuntimeError("Expected three 1280 x 720 gameplay captures")
    return {"passed": True, "report": str(directory / "runtime.json"), "checks": len(report["checks"]),
            "images": report["images"], "image_dimensions": dimensions, "proves_new_encounter": False,
            "physical_device_verified": False, "input_method": report["input_method"]}


def verify_standalone(directory, authored, env):
    image = Path(authored["standalone_image"])
    if image.exists():
        raise RuntimeError("Standalone proof must produce a fresh capture")
    engine = Path(SETTINGS["engine_root"]) / "Engine/Binaries/Win64/UnrealEditor.exe"
    args = [str(engine), str(ROOT / SETTINGS["project"]), authored["map"], "-game", "-RenderOffscreen",
            "-ResX=1280", "-ResY=720", "-unattended", "-nosplash", "-NoSound",
            f"-abslog={directory / 'standalone-engine.log'}", *unreal_local_arguments()]
    run_logged(args, directory / "standalone-process.log", timeout=180, env=env)
    data = require_file(image).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack_from(">II", data, 16) != (1280, 720):
        raise RuntimeError("Standalone game did not produce its expected rendered capture")
    log = (directory / "standalone-engine.log").read_text(encoding="utf-8", errors="replace")
    if authored["runtime_marker"] not in log:
        raise RuntimeError("Standalone game did not execute the saved generated Blueprint")
    return {"passed": True, "image": str(image), "map": authored["map"],
            "launch_mode": "UnrealEditor -game", "packaged_build_verified": False}


def astra_smoke(directory):
    fixture = directory / "astra-probe"
    fixture.mkdir()
    nonce = uuid.uuid4().hex
    write_json(fixture / "input.json", {"nonce": nonce, "purpose": "bounded setup check only"})
    schema = {"type": "object", "properties": {
        "nonce": {"type": "string"}, "camera_description": {"type": "string"},
        "camera_type": {"type": "string", "enum": ["elevated_oblique", "eye_level", "low_angle", "unclear"]},
        "player_side_in_first_image": {"type": "string", "enum": ["left", "right", "behind", "foreground", "unclear"]},
        "target_level": {"type": "string"},
        "engine_probe_passed": {"type": "boolean"}, "workspace_write_verified": {"type": "boolean"}},
        "required": ["nonce", "camera_description", "camera_type", "player_side_in_first_image", "target_level",
                     "engine_probe_passed", "workspace_write_verified"], "additionalProperties": False}
    write_json(fixture / "schema.json", schema)
    prompt = (f"SETUP SMOKE CHECK ONLY. Do not implement the game, launch another Codex or change instructions. "
              f"Read {fixture / 'input.json'} and RUN_ASTRA.md. Inspect the attached game frames. "
              f"Run this bounded existing verification command through your shell tool: "
              f'python tools/astra_setup.py probe --runtime --run-dir "{fixture / "engine"}". '
              f"It compiles shipped Blueprint assets, verifies a namespaced teddy import, creates fresh Blueprint behavior, "
              f"saves and reopens it, plays the stock Twin Stick map, checks action input and captures runtime images. "
              f"This is isolated setup evidence only, no native module or game implementation. "
              f"Read the resulting engine-probe.json. Write a JSON file at {fixture / 'workspace-write.json'} "
              f"containing the exact nonce from input.json. Return the requested structured result with that nonce, "
              f"a visual description of the camera, which side of the main creature the human is on in the FIRST attached image, "
              f"the new target level, and truthful booleans for the engine probe and file write. "
              f"If a tool fails, report false; do not request broader permissions or claim the game is complete.")
    args = [tool("codex.exe"), "exec", "--ephemeral", "--skip-git-repo-check", "--cd", str(ROOT),
            "--model", SETTINGS["model"], "--config", f'model_reasoning_effort="{SETTINGS["reasoning_effort"]}"',
            "--json", "--output-schema", str(fixture / "schema.json"), "--output-last-message", str(fixture / "result.json")]
    if unreal_cache_paths():
        args.extend(["--config", cache_config_argument()])
    for image in SETTINGS["reference_images"][:2]:
        args.extend(["--image", str(ROOT / image)])
    args.extend(["--", prompt])
    run_logged(args, fixture / "events.jsonl", timeout=600, env=tool_environment())
    result = json.loads(require_file(fixture / "result.json").read_text(encoding="utf-8-sig"))
    proof = json.loads(require_file(fixture / "workspace-write.json").read_text(encoding="utf-8-sig"))
    engine = json.loads(require_file(fixture / "engine/engine-probe.json").read_text(encoding="utf-8-sig"))
    if result["nonce"] != nonce or proof.get("nonce") != nonce:
        raise RuntimeError("Astra did not read/write the exact fresh setup fixture")
    if not result["engine_probe_passed"] or not result["workspace_write_verified"] or not engine.get("passed"):
        raise RuntimeError("Astra could not run the prepared tools under its actual CLI permissions")
    if (not engine.get("blueprint_authoring_verified") or not engine.get("runtime", {}).get("passed")
            or not engine.get("standalone", {}).get("passed")):
        raise RuntimeError("Astra's saved Blueprint authoring or rendered runtime proof is missing")
    if result["target_level"] != SETTINGS["target_map"]:
        raise RuntimeError("Astra did not identify the corrected target level")
    if (result.get("camera_type") != "elevated_oblique" or result["player_side_in_first_image"] != "right"
            or len(result["camera_description"].strip()) < 20):
        raise RuntimeError("Astra's visual smoke answer did not match the inspected reference; review result.json")
    return {"passed": True, "model_requested": SETTINGS["model"], "reasoning_requested": SETTINGS["reasoning_effort"],
            "response": result, "evidence": str(fixture), "verified": ["authenticated model request", "reference images accepted",
                "local brief read", "workspace write", "Blueprint creation, compilation, save/reopen and teddy import through Codex tools",
                "rendered starter runtime and input actions through Codex tools", "ordinary standalone game launch"],
            "runtime": engine["runtime"], "standalone": engine["standalone"]}


def full_verify():
    directory = EVIDENCE / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    directory.mkdir(parents=True, exist_ok=False)
    result = {"started_at_utc": utc(), "ready": False, "run_directory": str(directory), "checks": {},
              "project": SETTINGS["project"], "workflow": SETTINGS["workflow"],
              "implementation_complete": False, "visual_acceptance": False}
    baseline = ROOT / "BossShot/Content/Maps/BossArena.umap"
    try:
        baseline_before = sha256(require_file(baseline))
        quick = quick_check()
        print_check(quick)
        if not quick["ready"]:
            raise RuntimeError("Resolve the failed quick checks before full validation")
        result["checks"]["quick"] = {"passed": True}
        print("Preserving current source and content...", flush=True)
        result["baseline_backup"] = snapshot(directory)
        print("Checking authenticated Astra/Max, Blueprint authoring, teddy import and rendered gameplay...", flush=True)
        result["checks"]["astra"] = astra_smoke(directory)
        result["checks"]["runtime"] = result["checks"]["astra"]["runtime"]
        result["checks"]["standalone"] = result["checks"]["astra"]["standalone"]
        if sha256(baseline) != baseline_before:
            raise RuntimeError("Preserved BossArena changed during setup validation")
        result["checks"]["baseline_preserved"] = {"passed": True, "sha256": baseline_before}
        final_quick = quick_check()
        if not final_quick["ready"]:
            raise RuntimeError("Inputs or dependencies changed during setup validation")
        result["ready"] = True
        return result
    except KeyboardInterrupt:
        result["error"] = "Verification cancelled by the user"
        raise
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        result["finished_at_utc"] = utc()
        write_json(directory / "verification.json", result)
        write_json(EVIDENCE / "latest-verification.json", result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    start = sub.add_parser("start")
    start.add_argument("--dry-run", action="store_true")
    start.add_argument("--resume", metavar="SESSION_ID", help="Continue this exact saved CLI session")
    sub.add_parser("verify")
    probe = sub.add_parser("probe")
    probe.add_argument("--run-dir", required=True)
    probe.add_argument("--runtime", action="store_true")
    opener = sub.add_parser("open")
    opener.add_argument("--mode", choices=("play", "edit"), default="play")
    opener.add_argument("--baseline", action="store_true")
    opener.add_argument("--dry-run", action="store_true")
    editor = sub.add_parser("editor-script")
    editor.add_argument("script")
    editor.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if args.command == "editor-script":
        return run_editor_script(args.script, args.render)
    if args.command == "open":
        return open_project(args.mode, args.baseline, args.dry_run)
    if args.command == "probe":
        result = engine_probe(args.run_dir, args.runtime)
        print(json.dumps({"passed": result["passed"], "report": str(Path(args.run_dir) / "engine-probe.json"),
                          "blueprint_authoring_verified": result["blueprint_authoring_verified"],
                          "runtime": result.get("runtime"), "standalone": result.get("standalone")}, indent=2))
        return 0
    if args.command == "check":
        result = quick_check()
        print_check(result)
        return 0 if result["ready"] else 1
    if args.command == "verify":
        with launch_lock():
            full_verify()
        print(f"Full setup VERIFIED. Receipt: {EVIDENCE / 'latest-verification.json'}")
        return 0
    result = quick_check()
    print_check(result)
    if not result["ready"]:
        return 1
    arguments = launch_arguments(args.resume)
    if args.dry_run:
        print(json.dumps({"executable": arguments[0], "arguments": arguments[1:],
                          "permissions": {"approval_policy": "never", "sandbox_mode": "danger-full-access",
                                          "scope": "this launcher invocation; explicitly authorized by the user"},
                          "resume_session": args.resume,
                          "additional_writable_cache": [str(p) for p in unreal_cache_paths()]}, indent=2))
        return 0
    require_launch_verification()
    with launch_lock():
        print("Resuming Astra / Max in the saved encounter session." if args.resume else
              "Starting Astra / Max with the corrected encounter prompt and 3 reference images.", flush=True)
        print("Full Access is authorized for this run; routine command approval prompts are disabled. Ctrl+C interrupts.", flush=True)
        write_json(EVIDENCE / "last-launch.json", {"started_at_utc": utc(), "model": SETTINGS["model"],
                   "reasoning": SETTINGS["reasoning_effort"], "images": [] if args.resume else SETTINGS["reference_images"],
                   "prompt": "RUN_ASTRA.md", "resume_session": args.resume,
                   "cli": codex_version_check(), "approval_policy": "never", "sandbox_mode": "danger-full-access"})
        return subprocess.call(arguments, cwd=ROOT, env=cli_environment())


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(130)
    except Exception as error:
        print(f"SETUP ERROR: {error}", file=sys.stderr)
        sys.exit(1)
