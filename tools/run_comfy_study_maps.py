"""Queue original study maps on the local ComfyUI server. No reference-frame img2img."""
import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "study" / "comfy-raw"
OUT.mkdir(parents=True, exist_ok=True)
SERVER = "http://127.0.0.1:8195"
JOBS = [
    {
        "name": "cloth-weave",
        "seed": 61917,
        "prompt": (
            "Orthographic macro textile scan, seamless repeating swatch, worn plush fabric, "
            "muted olive and warm taupe fibers, dusty grey-green nap, fine weave a few millimeters across, "
            "small one-centimeter clumps, matted and uneven dye, flat even lighting, no animal, no face, "
            "no seam line, no text, no logo, no background"
        ),
    },
    {
        "name": "cloth-height",
        "seed": 61918,
        "prompt": (
            "Orthographic grayscale height scan of plush fabric, seamless, pale gray raised fiber nap, "
            "darker weave valleys, fine few-millimeter threads and small clumps, even lighting, "
            "no color cast, no animal, no text, no logo"
        ),
    },
    {
        "name": "concrete-damp",
        "seed": 61919,
        "prompt": (
            "Orthographic top-down scan of worn industrial concrete, seamless, cool grey aggregate, "
            "sparse irregular darker damp patches with fragmented soft edges, hairline branching cracks, "
            "dry areas lighter, no puddle silhouette, no objects, no people, no text, flat lighting"
        ),
    },
]


def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(SERVER + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def get(path):
    last = None
    for _ in range(40):
        try:
            with urllib.request.urlopen(SERVER + path, timeout=60) as response:
                return json.load(response)
        except Exception as exc:
            last = exc
            time.sleep(3)
    raise last


def graph(job):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": job["prompt"], "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "seed": job["seed"],
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "denoise": 1.0,
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "teddy-study/" + job["name"]}},
    }


def run_job(job):
    dest = OUT / (job["name"] + ".png")
    if dest.exists() and dest.stat().st_size > 100000:
        print("SKIP", dest, dest.stat().st_size, flush=True)
        return {"name": job["name"], "file": dest.name, "bytes": dest.stat().st_size, "seed": job["seed"], "prompt_id": "existing"}
    result = post("/prompt", {"prompt": graph(job), "client_id": str(uuid.uuid4())})
    if result.get("node_errors"):
        raise RuntimeError(json.dumps({"job": job["name"], "node_errors": result["node_errors"]})[:4000])
    prompt_id = result["prompt_id"]
    print("QUEUED", job["name"], prompt_id, flush=True)
    deadline = time.time() + 600
    while time.time() < deadline:
        time.sleep(5)
        history = get("/history/" + prompt_id)
        if prompt_id not in history:
            continue
        item = history[prompt_id]
        status = item.get("status", {})
        if status.get("status_str") == "error":
            raise RuntimeError(json.dumps({"job": job["name"], "messages": status.get("messages")})[:4000])
        images = []
        for node in item.get("outputs", {}).values():
            images.extend(node.get("images", []))
        if not images:
            continue
        image = images[0]
        query = urllib.parse.urlencode({"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")})
        with urllib.request.urlopen(SERVER + "/view?" + query, timeout=60) as response:
            payload = response.read()
        dest = OUT / (job["name"] + ".png")
        dest.write_bytes(payload)
        print("SAVED", dest, len(payload), flush=True)
        return {"name": job["name"], "file": dest.name, "bytes": len(payload), "seed": job["seed"], "prompt_id": prompt_id}
    raise TimeoutError(job["name"])


def main():
    saved = []
    for job in JOBS:
        saved.append(run_job(job))
    (OUT / "provenance.json").write_text(json.dumps({
        "server": SERVER,
        "model": "flux-2-klein-4b-fp8",
        "clip": "qwen_3_4b",
        "vae": "flux2-vae",
        "steps": 4,
        "cfg": 1.0,
        "sampler": "euler",
        "scheduler": "simple",
        "size": [1024, 1024],
        "not_from_reference_clip": True,
        "jobs": saved,
    }, indent=2) + "\n", encoding="utf-8")
    print("COMFY_MAPS_COMPLETE", len(saved), flush=True)


if __name__ == "__main__":
    main()
