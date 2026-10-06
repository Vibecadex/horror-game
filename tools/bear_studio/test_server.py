"""Behavioral integration checks for Bear Studio; all writes use temporary stores."""
from __future__ import annotations

import base64
import copy
import http.client
import json
import struct
import tempfile
import threading
import unittest
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import server


def glb(skinned=False, weights=(1, 0, 0, 0), offset=0.0, external=False, animated=False) -> bytes:
    """A real triangle mesh; optional two-joint skin with inverse bind matrices."""
    binary = bytearray()
    views, accessors = [], []

    def add(rows, kind, component, accessor_type):
        while len(binary) % 4:
            binary.append(0)
        start = len(binary)
        for row in rows:
            binary.extend(struct.pack("<" + kind * len(row), *row))
        view = {"buffer": 0, "byteOffset": start, "byteLength": len(binary) - start}
        views.append(view)
        entry = {"bufferView": len(views) - 1, "componentType": component, "count": len(rows), "type": accessor_type}
        accessors.append(entry)
        return len(accessors) - 1

    attrs = {"POSITION": add([(offset, 0, 0), (offset + 1, 0, 0), (offset, 1, 0)], "f", 5126, "VEC3")}
    document = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
                "nodes": [{"mesh": 0, "name": "LOD0"}], "meshes": [{"primitives": [{"attributes": attrs}]}]}
    if skinned:
        attrs["JOINTS_0"] = add([(1, 0, 0, 0)] * 3, "H", 5123, "VEC4")
        attrs["WEIGHTS_0"] = add([weights] * 3, "f", 5126, "VEC4")
        identity = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        bind = add([identity, identity], "f", 5126, "MAT4")
        document["nodes"].extend([{"name": "Root", "children": [2]}, {"name": "Head"}])
        document["nodes"][0]["skin"] = 0
        document["scenes"][0]["nodes"].append(1)
        document["skins"] = [{"joints": [1, 2], "inverseBindMatrices": bind}]
        if animated:
            times = add([(0,), (1,)], "f", 5126, "SCALAR")
            rotations = add([(0, 0, 0, 1), (0, 0, 0.38268343, 0.9238795)], "f", 5126, "VEC4")
            document["animations"] = [{"name": "Head turn", "channels": [{"sampler": 0, "target": {"node": 2, "path": "rotation"}}],
                                       "samplers": [{"input": times, "output": rotations}]}]
    document.update(bufferViews=views, accessors=accessors, buffers=[{"byteLength": len(binary)}])
    if external:
        document["images"] = [{"uri": "https://example.invalid/texture.png"}]
    raw_json = json.dumps(document).encode()
    raw_json += b" " * (-len(raw_json) % 4)
    binary.extend(b"\0" * (-len(binary) % 4))
    total = 12 + 8 + len(raw_json) + 8 + len(binary)
    return struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<II", len(raw_json), 0x4E4F534A) + raw_json + struct.pack("<II", len(binary), 0x004E4942) + bytes(binary)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = server.Store(self.root, seed=False)

    def tearDown(self):
        self.temp.cleanup()

    def bear(self):
        return self.store.import_local("Rupert.glb", glb())["bear"]

    def rig_body(self, bear):
        return {"sourceRevision": bear["sourceRevision"], "sourceSha256": bear["sourceSha256"],
                "recipe": {"preset": "seated", "sourceSha256": bear["sourceSha256"]},
                "validation": {"checks": [{"id": "deformation", "status": "warn"}]},
                "glbBase64": base64.b64encode(glb(True)).decode()}

    def test_import_is_immutable_idempotent_and_survives_restart(self):
        bear = self.bear()
        path = self.store.asset(bear["modelUrl"])
        original = path.read_bytes()
        changed = self.store.patch(bear["id"], {"expectedRevision": 1, "name": "Captain Rupert", "tags": ["hero"], "notes": "Clean the box"})
        repeated = self.store.import_local("Other name.glb", glb())
        self.assertFalse(repeated["imported"])
        self.assertEqual(repeated["bear"]["name"], "Captain Rupert")
        reopened = server.Store(self.root, seed=False).detail(bear["id"])
        self.assertEqual(reopened, changed)
        self.assertEqual(path.read_bytes(), original)

    def test_optimistic_revision_conflict_preserves_edits(self):
        bear = self.bear()
        self.store.patch(bear["id"], {"expectedRevision": 1, "notes": "first"})
        with self.assertRaises(server.APIError) as context:
            self.store.patch(bear["id"], {"expectedRevision": 1, "notes": "stale overwrite"})
        self.assertEqual(context.exception.status, 409)
        self.assertEqual(self.store.detail(bear["id"])["notes"], "first")

    def test_concurrent_saves_have_one_winner(self):
        bear = self.bear()
        def save(index):
            try:
                return self.store.patch(bear["id"], {"expectedRevision": 1, "notes": str(index)})["revision"]
            except server.APIError as error:
                return error.status
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(save, range(8)))
        self.assertEqual(results.count(2), 1)
        self.assertEqual(results.count(409), 7)

    def test_draft_does_not_claim_a_rig(self):
        bear = self.bear()
        updated = self.store.patch(bear["id"], {"expectedRevision": 1, "draftRecipe": {"bones": [{"name": "Head"}]}})
        self.assertEqual(updated["rigStatus"], "unrigged")
        self.assertEqual(updated["rigs"], [])
        with self.assertRaises(server.APIError):
            self.store.add_rig(bear["id"], {"sourceRevision": 1, "sourceSha256": bear["sourceSha256"], "recipe": {}})
        with self.assertRaises(server.APIError):
            self.store.add_test(bear["id"], {"rigRevision": 1, "suite": "motion", "results": []})

    def test_saved_skin_is_structurally_verified_with_separate_source(self):
        bear = self.bear()
        original = self.store.asset(bear["modelUrl"]).read_bytes()
        result = self.store.add_rig(bear["id"], self.rig_body(bear))
        rig = result["rig"]
        self.assertEqual(rig["status"], "draft")
        self.assertEqual(rig["stats"]["skinnedVertices"], 3)
        self.assertEqual(result["bear"]["rigStatus"], "draft-rig")
        self.assertEqual(result["bear"]["reviewStatus"], "unreviewed")
        self.assertEqual(self.store.asset(bear["modelUrl"]).read_bytes(), original)
        server.parse_glb(self.store.asset(rig["modelUrl"]).read_bytes(), require_skin=True)
        updated = self.store.patch(bear["id"], {"expectedRevision": result["bear"]["revision"], "draftRecipe": {"preset": "new"}})
        self.assertEqual(updated["rigStatus"], "draft-edited")
        self.assertEqual(len(updated["rigs"]), 1)

    def test_animated_rig_artifact_retains_real_channels_and_duration(self):
        bear = self.bear()
        body = self.rig_body(bear)
        body["glbBase64"] = base64.b64encode(glb(True, animated=True)).decode()
        rig = self.store.add_rig(bear["id"], body)["rig"]
        self.assertEqual(rig["stats"]["animations"], 1)
        self.assertEqual(rig["stats"]["animationNames"], ["Head turn"])
        self.assertEqual(rig["stats"]["animationDetails"][0]["duration"], 1)

    def test_rig_without_weights_or_wrong_source_is_rejected(self):
        bear = self.bear()
        body = self.rig_body(bear)
        body["glbBase64"] = base64.b64encode(glb()).decode()
        with self.assertRaises(server.APIError):
            self.store.add_rig(bear["id"], body)
        body = self.rig_body(bear)
        body["glbBase64"] = base64.b64encode(glb(True, (0, 0, 0, 0))).decode()
        with self.assertRaises(server.APIError):
            self.store.add_rig(bear["id"], body)
        body = self.rig_body(bear)
        body["sourceSha256"] = "0" * 64
        with self.assertRaises(server.APIError) as context:
            self.store.add_rig(bear["id"], body)
        self.assertEqual(context.exception.status, 409)
        self.assertEqual(self.store.detail(bear["id"])["rigs"], [])

    def test_embedded_recipe_identity_cannot_contradict_selected_source(self):
        bear = self.bear()
        body = self.rig_body(bear)
        body["recipe"]["sourceSha256"] = "another-bear"
        with self.assertRaises(server.APIError) as context:
            self.store.add_rig(bear["id"], body)
        self.assertEqual(context.exception.status, 409)
        for recipe in ({"sourceRevision": 2}, {"sourceSha256": "another-bear"}):
            with self.assertRaises(server.APIError) as context:
                self.store.patch(bear["id"], {"expectedRevision": 1, "draftRecipe": recipe})
            self.assertEqual(context.exception.status, 409)
        unchanged = self.store.detail(bear["id"])
        self.assertEqual(unchanged["revision"], 1)
        self.assertIsNone(unchanged["draftRecipe"])
        self.assertEqual(unchanged["rigs"], [])

    def test_changed_source_keeps_old_rigs_and_tests_historical(self):
        bear = self.store.import_source("scanner:test#abc", "Test", {"kind": "scanner"}, {"model.glb": glb()})["bear"]
        rig = self.store.add_rig(bear["id"], self.rig_body(bear))["rig"]
        recorded = self.store.add_test(bear["id"], {"rigRevision": rig["revision"], "suite": "motion", "results": [{"id": "bend", "status": "pass"}], "notes": "elbow checked"})
        self.assertEqual(recorded["test"]["sourceRevision"], 1)
        updated = self.store.import_source("scanner:test#abc", "Rebuilt", {"kind": "scanner"}, {"model.glb": glb(offset=1)})["bear"]
        self.assertEqual(updated["id"], bear["id"])
        self.assertEqual(updated["sourceRevision"], 2)
        self.assertTrue(updated["rigs"][0]["stale"])
        self.assertTrue(updated["tests"][0]["stale"])
        self.assertEqual(updated["rigStatus"], "unrigged")
        self.assertIsNone(updated["draftRecipe"])
        self.assertEqual(self.store.asset(bear["modelUrl"]).read_bytes(), glb())
        self.assertEqual(len(self.store.history(bear["id"])), 4)

    def test_invalid_glb_external_resources_and_filenames_rejected(self):
        for name, data in [("../outside.glb", glb()), ("C:\\scan.glb", glb()), ("scan.gltf", glb()), ("scan.glb", b"nope"), ("scan.glb", glb(external=True)), ("scan.glb", glb()[:-1])]:
            with self.subTest(name=name, length=len(data)):
                with self.assertRaises(server.APIError):
                    self.store.import_local(name, data)
        self.assertEqual(self.store.list(), [])

    def test_paths_and_unknown_artifacts_are_not_served(self):
        bear = self.bear()
        for path in ("/assets/../../catalogue.sqlite3", bear["modelUrl"].replace("model.glb", "../../catalogue.sqlite3"), bear["modelUrl"].replace("model.glb", "secret.txt"), bear["modelUrl"].replace("/1/", "/2/")):
            with self.assertRaises(server.APIError):
                self.store.asset(path)

    def test_bundled_sample_seed_is_labelled_and_repeat_safe(self):
        self.store.seed_sample()
        bears = self.store.list()
        self.assertEqual(len(bears), 1)
        self.assertIn("prebuilt sample", bears[0]["name"])
        self.assertEqual(bears[0]["source"]["kind"], "bundled-sample")
        self.assertEqual(bears[0]["sourceReport"]["status"], "warn")
        self.assertEqual(bears[0]["sourceStats"]["lods"][0]["triangles"], 8000)
        self.store.seed_sample()
        self.assertEqual(len(self.store.list()), 1)


