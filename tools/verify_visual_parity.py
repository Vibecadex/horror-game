"""Create independent visual-comparison evidence without launching Unreal.

Only reads explicitly supplied images/receipts. Writes a fresh folder below
evidence/parity-review. Metrics describe rendered pixels; they cannot accept art.
Run --help for the small CLI and study/PARITY_QA.md for the review contract.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "parity-review"
REFERENCE = ROOT / "study" / "visuals" / "direction-close-best.jpg"
SIZE = (1280, 720)
# Hand-marked semantic regions of the selected 1280x720 look study. These are
# approximate observation masks, not ground truth segmentations. Body masks
# omit most background; the player mask includes the gun but not its shadow.
REFERENCE_REGIONS = {
    "boss_body": {"polygon": [[498, 134], [516, 160], [504, 177], [525, 205], [530, 230], [510, 252], [493, 264], [489, 287], [471, 283], [449, 265], [419, 280], [416, 307], [432, 321], [419, 338], [392, 326], [373, 282], [370, 254], [387, 220], [390, 190], [420, 166], [468, 159]]},
    "player_body": {"polygon": [[818, 420], [843, 438], [851, 436], [860, 441], [866, 449], [860, 463], [857, 480], [865, 496], [858, 504], [848, 481], [834, 501], [826, 499], [837, 474], [838, 457], [829, 450], [836, 445]]},
    "player_pool": {"ellipse": [734, 436, 831, 508]},
    "pool_surround": {"polygon": [[688, 442], [728, 449], [730, 505], [777, 520], [813, 523], [813, 546], [710, 527], [676, 485]]},
    "boss_shadow": {"polygon": [[393, 313], [434, 308], [477, 280], [509, 283], [536, 315], [518, 345], [501, 390], [451, 452], [414, 476], [375, 466], [377, 414], [347, 393], [358, 350]]},
    "shadow_surround": {"polygon": [[550, 298], [606, 320], [605, 421], [529, 459], [476, 473], [483, 449], [521, 404], [548, 352]]},
    "cloth_detail": {"polygon": [[413, 190], [448, 167], [478, 175], [497, 204], [477, 228], [426, 225], [404, 218]]},
    "floor_detail": {"polygon": [[480, 506], [642, 463], [700, 552], [633, 654], [434, 642]]},
    "far_haze": {"rectangle": [245, 22, 1090, 127]},
    "central_floor": {"polygon": [[548, 246], [771, 236], [965, 293], [971, 405], [843, 402], [681, 413], [566, 467], [549, 398]]},
    "left_debris": {"rectangle": [34, 348, 286, 550]},
    "dark_perimeter": {"edge_fraction": 0.045},
    "dark_corners": {"rectangles": [[0, 0, 95, 71], [1184, 0, 1279, 71], [0, 648, 95, 719], [1184, 648, 1279, 719]]},
}
COLORS = [(255, 181, 71), (95, 221, 255), (255, 248, 170), (164, 232, 148),
          (199, 142, 255), (149, 158, 245), (245, 129, 204), (239, 158, 113),
          (121, 203, 180), (243, 216, 135), (255, 159, 133), (180, 180, 180)]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_image(path: Path) -> Image.Image:
    with Image.open(path) as im:
        im.load()
        if im.size != SIZE:
            raise ValueError(f"Expected an unrescaled {SIZE} image, got {im.size}: {path}")
        return im.convert("RGB")


def font(size=18):
    for path in [Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/arial.ttf")]:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def mask_for(spec: dict, size=SIZE) -> np.ndarray:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if "polygon" in spec:
        draw.polygon([tuple(p) for p in spec["polygon"]], fill=255)
    elif "rectangle" in spec:
        draw.rectangle(spec["rectangle"], fill=255)
    elif "ellipse" in spec:
        draw.ellipse(spec["ellipse"], fill=255)
    elif "edge_fraction" in spec:
        width, height = size
        edge = round(min(size) * spec["edge_fraction"])
        draw.rectangle((0, 0, width-1, height-1), fill=255)
        draw.rectangle((edge, edge, width-1-edge, height-1-edge), fill=0)
    elif "rectangles" in spec:
        for rectangle in spec["rectangles"]:
            draw.rectangle(rectangle, fill=255)
    else:
        raise ValueError(f"Unknown region geometry: {spec}")
    for polygon in spec.get("exclude_polygons", []):
        draw.polygon([tuple(p) for p in polygon], fill=0)
    result = np.asarray(mask) > 0
    if not result.any():
        raise ValueError(f"Empty region: {spec}")
    return result


def bounds(mask: np.ndarray) -> list[int]:
    yy, xx = np.nonzero(mask)
    return [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)]


def rounded(value):
    if isinstance(value, np.ndarray):
        return [round(float(x), 4) for x in value]
    return round(float(value), 4)


def stats(image: Image.Image, mask: np.ndarray) -> dict:
    rgb = np.asarray(image, dtype=np.float64)
    luma = rgb @ np.array([.2126, .7152, .0722])
    display = luma[mask]
    unit = rgb / 255
    linear = np.where(unit <= .04045, unit / 12.92, ((unit + .055) / 1.055)**2.4)
    linear_luma = linear @ np.array([.2126, .7152, .0722])
    blur = np.asarray(image.filter(ImageFilter.GaussianBlur(2)), dtype=np.float64)
    high_frequency = ((rgb - blur) @ np.array([.2126, .7152, .0722]))[mask]
    mean = rgb[mask].mean(axis=0)
    return {
        "pixels": int(mask.sum()),
        "image_fraction": rounded(mask.mean()),
        "bounds_xyxy": bounds(mask),
        "display_rgb_mean_0_255": rounded(mean),
        "display_luma_mean_0_255": rounded(display.mean()),
        "display_luma_p10_p50_p90": rounded(np.percentile(display, [10, 50, 90])),
        "display_luma_std": rounded(display.std()),
        "linear_luminance_mean_0_1": rounded(linear_luma[mask].mean()),
        "fraction_display_luma_below_8": rounded((display < 8).mean()),
        "fraction_display_luma_above_40": rounded((display > 40).mean()),
        "fraction_display_luma_above_80": rounded((display > 80).mean()),
        "fraction_display_luma_above_160": rounded((display > 160).mean()),
        "channel_share_r_g_b": rounded(mean / max(mean.sum(), 1e-6)),
        "detail_rms_after_2px_blur_display_luma": rounded(np.sqrt((high_frequency**2).mean())),
    }


def image_stats(image: Image.Image, regions: dict) -> dict:
    result = {name: stats(image, mask_for(spec)) for name, spec in regions.items()}
    result["whole_image"] = stats(image, np.ones((SIZE[1], SIZE[0]), dtype=bool))
    return result


def contrasts(measures: dict) -> dict:
    pairs = [("player_pool", "pool_surround"), ("boss_shadow", "shadow_surround"),
             ("central_floor", "dark_perimeter"), ("far_haze", "dark_perimeter")]
    result = {}
    for numerator, denominator in pairs:
        if numerator in measures and denominator in measures:
            a = measures[numerator]["display_luma_mean_0_255"]
            b = measures[denominator]["display_luma_mean_0_255"]
            result[f"{numerator}_over_{denominator}"] = round(a / max(b, .001), 4)
    return result


def framing_diagnostics(reference: dict, candidate: dict) -> dict:
    result = {}
    for name in ["boss_body", "player_body"]:
        if name not in candidate:
            continue
        rb = np.asarray(reference[name]["bounds_xyxy"], float)
        cb = np.asarray(candidate[name]["bounds_xyxy"], float)
        displacement = ((cb[:2] + cb[2:]) - (rb[:2] + rb[2:])) / 2
        ratio = (cb[2:] - cb[:2]) / (rb[2:] - rb[:2])
        within = (np.abs(displacement / np.asarray(SIZE)) <= .03).all() and (np.abs(ratio - 1) <= .15).all()
        result[name] = {"center_displacement_pixels_xy": rounded(displacement),
                        "candidate_over_reference_width_height": rounded(ratio),
                        "within_suggested_3_percent_frame_and_15_percent_size_band": bool(within)}
    return result


def add_label(image: Image.Image, label: str, width=1280) -> Image.Image:
    result = Image.new("RGB", (width, round(image.height*width/image.width) + 50), (20, 24, 28))
    resized = image.resize((width, result.height - 50), Image.Resampling.LANCZOS)
    result.paste(resized, (0, 50))
    ImageDraw.Draw(result).text((16, 12), label, font=font(20), fill=(225, 232, 237))
    return result


def pair_image(first: Image.Image, second: Image.Image, labels, width=1280) -> Image.Image:
    a, b = add_label(first, labels[0], width), add_label(second, labels[1], width)
    out = Image.new("RGB", (a.width+b.width, max(a.height, b.height)), (20, 24, 28))
    out.paste(a, (0, 0)); out.paste(b, (a.width, 0))
    return out


def annotated(image: Image.Image, regions: dict) -> Image.Image:
    out = image.copy()
    draw = ImageDraw.Draw(out)
    for idx, (name, spec) in enumerate(regions.items()):
        color = COLORS[idx % len(COLORS)]
        box = bounds(mask_for(spec))
        if "polygon" in spec:
            points = [tuple(p) for p in spec["polygon"]]
            draw.line(points + [points[0]], fill=color, width=2)
        elif "ellipse" in spec:
            draw.ellipse(box, outline=color, width=2)
        elif "rectangles" in spec:
            for rectangle in spec["rectangles"]:
                draw.rectangle(rectangle, outline=color, width=2)
        else:
            draw.rectangle(box, outline=color, width=2)
        for polygon in spec.get("exclude_polygons", []):
            points = [tuple(p) for p in polygon]
            draw.line(points + [points[0]], fill=color, width=2)
            draw.text(points[0], "excluded", fill=color, font=font(12), stroke_width=1, stroke_fill=(0, 0, 0))
        label_at = (min(box[0]+3, 1050), min(box[1]+3, 690))
        draw.text(label_at, name, fill=color, font=font(14), stroke_width=2, stroke_fill=(0, 0, 0))
    return out


def detail_sheet(reference: Image.Image, candidate: Image.Image, r_regions: dict, c_regions: dict):
    names = ["boss_body", "cloth_detail", "player_body", "player_pool", "floor_detail", "left_debris", "far_haze", "boss_shadow"]
    names = [name for name in names if name in r_regions and name in c_regions]
    width, height = 960, 260
    out = Image.new("RGB", (width, height*len(names)), (19, 23, 27))
    draw = ImageDraw.Draw(out)
    for row, name in enumerate(names):
        for col, (im, regions, label) in enumerate([(reference, r_regions, "REFERENCE"), (candidate, c_regions, "CANDIDATE")]):
            box = bounds(mask_for(regions[name]))
            crop = im.crop(box)
            crop.thumbnail((460, 205), Image.Resampling.LANCZOS)
            x, y = col*480, row*height
            out.paste(crop, (x+(480-crop.width)//2, y+45+(205-crop.height)//2))
            draw.text((x+12, y+7), f"{name} | {label}", fill=(229, 231, 233), font=font(17))
            draw.text((x+12, y+28), f"Source crop {box}; shown to fit, aspect preserved", fill=(156, 174, 184), font=font(13))
    return out


def luminance_map(image: Image.Image) -> Image.Image:
    luma = np.asarray(image, dtype=float) @ np.array([.2126, .7152, .0722])
    # Fixed shared thresholds, not independently stretched or exposure normalized.
    palette = np.array([[0, 0, 0], [25, 31, 71], [18, 106, 125], [75, 182, 130], [222, 205, 82], [255, 109, 76]], dtype=np.uint8)
    classes = np.digitize(luma, [8, 25, 40, 80, 160])
    return Image.fromarray(palette[classes])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True, help="Full unedited 1280x720 Unreal capture")
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--candidate-regions", type=Path, help="JSON {coordinate_size:[1280,720], regions:{...}} with manually inspected masks")
    parser.add_argument("--capture-receipt", type=Path, help="Capture receipt for provenance; does not itself prove parity")
    parser.add_argument("--capture-kind", choices=["ordinary-gameplay", "staged-gameplay", "architectural", "unknown"], default="unknown")
    parser.add_argument("--framing", choices=["unmatched", "approximate", "matched"], default="unmatched")
    parser.add_argument("--label", default="Unreal candidate")
    parser.add_argument("--output", type=Path, required=True, help="New directory below evidence/parity-review")
    args = parser.parse_args()
    out = args.output.resolve()
    if EVIDENCE.resolve() not in out.parents:
        parser.error("Output must be a new subdirectory of evidence/parity-review")
    if out.exists():
        parser.error("Output already exists; choose a fresh evidence directory")
    reference_path, candidate_path = args.reference.resolve(), args.candidate.resolve()
    reference, candidate = read_image(reference_path), read_image(candidate_path)
    supplied = None
    if args.candidate_regions:
        supplied = json.loads(args.candidate_regions.read_text(encoding="utf-8-sig"))
        if supplied.get("coordinate_size") != list(SIZE):
            parser.error("Candidate annotation coordinate_size must be [1280,720]")
        c_regions = supplied["regions"]
        if not isinstance(c_regions, dict) or not c_regions:
            parser.error("Candidate regions must be a nonempty object")
    else:
        c_regions = REFERENCE_REGIONS
    if args.framing == "matched" and (supplied is None or args.capture_receipt is None):
        parser.error("Matched framing requires independently marked candidate regions and a capture receipt")
    if args.capture_kind == "architectural" and args.framing != "unmatched":
        parser.error("An architectural hero view cannot be declared matched gameplay")
    ref_stats, can_stats = image_stats(reference, REFERENCE_REGIONS), image_stats(candidate, c_regions)
    frame = framing_diagnostics(ref_stats, can_stats) if supplied else {}
    matched_band = set(frame) == {"boss_body", "player_body"} and all(item["within_suggested_3_percent_frame_and_15_percent_size_band"] for item in frame.values())
    receipt_info = None
    if args.capture_receipt:
        receipt_path = args.capture_receipt.resolve()
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        captures = receipt.get("captures", [])
        corresponding = [c for c in captures if c.get("path") and Path(c["path"]).resolve() == candidate_path]
        receipt_info = {"path": str(receipt_path), "sha256": digest(receipt_path),
                        "reported_passed": receipt.get("passed"), "method": receipt.get("method"),
                        "corresponding_capture": corresponding, "postprocess": receipt.get("postprocess")}
        receipt_info["candidate_hash_matches_reported_capture"] = bool(corresponding) and all(
            c.get("validation", {}).get("sha256") == digest(candidate_path) for c in corresponding)
    report = {
        "schema": "visual-parity-diagnostics-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_generation_complete": True, "visual_parity": "requires_independent_visual_review",
        "reference": {"path": str(reference_path), "sha256": digest(reference_path), "size": list(reference.size), "role": "User-selected look study, not an engine capture"},
        "candidate": {"path": str(candidate_path), "sha256": digest(candidate_path), "size": list(candidate.size), "label": args.label, "capture_kind": args.capture_kind},
        "declared_framing": args.framing, "manually_annotated_candidate": supplied is not None,
        "framing_diagnostics": frame, "within_suggested_framing_band": matched_band,
        "pixelwise_error_or_similarity": None,
        "limitations": [
            "No numeric score or automatic visual-parity acceptance is produced.",
            "Regions are manually selected approximate masks, not semantic ground truth.",
            "Without candidate annotations, reference coordinates are exploratory fixed screen regions and are not valid subject comparisons.",
            "Different poses, geometry, texture placement and generated-reference inconsistencies invalidate literal pixelwise error.",
            "Display luma is computed on sRGB values; separately reported linear luminance does not recover scene radiance or exposure.",
            "Blur residual is a texture/detail cue, not proof of geometric depth, cloth, good anti-aliasing or art quality.",
            "A still does not verify animation, temporal fog, moving-light behavior, controls, physical input or performance.",
        ],
        "capture_receipt": receipt_info,
        "regions": {"reference": REFERENCE_REGIONS, "candidate": c_regions},
        "measurements": {"reference": ref_stats, "candidate": can_stats},
        "contrast_cues": {"reference": contrasts(ref_stats), "candidate": contrasts(can_stats)},
        "review_axes": {name: "pending_visual_review" for name in ["composition", "key_and_long_ground_shadow", "far_haze_dark_perimeter", "player_pool_and_readability", "woven_cloth_and_seams", "fractured_floor_and_rubble_depth", "restrained_gameplay_effects"]},
    }
    out.mkdir(parents=True, exist_ok=False)
    labels = ("REFERENCE — selected look study (not runtime)", f"CANDIDATE — {args.label}; framing: {args.framing}")
    pair_image(reference, candidate, labels).save(out / "comparison.jpg", quality=94, subsampling=0)
    pair_image(annotated(reference, REFERENCE_REGIONS), annotated(candidate, c_regions), labels).save(out / "regions.jpg", quality=94, subsampling=0)
    detail_sheet(reference, candidate, REFERENCE_REGIONS, c_regions).save(out / "details.png")
    pair_image(luminance_map(reference), luminance_map(candidate),
               ("REFERENCE display luma: black<8 blue8–25 cyan25–40 green40–80 yellow80–160 red>160", "CANDIDATE — same fixed thresholds; diagnostic map, not rendered art")).save(out / "luminance.png")
    (out / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    rows = []
    for name in ref_stats:
        if name not in can_stats:
            continue
        a, b = ref_stats[name], can_stats[name]
        rows.append(f"| {name} | {a['display_luma_mean_0_255']:.2f} | {b['display_luma_mean_0_255']:.2f} | {a['display_rgb_mean_0_255']} | {b['display_rgb_mean_0_255']} |")
    note = "Candidate regions were manually marked." if supplied else "**Candidate masks reuse reference screen coordinates. They are exploratory, not subject-aligned comparisons.**"
    lines = ["# Visual parity diagnostic evidence", "", f"Reference: `{reference_path}`", f"Candidate: `{candidate_path}`", "", f"Framing declared **{args.framing}**. Capture kind **{args.capture_kind}**. {note}", "",
             "**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**", "",
             "[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)", "",
             "Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.", "",
             "| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |", "| --- | ---: | ---: | --- | --- |", *rows, "",
             "Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.", "",
             "Reference light-pool, shadow and haze ratios: `" + json.dumps(report["contrast_cues"]["reference"]) + "`", "Candidate ratios: `" + json.dumps(report["contrast_cues"]["candidate"]) + "`", "",
             "Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    # Decode the output artifacts: evidence integrity, not an implementation test.
    decoded = {}
    for name in ["comparison.jpg", "regions.jpg", "details.png", "luminance.png"]:
        with Image.open(out / name) as im:
            im.load()
            decoded[name] = {"size": list(im.size), "sha256": digest(out / name)}
    (out / "artifact-integrity.json").write_text(json.dumps(decoded, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "visual_parity": report["visual_parity"],
                      "manually_annotated_candidate": supplied is not None,
                      "within_suggested_framing_band": matched_band, "artifacts_decoded": len(decoded)}))


if __name__ == "__main__":
    main()
