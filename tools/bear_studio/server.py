"""Persistent, loopback-only Bear Studio. Python standard library; no scanner writes."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import math
import mimetypes
import os
import re
import shutil
import sqlite3
import ssl
import struct
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from . import bear_pack
except ImportError:
    import bear_pack

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent / "web"
MAX_GLB = 64 * 1024 * 1024
MAX_JSON = 512 * 1024
MAX_RIG_JSON = 90 * 1024 * 1024
SOURCE_FILES = {"model.glb", "report.json", "thumb.webp", "collider.json", "cameras.json", "manifest.json", "landmarks.json", "pack-manifest.json"}
RIG_FILES = {"model.glb", "recipe.json", "validation.json", "manifest.json"}
SCANNER_FILES = SOURCE_FILES - {"manifest.json"}
LIBRARY_FILES = {
    "/library/quaternius/model.glb": ROOT / "Assets/ThirdParty/QuaterniusUAL/UAL1_Standard.glb",
    "/library/quaternius/provenance.json": ROOT / "Assets/ThirdParty/QuaterniusUAL/provenance.json",
    "/library/quaternius/license.txt": ROOT / "Assets/ThirdParty/QuaterniusUAL/License.txt",
}
ID_RE = re.compile(r"^bear_[0-9a-f]{16}$")
SCAN_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
COMPONENTS = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


class APIError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def object_json(data: bytes) -> dict:
    try:
        value = json.loads(data.decode("utf-8-sig"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise APIError(400, "Invalid JSON") from error
    if not isinstance(value, dict):
        raise APIError(400, "A JSON object is required")
    return value


def integer(value, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise APIError(400, f"{name} must be an integer >= {minimum}")
    return value


def text_value(value, name: str, limit: int, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > limit or "\x00" in value:
        raise APIError(400, f"{name} must be text of at most {limit} characters")
    value = value.strip()
    if required and not value:
        raise APIError(400, f"{name} is required")
    return value


def bounded_json(value, name: str, limit: int = MAX_JSON):
    try:
        serialized = encode(value)
    except (TypeError, ValueError, RecursionError) as error:
        raise APIError(400, f"{name} must contain finite JSON values") from error
    if len(serialized.encode("utf-8")) > limit:
        raise APIError(413, f"{name} is too large")
    return value


def check_recipe_source(recipe: dict, revision: int, sha256: str):
    if "sourceRevision" in recipe and (isinstance(recipe["sourceRevision"], bool) or recipe["sourceRevision"] != revision):
        raise APIError(409, "Recipe belongs to another source revision; reload this bear before saving")
    if "sourceSha256" in recipe and recipe["sourceSha256"] != sha256:
        raise APIError(409, "Recipe belongs to another source hash; reload this bear before saving")


def parse_glb(data: bytes, require_skin: bool = False) -> tuple[dict, dict]:
    """Check the saved artifact, not a client claim. Reject external resources."""
    if len(data) > MAX_GLB:
        raise APIError(413, "GLB exceeds the 64 MiB limit")
    if len(data) < 20:
        raise APIError(400, "Not a complete GLB file")
    magic, version, size = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or size != len(data):
        raise APIError(400, "Expected a complete GLB version 2 file")
    cursor, doc, binary = 12, None, b""
    while cursor < size:
        if cursor + 8 > size:
            raise APIError(400, "Truncated GLB chunk header")
        length, kind = struct.unpack_from("<II", data, cursor)
        cursor += 8
        if length % 4 or cursor + length > size:
            raise APIError(400, "Invalid GLB chunk length")
        chunk = data[cursor:cursor + length]
        if doc is None:
            if kind != 0x4E4F534A:
                raise APIError(400, "GLB must start with its JSON chunk")
            doc = object_json(chunk)
        elif kind == 0x004E4942:
            if binary:
                raise APIError(400, "Multiple GLB binary chunks are unsupported")
            binary = chunk
        elif kind == 0x4E4F534A:
            raise APIError(400, "Duplicate GLB JSON chunk")
        cursor += length
    if not doc or not isinstance(doc.get("asset"), dict) or str(doc["asset"].get("version", "")) != "2.0":
        raise APIError(400, "Missing glTF 2.0 asset metadata")
    for field in ("buffers", "images", "accessors", "bufferViews", "meshes", "nodes", "skins", "animations"):
        if not isinstance(doc.get(field, []), list) or any(not isinstance(item, dict) for item in doc.get(field, [])):
            raise APIError(400, f"Invalid GLB {field}")
    for resource in [*doc.get("buffers", []), *doc.get("images", [])]:
        if not isinstance(resource, dict):
            raise APIError(400, "Invalid GLB resource")
        uri = resource.get("uri")
        if uri is not None and (not isinstance(uri, str) or not uri.startswith("data:")):
            raise APIError(400, "Use a self-contained GLB; external buffers and images are refused")
    buffers = doc.get("buffers", [])
    if len(buffers) != 1 or buffers[0].get("uri"):
        raise APIError(400, "GLB must contain one embedded binary buffer")
    buffer_length = integer(buffers[0].get("byteLength"), "buffer byteLength")
    if buffer_length > len(binary) or len(binary) - buffer_length > 3:
        raise APIError(400, "GLB binary buffer length does not match")
    accessors = doc.get("accessors", [])
    views = doc.get("bufferViews", [])

    def accessor(index: int) -> dict:
        integer(index, "accessor index")
        if index >= len(accessors) or not isinstance(accessors[index], dict):
            raise APIError(400, "Invalid GLB accessor reference")
        item = accessors[index]
        integer(item.get("count"), "accessor count")
        if item.get("componentType") not in COMPONENTS or item.get("type") not in WIDTHS:
            raise APIError(400, "Invalid GLB accessor format")
        return item

    def values(index: int):
        item = accessor(index)
        if "sparse" in item:
            raise APIError(400, "Sparse rig accessors are unsupported; export dense weights")
        view_index = integer(item.get("bufferView"), "accessor bufferView")
        if view_index >= len(views):
            raise APIError(400, "Invalid GLB bufferView reference")
        view = views[view_index]
        if view.get("buffer", 0) != 0:
            raise APIError(400, "Invalid GLB buffer reference")
        fmt, component_size = COMPONENTS[item["componentType"]]
        width = WIDTHS[item["type"]]
        step = integer(view.get("byteStride", component_size * width), "byteStride", 1)
        item_size = component_size * width
        view_start = integer(view.get("byteOffset", 0), "bufferView byteOffset")
        view_length = integer(view.get("byteLength"), "bufferView byteLength")
        item_start = integer(item.get("byteOffset", 0), "accessor byteOffset")
        required = item_start + (item["count"] - 1) * step + item_size if item["count"] else item_start
        if step < item_size or required > view_length or view_start + view_length > buffer_length:
            raise APIError(400, "GLB accessor points outside its binary buffer")
        for i in range(item["count"]):
            row = struct.unpack_from("<" + fmt * width, binary, view_start + item_start + i * step)
            if item.get("normalized"):
                divisors = {5121: 255, 5123: 65535, 5120: 127, 5122: 32767}
                if item["componentType"] not in divisors:
                    raise APIError(400, "Invalid normalized accessor type")
                row = tuple(max(-1, n / divisors[item["componentType"]]) for n in row)
            yield row

    meshes, nodes, skins = doc.get("meshes", []), doc.get("nodes", []), doc.get("skins", [])
    if not isinstance(meshes, list) or not meshes:
        raise APIError(400, "GLB contains no mesh")
    lods, vertex_count, triangle_count, bounds = [], 0, 0, []
    for index, mesh in enumerate(meshes):
        if not isinstance(mesh, dict) or not mesh.get("primitives"):
            raise APIError(400, "GLB contains an empty mesh")
        if not isinstance(mesh["primitives"], list) or any(not isinstance(item, dict) for item in mesh["primitives"]):
            raise APIError(400, "Invalid GLB mesh primitives")
        vertices = triangles = 0
        for primitive in mesh["primitives"]:
            attributes = primitive.get("attributes", {})
            if not isinstance(attributes, dict):
                raise APIError(400, "Invalid GLB primitive attributes")
            if "POSITION" not in attributes:
                raise APIError(400, "GLB primitive has no positions")
            position = accessor(attributes["POSITION"])
            if position["type"] != "VEC3" or not position["count"]:
                raise APIError(400, "GLB positions are empty or malformed")
            # Validate positions are actually present and finite, not just advertised counts.
            for row in values(attributes["POSITION"]):
                if not all(math.isfinite(n) for n in row):
                    raise APIError(400, "GLB has non-finite vertex positions")
            vertices += position["count"]
            count = accessor(primitive["indices"])["count"] if "indices" in primitive else position["count"]
            if "indices" in primitive:
                indices = accessor(primitive["indices"])
                if indices["type"] != "SCALAR" or indices["componentType"] not in (5121, 5123, 5125):
                    raise APIError(400, "Mesh indices must be unsigned scalar integers")
                if any(row[0] >= position["count"] for row in values(primitive["indices"])):
                    raise APIError(400, "Mesh index points beyond its vertices")
            if primitive.get("mode", 4) == 4:
                if count % 3:
                    raise APIError(400, "Triangle mesh index count is incomplete")
                triangles += count // 3
            if isinstance(position.get("min"), list) and isinstance(position.get("max"), list):
                bounds.append((position["min"], position["max"]))
        names = [node.get("name") for node in nodes if isinstance(node, dict) and node.get("mesh") == index and node.get("name")]
        lods.append({"name": names[0] if names else mesh.get("name", f"Mesh {index}"), "vertices": vertices, "triangles": triangles})
        vertex_count += vertices
        triangle_count += triangles
    if triangle_count < 1:
        raise APIError(400, "GLB has no triangle mesh to inspect")
    animation_details = []
    for animation_index, animation in enumerate(doc.get("animations", [])):
        samplers, channels = animation.get("samplers"), animation.get("channels")
        if not isinstance(samplers, list) or not samplers or not isinstance(channels, list) or not channels:
            raise APIError(400, "Animation has no channels or samplers")
        duration = 0.0
        for channel in channels:
            if not isinstance(channel, dict) or not isinstance(channel.get("target"), dict):
                raise APIError(400, "Invalid animation channel")
            sample_index = integer(channel.get("sampler"), "animation sampler")
            target = channel["target"]
            target_node = integer(target.get("node"), "animation target node")
            if sample_index >= len(samplers) or target_node >= len(nodes) or target.get("path") not in ("translation", "rotation", "scale", "weights"):
                raise APIError(400, "Invalid animation channel target")
            sampler = samplers[sample_index]
            if not isinstance(sampler, dict) or sampler.get("interpolation", "LINEAR") not in ("LINEAR", "STEP", "CUBICSPLINE"):
                raise APIError(400, "Invalid animation sampler")
            times, outputs = accessor(sampler.get("input")), accessor(sampler.get("output"))
            if times["type"] != "SCALAR" or times["componentType"] != 5126 or not times["count"]:
                raise APIError(400, "Animation needs float keyframe times")
            previous = -1.0
            for row in values(sampler["input"]):
                if not math.isfinite(row[0]) or row[0] < 0 or row[0] <= previous:
                    raise APIError(400, "Animation times must be finite and increase")
                previous = row[0]
            multiplier = 3 if sampler.get("interpolation") == "CUBICSPLINE" else 1
            if target["path"] != "weights" and (outputs["count"] != times["count"] * multiplier or outputs["type"] != ("VEC4" if target["path"] == "rotation" else "VEC3")):
                raise APIError(400, "Animation values do not match its keyframes")
            if any(not all(math.isfinite(n) for n in row) for row in values(sampler["output"])):
                raise APIError(400, "Animation contains non-finite values")
            duration = max(duration, previous)
        animation_details.append({"name": animation.get("name", f"Animation {animation_index + 1}"), "duration": duration, "channels": len(channels)})
    stats = {"meshCount": len(meshes), "vertices": vertex_count, "triangles": triangle_count,
             "lods": lods, "skins": len(skins), "animations": len(doc.get("animations", [])),
             "animationNames": [item["name"] for item in animation_details], "animationDetails": animation_details}
    if bounds and all(len(low) == len(high) == 3 for low, high in bounds):
        stats["bounds"] = {"min": [min(p[0][i] for p in bounds) for i in range(3)],
                           "max": [max(p[1][i] for p in bounds) for i in range(3)], "space": "mesh-local"}
    checks = [{"id": "self-contained-glb", "status": "pass", "detail": "Valid embedded GLB 2.0"},
              {"id": "finite-geometry", "status": "pass", "detail": f"{vertex_count} finite mesh vertices"}]
    if require_skin:
        if not skins:
            raise APIError(400, "Rig artifact has no skin; saving bone markers is not a rig")
        skinned_vertices = 0
        for node in nodes:
            if "skin" not in node:
                continue
            skin_index = integer(node["skin"], "skin index")
            mesh_index = integer(node.get("mesh"), "skinned mesh index")
            if skin_index >= len(skins) or mesh_index >= len(meshes):
                raise APIError(400, "Invalid skinned node reference")
            skin = skins[skin_index]
            joints = skin.get("joints", [])
            if not isinstance(joints, list) or not joints:
                raise APIError(400, "Skin needs unique joints")
            for joint in joints:
                integer(joint, "skin joint")
                if joint >= len(nodes):
                    raise APIError(400, "Skin references a missing joint")
            if len(set(joints)) != len(joints):
                raise APIError(400, "Skin needs unique joints")
            if "inverseBindMatrices" in skin:
                bind = accessor(skin["inverseBindMatrices"])
                if bind["type"] != "MAT4" or bind["count"] != len(joints):
                    raise APIError(400, "Inverse bind matrices do not match the skeleton")
                if any(not all(math.isfinite(n) for n in row) for row in values(skin["inverseBindMatrices"])):
                    raise APIError(400, "Invalid inverse bind matrix")
            for primitive in meshes[mesh_index]["primitives"]:
                attrs = primitive.get("attributes", {})
                if "JOINTS_0" not in attrs or "WEIGHTS_0" not in attrs:
                    raise APIError(400, "Skinned mesh is missing joint indices or weights")
                jacc, wacc = accessor(attrs["JOINTS_0"]), accessor(attrs["WEIGHTS_0"])
                count = accessor(attrs["POSITION"])["count"]
                if jacc["type"] != "VEC4" or wacc["type"] != "VEC4" or jacc["count"] != count or wacc["count"] != count:
                    raise APIError(400, "Rig skin attributes do not match its vertices")
                if jacc["componentType"] not in (5121, 5123) or jacc.get("normalized"):
                    raise APIError(400, "Joint indices must be unsigned integer indices")
                if wacc["componentType"] not in (5121, 5123, 5126):
                    raise APIError(400, "Unsupported skin weight component type")
                for indices, weights in zip(values(attrs["JOINTS_0"]), values(attrs["WEIGHTS_0"])):
                    if any(j < 0 or j >= len(joints) for j in indices):
                        raise APIError(400, "Skin weight references a missing joint")
                    if any(not math.isfinite(w) or w < 0 or w > 1.001 for w in weights) or abs(sum(weights) - 1) > 0.02:
                        raise APIError(400, "Skin weights must be finite, nonnegative and normalized")
                skinned_vertices += count
        if not skinned_vertices:
            raise APIError(400, "Rig artifact has no skinned mesh vertices")
        stats["skinnedVertices"] = skinned_vertices
        checks.append({"id": "saved-skin-weights", "status": "pass", "detail": f"{skinned_vertices} vertices with valid joints and normalized weights"})
    return stats, {"status": "pass", "checks": checks, "scope": "Structural artifact checks only; deformation and visual acceptance require review."}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise APIError(502, "Scanner redirects are refused")


def settings() -> tuple[str, Path | None]:
    path = ROOT / "tools/project-settings.local.json"
    local = object_json(path.read_bytes()) if path.is_file() else {}
    scanner = os.environ.get("BEAR_SCANNER") or local.get("bear_scanner_url") or "https://127.0.0.1:8443"
    cert = os.environ.get("BEAR_CERT") or local.get("bear_cert")
    if not cert and local.get("bear_scanner_repo"):
        candidate = Path(local["bear_scanner_repo"]) / "data/certs/cert.pem"
        cert = str(candidate) if candidate.is_file() else None
    return scanner, Path(cert) if cert else None


class Scanner:
    def __init__(self, url: str, cert: Path | None = None):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
            raise ValueError("Scanner URL must be an HTTP(S) origin without credentials or a path")
        self.url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, "", "", ""))
        self.origin = parts.scheme.lower(), parts.netloc.lower()
        context = ssl.create_default_context(cafile=str(cert) if cert else None)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(), urllib.request.HTTPSHandler(context=context))

    def get(self, path: str, limit: int = MAX_JSON) -> bytes:
        request = urllib.request.Request(self.url + path, headers={"Accept": "application/json,model/gltf-binary,image/webp", "User-Agent": "BearStudio/1"})
        try:
            with self.opener.open(request, timeout=6) as response:
                size = response.headers.get("Content-Length")
                if size and int(size) > limit:
                    raise APIError(413, "Scanner artifact exceeds the import limit")
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise APIError(413, "Scanner artifact exceeds the import limit")
                return data
        except APIError:
            raise
        except urllib.error.HTTPError as error:
            code = error.code
            error.close()
            raise APIError(404 if code == 404 else 502, f"Scanner answered HTTP {code}") from error
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            raise APIError(502, f"Scanner unavailable: {error}") from error

    def scans(self) -> list:
        try:
            data = json.loads(self.get("/api/scans"))
        except (ValueError, UnicodeError) as error:
            raise APIError(502, "Scanner returned invalid scan metadata") from error
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise APIError(502, "Scanner returned an invalid scan list")
        return data

    def source(self, scan_id: str) -> tuple[dict, dict[str, bytes]]:
        if not isinstance(scan_id, str) or not SCAN_RE.fullmatch(scan_id):
            raise APIError(400, "Invalid scan ID")
        try:
            raw = self.get(f"/api/v1/bears/{scan_id}")
        except APIError as error:
            if error.status != 404:
                raise
            return self.legacy_source(scan_id)
        try:
            doc = bear_pack.document(raw)
            if doc['id'] != scan_id:
                raise ValueError("Scanner returned a different bear identity")
            def read(name, length):
                path = f"/api/v1/bears/{scan_id}/files/{urllib.parse.quote(name)}?r={doc['revision']}"
                return self.get(path, min(bear_pack.MAX_PACK, length + 1))
            files = bear_pack.verified(doc, read)
            after = bear_pack.document(self.get(f"/api/v1/bears/{scan_id}"))
            if any(after.get(key) != doc.get(key) for key in ('id', 'revision', 'version', 'files')):
                raise APIError(409, "Bear pack changed during import; retry after it finishes")
        except ValueError as error:
            raise APIError(502, str(error)) from error
        return {"id": scan_id, "name": doc.get('name'), "status": "done", "pack": object_json(files['pack-manifest.json'])}, files

    def legacy_source(self, scan_id: str) -> tuple[dict, dict[str, bytes]]:
        meta = object_json(self.get(f"/api/scans/{scan_id}"))
        if meta.get("id") != scan_id or meta.get("status") != "done":
            raise APIError(409, "Only a finished scan can be imported")
        listed = meta.get("files")
        if not isinstance(listed, dict) or not listed.get("model.glb"):
            raise APIError(502, "Finished scan has no model file")
        files = {}
        for name in SCANNER_FILES:
            address = listed.get(name)
            if address is None:
                continue
            if not isinstance(address, str):
                raise APIError(502, "Invalid scanner artifact address")
            target = urllib.parse.urlsplit(urllib.parse.urljoin(self.url + "/", address))
            if (target.scheme.lower(), target.netloc.lower()) != self.origin or target.path != f"/scans/{scan_id}/{name}" or target.fragment:
                raise APIError(502, "Scanner artifact address escapes the selected scan")
            files[name] = self.get(target.path + ("?" + target.query if target.query else ""), MAX_GLB if name == "model.glb" else 8 * 1024 * 1024)
        # Avoid mixing bytes from an old/new rebuild with one provenance record.
        after = object_json(self.get(f"/api/scans/{scan_id}"))
        if after.get("status") != "done" or after.get("updated") != meta.get("updated") or after.get("files") != listed:
            raise APIError(409, "Scan changed during import; retry after it finishes")
        return meta, files


class Store:
    def __init__(self, directory: Path, scanner: Scanner | None = None, seed: bool = True):
        self.root = directory.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / "catalogue.sqlite3"
        self.scanner = scanner
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS bears (
                    id TEXT PRIMARY KEY, identity TEXT NOT NULL UNIQUE, revision INTEGER NOT NULL,
                    created TEXT NOT NULL, updated TEXT NOT NULL, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sources (
                    bear_id TEXT NOT NULL REFERENCES bears(id), revision INTEGER NOT NULL,
                    sha256 TEXT NOT NULL, created TEXT NOT NULL, source TEXT NOT NULL,
                    report TEXT NOT NULL, stats TEXT NOT NULL, files TEXT NOT NULL,
                    PRIMARY KEY(bear_id,revision));
                CREATE TABLE IF NOT EXISTS rigs (
                    bear_id TEXT NOT NULL REFERENCES bears(id), revision INTEGER NOT NULL,
                    source_revision INTEGER NOT NULL, source_sha256 TEXT NOT NULL, sha256 TEXT NOT NULL,
                    created TEXT NOT NULL, recipe TEXT NOT NULL, validation TEXT NOT NULL,
                    structural TEXT NOT NULL, stats TEXT NOT NULL, PRIMARY KEY(bear_id,revision));
                CREATE TABLE IF NOT EXISTS tests (
                    id TEXT PRIMARY KEY, bear_id TEXT NOT NULL REFERENCES bears(id), rig_revision INTEGER NOT NULL,
                    source_revision INTEGER NOT NULL, created TEXT NOT NULL, suite TEXT NOT NULL,
                    results TEXT NOT NULL, notes TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY, bear_id TEXT NOT NULL REFERENCES bears(id), created TEXT NOT NULL,
                    action TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL);
            """)
        if seed:
            self.seed_sample()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def event(db, bear_id: str, action: str, revision: int, payload: dict):
        db.execute("INSERT INTO history(bear_id,created,action,revision,payload) VALUES(?,?,?,?,?)", (bear_id, now(), action, revision, encode(payload)))

    def _bear_row(self, db, bear_id: str):
        if not isinstance(bear_id, str) or not ID_RE.fullmatch(bear_id):
            raise APIError(404, "Bear not found")
        row = db.execute("SELECT * FROM bears WHERE id=?", (bear_id,)).fetchone()
        if row is None:
            raise APIError(404, "Bear not found")
        return row

    def list(self) -> list:
        with self.connect() as db:
            return [self.detail(row[0], db) for row in db.execute("SELECT id FROM bears ORDER BY created DESC,id")]

    def detail(self, bear_id: str, db=None) -> dict:
        if db is None:
            with self.connect() as owned:
                return self.detail(bear_id, owned)
        row = self._bear_row(db, bear_id)
        bear = json.loads(row["metadata"])
        bear.update(id=bear_id, revision=row["revision"], created=row["created"], updated=row["updated"])
        sources = []
        for source in db.execute("SELECT * FROM sources WHERE bear_id=? ORDER BY revision", (bear_id,)):
            prefix = f"/assets/{bear_id}/sources/{source['revision']}/"
            names = json.loads(source["files"])
            sources.append({"revision": source["revision"], "sha256": source["sha256"], "created": source["created"],
                            "modelUrl": prefix + "model.glb", "thumbnailUrl": prefix + "thumb.webp" if "thumb.webp" in names else None,
                            "source": json.loads(source["source"]), "report": json.loads(source["report"]),
                            "stats": json.loads(source["stats"]), "manifestUrl": prefix + "manifest.json"})
        source = sources[-1]
        bear.update(sources=sources, sourceRevision=source["revision"], sourceSha256=source["sha256"],
                    modelUrl=source["modelUrl"], thumbnailUrl=source["thumbnailUrl"], source=source["source"],
                    sourceReport=source["report"], sourceStats=source["stats"])
        rigs = []
        for rig in db.execute("SELECT * FROM rigs WHERE bear_id=? ORDER BY revision", (bear_id,)):
            prefix = f"/assets/{bear_id}/rigs/{rig['revision']}/"
            rigs.append({"revision": rig["revision"], "sourceRevision": rig["source_revision"], "sourceSha256": rig["source_sha256"],
                         "sha256": rig["sha256"], "created": rig["created"], "recipe": json.loads(rig["recipe"]),
                         "validation": json.loads(rig["validation"]), "structuralValidation": json.loads(rig["structural"]),
                         "stats": json.loads(rig["stats"]), "modelUrl": prefix + "model.glb", "recipeUrl": prefix + "recipe.json",
                         "validationUrl": prefix + "validation.json", "manifestUrl": prefix + "manifest.json", "status": "draft",
                         "stale": rig["source_revision"] != source["revision"]})
        tests = [{"id": test["id"], "rigRevision": test["rig_revision"], "sourceRevision": test["source_revision"],
                  "created": test["created"], "suite": test["suite"], "results": json.loads(test["results"]), "notes": test["notes"],
                  "stale": test["source_revision"] != source["revision"]}
                 for test in db.execute("SELECT * FROM tests WHERE bear_id=? ORDER BY created DESC,id", (bear_id,))]
        current_rigs = [rig for rig in rigs if not rig["stale"]]
        draft_dirty = bool(current_rigs and bear.get("draftRecipe") is not None and bear["draftRecipe"] != current_rigs[-1]["recipe"])
        bear.update(rigs=rigs, tests=tests, draftDirty=draft_dirty,
                    rigStatus="draft-edited" if draft_dirty else "draft-rig" if current_rigs else "unrigged",
                    manifestUrl=f"/api/bears/{bear_id}/manifest")
        return bear

    def _write_bundle(self, relative: Path, files: dict[str, bytes]):
        destination = self.root / relative
        if destination.exists():
            raise APIError(409, "An artifact revision already exists; existing files were preserved")
        staging = self.root / ".staging" / uuid.uuid4().hex
        staging.mkdir(parents=True)
        try:
            for name, data in files.items():
                (staging / name).write_bytes(data)
            destination.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def import_source(self, identity: str, name: str, source: dict, files: dict[str, bytes]) -> dict:
        if "model.glb" not in files or set(files) - SCANNER_FILES:
            raise APIError(400, "Invalid source file bundle")
        stats, _ = parse_glb(files["model.glb"])
        report = object_json(files["report.json"]) if "report.json" in files else {"status": "unreviewed", "checks": []}
        for sidecar in ("collider.json", "cameras.json", "landmarks.json", "pack-manifest.json"):
            if sidecar in files:
                try:
                    bounded_json(json.loads(files[sidecar]), sidecar, 8 * 1024 * 1024)
                except (ValueError, UnicodeError) as error:
                    raise APIError(400, f"Invalid {sidecar}") from error
        name = text_value(name, "name", 200, True)
        bounded_json(source, "source")
        sha = digest(files["model.glb"])
        hashes = {name: digest(data) for name, data in files.items()}
        with self.lock, self.connect() as db:
            row = db.execute("SELECT * FROM bears WHERE identity=?", (identity,)).fetchone()
            if row:
                bear_id = row["id"]
                previous = db.execute("SELECT * FROM sources WHERE bear_id=? ORDER BY revision DESC LIMIT 1", (bear_id,)).fetchone()
                old_source = json.loads(previous['source'])
                old_pack, new_pack = old_source.get('pack'), source.get('pack')
                if old_pack and new_pack and new_pack['version'] < old_pack['version']:
                    raise APIError(409, "An older bear pack cannot replace the newer source in this catalogue")
                previous_manifest = object_json((self.root / 'assets' / bear_id / 'sources' / str(previous['revision']) / 'manifest.json').read_bytes())
                if previous["sha256"] == sha and previous_manifest.get('files') == hashes:
                    return {"bear": self.detail(bear_id, db), "imported": False}
                source_revision, revision = previous["revision"] + 1, row["revision"] + 1
                metadata = json.loads(row["metadata"])
                metadata.update(reviewStatus="unreviewed", draftRecipe=None)
                db.execute("UPDATE bears SET revision=?,updated=?,metadata=? WHERE id=?", (revision, now(), encode(metadata), bear_id))
            else:
                bear_id, source_revision, revision = "bear_" + uuid.uuid4().hex[:16], 1, 1
                metadata = {"name": name, "tags": ["prebuilt-sample"] if source.get("kind") == "bundled-sample" else [],
                            "notes": "", "role": "prop", "reviewStatus": "unreviewed", "draftRecipe": None}
                created = now()
                db.execute("INSERT INTO bears VALUES(?,?,?,?,?,?)", (bear_id, identity, revision, created, created, encode(metadata)))
            created = now()
            manifest = {"schema": 1, "bearId": bear_id, "sourceRevision": source_revision, "sourceSha256": sha,
                        "created": created, "source": source, "files": hashes, "stats": stats}
            bundle = dict(files, **{"manifest.json": encode(manifest).encode("utf-8")})
            self._write_bundle(Path("assets") / bear_id / "sources" / str(source_revision), bundle)
            db.execute("INSERT INTO sources VALUES(?,?,?,?,?,?,?,?)", (bear_id, source_revision, sha, created, encode(source), encode(report), encode(stats), encode(sorted(bundle))))
            self.event(db, bear_id, "source-imported", revision, {"sourceRevision": source_revision, "sha256": sha, "kind": source.get("kind")})
            return {"bear": self.detail(bear_id, db), "imported": True}

    def seed_sample(self):
        sample = ROOT / "Assets/ThirdParty/BearScannerSample"
        if not (sample / "model.glb").is_file():
            return
        provenance = object_json((sample / "provenance.json").read_bytes()) if (sample / "provenance.json").is_file() else {}
        scan_id = provenance.get("workshop_scan_id")
        identity = f"scanner:{self.scanner.url}#{scan_id}" if self.scanner and scan_id else "bundled:real-bear"
        with self.connect() as db:
            if db.execute("SELECT 1 FROM bears WHERE identity=?", (identity,)).fetchone():
                return
        files = {name: (sample / name).read_bytes() for name in SCANNER_FILES if (sample / name).is_file()}
        expected = provenance.get("files", {})
        if any(expected.get(name) and expected[name] != digest(data) for name, data in files.items()):
            raise APIError(409, "Bundled sample hash differs from its provenance; seed was not imported")
        self.import_source(identity, provenance.get("workshop_scan_name", "Bundled real bear (prebuilt sample)"),
                           {"kind": "bundled-sample", "scanId": scan_id, "scannerUrl": self.scanner.url if self.scanner else None,
                            "originalFilename": "model.glb", "provenance": provenance}, files)

    def import_scanner(self, scan_id: str) -> dict:
        if not self.scanner:
            raise APIError(503, "Scanner is not configured")
        meta, files = self.scanner.source(scan_id)
        return self.import_source(f"scanner:{self.scanner.url}#{scan_id}", meta.get("name") or "Scanned bear",
                                  {"kind": "scanner", "scanId": scan_id, "scannerUrl": self.scanner.url,
                                   "originalFilename": "model.glb", "scannerMetadata": meta,
                                   **({'pack': meta['pack']} if 'pack' in meta else {})}, files)

    def import_pack(self, filename: str, data: bytes) -> dict:
        filename = text_value(filename, "filename", 240, True)
        if any(c in filename for c in '/\\:') or not filename.lower().endswith('.zip'):
            raise APIError(400, "Supply one bear's pack ZIP filename, without folders")
        try:
            doc, files = bear_pack.archive(data)
        except ValueError as error:
            raise APIError(400, str(error)) from error
        return self.import_source(f"pack:{doc['id']}", doc.get('name') or 'Packed bear',
                                  {'kind': 'bear-pack', 'scanId': doc['id'], 'originalFilename': filename,
                                   'pack': object_json(files['pack-manifest.json'])}, files)

    def import_local(self, filename: str, data: bytes) -> dict:
        filename = text_value(filename, "filename", 240, True)
        if "/" in filename or "\\" in filename or ":" in filename or not filename.lower().endswith(".glb"):
            raise APIError(400, "Supply a .glb filename, without folders")
        return self.import_source("local:" + digest(data), filename[:-4] or "Local bear", {"kind": "local-file", "originalFilename": filename}, {"model.glb": data})

    def patch(self, bear_id: str, body: dict) -> dict:
        expected = integer(body.get("expectedRevision"), "expectedRevision", 1)
        allowed = {"expectedRevision", "name", "tags", "notes", "role", "reviewStatus", "draftRecipe"}
        if set(body) - allowed:
            raise APIError(400, "Unknown catalogue fields")
        updates = {}
        for field, limit in (("name", 200), ("notes", 20000), ("role", 80)):
            if field in body:
                updates[field] = text_value(body[field], field, limit, field == "name")
        if "tags" in body:
            tags = body["tags"]
            if not isinstance(tags, list) or len(tags) > 32:
                raise APIError(400, "tags must be an array of at most 32 strings")
            updates["tags"] = list(dict.fromkeys(text_value(tag, "tag", 80, True) for tag in tags))
        if "reviewStatus" in body:
            if body["reviewStatus"] not in ("unreviewed", "needs-work", "approved"):
                raise APIError(400, "Unknown review status")
            updates["reviewStatus"] = body["reviewStatus"]
        if "draftRecipe" in body:
            if body["draftRecipe"] is not None and not isinstance(body["draftRecipe"], dict):
                raise APIError(400, "draftRecipe must be an object or null")
            updates["draftRecipe"] = bounded_json(body["draftRecipe"], "draftRecipe")
        with self.lock, self.connect() as db:
            row = self._bear_row(db, bear_id)
            if row["revision"] != expected:
                raise APIError(409, "Catalogue changed in another window; reload before saving")
            metadata = json.loads(row["metadata"])
            if isinstance(updates.get("draftRecipe"), dict):
                source = db.execute("SELECT revision,sha256 FROM sources WHERE bear_id=? ORDER BY revision DESC LIMIT 1", (bear_id,)).fetchone()
                check_recipe_source(updates["draftRecipe"], source["revision"], source["sha256"])
            if "draftRecipe" in updates and updates["draftRecipe"] != metadata.get("draftRecipe"):
                updates["reviewStatus"] = "unreviewed"
            metadata.update(updates)
            revision = row["revision"] + 1
            db.execute("UPDATE bears SET revision=?,updated=?,metadata=? WHERE id=?", (revision, now(), encode(metadata), bear_id))
            self.event(db, bear_id, "metadata-saved", revision, {"fields": sorted(updates), "values": updates})
            return self.detail(bear_id, db)

    def add_rig(self, bear_id: str, body: dict) -> dict:
        source_revision = integer(body.get("sourceRevision"), "sourceRevision", 1)
        source_sha = text_value(body.get("sourceSha256"), "sourceSha256", 64, True)
        recipe, validation = body.get("recipe"), body.get("validation", {})
        if not isinstance(recipe, dict) or not isinstance(validation, dict):
            raise APIError(400, "recipe and validation must be JSON objects")
        bounded_json(recipe, "recipe")
        bounded_json(validation, "validation")
        encoded = body.get("glbBase64")
        if not isinstance(encoded, str) or not encoded:
            raise APIError(400, "A complete exported GLB is required; use draftRecipe for settings only")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise APIError(400, "Invalid GLB base64 data") from error
        stats, structural = parse_glb(data, require_skin=True)
        sha = digest(data)
        with self.lock, self.connect() as db:
            row = self._bear_row(db, bear_id)
            source = db.execute("SELECT * FROM sources WHERE bear_id=? ORDER BY revision DESC LIMIT 1", (bear_id,)).fetchone()
            if source["revision"] != source_revision or source["sha256"] != source_sha:
                raise APIError(409, "Rig source no longer matches the current source revision and hash")
            check_recipe_source(recipe, source_revision, source_sha)
            rig_revision = db.execute("SELECT COALESCE(MAX(revision),0)+1 FROM rigs WHERE bear_id=?", (bear_id,)).fetchone()[0]
            created = now()
            manifest = {"schema": 1, "bearId": bear_id, "rigRevision": rig_revision, "sourceRevision": source_revision,
                        "sourceSha256": source_sha, "sha256": sha, "created": created, "status": "draft", "stats": stats,
                        "structuralValidation": structural}
            files = {"model.glb": data, "recipe.json": encode(recipe).encode("utf-8"),
                     "validation.json": encode({"reported": validation, "structural": structural}).encode("utf-8"),
                     "manifest.json": encode(manifest).encode("utf-8")}
            self._write_bundle(Path("assets") / bear_id / "rigs" / str(rig_revision), files)
            db.execute("INSERT INTO rigs VALUES(?,?,?,?,?,?,?,?,?,?)", (bear_id, rig_revision, source_revision, source_sha, sha,
                       created, encode(recipe), encode(validation), encode(structural), encode(stats)))
            metadata = json.loads(row["metadata"])
            metadata.update(draftRecipe=recipe, reviewStatus="unreviewed")
            revision = row["revision"] + 1
            db.execute("UPDATE bears SET revision=?,updated=?,metadata=? WHERE id=?", (revision, created, encode(metadata), bear_id))
            self.event(db, bear_id, "rig-saved", revision, {"rigRevision": rig_revision, "sourceRevision": source_revision, "sha256": sha})
            bear = self.detail(bear_id, db)
            return {"bear": bear, "rig": bear["rigs"][-1]}

    def add_test(self, bear_id: str, body: dict) -> dict:
        rig_revision = integer(body.get("rigRevision"), "rigRevision", 1)
        suite = text_value(body.get("suite"), "suite", 160, True)
        notes = text_value(body.get("notes", ""), "notes", 20000)
        results = body.get("results")
        if not isinstance(results, (dict, list)):
            raise APIError(400, "results must be an array or object")
        bounded_json(results, "results")
        with self.lock, self.connect() as db:
            row = self._bear_row(db, bear_id)
            rig = db.execute("SELECT * FROM rigs WHERE bear_id=? AND revision=?", (bear_id, rig_revision)).fetchone()
            if not rig:
                raise APIError(409, "Save a real rig revision before recording its tests")
            test_id, created = "test_" + uuid.uuid4().hex[:16], now()
            db.execute("INSERT INTO tests VALUES(?,?,?,?,?,?,?,?)", (test_id, bear_id, rig_revision, rig["source_revision"], created, suite, encode(results), notes))
            revision = row["revision"] + 1
            db.execute("UPDATE bears SET revision=?,updated=? WHERE id=?", (revision, created, bear_id))
            self.event(db, bear_id, "test-recorded", revision, {"testId": test_id, "rigRevision": rig_revision, "suite": suite})
            bear = self.detail(bear_id, db)
            return {"bear": bear, "test": next(test for test in bear["tests"] if test["id"] == test_id)}

    def history(self, bear_id: str) -> list:
        with self.connect() as db:
            self._bear_row(db, bear_id)
            return [{"id": row["id"], "created": row["created"], "action": row["action"], "revision": row["revision"], "payload": json.loads(row["payload"])}
                    for row in db.execute("SELECT * FROM history WHERE bear_id=? ORDER BY id DESC", (bear_id,))]

    def asset(self, path: str) -> Path:
        parts = path.strip("/").split("/")
        if len(parts) != 5 or parts[0] != "assets" or not ID_RE.fullmatch(parts[1]) or parts[2] not in ("sources", "rigs") or not parts[3].isdigit() or int(parts[3]) < 1:
            raise APIError(404, "Asset not found")
        if parts[4] not in (SOURCE_FILES if parts[2] == "sources" else RIG_FILES):
            raise APIError(404, "Asset not found")
        with self.connect() as db:
            if not db.execute(f"SELECT 1 FROM {parts[2]} WHERE bear_id=? AND revision=?", (parts[1], int(parts[3]))).fetchone():
                raise APIError(404, "Asset not found")
        resolved = (self.root / Path(*parts)).resolve()
        if not resolved.is_relative_to(self.root / "assets") or not resolved.is_file():
            raise APIError(404, "Asset not found")
        return resolved


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, store: Store, web_dir: Path = WEB):
        if address[0] != "127.0.0.1":
            raise ValueError("Bear Studio binds 127.0.0.1 only")
        self.store = store
        self.web_dir = web_dir.resolve()
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "BearStudio/1"

    def log_message(self, format, *args):
        # Basic server logs without user-supplied terminal control characters.
        message = format % args
        print(f"{now()} {message.encode('unicode_escape').decode('ascii')}", flush=True)

    def _guard(self):
        expected = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        host = self.headers.get("Host", "").lower()
        if host not in expected:
            raise APIError(421, "Unknown host")
        if self.command not in ("GET", "HEAD"):
            origin = self.headers.get("Origin")
            if origin is not None and origin != "http://" + host:
                raise APIError(403, "Cross-site mutation refused")
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                raise APIError(403, "Cross-site mutation refused")
        self.connection.settimeout(20)

    def _body(self, limit: int) -> bytes:
        if self.headers.get("Transfer-Encoding"):
            raise APIError(411, "Content-Length is required")
        value = self.headers.get("Content-Length")
        if value is None or not value.isdigit():
            raise APIError(411, "Content-Length is required")
        length = int(value)
        if length > limit:
            raise APIError(413, "Request exceeds the upload limit")
        data = self.rfile.read(length)
        if len(data) != length:
            raise APIError(400, "Incomplete request body")
        return data

    def _json_body(self, limit: int = MAX_JSON) -> dict:
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            raise APIError(415, "Content-Type application/json is required")
        return object_json(self._body(limit))

    def _headers(self, status: int, mime: str, length: int):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")

    def _json(self, data, status: int = 200, filename: str | None = None):
        body = encode(data).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(body))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _file(self, path: Path):
        mime = {".js": "text/javascript", ".mjs": "text/javascript", ".glb": "model/gltf-binary"}.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._headers(200, mime, path.stat().st_size)
        self.end_headers()
        if self.command != "HEAD":
            with path.open("rb") as source:
                shutil.copyfileobj(source, self.wfile)

    def _dispatch(self):
        self._guard()
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        if "\\" in path or "\x00" in path:
            raise APIError(404, "Not found")
        store = self.server.store
        method = "GET" if self.command == "HEAD" else self.command
        if method == "GET":
            if path == "/api/health":
                return self._json({"ok": True, "app": "bear-studio", "version": 1, "scannerUrl": store.scanner.url if store.scanner else None,
                                   "workspace": str(ROOT), "dataDir": str(store.root)})
            if path == "/api/scanner/scans":
                try:
                    if not store.scanner:
                        raise APIError(503, "Scanner not configured")
                    return self._json({"available": True, "scans": store.scanner.scans()})
                except APIError as error:
                    return self._json({"available": False, "scans": [], "error": str(error)})
            if path == "/api/bears":
                return self._json({"bears": store.list()})
            match = re.fullmatch(r"/api/bears/(bear_[0-9a-f]{16})(?:/(history|manifest))?", path)
            if match:
                bear_id, action = match.groups()
                if action == "history":
                    return self._json({"history": store.history(bear_id)})
                return self._json(store.detail(bear_id), filename=f"{bear_id}-manifest.json" if action == "manifest" else None)
            if path.startswith("/assets/"):
                return self._file(store.asset(path))
            if path in LIBRARY_FILES:
                if not LIBRARY_FILES[path].is_file():
                    raise APIError(404, "Animation library file is not available in this checkout")
                return self._file(LIBRARY_FILES[path])
            if path.startswith("/api/"):
                raise APIError(404, "API route not found")
            relative = path.lstrip("/") or "index.html"
            resolved = (self.server.web_dir / relative).resolve()
            if not resolved.is_relative_to(self.server.web_dir) or not resolved.is_file() or resolved.suffix.lower() not in (".html", ".css", ".js", ".mjs", ".json", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".woff2", ".txt"):
                raise APIError(404, "Page not found")
            return self._file(resolved)
        if method == "POST" and path == "/api/import/local":
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
            if content_type not in ("model/gltf-binary", "application/octet-stream"):
                raise APIError(415, "Send raw GLB bytes")
            filename = urllib.parse.unquote(self.headers.get("X-Filename", "Imported bear.glb"))
            return self._json(store.import_local(filename, self._body(MAX_GLB)), 201)
        if method == "POST" and path == "/api/import/pack":
            content_type = self.headers.get('Content-Type', '').split(';', 1)[0].strip()
            if content_type not in ('application/zip', 'application/octet-stream'):
                raise APIError(415, 'Send a bear-pack ZIP')
            filename = urllib.parse.unquote(self.headers.get('X-Filename', 'Bear.zip'))
            return self._json(store.import_pack(filename, self._body(bear_pack.MAX_PACK)), 201)
        if method == "POST" and path == "/api/import/scanner":
            return self._json(store.import_scanner(self._json_body().get("scanId")), 201)
        match = re.fullmatch(r"/api/bears/(bear_[0-9a-f]{16})(?:/(rigs|tests))?", path)
        if match:
            bear_id, action = match.groups()
            if method == "PATCH" and action is None:
                return self._json(store.patch(bear_id, self._json_body()))
            if method == "POST" and action == "rigs":
                return self._json(store.add_rig(bear_id, self._json_body(MAX_RIG_JSON)), 201)
            if method == "POST" and action == "tests":
                return self._json(store.add_test(bear_id, self._json_body()), 201)
        raise APIError(404, "API route not found")

    def _run(self):
        try:
            self._dispatch()
        except APIError as error:
            self._json({"error": str(error)}, error.status)
        except (ConnectionError, TimeoutError):
            self.close_connection = True
        except Exception as error:
            print(f"{now()} Request failed: {type(error).__name__}: {str(error)!r}", flush=True)
            self._json({"error": "Studio request failed; existing source files were preserved"}, 500)

    do_GET = do_HEAD = do_POST = do_PATCH = do_DELETE = do_OPTIONS = _run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8472)
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".team-local/bear-studio")
    parser.add_argument("--no-seed", action="store_true", help="Do not seed the repository's labelled sample")
    args = parser.parse_args()
    scanner_url, cert = settings()
    store = Store(args.data_dir, Scanner(scanner_url, cert), seed=not args.no_seed)
    server = StudioServer(("127.0.0.1", args.port), store)
    print(f"Bear Studio: http://127.0.0.1:{server.server_port}/", flush=True)
    print(f"Persistent catalogue: {store.root}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
