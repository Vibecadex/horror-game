"""Import scanned bears into Unreal Engine 5 as ready-to-use Static Meshes.

Run inside the UE editor (needs the Python Editor Script Plugin: Edit > Plugins):
    Tools > Execute Python Script...  and pick this file
or headless, as a commandlet:
    UnrealEditor-Cmd.exe <project>.uproject -run=pythonscript -script="<this file>" -nullrhi -unattended
(the Teddy project wraps this as tools/import_scanned_bears.py).

This is the reference Unreal client of the bear pack contract (docs/BEAR_PACK.md);
game teams can use it as is or adapt it in their own project.

Where the bears come from (first that applies):
  * SOURCE: a bear pack (.zip, bears.zip from the workshop's "Download all bears",
    or an unpacked pack folder with manifest.json), a .glb, or a folder of any of
    these (a scanner's data/scans folder works too: only finished scans' out/model.glb)
  * otherwise every finished bear on the bear scanner's /api/v1/bears (SCANNER, pinned
    to its certificate); each model.glb is checked against its manifest's hash

Each bear becomes <DEST>/<Name>_<id>/SM_Bear_<Name>: one Static Mesh with the scan's
three detail levels as LOD0-2, a convex collision hull, and the scan's material and
texture. Re-runs import only new or rebuilt bears: a pack with the same revision is up to
date, and one older than what's imported (lower version) is skipped, as are older
duplicates of a bear found twice in the sources. A rebuilt bear is copied into its
existing mesh asset, so the asset path never changes and placed copies update without
redirectors. A bear is only marked imported after its LODs, material and collision
have been checked, so a failed import is retried next time.

Everything created is tagged BearScanner.Owner. The script never deletes a folder that
holds an asset it didn't create (or can't load), and deletes an old material/texture
only when nothing references it any more.

Axes and units are converted by UE's glTF importer: real size in cm, Z up, pivot
under the feet. The bear's front (glTF +Z) should face -X; confirm on first import.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import ssl
import struct
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import unreal

# ---- settings (environment variables BEAR_SOURCE etc. override these) -------------
SOURCE = ""                           # a .glb or a folder; "" = the scanner
SCANNER = "https://127.0.0.1:8443"    # the scanner's address
CERT = ""                             # its certificate; "" = data/certs/cert.pem in this repo
DEST = "/Game/ScannedBears"           # content folder bears are imported into
FORCE = False                         # re-import even if nothing changed
# ---------------------------------------------------------------------------------

SOURCE = os.environ.get("BEAR_SOURCE", SOURCE)
SCANNER = os.environ.get("BEAR_SCANNER", SCANNER).rstrip("/")
CERT = os.environ.get("BEAR_CERT", CERT)
DEST = os.environ.get("BEAR_DEST", DEST).rstrip("/")
FORCE = FORCE or os.environ.get("BEAR_FORCE") == "1"

IMPORTER_API = 5  # wrappers (the Teddy project's tools/import_scanned_bears.py) check this
OWNER_TAG, OWNER = "BearScanner.Owner", "bear-scanner"
VERSION_TAG, SCAN_TAG, REVISION_TAG, MODEL_TAG = "BearScanVersion", "BearScanId", "BearPackRevision", "BearModelSha256"
REPO = Path(globals().get("__file__") or ".").resolve().parent.parent
TMP = Path(tempfile.gettempdir()) / "bear-scanner-ue"
PACK_FORMAT = 1  # newest bear pack format (docs/BEAR_PACK.md) this importer reads
MAX_DOWNLOAD = 200 * 1024 * 1024
LOD_COUNT = 3

assets = unreal.EditorAssetLibrary
meshes = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def safe(name: str, limit: int = 40) -> str:
    """Unreal asset names: letters, digits and underscores, kept short for Windows paths."""
    return (re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]", "_", name)).strip("_") or "Bear")[:limit]


def source_identity(value) -> str:
    """Pack IDs are opaque metadata, not Unreal package names."""
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or any(ord(c) < 32 for c in value):
        raise ValueError("invalid bear-pack identity")
    return value


def package(asset) -> str:
    """/Game/ScannedBears/X/SM_Bear_X.SM_Bear_X -> /Game/ScannedBears/X/SM_Bear_X"""
    return asset.get_path_name().split(".")[0]


def asset_class(path: str) -> str:
    """Class name from the asset registry, without loading the asset."""
    data = assets.find_asset_data(path)
    try:
        return str(data.asset_class_path.asset_name)
    except AttributeError:  # before UE 5.1
        return str(data.asset_class)


# ---- finding bears ----------------------------------------------------------------

def scan_dir_of(glb: Path, stop: Path):
    """The scanner scan folder (holding meta.json) a file sits in, if any."""
    for d in glb.parents:
        if (d / "meta.json").exists():
            return d
        if d == stop:
            return None
    return None


PLAIN_NAME = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]*")


def is_pack(folder: Path) -> bool:
    """Only a bear-pack manifest makes a folder a pack; any other manifest.json
    (a web app's, say) is ignored and the folder's .glb files import as usual."""
    try:
        text = (folder / "manifest.json").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    try:
        doc = json.loads(text)
        return isinstance(doc, dict) and doc.get("format") == "bear-pack"
    except ValueError:
        return '"bear-pack"' in text  # a damaged pack manifest: report it, don't import around it


def pack_bear(folder: Path) -> dict:
    """A bear pack folder (manifest.json + files, docs/BEAR_PACK.md), checked: a
    known format version, a model file that is a plain name inside the folder,
    and a model.glb that matches the manifest's hash. Never raises: a bad pack
    becomes a bear with an error, so the others still import."""
    try:
        m = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(m, dict) or m.get("format") != "bear-pack":
            raise ValueError("manifest.json isn't a bear pack manifest")
        fv = m.get("formatVersion")
        if not isinstance(fv, int) or fv > PACK_FORMAT:
            raise ValueError(f"pack format {fv!r} is newer than this importer; update bear-scanner")
        name_in_pack = m["model"]["file"]
        if not isinstance(name_in_pack, str) or not PLAIN_NAME.fullmatch(name_in_pack):
            raise ValueError(f"model.file {name_in_pack!r} isn't a plain file name inside the pack")
        model = folder / name_in_pack
        if model.resolve().parent != folder.resolve():
            raise ValueError(f"model.file {name_in_pack!r} points outside the pack")
        want = m["files"][name_in_pack]["sha256"]
        if hashlib.sha256(model.read_bytes()).hexdigest() != want:
            raise ValueError(f"{name_in_pack} doesn't match its manifest (incomplete copy?)")
        version = int(m["version"])
        sid = source_identity(m["id"])
        name = str(m.get("name") or "Bear")
        revision = str(m.get("revision") or want[:32])
    except Exception as e:  # noqa: BLE001 - any malformed pack: report it, carry on
        return {"id": safe(folder.name, 24), "name": folder.name, "key": safe(folder.name), "version": "",
                "error": f"{folder}: {type(e).__name__}: {e}"}
    return {"id": sid, "name": name, "key": f"{safe(name)}_{safe(sid[:6])}", "version": str(version),
            "revision": revision, "modelSha": want, "glb": model}


def unzip(archive: Path) -> Path:
    """Unpack a pack zip (one bear, or bears.zip) into TMP, refusing paths that
    would land outside it and archives that unpack to something huge."""
    dest = TMP / "unzipped" / f"{safe(archive.stem)}_{int(archive.stat().st_mtime)}"
    shutil.rmtree(dest, ignore_errors=True)
    with zipfile.ZipFile(archive) as zf:
        members = zf.infolist()
        if sum(m.file_size for m in members) > 20 * MAX_DOWNLOAD:
            raise RuntimeError(f"{archive.name} unpacks to more than {20 * MAX_DOWNLOAD // 2**30} GB")
        for m in members:
            parts = Path(m.filename.replace("\\", "/")).parts
            if Path(m.filename).is_absolute() or ".." in parts or ":" in m.filename:
                raise RuntimeError(f"{archive.name}: unsafe path {m.filename!r}")
        zf.extractall(dest)
    return dest


def _hidden(path: Path, stop: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(stop).parts)


def local_bears(source: Path) -> list[dict]:
    if not source.exists():
        raise RuntimeError(f"SOURCE {source} doesn't exist")
    bears = []
    roots = []  # (folder to search, folder it's relative to)
    if source.is_file() and source.suffix.lower() == ".zip":
        roots.append(unzip(source))
        source = None
    elif source.is_dir():
        roots.append(source)
        for archive in sorted(source.rglob("*.zip")):
            if _hidden(archive, source):
                continue
            try:
                roots.append(unzip(archive))
            except Exception as e:  # noqa: BLE001 - a bad zip fails alone
                bears.append({"id": safe(archive.stem, 24), "name": archive.stem, "key": safe(archive.stem),
                              "version": "", "error": f"{archive}: {type(e).__name__}: {e}"})
    packs = sorted({p.parent for root in roots for p in root.rglob("manifest.json")
                    if not _hidden(p, root) and is_pack(p.parent)})
    bears += [pack_bear(d) for d in packs]

    if source is None:
        return bears
    stop = source.parent if source.is_file() else source
    files = [source] if source.is_file() else sorted(source.rglob("*.glb"))
    for glb in files:
        if _hidden(glb, stop):
            continue
        if any(d == glb.parent or d in glb.parents for d in packs):
            continue  # already taken as a pack
        scan = scan_dir_of(glb, stop)
        if scan:
            # Inside a scanner scan only the published model counts: not work files,
            # not a half-written out.new, and only once the scan has finished.
            if glb != scan / "out" / "model.glb":
                continue
            meta = json.loads((scan / "meta.json").read_text())
            if meta.get("status", "done") != "done":
                continue
            sid = safe(str(meta.get("id") or scan.name), 24)
            name = meta.get("name") or scan.name
        else:
            # A downloaded bear is named by its file (Rupert.glb); a folder holding a
            # model.glb by the folder.
            name = glb.parent.name if glb.stem == "model" else glb.stem
            sid = safe(name, 24)
        bears.append({"id": sid, "name": name, "key": f"{safe(name)}_{sid[:6]}" if scan else safe(name),
                      "version": str(int(glb.stat().st_mtime)), "glb": glb})
    return bears


def server_bears() -> list[dict]:
    if SCANNER.startswith("https://"):
        cert = Path(CERT) if CERT else REPO / "data" / "certs" / "cert.pem"
        if not cert.exists():
            raise RuntimeError(f"Scanner certificate not found at {cert}. Start the scanner "
                               "once (it creates it), or set CERT or SOURCE.")
        ctx = ssl.create_default_context(cafile=str(cert))
        ctx.check_hostname = False  # trust exactly this certificate, whatever address it's reached on
        handlers = [urllib.request.HTTPSHandler(context=ctx)]
    else:
        cert, handlers = None, []
    # No proxy: the scanner is on this PC or the LAN, and its traffic stays there.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), *handlers)

    def get(path: str) -> bytes:
        with opener.open(SCANNER + path, timeout=60) as r:
            data = r.read(MAX_DOWNLOAD + 1)
        if len(data) > MAX_DOWNLOAD:
            raise RuntimeError(f"{path}: larger than {MAX_DOWNLOAD // 2**20} MB")
        return data

    try:
        index = json.loads(get("/api/v1/bears"))
        if not isinstance(index, dict) or index.get("format") != "bear-pack-index":
            raise ValueError("not a bear pack index")
        fv = index.get("formatVersion")
        if not isinstance(fv, int) or fv > PACK_FORMAT:
            raise RuntimeError(f"{SCANNER} serves bear pack format {fv!r}; update bear-scanner")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"{SCANNER} is reachable but has no /api/v1/bears: it's running an older "
                               "bear-scanner. Update it and restart it.") from None
        raise RuntimeError(f"{SCANNER}/api/v1/bears answered {e.code} {e.reason}") from None
    except (OSError, ValueError) as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            raise RuntimeError(f"{SCANNER} sent a different certificate than {cert}. Point CERT "
                               "at that scanner's data/certs/cert.pem.") from None
        raise RuntimeError(f"Can't read the scanner's bear pack API at {SCANNER}/api/v1/bears ({e}). "
                           "Is it running? Or set SOURCE to a pack, .glb or folder.") from None

    def fetch(bear: dict, b: dict, dest: Path) -> Path:
        # The manifest names the model file and its hash; a download that doesn't
        # match is refused. Version and revision are taken from that manifest, so
        # a rebuild between the listing and the download is recorded correctly.
        manifest = json.loads(get(b["urls"]["manifest"]))
        model = manifest["model"]["file"]
        data = get(manifest["urls"]["files"][model])
        if hashlib.sha256(data).hexdigest() != manifest["files"][model]["sha256"]:
            raise RuntimeError(f"downloaded {model} doesn't match its manifest (rebuilt meanwhile? run again)")
        bear.update(version=str(int(manifest["version"])), revision=str(manifest["revision"]),
                    modelSha=manifest["files"][model]["sha256"])
        dest.write_bytes(data)
        return dest

    bears = []
    for b in index.get("bears", []):
        name = str(b.get("name") or "Bear")
        sid = source_identity(b["id"])
        bear = {"id": sid, "name": name, "key": f"{safe(name)}_{safe(sid[:6])}", "version": str(b["version"]),
                "revision": str(b.get("revision") or ""), "modelSha": str(b.get("modelSha256") or ""),
                "download": TMP / f"{hashlib.sha256(sid.encode()).hexdigest()}.glb"}
        bear["fetch"] = (lambda bear=bear, b=b: fetch(bear, b, bear["download"]))
        bears.append(bear)
    return bears


def newest_per_id(bears: list[dict]) -> tuple[list[dict], list[dict]]:
    """Two sources for the same bear (an old export next to bears.zip, say): keep
    the newest version and report the rest as skipped."""
    keep: dict[str, dict] = {}
    skipped = []
    for b in bears:
        if "error" in b:
            continue
        other = keep.get(b["id"])
        if other is None or _int(b["version"]) > _int(other["version"]):
            if other:
                skipped.append(other)
            keep[b["id"]] = b
        else:
            skipped.append(b)
    return [b for b in bears if "error" in b] + list(keep.values()), skipped


def _int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return -1


# ---- one GLB per detail level -------------------------------------------------------

def split_lods(glb: Path, work: Path, stem: str, material: str) -> list[Path]:
    """Write one single-mesh GLB per LOD node. Each import then yields exactly one
    Static Mesh whatever the importer's mesh-combining defaults are, and we know
    which level it is. Every file names its material the same, so the levels share
    one material slot. Only the JSON changes; the binary chunk is reused as is."""
    data = glb.read_bytes()
    magic, _, _ = struct.unpack_from("<4sII", data, 0)
    json_len, json_type = struct.unpack_from("<I4s", data, 12)
    if magic != b"glTF" or json_type != b"JSON":
        raise RuntimeError(f"{glb.name} isn't a binary glTF file")
    doc = json.loads(data[20:20 + json_len])
    rest = data[20 + json_len:]  # the BIN chunk, header included

    levels = []
    for node in doc.get("nodes", []):
        m = re.fullmatch(r"LOD(\d+)", node.get("name") or "")
        if m and "mesh" in node:
            levels.append((int(m.group(1)), node))
    if not levels:  # an older scan with one plain mesh
        plain = [n for n in doc.get("nodes", []) if "mesh" in n]
        if not plain:
            raise RuntimeError(f"{glb.name} has no mesh")
        levels = [(0, plain[0])]
    levels.sort(key=lambda x: x[0])
    for _, node in levels:
        if any(k in node for k in ("matrix", "translation", "rotation", "scale", "children")):
            raise RuntimeError(f"{glb.name}: node {node.get('name')} has a transform; "
                               "scanner models have none, so this isn't one")

    if doc.get("materials"):
        doc["materials"] = [dict(m, name=material) for m in doc["materials"]]
    if doc.get("images"):
        doc["images"] = [dict(im, name=f"T_{material[3:]}" if material.startswith("MI_") else material)
                         for im in doc["images"]]

    work.mkdir(parents=True, exist_ok=True)
    files = []
    for i, node in levels:
        part = dict(doc)
        mesh = dict(doc["meshes"][node["mesh"]], name=f"{stem}_LOD{i}")
        part["meshes"] = [mesh]
        part["nodes"] = [{"name": mesh["name"], "mesh": 0}]
        part["scenes"] = [{"nodes": [0]}]
        part["scene"] = 0
        text = json.dumps(part, separators=(",", ":")).encode()
        text += b" " * (-len(text) % 4)
        body = struct.pack("<I4s", len(text), b"JSON") + text + rest
        path = work / (f"{stem}.glb" if i == 0 else f"{stem}_LOD{i}.glb")
        path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
        files.append(path)
    return files


# ---- importing ----------------------------------------------------------------------

def import_glb(glb: Path, folder: str) -> list:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(glb))
    task.set_editor_property("destination_path", folder)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", False)
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    try:
        objects = list(task.get_objects() or [])
    except AttributeError:
        objects = []
    if not objects:
        objects = [assets.load_asset(p) for p in task.get_editor_property("imported_object_paths") or []]
    # The importer puts everything under <folder>/<file stem>/; tag all of it,
    # including anything it made but didn't report.
    sub = f"{folder}/{glb.stem}"
    for p in assets.list_assets(sub, recursive=True, include_folder=False) if assets.does_directory_exist(sub) else []:
        a = assets.load_asset(p)
        if a is not None and a not in objects:
            objects.append(a)
    objects = [o for o in objects if o]
    if not objects:
        raise RuntimeError(f"{glb.name}: the importer returned nothing")
    for o in objects:
        if not package(o).startswith(folder + "/"):
            raise RuntimeError(f"importer wrote {package(o)} outside {folder}")
        assets.set_metadata_tag(o, OWNER_TAG, OWNER)
    return objects


def only_mesh(objects, glb: Path) -> unreal.StaticMesh:
    found = [o for o in objects if isinstance(o, unreal.StaticMesh)]
    if len(found) != 1:
        raise RuntimeError(f"{glb.name}: expected one Static Mesh, the importer made {len(found)}")
    return found[0]


def foreign_assets(folder: str) -> list[str]:
    """Assets under `folder` this script didn't create. Redirectors left by our own
    renames don't count; an asset that won't load (corrupt, or an un-pulled LFS
    file) can't be shown to be ours, so it does."""
    out = []
    for p in assets.list_assets(folder, recursive=True, include_folder=False):
        if asset_class(p) == "ObjectRedirector":
            continue
        a = assets.load_asset(p)
        if a is None or assets.get_metadata_tag(a, OWNER_TAG) != OWNER:
            out.append(p.split(".")[0])
    return out


def remove_folder(folder: str) -> None:
    if not assets.does_directory_exist(folder):
        return
    foreign = foreign_assets(folder)
    if foreign:
        raise RuntimeError(f"{folder} holds assets this script didn't create ({', '.join(foreign[:3])}); "
                           "move them out and run again")
    if not assets.delete_directory(folder):
        raise RuntimeError(f"couldn't delete {folder}")


def materials_of(mesh) -> list:
    return [s.get_editor_property("material_interface") for s in mesh.get_editor_property("static_materials")]


def use_material(mesh, material) -> None:
    """Point every slot at `material` (a bear has one material; extra slots can appear
    when a level's material didn't map onto LOD0's slot)."""
    slots = list(mesh.get_editor_property("static_materials"))
    for s in slots:
        s.set_editor_property("material_interface", material)
    mesh.set_editor_property("static_materials", slots)


def add_collision(mesh) -> str:
    try:
        meshes.remove_collisions(mesh)
    except Exception:  # noqa: BLE001 - nothing to remove
        pass
    # One convex hull around the bear, like collider.json for the web game.
    try:
        if meshes.set_convex_decomposition_collisions(mesh, 1, 32, 100000):
            return "convex hull"
    except Exception:  # noqa: BLE001 - API differs between versions
        pass
    try:
        meshes.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.NDOP26)
        return "26-sided hull"
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"couldn't add collision to {package(mesh)} ({e})") from None


