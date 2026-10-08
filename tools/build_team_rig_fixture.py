"""Build a SYNTHETIC validation bear using the team's installed rigfit source.

Run with bear-scanner's existing virtual-environment Python. Requires --scanner.
Does not install packages, edit the scanner checkout, or overwrite earlier output.
The result is an engine compatibility fixture, never a real scan or game character.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scanner', required=True, type=Path)
    ap.add_argument('--out', type=Path, default=ROOT / 'Assets/Adapted/BearRigfitReview/SyntheticV1')
    args = ap.parse_args()
    scanner, out = args.scanner.resolve(), args.out.resolve()
    if not out.is_relative_to(ROOT / 'Assets/Adapted/BearRigfitReview'):
        raise SystemExit('Output must be in the owned BearRigfitReview source namespace')
    if out.exists():
        raise SystemExit(f'Output already exists; choose a new revision: {out}')
    source_files = ['scanner/rigfit.py', 'scanner/landmarks.py',
                    'tests/test_landmarks.py', 'scripts/rig_test_package.py']
    hashes = {f: sha(scanner / f) for f in source_files}
    revision = subprocess.check_output(['git', '-C', str(scanner), 'rev-parse', 'HEAD'], text=True).strip()
    sys.path.insert(0, str(scanner))
    import numpy as np
    import trimesh
    import xatlas
    from PIL import Image
    from scanner import landmarks, rigfit
    from tests.test_landmarks import mesh_of, teddy

    spec = importlib.util.spec_from_file_location('team_rig_test_package', scanner / source_files[-1])
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    out.mkdir(parents=True, exist_ok=False)
    mesh = mesh_of(teddy(), noise=0.0015)
    lm = landmarks.compute(mesh)
    assert lm.get('complete'), 'Synthetic fixture must have complete landmarks'
    uv = (mesh.vertices[:, :2] - mesh.bounds[0, :2]) / mesh.extents[:2]
    x, y = np.meshgrid(np.linspace(0, 1, 256), np.linspace(1, 0, 256))
    pixels = np.dstack([x * 255, y * 255, np.full_like(x, 128)]).astype(np.uint8)
    mesh.visual = trimesh.visual.TextureVisuals(uv=uv, image=Image.fromarray(pixels))
    mesh.export(out / 'synthetic-source.glb')
    (out / 'landmarks.json').write_text(json.dumps(lm, indent=2) + '\n', encoding='utf-8')
    report = rigfit.fit(out / 'synthetic-source.glb', lm, out / 'fit', pose='animation')
    animated = out / 'synthetic-team-rig.glb'
    package.add_animations(out / 'fit/rigged.glb', animated)
    raw = animated.read_bytes()
    doc = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
    pos = doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['POSITION']]
    assert hashes == {f: sha(scanner / f) for f in source_files}, 'Team source changed during generation'
    manifest = {
        'schema': 1, 'id': 'synthetic-team-rig-v1', 'synthetic': True,
        'purpose': 'Native Unreal compatibility proof of the team 21-bone exporter; not a scanned or approved character.',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'scanner_revision': revision, 'scanner_source_sha256': hashes,
        'generator_sha256': sha(Path(__file__)), 'xatlas_version': xatlas.__version__,
        'texture': 'Diagnostic position colours: red=X, green=Y, blue=128; not production art.',
        'axes': {'unit': 'metres', 'up': '+Y', 'front': '+Z', 'left': '+X'},
        'model': animated.name, 'bones': rigfit.JOINTS, 'parents': {b: rigfit.PARENT[b] for b in rigfit.JOINTS},
        'clips': [a['name'] for a in doc['animations']], 'clip_duration_seconds': 2.0,
        'bounds_cm': {'min': [v * 100 for v in pos['min']], 'max': [v * 100 for v in pos['max']]},
        'rest_height_cm': (pos['max'][1] - pos['min'][1]) * 100,
        'rigfit_status': report['status'], 'warnings': report['warnings'],
        'files': {p.relative_to(out).as_posix(): {'sha256': sha(p), 'size': p.stat().st_size}
                  for p in sorted(out.rglob('*')) if p.is_file()},
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(out), 'bones': len(manifest['bones']), 'clips': manifest['clips'],
                      'height_cm': manifest['rest_height_cm'], 'status': report['status'],
                      'warnings': report['warnings']}, indent=2))


if __name__ == '__main__':
    main()
