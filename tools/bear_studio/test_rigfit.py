"""Job lifecycle and cross-window preservation checks; no scanner installs or writes."""
import base64
import json
import struct
import tempfile
import threading
import unittest
from pathlib import Path

import server
from rigfit_bridge import Jobs, LocalFitter
from test_server import glb


class Fitter:
    def __init__(self, available=True, failure=None):
        self.available = available
        self.failure = failure
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls = 0

    def capability(self):
        return {"available": self.available, "error": "Scanner tools are missing"}

    def run(self, directory, cancel):
        self.calls += 1
        self.started.set()
        while not self.release.wait(0.01):
            if cancel.is_set():
                raise InterruptedError("Cancelled")
        if self.failure:
            raise ValueError(self.failure)
        request = json.loads((directory / "request.json").read_text())
        (directory / "model.glb").write_bytes(glb(True, animated=True))
        (directory / "result.json").write_text(json.dumps({"recipe": {
            "method": "scanner-rigfit-v1", "sourceRevision": request["sourceRevision"], "sourceSha256": request["sourceSha256"],
        }, "validation": {"warnings": ["Fit needs visual review"]}}))


class RigfitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = server.Store(Path(self.temp.name), seed=False)
        self.bear = self.store.import_local("Original.glb", glb())["bear"]
        self.fitter = Fitter()
        self.jobs = Jobs(self.store, self.fitter)

    def tearDown(self):
        self.jobs.close()
        self.temp.cleanup()

    def start(self):
        value = self.jobs.start(self.bear["id"], {"expectedRevision": self.bear["revision"]})
        self.assertTrue(self.fitter.started.wait(2))
        return value

    def finish(self, value):
        self.fitter.release.set()
        self.jobs.thread.join(5)
        self.assertFalse(self.jobs.thread.is_alive())
        return self.jobs.get(value["id"])

    def test_fit_saves_separate_pinned_revision_and_survives_restart(self):
        original = self.store.asset(self.bear["modelUrl"]).read_bytes()
        job = self.finish(self.start())
        self.assertEqual(job["status"], "succeeded")
        bear = self.store.detail(self.bear["id"])
        self.assertEqual(bear["sourceRevision"], 1)
        self.assertEqual(bear["rigs"][0]["sourceSha256"], self.bear["sourceSha256"])
        self.assertEqual(bear["rigs"][0]["stats"]["animations"], 1)
        self.assertEqual(bear["rigs"][0]["recipe"]["fitJobId"], job["id"])
        self.assertEqual(bear["reviewStatus"], "unreviewed")
        self.assertEqual(original, self.store.asset(bear["modelUrl"]).read_bytes())
        self.jobs.close()
        reopened = Jobs(self.store, self.fitter)
        self.assertEqual(reopened.latest(bear["id"])["rigRevision"], 1)
        reopened.close()

    def test_duplicate_start_reuses_job_and_other_bear_waits(self):
        job = self.start()
        duplicate = self.jobs.start(self.bear["id"], {"expectedRevision": 1})
        self.assertEqual(job["id"], duplicate["id"])
        other = self.store.import_local("Other.glb", glb(offset=2))["bear"]
        with self.assertRaises(server.APIError) as caught:
            self.jobs.start(other["id"], {"expectedRevision": 1})
        self.assertEqual(caught.exception.status, 409)
        self.finish(job)
        self.assertEqual(self.fitter.calls, 1)

    def test_concurrent_edit_keeps_new_notes_and_draft(self):
        job = self.start()
        updated = self.store.patch(self.bear["id"], {"expectedRevision": 1, "notes": "Keep these notes", "draftRecipe": {"preset": "upright"}})
        result = self.finish(job)
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(self.store.detail(self.bear["id"]), updated)
        self.assertTrue((self.jobs.root / job["id"] / "model.glb").is_file())

    def test_source_change_cannot_publish_against_new_source(self):
        job = self.start()
        with self.store.connect() as db:
            identity = db.execute("SELECT identity FROM bears WHERE id=?", (self.bear["id"],)).fetchone()[0]
        changed = self.store.import_source(identity, "Updated", {"kind": "local"}, {"model.glb": glb(offset=4)})["bear"]
        self.assertEqual(self.finish(job)["status"], "conflict")
        self.assertEqual(self.store.detail(self.bear["id"]), changed)

    def test_cancel_never_saves_output_and_is_repeatable(self):
        job = self.start()
        self.assertEqual(self.jobs.cancel(job["id"])["status"], "cancelling")
        self.jobs.thread.join(5)
        self.assertEqual(self.jobs.get(job["id"])["status"], "cancelled")
        self.assertEqual(self.jobs.cancel(job["id"])["status"], "cancelled")
        self.assertEqual(self.store.detail(self.bear["id"]), self.bear)

    def test_failed_worker_keeps_existing_manual_rig(self):
        saved = self.store.add_rig(self.bear["id"], {"sourceRevision": 1, "sourceSha256": self.bear["sourceSha256"],
            "recipe": {"preset": "seated"}, "glbBase64": base64.b64encode(glb(True)).decode()})
        self.bear = saved["bear"]
        self.fitter.failure = "Scanner landmarks missing: hand_R"
        result = self.finish(self.start())
        self.assertEqual(result["status"], "failed")
        self.assertIn("hand_R", result["error"])
        self.assertEqual(self.store.detail(self.bear["id"]), self.bear)

    def test_missing_dependencies_and_skinned_input_do_not_start(self):
        self.fitter.available = False
        with self.assertRaises(server.APIError) as caught:
            self.jobs.start(self.bear["id"], {"expectedRevision": 1})
        self.assertEqual(caught.exception.status, 503)
        self.fitter.available = True
        skinned = self.store.import_local("Rigged.glb", glb(True))["bear"]
        with self.assertRaises(server.APIError) as caught:
            self.jobs.start(skinned["id"], {"expectedRevision": 1})
        self.assertEqual(caught.exception.status, 400)
        self.assertEqual(self.fitter.calls, 0)

    def test_restart_marks_unfinished_job_and_recovers_already_saved_result(self):
        job = self.finish(self.start())
        self.jobs.close()
        status_path = self.jobs.root / job["id"] / "status.json"
        job["status"] = "running"
        status_path.write_text(json.dumps(job))
        restarted = Jobs(self.store, self.fitter)
        self.assertEqual(restarted.get(job["id"])["status"], "succeeded")
        interrupted = {**job, "id": "fit_0000000000000000"}
        directory = self.jobs.root / interrupted["id"]
        directory.mkdir()
        (directory / "status.json").write_text(json.dumps(interrupted))
        restarted.close()
        restarted = Jobs(self.store, self.fitter)
        self.assertEqual(restarted.get(interrupted["id"])["status"], "interrupted")
        self.assertEqual(len(self.store.detail(self.bear["id"])["rigs"]), 1)
        restarted.close()

    def test_landmark_sidecar_cannot_silently_change_or_disappear(self):
        bear = self.store.import_source("pack:test", "Landmark source", {"kind": "pack"}, {
            "model.glb": glb(), "landmarks.json": b'{"points":{},"complete":false}',
        })["bear"]
        lm = self.store.asset(bear["modelUrl"]).with_name("landmarks.json")
        lm.write_bytes(b'{"points":{},"complete":true}')
        for remove in (False, True):
            if remove:
                lm.unlink()
            with self.assertRaises(server.APIError) as caught:
                self.jobs.start(bear["id"], {"expectedRevision": 1})
            self.assertEqual(caught.exception.status, 409)
        self.assertEqual(self.fitter.calls, 0)


class InstalledWorkerGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fitter = LocalFitter()
        capability = cls.fitter.capability()
        if not capability["available"]:
            raise unittest.SkipTest("Installed scanner required for worker guards: " + capability["error"])

    def rejected(self, mutate, expected):
        data = glb()
        size = struct.unpack_from("<I", data, 12)[0]
        doc = json.loads(data[20:20 + size])
        mutate(doc)
        encoded = json.dumps(doc).encode()
        encoded += b" " * (-len(encoded) % 4)
        tail = data[20 + size:]
        source = struct.pack("<4sII", b"glTF", 2, 20 + len(encoded) + len(tail)) + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + tail
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "source.glb").write_bytes(source)
            (directory / "request.json").write_text(json.dumps({"sourceSha256": server.digest(source), "sourceRevision": 1, "capturePose": "unknown"}))
            # Supplied but incomplete landmarks must never bypass geometry checks.
            (directory / "landmarks.json").write_text('{"points":{"pelvis":[0,0,0]},"complete":false}')
            with self.assertRaisesRegex(ValueError, expected):
                self.fitter.run(directory, threading.Event())
            self.assertFalse((directory / "model.glb").exists())
            self.assertEqual((directory / "source.glb").read_bytes(), source)

    def test_transformed_mesh_is_refused_before_fitting(self):
        self.rejected(lambda doc: doc["nodes"][0].update(scale=[2, 2, 2]), "Apply mesh transforms")

    def test_instanced_mesh_is_refused_before_fitting(self):
        def mutate(doc):
            doc["nodes"].append({"mesh": 0, "translation": [2, 0, 0]})
            doc["scenes"][0]["nodes"].append(1)
        self.rejected(mutate, "Apply mesh transforms")

    def test_ambiguous_meshes_are_refused_even_with_landmarks(self):
        def mutate(doc):
            doc["meshes"].append(doc["meshes"][0].copy())
            doc["nodes"].append({"mesh": 1})
            doc["scenes"][0]["nodes"].append(1)
        self.rejected(mutate, "Choose a single bear mesh")

    def test_known_incomplete_landmarks_are_not_silently_recomputed(self):
        self.rejected(lambda doc: None, "Scanner landmarks missing: neck, head, hand_L, hand_R, foot_L, foot_R")


if __name__ == "__main__":
    unittest.main()