def check_bear(mesh, lods: int) -> None:
    """Refuse to call a bear imported unless it really has its LODs, a material in
    every slot and collision."""
    problems = []
    if meshes.get_lod_count(mesh) != lods:
        problems.append(f"{meshes.get_lod_count(mesh)} LODs, expected {lods}")
    mats = materials_of(mesh)
    if not mats or any(m is None for m in mats):
        problems.append("a material slot is empty")
    elif any(re.search(r"/_lod\d+/", package(m)) for m in mats):
        problems.append("a material slot points at a scratch copy")
    try:
        hulls = meshes.get_convex_collision_count(mesh) + meshes.get_simple_collision_count(mesh)
    except Exception:  # noqa: BLE001 - counting API missing: trust add_collision's result
        hulls = 1
    if hulls < 1:
        problems.append("no collision")
    if problems:
        raise RuntimeError(f"{package(mesh)}: " + "; ".join(problems))


def build_bear(glb: Path, folder: str, bear: dict, name: str) -> tuple:
    """Import the GLB into `folder` as one Static Mesh with LODs, one material and
    collision. Nothing is saved here."""
    work = TMP / bear["key"]
    shutil.rmtree(work, ignore_errors=True)
    stem = f"{bear['key']}_{bear['version']}"
    lod_files = split_lods(glb, work, stem, f"MI_Bear_{bear['id'][:12]}")
    try:
        base = only_mesh(import_glb(lod_files[0], folder), lod_files[0])
        material = materials_of(base)[0]
        scratch = []
        for i, path in enumerate(lod_files[1:], start=1):
            scratch.append(f"{folder}/_lod{i}")
            extra = only_mesh(import_glb(path, scratch[-1]), path)
            if meshes.set_lod_from_static_mesh(base, i, extra, 0, True) != i:
                raise RuntimeError(f"couldn't add LOD{i} to {package(base)}")
        use_material(base, material)  # before the scratch materials go
        for s in scratch:
            remove_folder(s)
        collision = add_collision(base)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    target = f"{folder}/SM_Bear_{name}"
    if package(base) != target:
        if not assets.rename_asset(package(base), target):
            raise RuntimeError(f"couldn't rename {package(base)} to {target}")
        base = assets.load_asset(target)
    check_bear(base, len(lod_files))
    return base, collision


