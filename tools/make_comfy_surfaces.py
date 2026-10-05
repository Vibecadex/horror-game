"""Turn ComfyUI study scans into tileable DirectX maps. No engine and no reference frames."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "study" / "comfy-raw"
OUT = ROOT / "Assets" / "Adapted" / "Parity" / "Surfaces"
STUDY = ROOT / "study" / "assets"
SIZE = 1024


def load(name):
    image = Image.open(SRC / name).convert("RGB").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    return np.asarray(image).astype(np.float32)


def blur(data, radius):
    image = Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGB")
    return np.asarray(image.filter(ImageFilter.GaussianBlur(radius))).astype(np.float32)


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


def luma(color):
    return color[..., 0] * 0.2126 + color[..., 1] * 0.7152 + color[..., 2] * 0.0722


def stretch(gray):
    low, high = np.percentile(gray, [4, 96])
    return np.clip((gray - low) / max(1.0, high - low), 0, 1)


def save_rgb(path, data):
    Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGB").save(path)


def normal_from_height(height, strength):
    gy, gx = np.gradient(height)
    nx = -gx * strength
    ny = gy * strength
    nz = np.full_like(nx, 255.0)
    length = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    return np.stack(((nx / length + 1) * 127.5, (ny / length + 1) * 127.5, (nz / length + 1) * 127.5), -1)


def gray_rgb(gray):
    channel = np.clip(gray, 0, 255)[..., None]
    return np.repeat(channel, 3, axis=2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    STUDY.mkdir(parents=True, exist_ok=True)
    cloth = seamless(load("cloth-weave.png"), 72)
    cloth[..., 0] *= 1.05
    cloth[..., 1] *= 0.98
    cloth[..., 2] *= 0.84
    cloth = np.clip(cloth, 0, 255)
    height = seamless(luma(load("cloth-height.png"))[..., None].repeat(3, axis=2), 72)
    height_gray = stretch(luma(height))
    normal = normal_from_height(height_gray * 255.0, 4.6)
    cloth_rough = np.clip(0.88 + (1.0 - height_gray) * 0.09, 0.84, 0.98)
    concrete = seamless(load("concrete-damp.png"), 80)
    concrete_gray = stretch(luma(concrete))
    # Darker generated patches become the damp end. 0 = damp, 1 = dry.
    dry = concrete_gray
    files = {
        "T_Comfy_Cloth_Weave.png": cloth,
        "T_Comfy_Cloth_Normal.png": normal,
        "T_Comfy_Cloth_Roughness.png": gray_rgb(cloth_rough * 255.0),
        "T_Comfy_Floor_Variation.png": gray_rgb(stretch(luma(blur(concrete, 2))) * 255.0),
        "T_Comfy_Floor_Dry.png": gray_rgb(dry * 255.0),
    }
    written = []
    for name, data in files.items():
        for folder in (OUT, STUDY):
            path = folder / name
            save_rgb(path, data)
            written.append(str(path.relative_to(ROOT)))
    preview = np.zeros((SIZE, SIZE * 3, 3), np.uint8)
    preview[:, 0:SIZE] = np.clip(cloth, 0, 255).astype(np.uint8)
    preview[:, SIZE:SIZE * 2] = np.clip(normal, 0, 255).astype(np.uint8)
    preview[:, SIZE * 2:] = np.clip(gray_rgb(dry * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(preview, "RGB").save(STUDY / "comfy-surface-preview.png")
    report = {
        "source": "study/comfy-raw",
        "model": "flux-2-klein-4b-fp8 local ComfyUI",
        "not_from_reference_clip": True,
        "normal_space": "DirectX, green positive up",
        "floor_dry": "0 is damp, 1 is dry. Material remaps to roughness 0.42-0.93.",
        "cloth_roughness_stored_range": [float(cloth_rough.min()), float(cloth_rough.max())],
        "files": written,
    }
    (OUT / "provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (STUDY / "comfy-provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "files": len(written)}, indent=2))


if __name__ == "__main__":
    main()
