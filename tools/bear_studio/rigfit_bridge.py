"""Single-worker scanner jobs with immutable inputs and revision-checked publication."""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path

try:
    from . import server
except ImportError:
    import server

ACTIVE = {"running", "cancelling"}
JOB_RE = re.compile(r"^fit_[0-9a-f]{16}$")
WORKER = Path(__file__).with_name("rigfit_worker.py")


def scanner_root():
    settings = server.ROOT / "tools/project-settings.local.json"
    local = json.loads(settings.read_text(encoding="utf-8")) if settings.is_file() else {}
    value = os.environ.get("BEAR_SCANNER_REPO") or local.get("bear_scanner_repo")
    return Path(value).resolve() if value else None


class LocalFitter:
    def __init__(self, root=None, timeout=300):
        self.root = Path(root) if root else scanner_root()
        self.timeout = timeout
        self.cached = None
        self.checked = 0

    def command(self):
        root = self.root
        if not root:
            raise ValueError("Configure bear_scanner_repo in tools/project-settings.local.json first")
        python = root / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
        if not python.is_file() or not (root / "scripts/rig_test_package.py").is_file():
            raise ValueError("The scanner environment or rig tools are missing. Finish scanner setup first.")
        return [str(python), "-B", str(WORKER), "--scanner", str(root)]

    def options(self):
        return {"cwd": str(self.root), "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                "env": {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}}

    def capability(self):
        if self.cached is not None and time.monotonic() - self.checked < 60:
            return dict(self.cached)
        try:
            result = subprocess.run([*self.command(), "--probe"], capture_output=True, text=True,
                                    timeout=30, **self.options())
            value = json.loads(result.stdout.strip().splitlines()[-1])
            if result.returncode or not value.get("available"):
                raise ValueError(value.get("error", "Scanner dependency check failed"))
            self.cached = {"available": True, "bones": value["bones"]}
        except Exception as error:
            self.cached = {"available": False, "error": str(error)[:2000]}
        self.checked = time.monotonic()
        return dict(self.cached)

    def run(self, directory, cancel):
        with (directory / "worker.log").open("wb") as log:
            process = subprocess.Popen([*self.command(), "--job", str(directory)],
                                       stdout=log, stderr=subprocess.STDOUT, **self.options())
            deadline = time.monotonic() + self.timeout
            try:
                while process.poll() is None:
                    if cancel.wait(0.2):
                        raise InterruptedError("Fit cancelled; existing rigs were kept")
                    if time.monotonic() > deadline:
                        raise TimeoutError("Scanner fit exceeded five minutes; source and previous rigs were kept")
                if process.returncode:
                    error_file = directory / "error.json"
                    message = json.loads(error_file.read_text(encoding="utf-8")).get("error") if error_file.is_file() else "Scanner worker failed; inspect its retained worker.log"
                    raise ValueError(message)
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait()


class Jobs:
    def __init__(self, store, fitter=None):
        self.store = store
        self.fitter = fitter or LocalFitter()
        self.root = store.root / "jobs/rigfit"
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.thread = None
        self.cancel_event = threading.Event()
        self.active = None
        self.closed = False
        for path in self.root.glob("fit_*/status.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("status") in ACTIVE:
                # A killed server may have committed the rig before writing its final job status.
                bear = self.store.detail(value["bearId"])
                saved = next((rig for rig in bear["rigs"] if rig["recipe"].get("fitJobId") == value["id"]), None)
                value.update(status="succeeded" if saved else "interrupted", updated=server.now())
                if saved:
                    value["rigRevision"] = saved["revision"]
                else:
                    value["error"] = "Studio stopped during this fit. Previous rigs were kept; start a new fit."
                self._write(value)

    def _write(self, value):
        path = self.root / value["id"] / "status.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(server.encode(value), encoding="utf-8")
        temporary.replace(path)

    def get(self, job_id):
        if not JOB_RE.fullmatch(job_id):
            raise server.APIError(404, "Fit job not found")
        with self.lock:
            path = self.root / job_id / "status.json"
            if not path.is_file():
                raise server.APIError(404, "Fit job not found")
            return json.loads(path.read_text(encoding="utf-8"))

    def latest(self, bear_id):
        self.store.detail(bear_id)
        with self.lock:
            values = [self.get(path.parent.name) for path in self.root.glob("fit_*/status.json")]
            return max((v for v in values if v["bearId"] == bear_id), key=lambda v: v["created"], default=None)

    def start(self, bear_id, body):
        expected = server.integer(body.get("expectedRevision"), "expectedRevision", 1)
        with self.lock:
            if self.closed:
                raise server.APIError(503, "Studio is stopping")
            if self.active:
                active = self.get(self.active)
                if active["bearId"] == bear_id and active["expectedRevision"] == expected:
                    return active
                raise server.APIError(409, "Another scanner fit is running. Wait for it to finish or cancel it.")
            available = self.fitter.capability()
            if not available["available"]:
                raise server.APIError(503, available.get("error", "Scanner fitter unavailable"))
            with self.store.lock:
                bear = self.store.detail(bear_id)
                if bear["revision"] != expected:
                    raise server.APIError(409, "Catalogue changed; refresh before fitting")
                if bear["sourceStats"].get("skins"):
                    raise server.APIError(400, "This source already has a skin. Import its original unrigged scan to fit it.")
                source_path = self.store.asset(bear["modelUrl"])
                source = source_path.read_bytes()
                if server.digest(source) != bear["sourceSha256"]:
                    raise server.APIError(409, "Stored source hash does not match; fit refused")
                manifest = server.object_json(source_path.with_name("manifest.json").read_bytes())
                lm = source_path.with_name("landmarks.json")
                expected_landmarks = manifest.get("files", {}).get("landmarks.json")
                landmark_bytes = lm.read_bytes() if lm.is_file() else None
                if (landmark_bytes is not None or expected_landmarks) and (
                    landmark_bytes is None or server.digest(landmark_bytes) != expected_landmarks
                ):
                    raise server.APIError(409, "Stored landmarks differ from the imported source; fit refused")
                job_id = "fit_" + uuid.uuid4().hex[:16]
                directory = self.root / job_id
                directory.mkdir()
                (directory / "source.glb").write_bytes(source)
                if landmark_bytes is not None:
                    (directory / "landmarks.json").write_bytes(landmark_bytes)
                provenance = bear.get("source", {})
                pose = provenance.get("pack", {}).get("capture", {}).get("pose") or provenance.get("scannerMetadata", {}).get("pose") or provenance.get("capturePose") or "unknown"
                value = {"id": job_id, "bearId": bear_id, "status": "running", "created": server.now(),
                         "expectedRevision": expected, "sourceRevision": bear["sourceRevision"],
                         "sourceSha256": bear["sourceSha256"], "capturePose": pose,
                         "synthetic": provenance.get("kind") == "synthetic-example"}
                (directory / "request.json").write_text(server.encode(value), encoding="utf-8")
                self._write(value)
            self.active = job_id
            self.cancel_event = threading.Event()
            self.thread = threading.Thread(target=self._run, args=(value, directory, self.cancel_event), daemon=True)
            self.thread.start()
            return value

    def _run(self, value, directory, cancel):
        try:
            self.fitter.run(directory, cancel)
            result = server.object_json((directory / "result.json").read_bytes())
            recipe = result["recipe"]
            recipe["fitJobId"] = value["id"]
            # Serialize cancellation with publication; a successful save wins a late cancel.
            with self.lock:
                if cancel.is_set():
                    raise InterruptedError("Fit cancelled; existing rigs were kept")
                saved = self.store.add_rig(value["bearId"], {
                    "expectedRevision": value["expectedRevision"], "sourceRevision": value["sourceRevision"],
                    "sourceSha256": value["sourceSha256"], "recipe": recipe, "validation": result["validation"],
                    "glbBase64": base64.b64encode((directory / "model.glb").read_bytes()).decode("ascii"),
                })
                value.update(status="succeeded", rigRevision=saved["rig"]["revision"],
                             warnings=result["validation"].get("warnings", []))
        except InterruptedError as error:
            value.update(status="cancelled", error=str(error))
        except Exception as error:
            value.update(status="conflict" if isinstance(error, server.APIError) and error.status == 409 else "failed",
                         error=str(error)[:2000])
        finally:
            with self.lock:
                value["updated"] = server.now()
                self._write(value)
                self.active = None

    def cancel(self, job_id):
        with self.lock:
            value = self.get(job_id)
            if self.active == job_id:
                self.cancel_event.set()
                value.update(status="cancelling", updated=server.now())
                self._write(value)
            return value

    def close(self):
        with self.lock:
            self.closed = True
            self.cancel_event.set()
        if self.thread:
            self.thread.join(timeout=10)
