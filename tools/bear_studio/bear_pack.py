"""Read the team's bear-pack v1 contract without extracting uploaded archives."""
from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import PurePosixPath

MAX_PACK = 128 * 1024 * 1024
MAX_MODEL = 64 * 1024 * 1024
MAX_SIDECAR = 8 * 1024 * 1024
PLAIN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ROLES = {"model": "model.glb", "report": "report.json", "collider": "collider.json",
         "thumbnail": "thumb.webp", "landmarks": "landmarks.json"}


def document(raw: bytes) -> dict:
    if len(raw) > 512 * 1024:
        raise ValueError("Bear-pack manifest exceeds 512 KiB")
    try:
        doc = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise ValueError("Invalid bear-pack manifest JSON") from error
    if not isinstance(doc, dict) or doc.get("format") != "bear-pack" or type(doc.get("formatVersion")) is not int or doc["formatVersion"] != 1:
        raise ValueError("Expected a bear-pack formatVersion 1 manifest")
    if not isinstance(doc.get("id"), str) or not PLAIN.fullmatch(doc["id"]):
        raise ValueError("Invalid bear-pack identity")
    if type(doc.get("version")) is not int or doc["version"] < 0:
        raise ValueError("Invalid bear-pack version")
    if not isinstance(doc.get("revision"), str) or not re.fullmatch(r"[a-f0-9]{32,64}", doc["revision"]):
        raise ValueError("Invalid bear-pack content revision")
    coordinates = doc.get("coordinates", {})
    if not isinstance(coordinates, dict) or any(coordinates.get(k) != v for k, v in
            {"units": "meters", "handedness": "right", "up": "+Y", "front": "+Z"}.items()):
        raise ValueError("Bear packs must use metres, right-handed axes, +Y up and +Z front")
    files = doc.get("files")
    if not isinstance(files, dict) or not 1 <= len(files) <= 32:
        raise ValueError("Bear-pack file list is missing or too large")
    model = doc.get("model")
    if not isinstance(model, dict) or not isinstance(model.get("file"), str) or model["file"] not in files:
        raise ValueError("Bear-pack model is not listed in its manifest")
    for name, entry in files.items():
        if not isinstance(name, str) or not PLAIN.fullmatch(name) or not isinstance(entry, dict):
            raise ValueError("Bear-pack files must be plain filenames")
        limit = MAX_MODEL if name == model["file"] else MAX_SIDECAR
        if type(entry.get("bytes")) is not int or not 0 <= entry["bytes"] <= limit:
            raise ValueError(f"Invalid or oversized bear-pack file: {name}")
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"]):
            raise ValueError(f"Invalid SHA-256 for {name}")
    if sum(entry["bytes"] for entry in files.values()) > MAX_PACK:
        raise ValueError("Bear pack exceeds the total import limit")
    for role in ROLES:
        if role in doc and (not isinstance(doc[role], dict) or not isinstance(doc[role].get("file"), str) or doc[role]["file"] not in files):
            raise ValueError(f"Bear-pack {role} is not listed in its manifest")
    return doc


def verified(doc: dict, read) -> dict[str, bytes]:
    """Verify every declared file, then keep the supported roles and manifest."""
    found = {}
    for name, entry in doc["files"].items():
        data = read(name, entry["bytes"])
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"{name} does not match its bear-pack manifest; obtain a complete export")
        found[name] = data
    files = {canonical: found[doc[role]["file"]] for role, canonical in ROLES.items() if role in doc}
    # API URLs and rebuild state describe transport, not a saved source revision.
    saved = {key: value for key, value in doc.items() if key not in ("urls", "building")}
    files["pack-manifest.json"] = json.dumps(saved, sort_keys=True, separators=(",", ":")).encode()
    return files


def archive(data: bytes) -> tuple[dict, dict[str, bytes]]:
    if len(data) > MAX_PACK:
        raise ValueError("Bear-pack ZIP exceeds 128 MiB")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zipped:
            members = zipped.infolist()
            if len(members) > 128 or sum(item.file_size for item in members) > MAX_PACK:
                raise ValueError("Bear-pack ZIP expands beyond the import limit")
            names = {}
            for item in members:
                path = PurePosixPath(item.filename)
                if (path.is_absolute() or "\\" in item.filename or ":" in item.filename or
                        ".." in path.parts or item.flag_bits & 1 or
                        stat.S_ISLNK(item.external_attr >> 16) or item.filename.casefold() in names):
                    raise ValueError("Bear-pack ZIP contains an unsafe or duplicate path")
                names[item.filename.casefold()] = item
            manifests = [item for item in members if not item.is_dir() and PurePosixPath(item.filename).name == "manifest.json"]
            if len(manifests) != 1:
                raise ValueError("Choose one bear's pack ZIP; combined multi-bear archives are not supported here")
            manifest = manifests[0]
            if manifest.file_size > 512 * 1024:
                raise ValueError("Bear-pack manifest exceeds 512 KiB")
            doc = document(zipped.read(manifest))
            parent = PurePosixPath(manifest.filename).parent

            def read(name, length):
                target = str(parent / name)
                item = next((i for i in members if i.filename == target and not i.is_dir()), None)
                if item is None or item.file_size != length:
                    raise ValueError(f"Bear pack is missing a complete {name}")
                return zipped.read(item)

            return doc, verified(doc, read)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
        raise ValueError("Invalid or unsupported bear-pack ZIP") from error
