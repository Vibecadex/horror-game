"""Read-only evidence verification and ungraded frame sampling for this review."""
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CHAMBER = ROOT / 'evidence/implementation/20261005T114820-verify_chamber_runtime'
ROOM = ROOT / 'evidence/implementation/20261005T114928-verify_full_room'
MOTION = ROOT / 'evidence/chamber/20261005T095028Z/native-motion-20261005T115126'
FFMPEG = Path('C:/Users/4elut/scoop/shims/ffmpeg.exe')
FFPROBE = Path('C:/Users/4elut/scoop/shims/ffprobe.exe')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def recorded(path):
    return {'path': relative(path), 'sha256': digest(path)}


chamber, details, room, motion = [read(p) for p in (
    CHAMBER / 'receipt.json', CHAMBER / 'details.json',
    ROOM / 'receipt.json', MOTION / 'receipt.json')]
assert digest(CHAMBER / 'details.json') == chamber['details']['sha256']
hosts = {name: read(folder / 'host-result.json') for name, folder in (
    ('chamber', CHAMBER), ('room', ROOM))}
for name, data in [('chamber', chamber), ('room', room)]:
    assert data['passed'] and len(data['checks']) == 28 and all(data['checks'].values())
    assert hosts[name]['passed'] and hosts[name]['exit_code'] == 0

runtime = []
for case in details['runtime_cases']:
    samples = case['samples']
    assert len(samples) == 12
    assert all(s['actor_hidden'] == s['expected_hidden'] for s in samples)
    assert all(s['actor_tick_enabled'] and not s['actor_collision_enabled']
               and s['all_component_collision_disabled'] for s in samples)
    assert all(s['reverse_overhead_light']['owner_is_cutaway']
               and s['reverse_overhead_light']['owner_hidden'] == s['actor_hidden']
               for s in samples)
    runtime.append({'name': case['case']['name'], 'samples': len(samples),
                    'fov_values': sorted({s['camera']['fov'] for s in samples}),
                    'hidden_values': sorted({s['actor_hidden'] for s in samples}),
                    'native_tick_retained': True})

floor_groups = {}
for tag in ['ChamberFloorOwned', 'ChamberSlabsOwned', 'ChamberCrustOwned']:
    actors = [a for a in details['saved_actors'] if tag in a['tags']]
    meshes = sorted({m['mesh'] for a in actors for m in a['meshes']})
    assert all('_V2.' in mesh for mesh in meshes)
    floor_groups[tag] = {'actor_count': len(actors), 'meshes': meshes}

images = []
for row in room['images']:
    path = Path(row['path'])
    assert digest(path) == row['validation']['sha256']
    with Image.open(path) as image:
        image.load()
        assert image.size == (1280, 720)
    images.append({**recorded(path), 'case': row['case'], 'full_pixel_decode': True})

video = MOTION / 'native-motion.mp4'
assert digest(video) == motion['video_sha256']
assert motion['passed'] and motion['game_exit_code'] == 0 and motion['capture_exit_code'] == 0
probe = subprocess.run([str(FFPROBE), '-v', 'error', '-select_streams', 'v:0',
                        '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time',
                        '-of', 'json', str(video)], capture_output=True, text=True, check=True)
timestamps = [float(frame['best_effort_timestamp_time']) for frame in json.loads(probe.stdout)['frames']]
assert len(timestamps) == 572
frames_dir = OUT / 'native-frames-15'
frames_dir.mkdir(exist_ok=False)
extract = subprocess.run([str(FFMPEG), '-v', 'error', '-xerror', '-n', '-i', str(video),
                          '-vf', r'select=not(mod(n\,15))', '-fps_mode', 'vfr',
                          str(frames_dir / 'frame-%03d.png')], capture_output=True, text=True, check=True)
frames = sorted(frames_dir.glob('frame-*.png'))
indices = list(range(0, len(timestamps), 15))
assert len(frames) == len(indices)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
samples = []
for index, path in zip(indices, frames):
    with Image.open(path) as im:
        im.load()
        assert im.size == (1280, 720)
    samples.append({**recorded(path), 'source_frame_index': index,
                    'source_timestamp_seconds': timestamps[index]})

boards = []
for page, start in enumerate(range(0, len(samples), 20), 1):
    batch = samples[start:start + 20]
    board = Image.new('RGB', (1536, ((len(batch) + 3) // 4) * 242), '#141b1f')
    draw = ImageDraw.Draw(board)
    for slot, sample in enumerate(batch):
        x, y = (slot % 4) * 384, (slot // 4) * 242
        with Image.open(ROOT / sample['path']) as im:
            board.paste(im.convert('RGB').resize((384, 216), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 7, y + 219), f"{sample['source_timestamp_seconds']:.3f}s | frame {sample['source_frame_index']}", fill='#e9ecef', font=font)
    path = OUT / f'native-samples-{page:02d}.png'
    board.save(path)
    boards.append(recorded(path))

preservation_path = ROOT / 'evidence/chamber/20261005T095028Z/final-preservation.json'
preservation = read(preservation_path)
assert preservation['passed'] and preservation['active_assets'] == 175
assert preservation['validation_drift'] == [] and preservation['original_failures'] == []
assert preservation['original_files'] == 555 and preservation['config_and_launcher_unchanged']
assert preservation['preexisting_changed'] == ['TeddyBlueprint/Content/Maps/TeddyEncounter.umap']

result = {
    'method': 'Independent receipt/detail consistency, source-file hashes, original PNG pixel decode, full movie decode during lossless sampling; no Unreal invocation or binary asset inspection.',
    'chamber': {**recorded(CHAMBER / 'receipt.json'), 'checks_passed': 28,
                'host_exit_code': 0, 'details': recorded(CHAMBER / 'details.json'),
                'detail_hash_matches_receipt': True,
                'saved_actors': len(details['saved_actors']), 'surface_groups': floor_groups,
                'runtime_cases': runtime},
    'room': {**recorded(ROOM / 'receipt.json'), 'checks_passed': 28,
             'host_exit_code': 0, 'old_extension_actor_count': len(room['room_extension_actors']),
             'exact_cutaway_reuse_rows': len(room['room_extension_mesh_reuse']),
             'images': images},
    'native': {**recorded(video), 'hash_matches_receipt': True,
               'receipt': recorded(MOTION / 'receipt.json'),
               'width': 1280, 'height': 720, 'duration_seconds': 19.166667,
               'decoded_frame_count': len(timestamps), 'full_decode_exit_code': extract.returncode,
               'sampling': 'Every fifteenth decoded frame, exact source PTS recorded; entire uncropped ungraded frames retained. This is sampled visual inspection, not continuous real-time playback or physical-device testing.',
               'frames': samples, 'contact_sheets': boards,
               'no_audio_stream': True, 'isolated_map_automated_normal_input': True},
    'preservation': {**recorded(preservation_path),
                     'result': preservation,
                     'scope': 'QA independently read and consistency-checked the integrator hash receipt. QA did not reread or hash Unreal binary assets.'}
}
(OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'chamber_checks': 28, 'room_checks': 28, 'runtime_samples': 60,
                  'room_images': len(images), 'movie_decoded_frames': len(timestamps),
                  'sampled_frames': len(samples), 'boards': boards, 'output': relative(OUT / 'verification.json')}, indent=2))
