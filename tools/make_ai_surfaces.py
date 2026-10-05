"""Turn the generated color maps into tileable Unreal textures. No engine."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\4elut\.grok\sessions\C%3A%5CProjects%5Cto-deploy%5Chorror-game\01a10a54-69ee-7253-978b-c01aa506ee63\images")
OUT = ROOT / "Assets" / "Adapted" / "Arena"
CHECK = ROOT / "study" / "visuals"
SIZE = 1024


def arr(path):
    image = Image.open(path).convert("RGB")
    image = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    return np.asarray(image).astype(np.float32)


def save_rgb(path, data):
    Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGB").save(path)


def save_rgba(path, data):
    Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGBA").save(path)


def blur(data, radius):
    image = Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGB")
    return np.asarray(image.filter(ImageFilter.GaussianBlur(radius))).astype(np.float32)


def flatten_large_shapes(data, radius, keep):
    low = blur(data, radius)
    mean = low.mean(axis=(0, 1), keepdims=True)
    high = data - low
    return np.clip(mean + (low - mean) * keep + high, 0, 255)


def seamless(data, band):
    rolled = np.roll(np.roll(data, SIZE // 2, 0), SIZE // 2, 1)
    y = np.linspace(-1, 1, SIZE, dtype=np.float32)
    x = np.linspace(-1, 1, SIZE, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    edge = np.maximum(np.abs(xx), np.abs(yy))
    width = band / (SIZE / 2)
    weight = np.clip((edge - (1 - width)) / width, 0, 1)[..., None]
    mixed = data * (1 - weight) + rolled * weight
    return np.roll(np.roll(mixed, -SIZE // 2, 0), -SIZE // 2, 1)


def repeat(data):
    tile = np.clip(data, 0, 255).astype(np.uint8)
    canvas = np.zeros((SIZE * 2, SIZE * 2, 3), np.uint8)
    for iy in range(2):
        for ix in range(2):
            canvas[iy * SIZE:(iy + 1) * SIZE, ix * SIZE:(ix + 1) * SIZE] = tile
    return canvas


def maps_from_color(color, strength):
    gray = color[..., 0] * 0.2126 + color[..., 1] * 0.7152 + color[..., 2] * 0.0722
    gy, gx = np.gradient(gray)
    nx = -gx * strength
    ny = gy * strength
    nz = np.full_like(nx, 255.0)
    length = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    normal = np.stack(((nx / length + 1) * 127.5, (ny / length + 1) * 127.5, (nz / length + 1) * 127.5), -1)
    rough = np.clip(196 + (128 - gray) * 0.35, 150, 245)
    roughness = np.stack([rough, rough, rough], -1)
    return normal, roughness


def main():
    floor = seamless(flatten_large_shapes(arr(SRC / "3.jpg"), 28, 0.35), 72)
    plush = seamless(flatten_large_shapes(arr(SRC / "6.jpg"), 36, 0.15), 64)
    floor_n, floor_r = maps_from_color(floor, 3.2)
    plush_n, plush_r = maps_from_color(plush, 6.0)
    names = {
        "T_AI_Floor_Color.png": floor,
        "T_AI_Floor_Normal.png": floor_n,
        "T_AI_Floor_Roughness.png": floor_r,
        "T_AI_Plush_Normal.png": plush_n,
        "T_AI_Plush_Roughness.png": plush_r,
    }
    for name, data in names.items():
        save_rgb(OUT / name, data)
    Image.fromarray(repeat(floor)).save(CHECK / "ai-floor-2x2.png")
    Image.fromarray(repeat(plush)).save(CHECK / "ai-plush-2x2.png")

    sheet = arr(SRC / "5.jpg")
    gray = sheet.mean(axis=2)
    half = SIZE // 2
    quads = {
        "Crack": (0, 0, half, half),
        "Stain": (half, 0, SIZE, half),
        "Scuff": (0, half, half, SIZE),
        "Debris": (half, half, SIZE, SIZE),
    }
    for label, (x0, y0, x1, y1) in quads.items():
        crop_rgb = sheet[y0:y1, x0:x1]
        crop_gray = gray[y0:y1, x0:x1]
        alpha = np.clip((crop_gray - 14) * 3.0, 0, 255)
        alpha_image = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.8))
        crop = np.dstack((crop_rgb, np.asarray(alpha_image).astype(np.float32)))
        square = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        chip = Image.fromarray(np.clip(crop, 0, 255).astype(np.uint8), "RGBA")
        chip.thumbnail((460, 460), Image.Resampling.LANCZOS)
        square.paste(chip, ((512 - chip.width) // 2, (512 - chip.height) // 2), chip)
        square.save(OUT / f"T_AI_Decal_{label}.png")
    note = {
        "author": "Original generated surfaces for this encounter",
        "date": "2026-10-05",
        "source": "Imagine color maps, then local flatten, tile, and DirectX normal derivation",
        "not_from_reference_clip": True,
        "files": sorted(path.name for path in OUT.glob("T_AI_*.png")),
        "normal_space": "DirectX, green positive up",
        "floor_source": "images/3.jpg",
        "plush_source": "images/6.jpg",
        "decal_sheet": "images/5.jpg",
    }
    (OUT / "ai-provenance.json").write_text(json.dumps(note, indent=2))
    print(json.dumps(note, indent=2))


if __name__ == "__main__":
    main()
