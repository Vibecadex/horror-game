"""Build ungraded aspect-preserving chamber reference/capture comparisons.

Usage: python evidence/chamber-qa/build_comparison.py --capture-dir evidence/implementation/RUN --output evidence/chamber-qa/ITERATION
Only a fresh output folder below evidence/chamber-qa may be created.
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OWNED = ROOT / 'evidence/chamber-qa'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def opened(path):
    with Image.open(path) as im:
        im.load()
        return im.convert('RGB')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-dir', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    capture = (ROOT / args.capture_dir).resolve()
    output = (ROOT / args.output).resolve()
    assert output != OWNED and OWNED in output.parents, 'Output must be a child of evidence/chamber-qa.'
    assert not output.exists(), 'Refusing to overwrite any previous comparison.'
    receipt_path = capture / 'receipt.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    assert receipt.get('passed'), 'Capture did not complete successfully.'
    rows = {row['name']: row for row in receipt['captures']}
    pairs = []
    for view, name in [('front', '01-chamber-front'), ('reverse', '02-chamber-reverse')]:
        candidate = capture / f'{name}.png'
        reference = ROOT / f'study/visuals/chamber-target-{view}.png'
        row = rows[name]
        assert sha(candidate) == row['validation']['sha256'], f'{view}: source differs from capture receipt.'
        ref_im, cand_im = opened(reference), opened(candidate)
        assert cand_im.size == (row['validation']['width'], row['validation']['height'])
        pairs.append((view, reference, ref_im, candidate, cand_im, row))
    output.mkdir(parents=True)
    font_path = Path('C:/Windows/Fonts/segoeui.ttf')
    title_font = ImageFont.truetype(str(font_path), 20) if font_path.exists() else ImageFont.load_default()
    body_font = ImageFont.truetype(str(font_path), 15) if font_path.exists() else ImageFont.load_default()
    board = Image.new('RGB', (1600, 1230), '#171c21')
    draw = ImageDraw.Draw(board)
    records = []
    for index, (view, ref_path, ref_im, cand_path, cand_im, row) in enumerate(pairs):
        y = index * 610
        for column, (im, title) in enumerate([(ref_im, f'{view.upper()} — USER CONCEPT TARGET'), (cand_im, f'{view.upper()} — ACTUAL SAVED UNREAL, ARCHITECTURAL CAMERA')]):
            x = column * 800
            draw.text((x + 12, y + 10), title, fill='white', font=title_font)
            draw.text((x + 12, y + 39), f'Original {im.width} x {im.height}; entire frame, ungraded, aspect preserved', fill='#adbdca', font=body_font)
            scale = min(776 / im.width, 520 / im.height)
            display = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
            board.paste(display, (x + (800 - display.width) // 2, y + 69))
        records.append({'view': view, 'reference': {'path': ref_path.relative_to(ROOT).as_posix(), 'sha256': sha(ref_path), 'size': list(ref_im.size), 'kind': 'user concept target'}, 'candidate': {'path': cand_path.relative_to(ROOT).as_posix(), 'sha256': sha(cand_path), 'size': list(cand_im.size), 'kind': row['kind'], 'held_state': row['held_state'], 'caption': row['caption'], 'hash_matches_capture_receipt': True, 'full_pixel_decode': True}})
    destination = output / 'comparison.png'
    board.save(destination)
    opened(destination)
    provenance = {'capture_receipt': receipt_path.relative_to(ROOT).as_posix(), 'capture_receipt_sha256': sha(receipt_path), 'map': receipt['map'], 'engine': receipt['engine'], 'capture_method': receipt.get('method'), 'sources': records, 'comparison': {'path': destination.relative_to(ROOT).as_posix(), 'size': list(board.size), 'sha256': sha(destination), 'full_pixel_decode': True}, 'limitations': ['Reference concepts are small and differ slightly in aspect ratio. All full images remain unwarped, ungraded and uncropped.', 'Display resizes each image separately with Lanczos and retains all source bounds. The originals remain primary evidence.', 'Architectural cameras and frozen actors are disclosed. This comparison does not establish ordinary gameplay or user acceptance.', 'No similarity percentage, automatic parity score or physical-light measurement is computed.']}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(provenance['comparison'], indent=2))


if __name__ == '__main__':
    main()
