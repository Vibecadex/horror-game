"""Regression checks for the team-handoff guards; plain Python, no Unreal needed.

    python tools/test_handoff_guards.py
"""
import json
import os
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import astra_setup as setup  # noqa: E402

GUARDED = ["build_encounter_scene", "build_boss", "build_combat", "build_encounter_hud", "fix_encounter_camera",
           "refine_encounter_stage", "refine_scene_lighting", "import_encounter_art", "refine_player_controls",
           "tune_encounter"]


class EditorCheck(unittest.TestCase):
    def listing(self, running):
        def capture(args, timeout=30):
            image = args[2].split(" eq ")[1]
            if image in running:
                return f'"{image}","1234","Console","1","900,000 K"'
            return "INFO: No tasks are running which match the specified criteria."
        return capture

    def test_no_editor_running_passes(self):
        with patch.object(setup, "capture", self.listing(set())):
            setup.require_editor_closed()

    def test_running_editor_or_commandlet_is_refused(self):
        for image in ("UnrealEditor.exe", "UnrealEditor-Cmd.exe"):
            with patch.object(setup, "capture", self.listing({image})):
                with self.assertRaisesRegex(RuntimeError, "Close existing Unreal"):
                    setup.require_editor_closed()

    def test_similar_process_names_are_not_editors(self):
        def capture(args, timeout=30):
            return '"UnrealEditorServices.exe","1","Console","1","1 K"'
        with patch.object(setup, "capture", capture):
            setup.require_editor_closed()

    def test_listing_failure_fails_closed(self):
        def capture(args, timeout=30):
            raise RuntimeError("tasklist failed (1): access denied")
        with patch.object(setup, "capture", capture):
            with self.assertRaisesRegex(RuntimeError, "Could not check for running Unreal editors"):
                setup.require_editor_closed()

    def test_does_not_need_pwsh(self):
        with patch.object(setup, "capture", self.listing(set())), \
             patch.object(setup.shutil, "which", side_effect=AssertionError("looked up a tool")):
            setup.require_editor_closed()

    def test_real_tasklist(self):
        if os.name != "nt":
            self.skipTest("Windows only")
        if "UnrealEditor" in subprocess.run(["tasklist"], capture_output=True, text=True).stdout:
            self.skipTest("an Unreal editor is running")
        setup.require_editor_closed()


class HistoricalBuilders(unittest.TestCase):
    def setUp(self):
        class Any(types.ModuleType):
            def __getattr__(self, name):
                return type(name, (), {})
        self.unreal = Any("unreal")
        self.map_exists = True
        self.unreal.EditorAssetLibrary = type("A", (), {"does_asset_exist": staticmethod(lambda p: self.map_exists)})
        patcher = patch.dict(sys.modules, {"unreal": self.unreal})
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.modules.pop("encounter_authoring", None)
        import encounter_authoring
        self.ea = encounter_authoring
        os.environ.pop("TEDDY_ALLOW_HISTORICAL_REBUILD", None)

    def test_refuses_on_saved_project(self):
        with self.assertRaisesRegex(RuntimeError, "historical builder"):
            self.ea.historical_builder("build_boss.py")

    def test_person_can_allow_a_scratch_rebuild(self):
        with patch.dict(os.environ, {"TEDDY_ALLOW_HISTORICAL_REBUILD": "1"}):
            self.ea.historical_builder("build_boss.py")

    def test_first_build_without_map_is_allowed(self):
        self.map_exists = False
        self.ea.historical_builder("build_encounter_scene.py")

    def test_every_guarded_builder_calls_it_before_doing_anything(self):
        for name in GUARDED:
            text = (TOOLS / f"{name}.py").read_text(encoding="utf-8")
            call = text.find("historical_builder(__file__)")
            self.assertGreater(call, 0, name)
            first_action = min(i for i in (text.find("load_level"), text.find("existing("), text.find("try:"),
                                           text.find("get_all_level_actors"), text.find("blueprint("))
                               if i > 0)
            self.assertLess(call, first_action, name)


class RunPointers(unittest.TestCase):
    def test_pointers_are_relative_and_exist(self):
        for kind in ("parity", "full-room", "chamber"):
            out = json.loads((ROOT / f"evidence/{kind}/current-run.json").read_text())["out"]
            self.assertFalse(Path(out).is_absolute(), kind)
            self.assertTrue((ROOT / out).is_dir(), kind)


if __name__ == "__main__":
    unittest.main(verbosity=2)
