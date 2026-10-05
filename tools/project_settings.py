"""Shared defaults with optional, ignored workstation overrides. No side effects."""
import json
import os
from pathlib import Path


def load_settings(root):
    root = Path(root)
    settings = json.loads((root / "tools/project-settings.json").read_text(encoding="utf-8-sig"))
    local = root / "tools/project-settings.local.json"
    if local.is_file():
        settings.update(json.loads(local.read_text(encoding="utf-8-sig")))
    if os.environ.get("TEDDY_ENGINE_ROOT"):
        settings["engine_root"] = os.environ["TEDDY_ENGINE_ROOT"]
    return settings
