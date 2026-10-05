"""Import phone-scanned bears from the Vibecadex bear scanner into this project.

Runs the bear scanner's own importer (bear-scanner/unreal/import_bears.py) with this
project's settings. Each finished scan becomes /Game/ScannedBears/<Name>_<id>/SM_Bear_<Name>:
one Static Mesh with LOD0-2 (8,000 / 2,500 / 800 triangles), a convex collision hull and
the scan's texture, at real size in cm with the pivot under the feet. Bears are props
for placement; nothing here changes TeddyEncounter, its Blueprints or /Game/TeddyEncounter.

Close the editor, then either (headless, writes evidence/implementation/<stamp>-import_scanned_bears):
    python tools/run_encounter_test.py tools/import_scanned_bears.py
or, in an open editor: Tools > Execute Python Script... > this file.

Settings, in tools/project-settings.local.json (ignored by Git) or environment variables:
    "bear_scanner_repo": "C:/path/to/bear-scanner"     BEAR_SCANNER_REPO  (default: ../bear-scanner)
    "bear_source": "C:/path/to/model.glb or folder"    BEAR_SOURCE        (default: the running scanner)
    "bear_scanner_url": "https://127.0.0.1:8443"       BEAR_SCANNER
    "bear_cert": "C:/path/to/cert.pem"                 BEAR_CERT          (default: <bear_scanner_repo>/data/certs/cert.pem)
Re-runs skip unchanged bears; rebuilt bears replace the old mesh where it's placed.
The importer only ever deletes folders whose assets it created itself.
"""
import json
import os
import runpy
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ["TEDDY_TEST_DIR"]) if os.environ.get("TEDDY_TEST_DIR") else None
receipt = {"passed": False, "destination": "/Game/ScannedBears"}


def local_settings() -> dict:
    path = ROOT / "tools/project-settings.local.json"
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


try:
    settings = local_settings()
    repo = Path(os.environ.get("BEAR_SCANNER_REPO") or settings.get("bear_scanner_repo")
                or ROOT.parent / "bear-scanner")
    script = repo / "unreal/import_bears.py"
    if not script.is_file():
        raise RuntimeError(f"Bear scanner importer not found at {script}. Clone "
                           "github.com/Vibecadex/bear-scanner and set bear_scanner_repo in "
                           "tools/project-settings.local.json.")
    # This runs that file's code inside the editor: only point it at your own clone.
    if "IMPORTER_API = 2" not in script.read_text(encoding="utf-8"):
        raise RuntimeError(f"{script} is an older or different importer than this wrapper "
                           "expects. Pull the latest bear-scanner main.")
    for key, env in (("bear_source", "BEAR_SOURCE"), ("bear_scanner_url", "BEAR_SCANNER"),
                     ("bear_cert", "BEAR_CERT")):
        if settings.get(key) and not os.environ.get(env):
            os.environ[env] = str(settings[key])
    os.environ.setdefault("BEAR_DEST", receipt["destination"])
    receipt.update(importer=str(script), source=os.environ.get("BEAR_SOURCE") or
                   os.environ.get("BEAR_SCANNER") or "https://127.0.0.1:8443")
    results = runpy.run_path(str(script), run_name="__main__")["RESULTS"]
    receipt["bears"] = results
    receipt["passed"] = bool(results) and all(r["result"] != "failed" for r in results)
except Exception:
    receipt["error"] = traceback.format_exc()
    raise
finally:
    if OUT:
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2))
