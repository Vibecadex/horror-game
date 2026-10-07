"""Bounded local adapter, executed only by the configured scanner environment."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def run(scanner: Path, job: Path):
    import numpy as np
    import trimesh
    from scanner import landmarks, rigfit

    request = json.loads((job / "request.json").read_text(encoding="utf-8"))
    source = job / "source.glb"
    if sha(source) != request["sourceSha256"]:
        raise ValueError("Source identity changed before fitting")
    scene = trimesh.load(source, force="scene", process=False)
    mesh_name = "LOD0" if "LOD0" in scene.geometry else next(iter(scene.geometry), None)
    if mesh_name is None or (mesh_name != "LOD0" and len(scene.geometry) != 1):
        raise ValueError("Choose a single bear mesh or a scanner pack with LOD0 before fitting")
    placements = [scene.graph[node][0] for node in scene.graph.nodes_geometry if scene.graph[node][1] == mesh_name]
    if len(placements) != 1 or not np.allclose(placements[0], np.eye(4), atol=1e-6):
        raise ValueError("Apply mesh transforms before scanner fitting; its landmarks use the original mesh coordinates")
    lm_path = job / "landmarks.json"
    supplied = lm_path.is_file()
    if supplied:
        lm = json.loads(lm_path.read_text(encoding="utf-8"))
    else:
        lm = landmarks.compute(scene.geometry[mesh_name])
        write(lm_path, lm)
    points = lm.get("points", {})
    missing = [name for name in rigfit.REQUIRED if name not in points]
    if missing:
        raise ValueError("Scanner landmarks missing: " + ", ".join(missing)
                         + ". Rescan upright with arms and legs apart, or use the manual draft tools.")
    if not all(np.asarray(p).shape == (3,) and np.isfinite(np.asarray(p, dtype=float)).all() for p in points.values()):
        raise ValueError("Scanner landmarks contain invalid coordinates")
    modules = ["scanner/rigfit.py", "scanner/landmarks.py", "scripts/rig_test_package.py"]
    hashes = {name: sha(scanner / name) for name in modules}
    report = rigfit.fit(source, lm, job / "fit", pose=request["capturePose"], surface="template")
    spec = importlib.util.spec_from_file_location("team_rig_clips", scanner / "scripts/rig_test_package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.add_animations(job / "fit/rigged.glb", job / "model.glb")
    if hashes != {name: sha(scanner / name) for name in modules}:
        raise ValueError("Scanner code changed during the fit; retry with a stable checkout")
    recipe = {
        "schemaVersion": 1, "method": "scanner-rigfit-v1",
        "sourceRevision": request["sourceRevision"], "sourceSha256": request["sourceSha256"],
        "capturePose": request["capturePose"], "surface": "template",
        "landmarksOrigin": "source-pack" if supplied else "computed-from-source",
        "scannerLandmarks": lm, "landmarksSha256": sha(lm_path),
        "scannerSourceSha256": hashes, "adapterSha256": sha(Path(__file__)),
        "fitReport": report, "synthetic": request.get("synthetic", False),
        "axes": {"unit": "metres", "up": "+Y", "front": "+Z", "left": "+X"},
    }
    write(job / "result.json", {"recipe": recipe, "validation": {
        "kind": "scanner-template-fit", "review": "pending", "fitReport": report,
        "warnings": ["Prototype template fit: review shape, texture, joint pinching and floor contact.",
                     "Collision and foot planting have not been generated.", *report.get("warnings", [])],
    }})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scanner", type=Path, required=True)
    parser.add_argument("--job", type=Path)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    scanner = args.scanner.resolve()
    sys.path.insert(0, str(scanner))
    try:
        # Import the actual optional packages before accepting a long-running job.
        import numpy, scipy, trimesh, xatlas, pymeshlab, skimage, PIL  # noqa: F401
        from scanner import landmarks, rigfit  # noqa: F401
        if args.probe:
            print(json.dumps({"available": True, "bones": len(rigfit.JOINTS)}))
        else:
            run(scanner, args.job.resolve())
    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        if args.job:
            write(args.job / "error.json", {"error": message[:2000]})
        print(json.dumps({"available": False, "error": message[:2000]}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