def update_in_place(old, glb: Path, folder: str, bear: dict, name: str) -> str:
    """Copy a rebuilt bear into the existing mesh asset: its path never changes, so
    everything referencing it keeps working, with no consolidation or redirectors."""
    scratch = f"{folder}/_rebuild"
    remove_folder(scratch)
    new, _ = build_bear(glb, scratch, bear, name)
    old_material_assets = [p.split(".")[0] for p in assets.list_assets(folder, recursive=True, include_folder=False)
                           if "/_rebuild/" not in p and asset_class(p) not in ("StaticMesh", "ObjectRedirector")]

    lods = meshes.get_lod_count(new)
    if meshes.set_lod_from_static_mesh(old, 0, new, 0, True) != 0:
        raise RuntimeError(f"couldn't replace LOD0 of {package(old)}")
    meshes.remove_lods(old)
    for i in range(1, lods):
        if meshes.set_lod_from_static_mesh(old, i, new, i, True) != i:
            raise RuntimeError(f"couldn't replace LOD{i} of {package(old)}")

    # The new material and texture move next to the mesh; the old ones go once
    # nothing references them.
    stem = f"{bear['key']}_{bear['version']}"
    src, dst = f"{scratch}/{stem}", f"{folder}/{stem}"
    # UE 5.8 requires saved staged packages before RenameDirectory.
    # Keep the locally verified fix while updating the upstream importer.
    if not assets.save_directory(src, only_if_is_dirty=False, recursive=True):
        raise RuntimeError(f"couldn't save staged material folder {src}")
    remove_folder(dst)
    if not assets.rename_directory(src, dst):
        raise RuntimeError(f"couldn't move {src} to {dst}")
    for p in assets.list_assets(dst, recursive=True, include_folder=False):
        a = assets.load_asset(p)
        if a is not None and asset_class(p) != "ObjectRedirector":
            assets.set_metadata_tag(a, OWNER_TAG, OWNER)
    material = next(assets.load_asset(p) for p in assets.list_assets(dst, recursive=True, include_folder=False)
                    if isinstance(assets.load_asset(p), unreal.MaterialInterface))
    use_material(old, material)
    collision = add_collision(old)
    check_bear(old, lods)

    remove_folder(scratch)  # the scratch mesh; its material and texture were moved out
    if not assets.save_directory(folder, only_if_is_dirty=False, recursive=True):
        raise RuntimeError(f"couldn't save {folder}")
    for p in old_material_assets:
        if not assets.does_asset_exist(p) or p.startswith(dst + "/"):
            continue
        users = [str(u) for u in assets.find_package_referencers_for_asset(p, False) if not str(u).startswith(p)]
        if users:
            unreal.log_warning(f"Bear import: kept {p}, still used by {users[0]}")
        elif assets.get_metadata_tag(assets.load_asset(p), OWNER_TAG) == OWNER:
            assets.delete_asset(p)
    return collision


