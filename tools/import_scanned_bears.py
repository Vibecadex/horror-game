"""Import phone-scanned bears from the Vibecadex bear scanner into this project.

Runs the pinned importer in tools/vendor/bear_scanner_importer.py with this
project's settings. Its provenance records the team scanner source and UE 5.8 fix.
Each finished scan becomes /Game/ScannedBears/<Name>_<id>/SM_Bear_<Name>:
one Static Mesh with LOD0-2 (8,000 / 2,500 / 800 triangles), a convex collision hull and
the scan's texture, at real size in cm with the pivot under the feet. Bears are props
for placement; nothing here changes TeddyEncounter, its Blueprints or /Game/TeddyEncounter.

Close the editor, then either (headless, writes evidence/implementation/<stamp>-import_scanned_bears):
    python tools/run_encounter_test.py tools/import_scanned_bears.py
or, in an open editor: Tools > Execute Python Script... > this file.
Many bears on a first run (shader compile + import) can take longer than the runner's
default 420 s: set TEDDY_TEST_TIMEOUT=1800 first.

Settings, in tools/project-settings.local.json (ignored by Git) or environment variables:
    "bear_scanner_repo": "C:/path/to/bear-scanner"     BEAR_SCANNER_REPO  (certificate root; default: ../bear-scanner)
    "bear_source": "C:/path/to/Rupert.glb or folder"   BEAR_SOURCE        (default: the running scanner)
    "bear_scanner_url": "https://127.0.0.1:8443"       BEAR_SCANNER
    "bear_cert": "C:/path/to/cert.pem"                 BEAR_CERT          (default: <bear_scanner_repo>/data/certs/cert.pem)
Environment variables win over the settings file. Re-runs skip unchanged bears; rebuilt
or renamed bears update their existing mesh. The importer only ever deletes folders whose
assets it created itself. The run fails (and says why) if any bear fails or none is found.
"""
import hashlib
import json
import os
import re
import runpy
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ["TEDDY_TEST_DIR"]) if os.environ.get("TEDDY_TEST_DIR") else None
IMPORTER_API = 5  # bear-pack API, integrity checks and version-aware updates
SETTINGS = {"bear_source": "BEAR_SOURCE", "bear_scanner_url": "BEAR_SCANNER", "bear_cert": "BEAR_CERT"}
receipt = {"passed": False}


def local_settings() -> dict:
    path = ROOT / "tools/project-settings.local.json"
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def run() -> list:
    settings = local_settings()
    repo = Path(os.environ.get("BEAR_SCANNER_REPO") or settings.get("bear_scanner_repo")
                or ROOT.parent / "bear-scanner")
    script = ROOT / "tools/vendor/bear_scanner_importer.py"
    if not script.is_file():
        raise RuntimeError(f"Pinned bear scanner importer not found at {script}. Restore this checkout's tools/vendor files.")
    found = re.search(r"^IMPORTER_API = (\d+)\b", script.read_text(encoding="utf-8"), re.M)
    if not found or int(found.group(1)) < IMPORTER_API:
        raise RuntimeError(f"{script} is an older or different importer than this wrapper "
                           "expects. Restore this checkout's matching tools/vendor files.")

    # Settings reach the importer as environment variables for this run only, so a
    # second run in the same open editor sees the settings file as it is then.
    overrides = {env: str(settings[key]) for key, env in SETTINGS.items()
                 if settings.get(key) and not os.environ.get(env)}
    if not os.environ.get('BEAR_CERT'):
        overrides.setdefault('BEAR_CERT', str(repo / 'data/certs/cert.pem'))
    overrides.setdefault("BEAR_DEST", os.environ.get("BEAR_DEST") or "/Game/ScannedBears")
    saved = {k: os.environ.get(k) for k in overrides}
    os.environ.update(overrides)
    try:
        receipt.update(importer=str(script), importer_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
                       destination=os.environ["BEAR_DEST"],
                       source=os.environ.get("BEAR_SOURCE") or os.environ.get("BEAR_SCANNER")
                       or "https://127.0.0.1:8443")
        return runpy.run_path(str(script), run_name="__main__")["RESULTS"]
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def use_authored_lods(result: dict) -> None:
    """Keep the scan's LODs active despite UE 5.8's default Nanite import setting.

    Repair previous Nanite imports once; unchanged repeats do not save the mesh.
    """
    import unreal
    assets = unreal.EditorAssetLibrary
    path = result['mesh']
    if not path.startswith(receipt['destination'].rstrip('/') + '/'):
        raise RuntimeError(f'Imported mesh is outside the requested destination: {path}')
    mesh = assets.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh) or assets.get_metadata_tag(mesh, 'BearScanner.Owner') != 'bear-scanner':
        raise RuntimeError(f'Refusing to configure a mesh not owned by Bear Scanner: {path}')
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    settings = subsystem.get_nanite_settings(mesh)
    changed = bool(settings.get_editor_property('enabled'))
    if changed:
        settings.set_editor_property('enabled', False)
        subsystem.set_nanite_settings(mesh, settings, True)
    lods = subsystem.get_lod_count(mesh)
    triangles = [mesh.get_num_triangles(i) for i in range(lods)]
    if not triangles or any(n <= 0 for n in triangles) or any(a <= b for a, b in zip(triangles, triangles[1:])):
        raise RuntimeError(f'{path}: invalid authored LOD geometry: {triangles}')
    if subsystem.get_nanite_settings(mesh).get_editor_property('enabled'):
        raise RuntimeError(f'{path}: Nanite is still enabled')
    if changed:
        if not assets.save_loaded_asset(mesh):
            raise RuntimeError(f'Could not save authored LOD settings: {path}')
        if result['result'] == 'up to date':
            result['result'] = 'updated'
        result['settings_change'] = 'Disabled Nanite to retain authored LODs'
    result.update(nanite_enabled=False, lod_triangles=triangles)


try:
    results = run()
    receipt["bears"] = results
    failed = [r for r in results if r["result"] == "failed"]
    if not results:
        raise RuntimeError("No finished bears found to import.")
    if failed:
        raise RuntimeError(f"{len(failed)} of {len(results)} bears failed: "
                           + "; ".join(f"{r['bear']}: {r['error']}" for r in failed))
    for result in results:
        use_authored_lods(result)
    receipt["passed"] = True
except Exception:
    receipt["error"] = traceback.format_exc()
    raise
finally:
    if OUT:
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2))
