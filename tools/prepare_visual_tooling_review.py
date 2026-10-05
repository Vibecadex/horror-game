"""Assemble the bounded project material requested for an external visual-tooling review."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "evidence/reviews/grok-heavy-20261004"
DESTINATION.mkdir(parents=True, exist_ok=True)
receipt = json.loads((ROOT / "evidence/setup/latest-verification.json").read_text())
run = Path(receipt["run_directory"]) / "astra-probe/engine"
runtime = json.loads((run / "runtime/runtime.json").read_text())
summary = {key: runtime[key] for key in ("passed", "checks", "input_method", "physical_device_verified",
                                         "proves_new_encounter", "positions", "yaws", "max_projectiles",
                                         "max_enemies", "wall_seconds", "world_start_time", "world_end_time")}
driver = (ROOT / "tools/astra_setup.py").read_text()
functions = {node.name: ast.get_source_segment(driver, node) for node in ast.parse(driver).body
             if isinstance(node, ast.FunctionDef)}
intro = """# Unreal visual verification tooling: independent review packet

Prepared 4 October 2026 for the user's explicit request to employ Grok Heavy in the browser.
This packet contains only task-related verification source, a reduced test receipt and visual examples.
No authentication files, account configuration, unrelated project material or raw machine logs are included.

## Goal and current scope

The future game must recreate the supplied phone video's elevated oblique horror-combat view:
small human, large grounded pale monster, worn dark floor, localized blue/teal illumination,
dark perimeter, restrained red glow, independent movement/aiming, cyan weapon flashes.
A monstrous teddy is a deliberate replacement for the original monster.
Source video is 22.99 seconds, 384x848, 60 fps with rotated landscape gameplay and social UI.
Upright supplied frames are 848x384. Phone/social overlays and unrelated feed frames must be excluded
from comparison. Useful gameplay is about source seconds 5–18. Exact source bindings are unknown.
The downloaded teddy is textured but unrigged/unanimated. Sound has not been auditioned.

The finished horror scene has NOT been built. The current validated scene is Epic's bright stock
Blueprint Twin Stick starter. Its screenshots are setup evidence, not a claimed reference match.
The active project has no native project module. Windows Smart App Control remains On;
new unsigned native game DLLs were blocked, so no custom compiled plugin should be assumed usable.
Installed tools: Unreal 5.8.3, Blender 5.2, FFmpeg/FFprobe 8, Python 3.14, Codex with Astra access.
Unreal's built-in Python editor authoring and BlueprintGraphEditor APIs are exercised below.

The model/browser review can inspect the supplied material; it cannot execute these local tools.
Do not claim to have run the project or endorse a passing test as final visual acceptance.

## Attached image roles

- upright-05.png, upright-10.png, upright-16.png: actual source reference frames, not target game output.
- runtime-01.png, runtime-03.png: actual editor-play captures from the verified stock starter run.
- standalone.png: actual separate UnrealEditor -game capture from the same run.
- teddy-front.png: Blender render of the actual downloaded candidate, not in-game final artwork.

## Verification currently implemented

Full setup: 34 local prerequisites; authenticated Astra reads reference images and runs tools;
16 shipped Blueprints load/compile; namespaced teddy mesh/material/texture import; fresh custom
Blueprint generation/compile/save; second-process reopen; seven editor-play checks; three 1280x720
captures; separate ordinary -game launch with one additional image. Source/reference hashes preserved.
Input is Enhanced Input action injection, not physical keyboard/mouse/gamepad testing.
The driver checks PNG signatures/dimensions, fresh output directories, report booleans and a runtime
log marker. A human/agent has viewed captures. No automated reference-fidelity score is implemented.
No final-encounter animation/damage/dodge/pause/restart, audio or packaged-build acceptance is claimed.

## Questions for the independent reviewer

1. Distinguish capture infrastructure, functional smoke testing, visual regression and reference fidelity.
2. Audit false positives and false negatives in the exact scripts, especially screenshot completion,
   frame/state correspondence, timing/warmup, pixel validity, old receipts, project/map identity,
   action-path causality, wraparound angles, input coverage and shutdown.
3. Recommend the smallest practical visual-verification stack for this local Unreal 5.8 Blueprint
   workflow. Evaluate ordinary runtime screenshots/video, Unreal automation screenshot comparison,
   Movie Render Queue, Unreal Insights/GPU profiling, RenderDoc only when needed, and external
   image metrics or visual-model review. Explain what should be used for this task and what should
   not become a misleading pass gate. Prefer installed/built-in tools and normal free tooling.
4. Specify reliable comparison outputs for the deliberately different teddy and camera/player motion:
   crop/mask source overlays, aspect/field-of-view and relative scale, silhouettes, contact shadows,
   floor readability, light distribution, fog/exposure, temporal stability, animation and effects.
5. Give a concrete prioritized implementation plan with severity, source location, rationale and
   meaningful acceptance tests. Separate minimum pre-art changes from later fidelity/behavior checks.
6. Verify version-sensitive tool/API recommendations against current primary documentation, link
   sources, and label anything not confirmed for Unreal 5.8. Do not invent API names or results.

Please review the actual images as well as source. Be independent and specific; do not merely repeat
the packet. Return a concise verdict, prioritized findings, recommended tool stack and acceptance matrix.
"""
parts = [intro, "\n## Actual reduced runtime receipt\n```json\n" + json.dumps(summary, indent=2) + "\n```\n"]
for name in ("verify_blueprint_runtime.py", "verify_blueprint_authoring.py"):
    parts.append(f"\n## tools/{name}\n```python\n" + (ROOT / "tools" / name).read_text() + "\n```\n")
for name in ("unreal_local_arguments", "run_logged", "require_launch_verification", "verify_runtime", "verify_standalone"):
    parts.append(f"\n## tools/astra_setup.py::{name}\n```python\n" + functions[name] + "\n```\n")
packet = DESTINATION / "VISUAL_TOOLING_REVIEW_PACKET.md"
packet.write_text("\n".join(parts), encoding="utf-8")
attachments = [packet,
    *[ROOT / "evidence/reference-video" / f"upright-{second}.png" for second in ("05", "10", "16")],
    run / "runtime/runtime-01.png", run / "runtime/runtime-03.png", run / "standalone.png",
    ROOT / "evidence/asset-research/teddy-front.png"]
manifest = {"prepared_at_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "User-requested Grok Heavy review of visual verification tooling",
            "source_setup_receipt": str(Path(receipt["run_directory"]) / "verification.json"),
            "attachments": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                             "bytes": p.stat().st_size} for p in attachments]}
(DESTINATION / "upload-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"packet": str(packet), "files": len(attachments),
                  "total_bytes": sum(f["bytes"] for f in manifest["attachments"])}, indent=2))
