"""Tileable maps for the room shell. No engine, no reference frames, no teal bake.

Writes Assets/Adapted/RoomShell/Surfaces only. The scene pass does not import these.
Roughness is linear (byte/255). Normals are DirectX, green positive up.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Assets" / "Adapted" / "RoomShell" / "Surfaces"
SIZE = 1024
RNG = np.random.default_rng(20261005)


def wrapped_upsample(grid):
    gh, gw = grid.shape
    ys = np.linspace(0, gh, SIZE, endpoint=False)
    xs = np.linspace(0, gw, SIZE, endpoint=False)
    y0 = np.floor(ys).astype(np.int32) % gh
    x0 = np.floor(xs).astype(np.int32) % gw
    y1 = (y0 + 1) % gh
    x1 = (x0 + 1) % gw
    fy = (ys - np.floor(ys)).astype(np.float32)[:, None]
    fx = (xs - np.floor(xs)).astype(np.float32)[None, :]
    top = grid[y0][:, x0] * (1 - fx) + grid[y0][:, x1] * fx
    bottom = grid[y1][:, x0] * (1 - fx) + grid[y1][:, x1] * fx
    return top * (1 - fy) + bottom * fy


def noise(cells, octaves=4):
    field = np.zeros((SIZE, SIZE), np.float32)
    weight = 0.0
    cells = max(2, int(cells))
    for octave in range(octaves):
        amp = 0.55 ** octave
        grid_n = min(SIZE // 2, max(2, cells * (2 ** octave)))
        field += amp * wrapped_upsample(RNG.random((grid_n, grid_n), np.float32))
        weight += amp
    field /= weight
    low, high = np.percentile(field, [1.5, 98.5])
    return np.clip((field - low) / max(1e-6, high - low), 0, 1)


def save_rgb(path, data):
    Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGB").save(path)


def gray_rgb(gray):
    channel = np.clip(gray * 255.0, 0, 255)[..., None]
    return np.repeat(channel, 3, axis=2)


def normal_from_height(height, strength):
    gy, gx = np.gradient(height * 255.0)
    nx = -gx * strength
    ny = gy * strength
    nz = np.full_like(nx, 255.0)
    length = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    return np.stack(((nx / length + 1) * 127.5, (ny / length + 1) * 127.5, (nz / length + 1) * 127.5), -1)


def lines(count, vertical=False, width=0.004):
    axis = np.linspace(0, 1, SIZE, endpoint=False, dtype=np.float32)
    coord = axis[None, :] if vertical else axis[:, None]
    mask = np.zeros((SIZE, SIZE), np.float32)
    for index in range(count):
        center = (index + 0.5) / count
        mask = np.maximum(mask, np.exp(-((coord - center) ** 2) / (2 * width ** 2)))
    return mask


def build():
    concrete_n = noise(6, 5)
    streak = noise(3, 3)
    streak = np.clip((streak - 0.45) * 3.2, 0, 1) * lines(5, vertical=True, width=0.01)
    # Gravity reads as a soft darkening toward the bottom of each tile repeat.
    fall = np.linspace(0.0, 1.0, SIZE, dtype=np.float32)[:, None]
    mineral = 0.125 + concrete_n * 0.085 - streak * fall * 0.04
    mineral = np.clip(mineral, 0.09, 0.24)
    concrete = np.stack((mineral * 1.04, mineral, mineral * 0.94), -1)
    concrete_rough = np.clip(0.82 + (1.0 - concrete_n) * 0.13, 0.82, 0.95)
    concrete_height = concrete_n * 0.82 + lines(5, width=0.0016) * 0.10 + lines(1, vertical=True, width=0.0014) * 0.08

    steel_n = noise(10, 4)
    chips = np.clip((noise(28, 2) - 0.72) * 5.5, 0, 1)
    steel_g = np.clip(0.09 + steel_n * 0.05 + chips * 0.045, 0.07, 0.20)
    steel = np.stack((steel_g * 0.90, steel_g, steel_g * 0.94), -1)
    steel_rough = np.clip(0.78 - chips * 0.23 + (steel_n - 0.5) * 0.04, 0.55, 0.80)
    steel_height = steel_n * 0.45 + chips * 0.55 + lines(18, width=0.0012) * 0.15

    oxide_n = noise(8, 5)
    flake = np.clip((noise(22, 2) - 0.66) * 4.5, 0, 1)
    oxide_r = np.clip(0.15 + oxide_n * 0.12 + flake * 0.04, 0.12, 0.32)
    oxide = np.stack((oxide_r, oxide_r * 0.58, oxide_r * 0.44), -1)
    oxide_rough = np.clip(0.66 + oxide_n * 0.22 - flake * 0.04, 0.65, 0.90)
    oxide_height = oxide_n * 0.7 + flake * 0.5

    recess_n = noise(4, 3)
    recess_g = np.clip(0.03 + recess_n * 0.045, 0.025, 0.085)
    recess = np.stack((recess_g * 0.82, recess_g * 0.94, recess_g), -1)
    recess_rough = np.clip(0.84 + recess_n * 0.08, 0.84, 0.92)
    recess_height = recess_n * 0.65 + lines(4, width=0.003) * 0.35

    families = {
        "Concrete": (concrete, concrete_rough, concrete_height, 3.2),
        "Steel": (steel, steel_rough, steel_height, 2.0),
        "Oxide": (oxide, oxide_rough, oxide_height, 3.6),
        "Recess": (recess, recess_rough, recess_height, 4.0),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"owner": "teddy-room-shell-20261005", "size": SIZE, "color_space": "sRGB albedo, linear roughness, DirectX normal", "families": {}}
    thumbs = []
    for name, (color, rough, height, strength) in families.items():
        assert float(rough.max() - rough.min()) > 0.06, (name, float(rough.min()), float(rough.max()))
        if name == "Concrete":
            assert color[..., 2].mean() < color[..., 1].mean() <= color[..., 0].mean()
            assert float(color.max()) < 0.30
        if name == "Oxide":
            assert float(color[..., 0].max()) < 0.36
        color_u8 = np.clip(color * 255.0, 0, 255)
        normal = normal_from_height(height, strength)
        assert float(normal[..., 0].std()) > (0.8 if name == "Recess" else 1.5), name
        paths = {
            "color": OUT / f"T_Shell_{name}_Color.png",
            "roughness": OUT / f"T_Shell_{name}_Roughness.png",
            "normal": OUT / f"T_Shell_{name}_Normal.png",
        }
        save_rgb(paths["color"], color_u8)
        save_rgb(paths["roughness"], gray_rgb(rough))
        save_rgb(paths["normal"], normal)
        report["families"][name] = {
            "color_mean_srgb_byte": [round(float(v), 2) for v in color_u8.mean(axis=(0, 1))],
            "roughness_min": round(float(rough.min()), 3),
            "roughness_max": round(float(rough.max()), 3),
            "files": [path.name for path in paths.values()],
        }
        thumbs.append((name, color_u8, gray_rgb(rough), normal))
    sheet = Image.new("RGB", (256 * 3, 48 + 256 * 4), (12, 14, 16))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row, (name, color, rough, normal) in enumerate(thumbs):
        draw.text((8, 8 + row * 256), name, fill=(210, 205, 190), font=font)
        for col, image in enumerate((color, rough, normal)):
            thumb = Image.fromarray(image.astype(np.uint8), "RGB").resize((256, 240), Image.Resampling.BOX)
            sheet.paste(thumb, (col * 256, 28 + row * 256))
    sheet_path = OUT / "shell-surface-preview.png"
    sheet.save(sheet_path)
    report["preview"] = sheet_path.name
    report["excludes"] = ["teal wash", "player pool", "baked shadow", "red practical"]
    (OUT / "provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("SHELL_SURFACES", json.dumps(report["families"]), flush=True)


if __name__ == "__main__":
    build()