class FakeScanner(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        root = "/scans/scan123/"
        meta = {"id": "scan123", "name": "Scanner bear", "status": self.server.scan_status, "updated": 1,
                "files": {"model.glb": self.server.model_url, "report.json": root + "report.json?v=1"}}
        path = self.path.split("?", 1)[0]
        payload = None
        if path == "/api/scans":
            payload = json.dumps([meta]).encode()
        elif path == "/api/scans/scan123":
            self.server.read_count += 1
            if self.server.change_during_import and self.server.read_count > 1:
                meta["updated"] = 2
            payload = json.dumps(meta).encode()
        elif path == root + "model.glb":
            payload = glb()
        elif path == root + "report.json":
            payload = b'{"status":"warn","checks":[]}'
        if payload is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.scanner = ThreadingHTTPServer(("127.0.0.1", 0), FakeScanner)
        self.scanner.scan_status = "done"
        self.scanner.model_url = "/scans/scan123/model.glb?v=1"
        self.scanner.change_during_import = False
        self.scanner.read_count = 0
        self.thread = threading.Thread(target=self.scanner.serve_forever, daemon=True)
        self.thread.start()
        self.client = server.Scanner(f"http://127.0.0.1:{self.scanner.server_port}")
        self.temp = tempfile.TemporaryDirectory()
        self.store = server.Store(Path(self.temp.name), self.client, seed=False)

    def tearDown(self):
        self.scanner.shutdown()
        self.scanner.server_close()
        self.thread.join()
        self.temp.cleanup()

    def test_scanner_copies_artifacts_and_preserves_report(self):
        imported = self.store.import_scanner("scan123")
        self.assertTrue(imported["imported"])
        bear = imported["bear"]
        self.assertEqual(bear["sourceReport"]["status"], "warn")
        self.assertEqual(self.store.asset(bear["modelUrl"]).read_bytes(), glb())
        self.assertFalse(self.store.import_scanner("scan123")["imported"])

    def test_failed_or_rebuilding_scans_cannot_import(self):
        self.scanner.scan_status = "failed"
        self.assertEqual(self.client.scans()[0]["status"], "failed")
        with self.assertRaises(server.APIError) as context:
            self.store.import_scanner("scan123")
        self.assertEqual(context.exception.status, 409)

    def test_scanner_urls_cannot_escape_selected_origin_or_scan(self):
        for url in ("http://example.invalid/secret", "/api/config", "/scans/other/model.glb", "/scans/scan123/../../secret"):
            self.scanner.model_url = url
            with self.subTest(url=url):
                with self.assertRaises(server.APIError) as context:
                    self.store.import_scanner("scan123")
                self.assertEqual(context.exception.status, 502)
        self.assertEqual(self.store.list(), [])

    def test_rebuild_race_does_not_commit_mixed_provenance(self):
        self.scanner.change_during_import = True
        with self.assertRaises(server.APIError) as context:
            self.store.import_scanner("scan123")
        self.assertEqual(context.exception.status, 409)
        self.assertEqual(self.store.list(), [])


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = server.Store(Path(self.temp.name), seed=False)
        self.http = server.StudioServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.logs = patch.object(server.Handler, "log_message", lambda *args: None)
        self.logs.start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.logs.stop()
        self.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.http.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        data = response.read()
        status = response.status
        connection.close()
        return status, data

    def test_health_local_upload_metadata_history_download_and_offline(self):
        status, data = self.request("GET", "/api/health")
        health = json.loads(data)
        self.assertEqual(status, 200)
        self.assertEqual(health["app"], "bear-studio")
        self.assertEqual(Path(health["dataDir"]), self.store.root)
        status, data = self.request("POST", "/api/import/local", glb(), {"Content-Type": "model/gltf-binary", "X-Filename": "Rupert.glb"})
        self.assertEqual(status, 201, data)
        bear = json.loads(data)["bear"]
        patch_body = json.dumps({"expectedRevision": 1, "notes": "HTTP saved"})
        status, data = self.request("PATCH", f"/api/bears/{bear['id']}", patch_body, {"Content-Type": "application/json"})
        self.assertEqual(json.loads(data)["notes"], "HTTP saved")
        status, data = self.request("GET", f"/api/bears/{bear['id']}/history")
        self.assertEqual(len(json.loads(data)["history"]), 2)
        self.assertEqual(self.request("GET", bear["modelUrl"]), (200, glb()))
        status, data = self.request("GET", "/api/scanner/scans")
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(data)["available"])
        status, data = self.request("GET", "/api/bears")
        self.assertEqual(len(json.loads(data)["bears"]), 1)

    def test_unknown_host_and_cross_site_mutation_are_rejected(self):
        status, _ = self.request("GET", "/api/health", headers={"Host": "untrusted.invalid"})
        self.assertEqual(status, 421)
        status, _ = self.request("POST", "/api/import/local", glb(), {"Content-Type": "model/gltf-binary", "Origin": "https://untrusted.invalid"})
        self.assertEqual(status, 403)
        self.assertEqual(self.store.list(), [])

    def test_encoded_browser_filename_roundtrips_and_encoded_paths_are_rejected(self):
        name = "Brün teddy.glb"
        status, data = self.request("POST", "/api/import/local", glb(), {"Content-Type": "model/gltf-binary", "X-Filename": urllib.parse.quote(name)})
        self.assertEqual(status, 201)
        self.assertEqual(json.loads(data)["bear"]["source"]["originalFilename"], name)
        status, _ = self.request("POST", "/api/import/local", glb(offset=2), {"Content-Type": "model/gltf-binary", "X-Filename": "%2e%2e%2foutside.glb"})
        self.assertEqual(status, 400)
        self.assertEqual(len(self.store.list()), 1)

    def test_upload_limit_wrong_type_and_path_traversal_fail(self):
        status, _ = self.request("POST", "/api/import/local", b"", {"Content-Type": "model/gltf-binary", "Content-Length": str(server.MAX_GLB + 1)})
        self.assertEqual(status, 413)
        status, _ = self.request("POST", "/api/import/local", b"{}", {"Content-Type": "application/json"})
        self.assertEqual(status, 415)
        for path in ("/../../server.py", "/%2e%2e/server.py", "/assets/../../catalogue.sqlite3", "/api/execute"):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_animation_library_routes_are_fixed(self):
        for route, file in server.LIBRARY_FILES.items():
            status, data = self.request("GET", route)
            if file.is_file():
                self.assertEqual(status, 200)
                self.assertEqual(server.digest(data), server.digest(file.read_bytes()))
            else:
                self.assertEqual(status, 404)
        for route in ("/library/quaternius/../../server.py", "/library/quaternius/UPSTREAM_README.txt"):
            self.assertEqual(self.request("GET", route)[0], 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
