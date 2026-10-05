"""Small manually chosen reference tone samples; diagnostic, never a parity score."""

from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REGIONS = {
    'front': {
        'rear_wall_plane': [119, 31, 161, 82],
        'door_leaf': [225, 48, 268, 87],
        'left_equipment_face': [46, 118, 59, 154],
        'right_wall_pipe_area': [500, 47, 517, 83],
        'central_clear_floor': [267, 152, 319, 182],
        'near_fracture_floor': [208, 287, 260, 331],
    },
    'reverse': {
        'rear_wall_plane': [204, 40, 260, 81],
        'door_recess': [149, 55, 175, 92],
        'left_equipment_face': [20, 89, 40, 125],
        'right_wall_pipe_area': [369, 47, 391, 77],
        'central_clear_floor': [197, 163, 236, 200],
        'near_fracture_floor': [173, 239, 237, 284],
    },
}


def main():
    report = {'method': 'Manual small rectangles within each source, marked in companion PNGs. Display luma = 0.2126R + 0.7152G + 0.0722B on encoded 8-bit RGB; it is not physical luminance or EV. No resizing before measurements. Boxes exclude text/borders and conspicuous characters or emissive fixtures. Different surfaces, perspective and haze remain confounders. No pass band, similarity score or automatic candidate masks are assigned.', 'sources': {}}
    font_path = Path('C:/Windows/Fonts/segoeui.ttf')
    font = ImageFont.truetype(str(font_path), 13) if font_path.exists() else ImageFont.load_default()
    for view, regions in REGIONS.items():
        source = ROOT / f'study/visuals/chamber-target-{view}.png'
        with Image.open(source) as opened:
            opened.load()
            im = opened.convert('RGB')
        pixels = np.asarray(im, dtype=np.float64)
        luma = pixels @ np.array([0.2126, 0.7152, 0.0722])
        annotated = Image.new('RGB', (im.width, im.height + 160), '#161b20')
        annotated.paste(im, (0, 0))
        draw = ImageDraw.Draw(annotated)
        rows = {}
        for number, (name, bounds) in enumerate(regions.items(), start=1):
            x0, y0, x1, y1 = bounds
            rgb = pixels[y0:y1, x0:x1].reshape(-1, 3)
            tone = luma[y0:y1, x0:x1].reshape(-1)
            rows[name] = {'rectangle_xyxy': bounds, 'pixels': len(tone), 'display_rgb_mean': np.round(rgb.mean(axis=0), 3).tolist(), 'display_luma_mean': round(float(tone.mean()), 3), 'display_luma_p10_p50_p90': np.round(np.percentile(tone, [10, 50, 90]), 3).tolist()}
            draw.rectangle(bounds, outline='#ffd66b', width=1)
            draw.text((x0 + 1, y0), str(number), fill='#fff2a6', font=font)
            draw.text((7, im.height + 8 + (number - 1) * 23), f'{number}. {name}: display luma {tone.mean():.1f}', fill='white', font=font)
        destination = OUT / f'{view}-tone-regions.png'
        annotated.save(destination)
        with Image.open(destination) as check:
            check.load()
        report['sources'][view] = {'path': source.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'dimensions': list(im.size), 'regions': rows, 'annotation': destination.relative_to(ROOT).as_posix()}
    (OUT / 'tone-diagnostics.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({view: {name: row['display_luma_mean'] for name, row in data['regions'].items()} for view, data in report['sources'].items()}, indent=2))


if __name__ == '__main__':
    main()
