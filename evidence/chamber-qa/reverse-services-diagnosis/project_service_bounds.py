"""Read-only geometric diagnosis; no engine, image edits or visibility claims."""
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'projection-diagnostics.json'
ROOM = ROOT / 'evidence/implementation/20261005T105657-verify_full_room/receipt.json'
CAPTURE = ROOT / 'evidence/implementation/20261005T110142-capture_chamber_views/receipt.json'
LABELS = {'TE_Room_LeftPipeRun_0', 'TE_Room_LeftPipeRun_1',
          'TE_Room_RightCabinetA', 'TE_Room_RightCabinetB'}

assert not OUT.exists(), 'Preserve prior diagnostics.'
room = json.loads(ROOM.read_bytes())
capture = json.loads(CAPTURE.read_bytes())
view = next(c for c in capture['captures'] if c['name'] == '02-chamber-reverse')
camera = np.array(view['location'], dtype=float)
forward = np.array(view['target'], dtype=float) - camera
forward /= np.linalg.norm(forward)
right = np.cross([0., 0., 1.], forward)
right /= np.linalg.norm(right)
up = np.cross(forward, right)
aspect = capture['resolution'][0] / capture['resolution'][1]
cases = []
for fov in [view['fov'], 70., 72.]:
    tangent = math.tan(math.radians(fov / 2))
    rows = []
    for actor in room['room_actors']:
        if actor['label'] not in LABELS:
            continue
        bound = actor['meshes'][0]['bounds']
        projected = []
        for corner in itertools.product(*zip(bound['min'], bound['max'])):
            delta = np.array(corner) - camera
            depth = np.dot(delta, forward)
            assert depth > 0, 'Projection does not handle camera-plane intersections.'
            projected.append([.5 + .5 * np.dot(delta, right) / (depth * tangent),
                              .5 - .5 * np.dot(delta, up) / (depth * tangent / aspect)])
        lo, hi = np.min(projected, axis=0), np.max(projected, axis=0)
        clipped = np.maximum(0, np.minimum(1, hi) - np.maximum(0, lo))
        rows.append({'actor': actor['label'], 'source_bounds_cm': bound,
                     'normalized_screen_bounds': [float(v) for v in [*lo, *hi]],
                     'projected_box_fraction_inside_frame': float(np.prod(clipped) / np.prod(hi - lo))})
    cases.append({'horizontal_fov': fov, 'actual_capture_fov': fov == view['fov'], 'actors': rows})
result = {
    'sources': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in [ROOM, CAPTURE]],
    'camera_location': view['location'], 'camera_target': view['target'], 'aspect': aspect,
    'cases': cases,
    'limitations': ['Conservative saved component boxes projected analytically, not an engine screenshot or rendered silhouette.',
                   'Fractions describe screen-box clipping only. They do not measure visible mesh area, lighting, depth occlusion or acceptance.',
                   'FOV70 and FOV72 are predicted architectural framing trials; neither changes or validates the saved gameplay camera.',
                   'Geometry receipt predates wall material/light adjustments, which do not change these saved bounds.']}
OUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(OUT)
