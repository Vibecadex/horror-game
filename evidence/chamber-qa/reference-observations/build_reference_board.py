"""Read-only reference annotation for chamber QA; never edits either source image."""

from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FONT_PATH = Path('C:/Windows/Fonts/segoeui.ttf')


def font(size):
    return ImageFont.truetype(str(FONT_PATH), size) if FONT_PATH.exists() else ImageFont.load_default()


SPECS = [
    {
        'id': 'front',
        'source': 'study/visuals/chamber-target-front.png',
        'title': 'FRONT: user concept target, not an Unreal capture',
        'features': [
            ('1', 'Broad blast door; layered frame/threshold', [205, 15, 374, 117]),
            ('2', 'Thick wall returns and readable panels', [106, 6, 204, 122]),
            ('3', 'Electrical/service attachment along left wall', [30, 70, 111, 177]),
            ('4', 'Fan, tanks, cabinets and pipe connections', [391, 14, 548, 243]),
            ('5', 'Connected foreground fractures and large chips', [166, 280, 371, 352]),
            ('6', 'Grouped dark wear within usable open floor', [296, 192, 379, 232]),
        ],
        'approximate_landmarks': {
            'center_back_wall_floor_junction_y': 114,
            'blast_door_frame_bounds_xyxy': [205, 15, 374, 117],
            'scene_border_and_caption_exclusions': 'White outer border; FULL CHAMBER text at lower left. Do not use text/border contrast as scene detail.',
        },
    },
    {
        'id': 'reverse',
        'source': 'study/visuals/chamber-target-reverse.png',
        'title': 'REVERSE: user concept target, not an Unreal capture',
        'features': [
            ('1', 'Left dark door bay with red indicator', [140, 40, 183, 108]),
            ('2', 'Right dark door bay and separating structure', [278, 36, 339, 113]),
            ('3', 'Left electrical bank and coherent conduits', [6, 33, 108, 145]),
            ('4', 'Right elbowed pipes and floor-level tanks', [354, 20, 470, 153]),
            ('5', 'Same connected floor fracture scale close up', [100, 217, 262, 291]),
            ('6', 'Lit but enclosed wall visible through haze', [188, 8, 274, 114]),
        ],
        'approximate_landmarks': {
            'center_back_wall_floor_junction_y': 111,
            'left_door_bounds_xyxy': [140, 40, 183, 108],
            'right_door_and_pier_bounds_xyxy': [278, 36, 339, 113],
            'scene_border_and_caption_exclusions': 'White outer border; REVERSE VIEW text at lower left. Do not use text/border contrast as scene detail.',
        },
    },
]


def main():
    colors = ['#ffd66b', '#7cc7ff', '#d8a2ff', '#ff9f80', '#85efbd', '#f4a8d4']
    panel_width = 850
    top = 60
    image_box_height = 565
    board = Image.new('RGB', (panel_width * 2, 870), '#161b20')
    draw = ImageDraw.Draw(board)
    records = []
    for index, spec in enumerate(SPECS):
        source = ROOT / spec['source']
        raw = source.read_bytes()
        with Image.open(source) as opened:
            opened.load()
            original = opened.convert('RGB')
        scale = min((panel_width - 30) / original.width, image_box_height / original.height)
        display = original.resize((round(original.width * scale), round(original.height * scale)), Image.Resampling.LANCZOS)
        ox = index * panel_width + (panel_width - display.width) // 2
        oy = top
        draw.text((index * panel_width + 15, 14), spec['title'], fill='white', font=font(19))
        draw.text((index * panel_width + 15, 39), f'{original.width} x {original.height}; displayed with aspect preserved; approximate reviewer boxes', fill='#a9b7c3', font=font(15))
        board.paste(display, (ox, oy))
        features = []
        for color, (number, label, box) in zip(colors, spec['features']):
            scaled = [round(ox + box[0] * scale), round(oy + box[1] * scale), round(ox + box[2] * scale), round(oy + box[3] * scale)]
            draw.rectangle(scaled, outline=color, width=2)
            nx, ny = scaled[0] + 3, scaled[1] + 3
            draw.rectangle((nx, ny, nx + 22, ny + 25), fill='#161b20')
            draw.text((nx + 4, ny + 1), number, fill=color, font=font(17))
            ly = 643 + (int(number) - 1) * 31
            draw.text((index * panel_width + 18, ly), f'{number}. {label}', fill=color, font=font(18))
            features.append({'number': number, 'label': label, 'bounds_xyxy': box, 'normalized_bounds': [round(box[0] / original.width, 4), round(box[1] / original.height, 4), round(box[2] / original.width, 4), round(box[3] / original.height, 4)]})
        records.append({'source': spec['source'], 'kind': 'user concept target, not actual engine output', 'source_size': list(original.size), 'sha256': hashlib.sha256(raw).hexdigest(), 'features': features, 'approximate_landmarks': spec['approximate_landmarks']})
    destination = OUT / 'reference-landmarks.png'
    board.save(destination)
    with Image.open(destination) as check:
        check.load()
        assert check.size == board.size
    result = {'purpose': 'Qualitative chamber landmarks for independent front/reverse visual review. Boxes are approximate reviewer annotations, not segmentation ground truth or pass thresholds.', 'sources': records, 'output': {'path': destination.relative_to(ROOT).as_posix(), 'size': list(board.size), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'full_pixel_decode': True}, 'method': 'Original source pixels are not color-adjusted, stretched or overwritten. Annotation board resizes each source with Lanczos while preserving its aspect ratio, then draws labelled rectangles. It is an annotated aid; original files remain the primary visual evidence.'}
    (OUT / 'provenance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['output'], indent=2))


if __name__ == '__main__':
    main()
