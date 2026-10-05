"""Regression checks for truthful setup receipts and safe launch boundaries."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import astra_setup as setup


class SetupSafetyTests(unittest.TestCase):
    def test_success_for_another_project_does_not_unlock_launch(self):
        with tempfile.TemporaryDirectory(prefix="astra-setup-test-") as temporary:
            evidence = Path(temporary)
            setup.write_json(evidence / "latest-verification.json", {
                "ready": True, "project": "Other/Other.uproject", "workflow": setup.SETTINGS["workflow"]})
            with patch.object(setup, "EVIDENCE", evidence):
                with self.assertRaisesRegex(RuntimeError, "No model implementation request was sent"):
                    setup.require_launch_verification()

    def test_failed_full_receipt_blocks_implementation_launch(self):
        with tempfile.TemporaryDirectory(prefix="astra-setup-test-") as temporary:
            evidence = Path(temporary)
            setup.write_json(evidence / "latest-verification.json", {"ready": False})
            with patch.object(setup, "EVIDENCE", evidence):
                with self.assertRaisesRegex(RuntimeError, "No model implementation request was sent"):
                    setup.require_launch_verification()

    def test_missing_baseline_replaces_previous_success_with_failure(self):
        with tempfile.TemporaryDirectory(prefix="astra-setup-test-") as temporary:
            root = Path(temporary)
            evidence = root / "evidence/setup"
            setup.write_json(evidence / "latest-verification.json", {"ready": True})
            with patch.object(setup, "ROOT", root), patch.object(setup, "EVIDENCE", evidence):
                with self.assertRaisesRegex(RuntimeError, "missing or empty"):
                    setup.full_verify()
            receipt = json.loads((evidence / "latest-verification.json").read_text())
            self.assertFalse(receipt["ready"])
            self.assertIn("BossArena.umap", receipt["error"])
            self.assertIn("finished_at_utc", receipt)

    def test_probe_rejects_output_outside_evidence_before_writing(self):
        with tempfile.TemporaryDirectory(prefix="astra-setup-test-") as temporary:
            root = Path(temporary)
            forbidden = root / "elsewhere"
            with patch.object(setup, "EVIDENCE", root / "allowed"):
                with self.assertRaisesRegex(RuntimeError, "must remain under"):
                    setup.engine_probe(forbidden)
            self.assertFalse(forbidden.exists())

    def test_probe_cannot_reuse_an_old_success_report(self):
        with tempfile.TemporaryDirectory(prefix="astra-setup-test-") as temporary:
            evidence = Path(temporary)
            old = evidence / "previous-run"
            setup.write_json(old / "unreal-import.json", {"passed": True})
            with patch.object(setup, "EVIDENCE", evidence):
                with self.assertRaises(FileExistsError):
                    setup.engine_probe(old)
            self.assertFalse((old / "engine-probe.json").exists())

    def test_image_arguments_keep_spaces_and_terminate_before_prompt(self):
        with patch.object(setup, "ROOT", Path("C:/A project with spaces")), patch.object(setup, "tool", return_value="codex.exe"):
            arguments = setup.launch_arguments()
        self.assertEqual(arguments[-2], "--")
        images = [arguments[i + 1] for i, value in enumerate(arguments) if value == "--image"]
        self.assertEqual(len(images), 3)
        self.assertTrue(all("A project with spaces" in value for value in images))
        self.assertTrue(all(value.endswith(".png") for value in images))
        self.assertNotIn("--add-dir", arguments)
        self.assertEqual(setup.unreal_cache_paths(), [])
        self.assertFalse(any(value.startswith("sandbox_workspace_write.writable_roots=") for value in arguments))
        self.assertFalse(any(value.startswith("--dangerously-") for value in arguments))

    def test_launch_has_the_authorized_permissions_on_every_run(self):
        arguments = setup.launch_arguments()
        self.assertEqual(arguments[arguments.index("--sandbox") + 1], "danger-full-access")
        self.assertEqual(arguments[arguments.index("--ask-for-approval") + 1], "never")
        self.assertEqual(arguments[arguments.index("--model") + 1], "gpt-6-astra")
        self.assertIn('model_reasoning_effort="max"', arguments)

    def test_resume_preserves_the_exact_session_and_its_existing_images(self):
        session = "01a10885-6a2c-7af0-b81a-fec9b203670c"
        arguments = setup.launch_arguments(session)
        self.assertEqual(arguments[1], "resume")
        self.assertEqual(arguments[-3:-1], ["--", session])
        self.assertNotIn("--last", arguments)
        self.assertNotIn("--image", arguments)
        self.assertEqual(arguments[arguments.index("--ask-for-approval") + 1], "never")
        with self.assertRaises(ValueError):
            setup.launch_arguments("some-other-task")

    def test_terminal_repair_preserves_valid_settings_and_the_parent_environment(self):
        for terminal, expected in [("dumb", "xterm-256color"), ("", "xterm-256color"), ("vt100", "vt100")]:
            original = {"TERM": terminal, "PATH": "original-path"}
            with patch.object(setup, "tool_environment", side_effect=lambda: dict(original)):
                environment = setup.cli_environment()
            self.assertEqual(environment["TERM"], expected)
            self.assertEqual(original["TERM"], terminal)
            self.assertEqual(environment["PATH"].split(setup.os.pathsep)[0], str(Path(setup.tool("codex.exe")).parent))

    def test_wrong_cli_version_is_rejected_instead_of_silently_using_an_old_copy(self):
        with patch.object(setup, "capture", return_value="codex-cli 0.155.0"):
            with self.assertRaisesRegex(RuntimeError, "version mismatch"):
                setup.codex_version_check()

    def test_play_switches_to_new_level_and_baseline_remains_addressable(self):
        with tempfile.TemporaryDirectory(prefix="astra-setup-test-") as temporary:
            root = Path(temporary)
            for relative in ("TeddyBlueprint/Content/Variant_TwinStick/LVL_TwinStick.umap", "TeddyBlueprint/Content/Maps/TeddyEncounter.umap",
                             "TeddyBlueprint/TeddyBlueprint.uproject"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test fixture")
            with patch.object(setup, "ROOT", root), patch.object(setup.subprocess, "Popen") as process:
                output = io.StringIO()
                with redirect_stdout(output):
                    setup.open_project("play", dry_run=True)
                self.assertEqual(json.loads(output.getvalue())["level"], "/Game/Maps/TeddyEncounter")
                output = io.StringIO()
                with redirect_stdout(output):
                    setup.open_project("play", baseline=True, dry_run=True)
                self.assertEqual(json.loads(output.getvalue())["level"], "/Game/Variant_TwinStick/LVL_TwinStick")
                process.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