def find_existing(scan_id: str):
    """The bear's mesh from an earlier run, found by scan id so a bear renamed in
    the scanner is still updated in place rather than imported a second time."""
    if not assets.does_directory_exist(DEST):
        return None
    depth = DEST.count("/") + 2  # <DEST>/<bear folder>/<mesh>
    for p in assets.list_assets(DEST, recursive=True, include_folder=False):
        pkg = p.split(".")[0]
        if pkg.count("/") != depth or "/_" in pkg[len(DEST):] or asset_class(p) != "StaticMesh":
            continue
        a = assets.load_asset(p)
        if a is not None and assets.get_metadata_tag(a, SCAN_TAG) == scan_id:
            if assets.get_metadata_tag(a, OWNER_TAG) != OWNER:
                raise RuntimeError(f"Refusing to update an unowned mesh: {p}")
            return a
    return None


def sync(bear: dict) -> dict:
    if "error" in bear:
        raise RuntimeError(bear["error"])
    name = safe(bear["name"])
    old = find_existing(bear["id"])
    folder = package(old).rsplit("/", 1)[0] if old else f"{DEST}/{bear['key']}"
    if old is None and assets.does_directory_exist(folder):
        for path in assets.list_assets(folder, recursive=True, include_folder=False):
            if asset_class(path) == 'StaticMesh':
                previous = assets.load_asset(path)
                previous_id = assets.get_metadata_tag(previous, SCAN_TAG) if previous else ''
                if previous_id and previous_id != bear['id']:
                    raise RuntimeError(f"{folder} belongs to a different bear identity; refusing to overwrite it")
    if old and not FORCE:
        have_version = assets.get_metadata_tag(old, VERSION_TAG)
        have_revision = assets.get_metadata_tag(old, REVISION_TAG)
        # Same content (revision), the same model with only sidecars changed (say,
        # landmarks added later), or, for loose .glb files, the same version.
        if (bear.get("revision") and have_revision == bear["revision"]) or                 (bear.get("modelSha") and assets.get_metadata_tag(old, MODEL_TAG) == bear["modelSha"]) or                 (not bear.get("revision") and have_version == bear["version"]):
            return {"bear": name, "result": "up to date", "mesh": package(old)}
        if _int(bear["version"]) < _int(have_version):
            return {"bear": name, "result": "skipped", "mesh": package(old),
                    "error": f"older than the imported build (v{bear['version']} < v{have_version}); "
                             "set FORCE to re-import it anyway"}
    glb = bear["glb"] if "glb" in bear else bear["fetch"]()
    try:
        if old:
            collision = update_in_place(old, glb, folder, bear, name)
            mesh = old
        else:
            remove_folder(folder)  # leftovers of an interrupted import, if all ours
            mesh, collision = build_bear(glb, folder, bear, name)
    finally:
        if "download" in bear:
            bear["download"].unlink(missing_ok=True)
    # Only now is the bear known good: mark it, so a failure above is retried next run.
    for tag, value in ((VERSION_TAG, bear["version"]), (REVISION_TAG, bear.get("revision", "")),
                       (MODEL_TAG, bear.get("modelSha", "")),
                       (SCAN_TAG, bear["id"]), (OWNER_TAG, OWNER)):
        assets.set_metadata_tag(mesh, tag, value)
    if not assets.save_directory(folder, only_if_is_dirty=False, recursive=True):
        raise RuntimeError(f"couldn't save {folder}")

    box = mesh.get_bounding_box()
    size = box.max - box.min
    return {"bear": name, "result": "updated" if old else "imported", "mesh": package(mesh),
            "lods": meshes.get_lod_count(mesh), "collision": collision,
            "size_cm": [round(size.x, 1), round(size.y, 1), round(size.z, 1)]}


