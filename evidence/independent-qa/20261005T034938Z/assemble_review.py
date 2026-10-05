"""Package independent QA evidence. Never edits game files."""
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def save_json(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

board = Image.new('RGB', (1460, 505), '#081217')
draw = ImageDraw.Draw(board)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 21)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 16)
for xpos, title, source, caption in [
    (20, 'ORIGINAL VIDEO / 5 seconds', 'derived/original-gameplay-05.png', 'Original crop; social-player overlays retained.'),
    (740, 'INDEPENDENT QA / current saved build', 'engine/01-initial-composition.png', 'Fresh gameplay held for capture; HUD hidden.'),
]:
    with Image.open(HERE / source) as source_image:
        source_image.load()
        plate = source_image.convert('RGB')
        height = round(700 * plate.height / plate.width)
        plate = plate.resize((700, height), Image.Resampling.LANCZOS)
        board.paste(plate, (xpos, 54))
    draw.text((xpos, 16), title, fill='#d6e6ed', font=font)
    draw.text((xpos, 466), caption, fill='#adc4ce', font=small)
board.save(HERE / 'comparison.png')

baseline = read_json(HERE / 'source-and-build.json')
checks = []
for entry in baseline['build_files']:
    actual = sha(ROOT / entry['path'])
    checks.append({'path': entry['path'], 'unchanged': actual == entry['sha256'], 'sha256': actual})
source_unchanged = sha(Path(baseline['source_video'])) == baseline['source_sha256']
assert len(checks) == 68 and all(entry['unchanged'] for entry in checks)
assert source_unchanged
save_json('preservation.json', {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'all_68_build_files_unchanged': True,
    'source_video_unchanged': source_unchanged,
    'files': checks,
})

behavior = read_json(HERE / 'engine/receipt.json')
bindings = read_json(HERE / 'bindings.json')
save_json('qa-result.json', {
    'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'timezone': 'Africa/Johannesburg',
    'independent_of_authoring_session': True,
    'overall': 'needs_revision',
    'sign_off_recommended': False,
    'functional_action_checks': {
        'passed': sum(value is True for value in behavior['checks'].values()),
        'total': len(behavior['checks']),
        'method': behavior['input_method'],
        'evidence': 'engine/receipt.json',
    },
    'required_keyboard_bindings': {
        'passed': bindings['passed'],
        'valid': sum(row['present_and_valid'] for row in bindings['required_bindings']),
        'total': len(bindings['required_bindings']),
        'evidence': 'bindings.json',
    },
    'visual_fidelity': 'needs_revision',
    'findings': [
        {'id': 'QA-01', 'priority': 'P1', 'title': 'Invalid Space, Escape and F5 bindings'},
        {'id': 'QA-02', 'priority': 'P2', 'title': 'Camera and subject framing too distant and overhead'},
        {'id': 'QA-03', 'priority': 'P2', 'title': 'Lighting and atmospheric depth differ from reference'},
        {'id': 'QA-04', 'priority': 'P2', 'title': 'Repetitive floor and simplified surface detail'},
        {'id': 'QA-05', 'priority': 'P2', 'title': 'Bright warning ring dominates visual emphasis'},
    ],
    'unverified': ['physical keyboard/mouse play', 'gamepad operation', 'fine animation smoothness', 'audio match', 'packaged delivery', 'production performance'],
    'game_assets_changed': False,
    'build_files_unchanged': 68,
    'source_video_unchanged': source_unchanged,
    'report': 'QA_REPORT.md',
    'review': 'review.html',
    'comparison': 'comparison.png',
})

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value and not value.startswith(('http:', 'https:', '#', 'data:')):
                self.paths.append(value)

html = (HERE / 'review.html').read_text(encoding='utf-8')
parser = Links()
parser.feed(html)
paths = set(parser.paths)
paths.update(re.findall(r"path:'([^']+)'", html))
for second in ('05', '10', '16'):
    paths.add(f'derived/original-gameplay-{second}.png')
markdown = (HERE / 'QA_REPORT.md').read_text(encoding='utf-8')
paths.update(re.findall(r'\]\(([^)]+)\)', markdown))
missing = [name for name in sorted(paths) if not (HERE / name).is_file()]
assert not missing, missing
images = []
for name in sorted(paths):
    if Path(name).suffix.lower() == '.png':
        with Image.open(HERE / name) as img:
            img.load()
            images.append({'path': name, 'size': list(img.size)})
for name in ['qa-result.json', 'preservation.json', 'bindings.json', 'engine/receipt.json']:
    read_json(HERE / name)
save_json('review-validation.json', {
    'all_local_links_resolve': True,
    'unique_links_checked': len(paths),
    'images_fully_decoded': images,
    'comparison_equal_width': 700,
    'comparison_aspect_ratios_preserved': True,
    'json_parsing_passed': True,
    'build_hashes_rechecked': 68,
})
print(json.dumps({'review': str(HERE / 'review.html'), 'behavior_checks': len(behavior['checks']), 'valid_required_keys': 0, 'files_unchanged': len(checks), 'links_checked': len(paths)}))