def main() -> list:
    if not DEST.startswith("/") or DEST.count("/") < 2:
        raise RuntimeError(f"DEST {DEST!r} must be a content folder such as /Game/ScannedBears")
    TMP.mkdir(parents=True, exist_ok=True)
    try:
        return _run()
    finally:
        shutil.rmtree(TMP / "unzipped", ignore_errors=True)


def _run() -> list:
    bears, older = newest_per_id(local_bears(Path(SOURCE)) if SOURCE else server_bears())
    if not bears:
        unreal.log_warning("Bear import: no finished bears found.")
    results = [{"bear": safe(b["name"]), "result": "skipped",
                "error": f"another copy of this bear is newer (v{b['version']} isn't the newest)"} for b in older]
    with unreal.ScopedSlowTask(max(len(bears), 1), "Importing scanned bears") as task:
        try:
            task.make_dialog(True)
        except Exception:  # noqa: BLE001 - no dialog in a commandlet
            pass
        for bear in bears:
            if task.should_cancel():
                break
            task.enter_progress_frame(1, f"Bear: {bear['name']}")
            try:
                results.append(sync(bear))
            except Exception as e:  # noqa: BLE001 - report and carry on with the others
                results.append({"bear": bear["name"], "result": "failed", "error": str(e)})
    for r in results:
        line = f"Bear import: {r['bear']}: {r['result']} {r.get('mesh') or r.get('error', '')}"
        if r.get("lods"):
            line += f" ({r['lods']} LODs, {r['collision']} collision, {' x '.join(map(str, r['size_cm']))} cm)"
        log = {"failed": unreal.log_error, "skipped": unreal.log_warning}.get(r["result"], unreal.log)
        log(line)
    unreal.log("BEAR_IMPORT_RESULT " + json.dumps(results))
    return results


RESULTS = main()
