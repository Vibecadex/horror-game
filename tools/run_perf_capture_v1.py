"""Milestone 1 performance capture and analysis (QA gate B8), version 1.

Launches the saved encounter in an ordinary ``UnrealEditor.exe -game`` process with the
CSV profiler on, waits a fixed duration, stops the capture, then analyses the CSV and the
engine log. Pure Python standard library (3.11+). It never saves, builds or edits assets.

Usage (from the repository root, with no Unreal editor or game running):

    python tools/run_perf_capture_v1.py --dry-run          # print the exact command, exit 0
    python tools/run_perf_capture_v1.py                    # 1920x1080 windowed, 180 s capture
    python tools/run_perf_capture_v1.py --duration 600 --fullscreen
    python tools/run_perf_capture_v1.py --analyze old.csv --log old-engine.log

Play normally during the capture and press F5 at least once (B8 measures reload time).
When the duration has passed, the script stops the CSV capture by typing ``csvprofile stop``
into the game console (``--stop inject``, the default). If that does not end the capture
within 30 s, it asks you to open the console (~) and type ``csvprofile stop`` yourself.
``--stop manual`` always asks. The game window is then closed with WM_CLOSE.

Outputs go to ``evidence/perf/<UTC timestamp>/``: ``profile.csv`` (the raw CSV copy),
``engine.log``, ``process.log``, ``frames.csv``, ``hitches.csv`` and ``summary.json``.

Exit codes: 0 = every B8 check passed; 1 = a check failed; 2 = invalid run. A run is invalid
when the read-back session header does not match the request (engine version, resolution,
t.MaxFPS, r.VSync, GPU) or required data is missing: the CSV, a frame-time column, memory,
no F5 reload observed (unless ``--no-require-reload``), or a capture shorter than requested.

B8 defaults (all are CLI options): p95 frame time <= 8.3 ms over gated play frames; no frame
>= 33.3 ms outside F5-reload, shader-compile and warmup windows; every F5 reload <= 3 s from
its LoadMap start to the first stable frame; PhysicalUsedMB growth <= 10 % from the first sample after warmup to the
last frame of the analysed window (samples every 10 s in between).

Sources for names used here (UE 5.8.3 as installed on Latrine): CSV columns FrameTime,
GameThreadTime, RenderThreadTime, GPUTime, RHIThreadTime, RHI/DrawCalls, PhysicalUsedMB,
MemoryFreeMB, VirtualUsedMB, ActorCount/TotalActorCount, PSO/PSOMissesOnHitch and the
metadata keys were read from the project's own CSV capture
(evidence/implementation/native-20261004T223036/runtime-profile.csv). Command-line flags
(-csvGpuStats, -dpcvars, -ExecCmds, -LogCmds, -abslog, -ResX/-ResY/-ForceRes, -windowed,
-fullscreen), ``csvprofile start|stop``, the cvar echo format, LogGarbage, LogLoad and
LogShaderCompilers messages were read from the installed engine source. Anything that
could not be confirmed that way is listed under ``assumptions`` in summary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "run_perf_capture_v1"
ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MAP = "/Game/Maps/TeddyEncounter"
DEFAULT_DURATION_S = 180.0
SCALABILITY_GROUPS = ("ViewDistanceQuality", "AntiAliasingQuality", "ShadowQuality",
                      "GlobalIlluminationQuality", "ReflectionQuality", "PostProcessQuality",
                      "TextureQuality", "EffectsQuality", "FoliageQuality", "ShadingQuality",
                      "LandscapeQuality")
METRICS = (("FrameTime", "FrameTime"), ("GameThread", "GameThreadTime"),
           ("RenderThread", "RenderThreadTime"), ("GPU", "GPUTime"),
           ("RHIThread", "RHIThreadTime"), ("DrawCalls", "RHI/DrawCalls"))
LIMITER_COLUMNS = (("GameThread", "GameThreadTime"), ("RenderThread", "RenderThreadTime"),
                   ("GPU", "GPUTime"), ("RHIThread", "RHIThreadTime"))
MEMORY_COLUMNS = ("PhysicalUsedMB", "MemoryFreeMB", "VirtualUsedMB")
ACTOR_COLUMN = "ActorCount/TotalActorCount"
PSO_HITCH_COLUMNS = ("PSO/PSOMissesOnHitch", "PSO/GraphicsPSOHitch", "PSO/ComputePSOHitch")

ASSUMPTIONS = [
    "Stopping the capture: CsvProfiler has no time-based stop and does not finalise the CSV on "
    "engine exit (no exit hook in CsvProfiler.cpp), so the script types 'csvprofile stop' into "
    "the game console with PostMessage (console key Tilde/VK_OEM_3, US layout). Unverified until "
    "QA's first run; the manual fallback asks the person playing to type it.",
    "-dpcvars=t.MaxFPS=0,r.VSync=0 uses the comma-separated key=value form; the values are set "
    "again and echoed through -ExecCmds, and the echo is what the gate reads back.",
    "Log timestamps and the 'Capture started' line share one clock (UE writes UTC log times); "
    "log events are placed on the CSV timeline relative to 'Capture started'.",
    "Frame start times are the cumulative sum of FrameTime from the first CSV row.",
    "GC pauses come from 'LogGarbage: <ms> ms for [Incremental ]GC - ...' (reachability total) "
    "lines, which are Log verbosity and need -LogCmds=\"LogGarbage Log\". Purge times from "
    "'GC purged ... in <ms>ms' are reported separately because purging is spread over frames.",
    "Shader-compile windows come from 'LogShaderCompilers: Verbose: Worker (i/n): shaders left "
    "to compile N' lines (needs -LogCmds LogShaderCompilers Verbose) plus frames whose PSO hitch "
    "counters are non-zero. Whether a -game session logs these at runtime is unverified.",
    "F5 reload = a 'LogLoad: LoadMap:' after capture start (the F5 graph calls OpenLevel "
    "/Game/Maps/TeddyEncounter per tools/build_combat.py); it ends at the first frame after "
    "'Took N seconds to LoadMap' that begins a run of stable frames. The encounter logs no "
    "restart marker or actor counts of its own; actor counts come from the CSV column "
    "ActorCount/TotalActorCount when present.",
    "The CSV is written under the -UserDir profiling folder; its path is read from the log line "
    "'Capture Ended. Writing CSV to file : <path>'.",
]


# --------------------------------------------------------------------------- helpers

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def percentile(values, p):
    """Linear-interpolated percentile, p in [0, 100] (same method as summarize_standalone_evidence)."""
    data = sorted(v for v in values if v is not None and not math.isnan(v))
    if not data:
        return None
    index = (len(data) - 1) * p / 100.0
    low, high = math.floor(index), math.ceil(index)
    return data[low] + (data[high] - data[low]) * (index - low)


def stats(values):
    data = [v for v in values if v is not None and not math.isnan(v)]
    if not data:
        return None
    return {"samples": len(data), "p50": round(percentile(data, 50), 4),
            "p95": round(percentile(data, 95), 4), "p99": round(percentile(data, 99), 4),
            "max": round(max(data), 4)}


def to_float(text):
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load_settings(root: Path) -> dict:
    """Mirror of tools/project_settings.load_settings (kept local so tests need no Windows)."""
    settings = json.loads((root / "tools/project-settings.json").read_text(encoding="utf-8-sig"))
    local = root / "tools/project-settings.local.json"
    if local.is_file():
        settings.update(json.loads(local.read_text(encoding="utf-8-sig")))
    if os.environ.get("TEDDY_ENGINE_ROOT"):
        settings["engine_root"] = os.environ["TEDDY_ENGINE_ROOT"]
    return settings


def git_info(root: Path) -> dict:
    info = {}
    for key, args in (("sha", ["rev-parse", "HEAD"]), ("branch", ["rev-parse", "--abbrev-ref", "HEAD"])):
        try:
            info[key] = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args],
                                       capture_output=True, text=True, timeout=20).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            info[key] = None
    return info


# --------------------------------------------------------------------------- CSV parsing

def parse_profile_csv(path: Path) -> dict:
    """Parse an Unreal CSV profiler file.

    Unreal writes a first header row, data rows that grow as new stats appear, then (when
    [HasHeaderRowAtEnd] is 1) the complete header row and a final metadata row of
    ``[key],value`` pairs.
    """
    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        rows = [row for row in csv.reader(handle) if row]
    if not rows:
        raise ValueError("CSV is empty")
    metadata = {}
    if rows[-1] and rows[-1][0].startswith("["):
        meta_row = rows.pop()
        for i in range(0, len(meta_row) - 1, 2):
            metadata[meta_row[i].strip("[]").lower()] = meta_row[i + 1]
    header = rows[0]
    body = rows[1:]
    if metadata.get("hasheaderrowatend") == "1" and body and body[-1] and body[-1][0] == "EVENTS":
        header = body.pop()
        if header[:len(rows[0])] != rows[0]:
            raise ValueError("Final CSV header does not extend the first header row")
    if not header or header[0] != "EVENTS":
        raise ValueError("CSV header does not start with EVENTS")
    index = {name: i for i, name in enumerate(header)}
    frames = []
    elapsed_ms = 0.0
    for number, row in enumerate(body):
        values = {name: to_float(row[i]) if i < len(row) else None
                  for name, i in index.items() if name != "EVENTS"}
        frame_ms = values.get("FrameTime")
        if frame_ms is None:
            continue
        events = []
        raw_events = row[0] if row else ""
        for part in filter(None, raw_events.split(";")):
            text, _, stamp = part.partition("##")
            events.append({"text": text, "time_s": to_float(stamp)})
        frames.append({"frame": number, "t": elapsed_ms / 1000.0, "values": values, "events": events})
        elapsed_ms += frame_ms
    return {"header": header, "metadata": metadata, "frames": frames,
            "duration_s": elapsed_ms / 1000.0}


# --------------------------------------------------------------------------- log parsing

LOG_LINE = re.compile(r"^\[(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2}):(\d{3})\]\[\s*\d+\](.*)$")
RE_CVAR_ECHO = re.compile(r'^(?:LogConsoleResponse: (?:Display: )?)?([A-Za-z][\w.]*) = "([^"]*)"(?:\s+LastSetBy: (\w+))?')
RE_SCALABILITY = re.compile(r"Applying CVar settings from Section \[(\w+)@(\d+)\] File \[Scalability\]")
RE_METADATA = re.compile(r'LogCsvProfiler: Display: Metadata set : ([\w.]+)="(.*)"$')
RE_LOADMAP = re.compile(r"^LogLoad: LoadMap: (.+)$")
RE_LOADMAP_TOOK = re.compile(r"^LogLoad: Took ([\d.]+) seconds to LoadMap\((.+)\)")
RE_ENGINE_INIT = re.compile(r"LogLoad: \(Engine Initialization\) Total time: ([\d.]+) seconds")
RE_GC_PAUSE = re.compile(r"LogGarbage: ([\d.]+) ms for (Incremental )?GC - ")
RE_GC_PURGE = re.compile(r"LogGarbage: GC purged (\d+) objects .* in ([\d.]+)ms")
RE_SHADERS_LEFT = re.compile(r"LogShaderCompilers: Verbose: Worker \(\d+/\d+\): shaders left to compile (\d+)")
RE_CSV_START = re.compile(r"LogCsvProfiler: Display: Capture started")
RE_CSV_END = re.compile(r"LogCsvProfiler: Display: Capture Ended\. Writing CSV to file : (.+)$")
RE_RHI_USED = re.compile(r"LogRHI: RHI (\w+) with Feature Level (\w+) is supported and will be used")
RE_ADAPTER_NAME = re.compile(r"^LogRHI:\s+Name: (.+)$")


def parse_log(path: Path) -> dict:
    result = {"cvars": {}, "cvar_history": [], "scalability_sections": {}, "metadata": {},
              "loadmaps": [], "gc": [], "gc_purge": [], "shader_points": [], "capture_start": None,
              "capture_end_csv": None, "engine_init_s": None, "rhi": None, "adapter": None}
    open_load = None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.rstrip("\r\n")
            match = LOG_LINE.match(line)
            when = None
            message = line
            if match:
                y, mo, d, h, mi, s, ms = (int(x) for x in match.groups()[:7])
                when = datetime(y, mo, d, h, mi, s, ms * 1000, tzinfo=timezone.utc)
                message = match.group(8)
            if (m := RE_CVAR_ECHO.match(message)):
                result["cvars"][m.group(1).lower()] = m.group(2)
                result["cvar_history"].append({"name": m.group(1), "value": m.group(2),
                                               "set_by": m.group(3), "at": when.isoformat() if when else None})
            elif (m := RE_SCALABILITY.search(message)):
                result["scalability_sections"][m.group(1)] = int(m.group(2))
            elif (m := RE_METADATA.search(message)):
                result["metadata"][m.group(1).lower()] = m.group(2)
            elif RE_CSV_START.search(message) and result["capture_start"] is None and when:
                result["capture_start"] = when
            elif (m := RE_CSV_END.search(message)):
                result["capture_end_csv"] = m.group(1).strip()
            elif (m := RE_LOADMAP.match(message)):
                open_load = {"url": m.group(1), "start": when, "end": None, "took_s": None}
                result["loadmaps"].append(open_load)
            elif (m := RE_LOADMAP_TOOK.match(message)):
                if open_load is not None and open_load["end"] is None:
                    open_load["end"], open_load["took_s"], open_load["map"] = when, float(m.group(1)), m.group(2)
            elif (m := RE_ENGINE_INIT.search(message)):
                result["engine_init_s"] = float(m.group(1))
            elif (m := RE_GC_PAUSE.search(message)):
                result["gc"].append({"at": when, "ms": float(m.group(1)), "incremental": bool(m.group(2))})
            elif (m := RE_GC_PURGE.search(message)):
                result["gc_purge"].append({"at": when, "objects": int(m.group(1)), "ms": float(m.group(2))})
            elif (m := RE_SHADERS_LEFT.search(message)):
                result["shader_points"].append({"at": when, "left": int(m.group(1))})
            elif (m := RE_RHI_USED.search(message)):
                result["rhi"] = f"{m.group(1)} {m.group(2)}"
            elif (m := RE_ADAPTER_NAME.match(message)) and result["adapter"] is None:
                result["adapter"] = m.group(1).strip()
    return result


# --------------------------------------------------------------------------- analysis

def rel(when, start):
    return None if when is None or start is None else (when - start).total_seconds()


def merge_windows(points, gap, pad):
    windows = []
    for t in sorted(points):
        if windows and t - windows[-1][1] <= gap:
            windows[-1][1] = t
        else:
            windows.append([t, t])
    return [(a - pad, b + pad) for a, b in windows]


def in_any(t, windows):
    return any(a <= t <= b for a, b in windows)


def analyze(csv_path: Path, log_path: Path | None, args) -> tuple[int, dict, list, list]:
    profile = parse_profile_csv(csv_path)
    log = parse_log(log_path) if log_path else None
    frames = profile["frames"]
    meta = dict(log["metadata"]) if log else {}
    meta.update(profile["metadata"])  # the CSV's own end-of-capture metadata wins
    invalid, warnings = [], []
    start = log["capture_start"] if log else None
    if log and start is None:
        invalid.append("Log has no 'LogCsvProfiler: Display: Capture started' line")

    # ---------- analysis window
    warmup = max(0.0, args.warmup)
    end_t = profile["duration_s"]
    if args.duration is not None:
        wanted = warmup + args.duration
        if profile["duration_s"] < wanted - 1.0:
            invalid.append(f"Capture covers {profile['duration_s']:.1f} s; requested warmup+duration is {wanted:.1f} s")
        end_t = min(end_t, wanted)
    frames = [f for f in frames if f["t"] < end_t]
    if not frames:
        invalid.append("CSV has no frames with FrameTime")

    # ---------- session header (read back, not assumed)
    cvars = log["cvars"] if log else {}
    header = {
        "engine_version": meta.get("engineversion"),
        "engine_release_version": meta.get("enginereleaseversion"),
        "build_config": meta.get("config"),
        "rhi": meta.get("rhiname") or (log or {}).get("rhi"),
        "rhi_feature_level": meta.get("rhifeaturelevel"),
        "gpu": meta.get("gpu") or (log or {}).get("adapter"),
        "gpu_driver": meta.get("gpudriver"),
        "cpu": meta.get("cpu"),
        "os": meta.get("os"),
        "device_profile": meta.get("deviceprofile"),
        "resolution": [to_float(meta.get("systemresolution.resx")), to_float(meta.get("systemresolution.resy"))],
        "t.MaxFPS": cvars.get("t.maxfps"),
        "r.VSync": cvars.get("r.vsync"),
        "vsyncenabled_metadata": meta.get("vsyncenabled"),
        "scalability_cvars": {g: cvars.get(f"sg.{g.lower()}") for g in SCALABILITY_GROUPS},
        "scalability_sections_applied": (log or {}).get("scalability_sections", {}),
        "commandline": meta.get("commandline"),
        "csv_id": meta.get("csvid"),
        "capture_duration_metadata_s": to_float(meta.get("captureduration")),
    }
    checks = []

    def check(name, expected, actual, ok):
        checks.append({"field": name, "expected": expected, "actual": actual,
                       "status": "ok" if ok else ("missing" if actual in (None, "", [None, None]) else "mismatch")})

    release = header["engine_release_version"] or ""
    check("engine_version", args.expect_engine, header["engine_version"] or release,
          bool(release) and release.startswith(args.expect_engine))
    check("resolution", [args.resx, args.resy], header["resolution"],
          header["resolution"] == [float(args.resx), float(args.resy)])
    for key in ("t.MaxFPS", "r.VSync"):
        value = to_float(header[key])
        check(key, 0, header[key], value is not None and value == 0)
    if args.expect_gpu:
        check("gpu", args.expect_gpu, header["gpu"], bool(header["gpu"]) and args.expect_gpu.lower() in header["gpu"].lower())
    if args.expect_rhi:
        check("rhi", args.expect_rhi, header["rhi"], (header["rhi"] or "").upper() == args.expect_rhi.upper())
    if args.expect_scalability is not None:
        levels = header["scalability_cvars"]
        check("scalability", args.expect_scalability, levels,
              all(to_float(v) == args.expect_scalability for v in levels.values()))
    elif not any(header["scalability_cvars"].values()) and not header["scalability_sections_applied"]:
        warnings.append("Scalability levels were not found in the log")
    if header["vsyncenabled_metadata"] not in (None, "0"):
        warnings.append("CSV metadata vsyncenabled is not 0 (it reflects GameUserSettings; r.VSync echo is authoritative)")
    for item in checks:
        if item["status"] != "ok":
            invalid.append(f"Header {item['field']} {item['status']}: expected {item['expected']!r}, got {item['actual']!r}")

    # ---------- required columns
    header_cols = set(profile["header"])
    for col in ("FrameTime", "PhysicalUsedMB"):
        if col not in header_cols:
            invalid.append(f"CSV column {col} is missing")
    present_metrics = [(label, col) for label, col in METRICS if col in header_cols]
    for label, col in METRICS:
        if col not in header_cols:
            warnings.append(f"CSV column {col} not present; {label} not reported")

    # ---------- shader windows
    shader_windows = []
    if log and start:
        points = [rel(p["at"], start) for p in log["shader_points"] if p["left"] > 0 and p["at"]]
        shader_windows = merge_windows([p for p in points if p is not None], args.shader_gap, args.shader_pad)
    pso_frames = set()
    for f in frames:
        if any((f["values"].get(c) or 0) > 0 for c in PSO_HITCH_COLUMNS):
            pso_frames.add(f["frame"])

    # ---------- F5 reloads
    reloads = []
    detection = "log"
    if log and start:
        for load in log["loadmaps"]:
            t0 = rel(load["start"], start)
            if t0 is None or t0 < 0 or t0 > end_t:
                continue
            t_loaded = rel(load["end"], start) if load["end"] else None
            reloads.append({"url": load["url"], "start_s": t0, "loaded_s": t_loaded,
                            "loadmap_took_s": load["took_s"], "source": "log"})
    elif frames:
        detection = "heuristic"
        warnings.append("No log markers for reloads: using the frame-time spike heuristic (labelled heuristic)")
        for f in frames:
            if f["values"]["FrameTime"] >= args.reload_spike_ms:
                if not reloads or f["t"] - reloads[-1]["start_s"] > 2.0:
                    reloads.append({"url": None, "start_s": f["t"],
                                    "loaded_s": f["t"] + f["values"]["FrameTime"] / 1000.0,
                                    "loadmap_took_s": None, "source": "heuristic"})
    for r in reloads:
        anchor = r["loaded_s"] if r["loaded_s"] is not None else r["start_s"]
        stable = None
        for i, f in enumerate(frames):
            if f["t"] < anchor:
                continue
            run = frames[i:i + args.stable_frames]
            if len(run) == args.stable_frames and all(x["values"]["FrameTime"] < args.hitch_ms for x in run):
                stable = f
                break
        before = [f for f in frames if f["t"] < r["start_s"]]
        r["stable_s"] = stable["t"] if stable else None
        r["duration_s"] = round(stable["t"] - r["start_s"], 4) if stable else None
        r["window"] = [r["start_s"], max(r["stable_s"] if stable else end_t, r["start_s"] + args.f5_grace)]
        r["actors_before"] = before[-1]["values"].get(ACTOR_COLUMN) if before else None
        r["actors_after"] = stable["values"].get(ACTOR_COLUMN) if stable else None
        if stable is None:
            invalid.append(f"F5 reload at {r['start_s']:.2f} s never reached {args.stable_frames} stable frames")
    f5_windows = [tuple(r["window"]) for r in reloads]
    if not reloads and args.require_reload:
        invalid.append("No F5 reload observed during the capture (B8 needs one; pass --no-require-reload to skip)")

    # ---------- phases, frames.csv rows
    def phase_of(f):
        if in_any(f["t"], f5_windows):
            return "f5_reload"
        if in_any(f["t"], shader_windows) or f["frame"] in pso_frames:
            return "shader_compile"
        if f["t"] < warmup:
            return "warmup"
        return "play"

    frame_rows = []
    for f in frames:
        f["phase"] = phase_of(f)
        v = f["values"]
        frame_rows.append({"frame": f["frame"], "time_s": round(f["t"], 4), "phase": f["phase"],
                           **{col: v.get(col) for _, col in METRICS},
                           **{col: v.get(col) for col in MEMORY_COLUMNS},
                           ACTOR_COLUMN: v.get(ACTOR_COLUMN),
                           "events": " | ".join(e["text"] for e in f["events"])})
    play = [f for f in frames if f["phase"] == "play"]

    metrics = {}
    for label, col in present_metrics:
        metrics[label] = {"column": col,
                          "gated_play": stats([f["values"].get(col) for f in play]),
                          "all_frames": stats([f["values"].get(col) for f in frames])}

    # ---------- hitches
    hitches = []
    for f in frames:
        ft = f["values"]["FrameTime"]
        if ft >= args.hitch_ms:
            threads = {name: f["values"].get(col) for name, col in LIMITER_COLUMNS}
            known = {k: v for k, v in threads.items() if v is not None}
            limiter = max(known, key=known.get) if known else "unknown"
            hitches.append({"frame": f["frame"], "time_s": round(f["t"], 4), "frame_ms": ft,
                            "limiter": limiter, **{f"{k}_ms": v for k, v in threads.items()},
                            "phase": f["phase"], "gated": f["phase"] == "play",
                            "events": " | ".join(e["text"] for e in f["events"])})
    gated_hitches = [h for h in hitches if h["gated"]]

    # ---------- memory every N seconds
    memory = {"interval_s": args.mem_interval, "samples": [], "growth_pct": None}
    if "PhysicalUsedMB" in header_cols and frames:
        next_t = warmup
        for f in frames:
            if f["t"] >= next_t and f["values"].get("PhysicalUsedMB") is not None:
                memory["samples"].append({"time_s": round(f["t"], 3),
                                          **{c: f["values"].get(c) for c in MEMORY_COLUMNS}})
                next_t += args.mem_interval
        last = frames[-1]
        if memory["samples"] and last["t"] > memory["samples"][-1]["time_s"] and last["values"].get("PhysicalUsedMB") is not None:
            memory["samples"].append({"time_s": round(last["t"], 3), "end_of_window": True,
                                      **{c: last["values"].get(c) for c in MEMORY_COLUMNS}})
        series = [s["PhysicalUsedMB"] for s in memory["samples"]]
        if len(series) >= 2 and series[0]:
            memory["growth_pct"] = round((series[-1] - series[0]) / series[0] * 100.0, 3)
            memory["first_mb"], memory["last_mb"], memory["peak_mb"] = series[0], series[-1], max(series)
        else:
            invalid.append("Fewer than two PhysicalUsedMB samples after warmup; memory growth unknown")

    # ---------- GC
    gc = {"source": "LogGarbage (-LogCmds=\"LogGarbage Log\")", "count": 0, "p95_ms": None, "max_ms": None}
    if log:
        pauses = [g["ms"] for g in log["gc"] if start is None or (g["at"] and 0 <= rel(g["at"], start) <= end_t)]
        purges = [g["ms"] for g in log["gc_purge"] if start is None or (g["at"] and 0 <= rel(g["at"], start) <= end_t)]
        gc.update(count=len(pauses), p95_ms=percentile(pauses, 95), max_ms=max(pauses) if pauses else None,
                  purge_count=len(purges), purge_p95_ms=percentile(purges, 95), purge_max_ms=max(purges) if purges else None)
        if not log["gc"]:
            warnings.append("No LogGarbage pause lines in the log (check that -LogCmds took effect)")
    else:
        gc["source"] = "unavailable: no log supplied"

    # ---------- checks
    p95 = (metrics.get("FrameTime") or {}).get("gated_play") or {}
    durations = [r["duration_s"] for r in reloads if r["duration_s"] is not None]
    results = {
        "p95_frame_time": {"threshold_ms": args.p95_ms, "value_ms": p95.get("p95"),
                           "pass": p95.get("p95") is not None and p95["p95"] <= args.p95_ms},
        "hitches_outside_windows": {"threshold_ms": args.hitch_ms, "count": len(gated_hitches),
                                    "pass": not gated_hitches},
        "reload_time": {"threshold_s": args.reload_s, "values_s": durations, "detection": detection if reloads else None,
                        "pass": bool(durations) and max(durations) <= args.reload_s if reloads else None},
        "memory_growth": {"threshold_pct": args.mem_growth_pct, "value_pct": memory["growth_pct"],
                          "pass": memory["growth_pct"] is not None and memory["growth_pct"] <= args.mem_growth_pct},
    }
    if p95.get("p95") is None:
        invalid.append("No gated play frames to compute p95")
    if invalid:
        verdict, code = "invalid", 2
    elif all(r["pass"] is not False for r in results.values()) and results["p95_frame_time"]["pass"]:
        verdict, code = "pass", 0
    else:
        verdict, code = "fail", 1

    load_info = {}
    if log:
        startup = [l for l in log["loadmaps"] if l["start"] and start and l["start"] < start]
        load_info = {"engine_initialization_s": log["engine_init_s"],
                     "startup_loadmap_s": startup[-1]["took_s"] if startup else None,
                     "note": "Cold versus warm is not distinguished; compare a first run after a reboot with a repeat run."}

    summary = {
        "tool": VERSION, "verdict": verdict, "exit_code": code,
        "invalid_reasons": invalid, "warnings": warnings,
        "thresholds": {"p95_ms": args.p95_ms, "hitch_ms": args.hitch_ms, "reload_s": args.reload_s,
                       "mem_growth_pct": args.mem_growth_pct, "f5_grace_s": args.f5_grace,
                       "stable_frames": args.stable_frames, "warmup_s": warmup, "duration_s": args.duration},
        "checks": results, "header": header, "header_checks": checks,
        "window": {"analysed_s": round(min(end_t, profile["duration_s"]), 3),
                   "capture_s": round(profile["duration_s"], 3), "frames": len(frames),
                   "gated_play_frames": len(play),
                   "phase_counts": {p: sum(1 for f in frames if f["phase"] == p)
                                    for p in ("warmup", "shader_compile", "f5_reload", "play")}},
        "metrics_ms": metrics, "hitches": {"total": len(hitches), "gated": len(gated_hitches),
                                           "by_phase": {p: sum(1 for h in hitches if h["phase"] == p)
                                                        for p in ("warmup", "shader_compile", "f5_reload", "play")}},
        "reloads": reloads, "reload_detection": detection if reloads else None,
        "shader_compile_windows_s": [[round(a, 3), round(b, 3)] for a, b in shader_windows],
        "pso_hitch_frames": len(pso_frames),
        "memory": memory, "gc": gc, "load_times": load_info,
        "inputs": {"csv": str(csv_path), "log": str(log_path) if log_path else None},
        "assumptions": ASSUMPTIONS,
    }
    return code, summary, frame_rows, hitches


def write_outputs(out: Path, summary, frame_rows, hitches):
    out.mkdir(parents=True, exist_ok=True)
    frame_fields = ["frame", "time_s", "phase", *[c for _, c in METRICS], *MEMORY_COLUMNS, ACTOR_COLUMN, "events"]
    with open(out / "frames.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=frame_fields)
        writer.writeheader()
        writer.writerows(frame_rows)
    hitch_fields = ["frame", "time_s", "frame_ms", "limiter", "GameThread_ms", "RenderThread_ms", "GPU_ms",
                    "RHIThread_ms", "phase", "gated", "events"]
    with open(out / "hitches.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=hitch_fields)
        writer.writeheader()
        writer.writerows(hitches)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")


# --------------------------------------------------------------------------- launch

def unreal_local_arguments(root: Path):
    # Same as tools/astra_setup.py unreal_local_arguments(): the project's local DDC and user dir.
    cache = root / ".tool-cache"
    return ["-DDC=InstalledNoZenLocalFallback", f"-LocalDataCachePath={cache / 'derived-data'}",
            f"-UserDir={cache / 'unreal-user'}"]


def build_command(args, settings, out: Path):
    engine = Path(args.engine_root or settings["engine_root"]) / "Engine/Binaries/Win64/UnrealEditor.exe"
    project = ROOT / settings["project"]
    execs = ["t.MaxFPS 0", "r.VSync 0", "t.MaxFPS", "r.VSync",
             *[f"sg.{g}" for g in SCALABILITY_GROUPS], "csvprofile start"]
    return [str(engine), str(project), args.map, "-game",
            "-fullscreen" if args.fullscreen else "-windowed",
            f"-ResX={args.resx}", f"-ResY={args.resy}", "-ForceRes", "-nosplash", "-nop4",
            "-csvGpuStats", "-dpcvars=t.MaxFPS=0,r.VSync=0",
            "-ExecCmds=" + ",".join(execs),
            "-LogCmds=LogGarbage Log, LogShaderCompilers Verbose",
            f"-abslog={out / 'engine.log'}", *unreal_local_arguments(ROOT)]


def command_text(cmd):
    return subprocess.list2cmdline(cmd)


def running_editors():
    """Return running UnrealEditor processes; raise if they cannot be listed (fail closed)."""
    found = []
    for image in ("UnrealEditor.exe", "UnrealEditor-Cmd.exe"):
        listing = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
                                 capture_output=True, text=True, timeout=30, check=True).stdout
        found += [line for line in listing.splitlines() if line.lower().startswith(f'"{image.lower()}"')]
    return found


def wait_for_log(log_path: Path, pattern: re.Pattern, timeout: float, process=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
                m = pattern.search(line)
                if m:
                    return m
        if process is not None and process.poll() is not None:
            return None
        time.sleep(0.5)
    return None


def game_window(pid):
    import ctypes
    from ctypes import wintypes as w
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, w.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
    user32.IsWindowVisible.argtypes = [w.HWND]
    found = []

    @callback_type
    def visit(hwnd, _):
        owner = w.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(visit, 0)
    return (user32, found[0]) if found else (user32, None)


def inject_console_command(pid, text):
    from ctypes import wintypes as w
    user32, hwnd = game_window(pid)
    if not hwnd:
        return False
    user32.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
    WM_KEYDOWN, WM_KEYUP, WM_CHAR, VK_OEM_3, VK_RETURN = 0x0100, 0x0101, 0x0102, 0xC0, 0x0D
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_OEM_3, 0)
    user32.PostMessageW(hwnd, WM_KEYUP, VK_OEM_3, 0xC0000001)
    time.sleep(0.5)
    for ch in text:
        user32.PostMessageW(hwnd, WM_CHAR, ord(ch), 0)
        time.sleep(0.02)
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RETURN, 0)
    user32.PostMessageW(hwnd, WM_KEYUP, VK_RETURN, 0xC0000001)
    return True


def close_game(process):
    try:
        from ctypes import wintypes as w
        user32, hwnd = game_window(process.pid)
        if hwnd:
            user32.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE, as tools/capture_qa_native_motion.py does
    except OSError:
        pass
    try:
        process.wait(timeout=60)
        return "closed"
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=30)
        return "terminated after 60 s"


def launch(args) -> int:
    settings = load_settings(ROOT)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) if args.out else ROOT / "evidence/perf" / stamp
    cmd = build_command(args, settings, out)
    text = command_text(cmd)
    if args.dry_run:
        print(text)
        if not Path(cmd[0]).is_file():
            print(f"note: engine executable not found at {cmd[0]}", file=sys.stderr)
        if not Path(cmd[1]).is_file():
            print(f"note: project not found at {cmd[1]}", file=sys.stderr)
        return 0
    try:
        editors = running_editors()
    except (OSError, subprocess.SubprocessError) as error:
        print(f"Refusing to start: could not list Unreal processes ({error}).", file=sys.stderr)
        return 2
    if editors:
        print("Refusing to start: an Unreal editor/game is already running (one editor session rule):\n  "
              + "\n  ".join(editors), file=sys.stderr)
        return 2
    for path in (cmd[0], cmd[1]):
        if not Path(path).is_file():
            print(f"Refusing to start: {path} not found.", file=sys.stderr)
            return 2
    out.mkdir(parents=True, exist_ok=False)
    duration = args.duration if args.duration is not None else DEFAULT_DURATION_S
    args.duration = duration
    started = utc_now()
    receipt = {"tool": VERSION, "command": cmd, "command_text": text, "git": git_info(ROOT),
               "started_utc": started.isoformat(), "duration_s": duration, "warmup_s": args.warmup}
    print(text, flush=True)
    cache = ROOT / ".tool-cache"
    env = dict(os.environ)
    if (cache / "temp").is_dir():
        env.update(TMP=str(cache / "temp"), TEMP=str(cache / "temp"))
    log_path = out / "engine.log"
    with open(out / "process.log", "w", encoding="utf-8") as plog:
        process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=plog, stderr=subprocess.STDOUT)
        receipt["pid"] = process.pid
        stop_note = None
        try:
            if not wait_for_log(log_path, RE_CSV_START, args.startup_timeout, process):
                receipt["error"] = "CSV capture did not start (no 'Capture started' line)"
                return finish_invalid(out, receipt, process)
            print(f"Capture running. Warmup {args.warmup:.0f} s + {duration:.0f} s. Play normally and press F5 at least once.", flush=True)
            deadline = time.monotonic() + args.warmup + duration + 1.0
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    receipt["error"] = "Game exited before the capture duration elapsed"
                    return finish_invalid(out, receipt, process)
                time.sleep(1.0)
            ended = None
            if args.stop == "inject":
                if inject_console_command(process.pid, "csvprofile stop"):
                    ended = wait_for_log(log_path, RE_CSV_END, 30, process)
                    stop_note = "inject" if ended else "inject did not end the capture"
            if not ended:
                print("\n>>> Open the console with ~ and type:  csvprofile stop   (then Enter) <<<\n", flush=True)
                ended = wait_for_log(log_path, RE_CSV_END, args.manual_timeout, process)
                stop_note = (stop_note + "; manual" if stop_note else "manual") if ended else stop_note
            receipt["stop"] = stop_note
            receipt["close"] = close_game(process)
        finally:
            if process.poll() is None:
                receipt["close"] = close_game(process)
    receipt["ended_utc"] = utc_now().isoformat()
    receipt["game_exit_code"] = process.returncode
    log = parse_log(log_path) if log_path.exists() else None
    csv_source = Path(log["capture_end_csv"]) if log and log["capture_end_csv"] else None
    if not csv_source or not csv_source.is_file():
        receipt["error"] = f"CSV file not found (log reported {csv_source})"
        return finish_invalid(out, receipt, None)
    shutil.copyfile(csv_source, out / "profile.csv")
    receipt["csv_source"] = str(csv_source)
    code, summary, rows, hitches = analyze(out / "profile.csv", log_path, args)
    summary["run"] = receipt
    write_outputs(out, summary, rows, hitches)
    print_summary(out, summary)
    return code


def finish_invalid(out: Path, receipt, process):
    if process is not None and process.poll() is None:
        receipt["close"] = close_game(process)
    receipt["ended_utc"] = utc_now().isoformat()
    summary = {"tool": VERSION, "verdict": "invalid", "exit_code": 2,
               "invalid_reasons": [receipt.get("error", "unknown")], "run": receipt, "assumptions": ASSUMPTIONS}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"INVALID: {receipt.get('error')} (see {out})", file=sys.stderr)
    return 2


def print_summary(out: Path, summary):
    checks = summary["checks"]
    print(f"\n{VERSION}: {summary['verdict'].upper()} (exit {summary['exit_code']}) -> {out}")
    for name, item in checks.items():
        print(f"  {name}: {item}")
    for reason in summary["invalid_reasons"]:
        print(f"  INVALID: {reason}")
    for note in summary["warnings"]:
        print(f"  warning: {note}")


# --------------------------------------------------------------------------- CLI

def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--dry-run", action="store_true", help="print the exact launch command and exit 0")
    p.add_argument("--analyze", metavar="CSV", help="analyse an existing CSV instead of launching")
    p.add_argument("--log", metavar="LOG", help="engine log for --analyze (header read-back, reloads, GC, shaders)")
    p.add_argument("--out", help="output folder (default evidence/perf/<UTC timestamp>)")
    p.add_argument("--map", default=DEFAULT_MAP, help=f"map to open (default {DEFAULT_MAP}); F5 always reopens TeddyEncounter")
    p.add_argument("--engine-root", help="override engine_root from tools/project-settings*.json")
    p.add_argument("--fullscreen", action="store_true", help="-fullscreen instead of -windowed")
    p.add_argument("--resx", type=int, default=1920)
    p.add_argument("--resy", type=int, default=1080)
    p.add_argument("--duration", type=float, default=None,
                   help=f"seconds analysed after warmup (launch default {DEFAULT_DURATION_S:.0f}; --analyze default: whole CSV)")
    p.add_argument("--warmup", type=float, default=5.0, help="seconds at capture start reported but not gated (default 5)")
    p.add_argument("--stop", choices=("inject", "manual"), default="inject", help="how the CSV capture is stopped")
    p.add_argument("--startup-timeout", type=float, default=300.0)
    p.add_argument("--manual-timeout", type=float, default=300.0)
    p.add_argument("--p95-ms", type=float, default=8.3)
    p.add_argument("--hitch-ms", type=float, default=33.3)
    p.add_argument("--reload-s", type=float, default=3.0)
    p.add_argument("--mem-growth-pct", type=float, default=10.0)
    p.add_argument("--mem-interval", type=float, default=10.0, help="memory sample spacing in seconds (default 10)")
    p.add_argument("--f5-grace", type=float, default=1.5, help="minimum excluded seconds after each F5 reload start (default 1.5)")
    p.add_argument("--stable-frames", type=int, default=5, help="consecutive frames under --hitch-ms that end a reload")
    p.add_argument("--reload-spike-ms", type=float, default=200.0, help="heuristic reload detection threshold without a log")
    p.add_argument("--shader-gap", type=float, default=2.0)
    p.add_argument("--shader-pad", type=float, default=0.5)
    p.add_argument("--no-require-reload", dest="require_reload", action="store_false")
    p.add_argument("--expect-engine", default="5.8.3")
    p.add_argument("--expect-gpu", default="RTX 5080", help="substring the GPU name must contain ('' to skip)")
    p.add_argument("--expect-rhi", default=None, help="e.g. D3D12 (default: report only)")
    p.add_argument("--expect-scalability", type=int, default=None, help="require every sg.* level to equal this")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.analyze:
        csv_path = Path(args.analyze).resolve()
        log_path = Path(args.log).resolve() if args.log else None
        stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
        out = Path(args.out) if args.out else ROOT / "evidence/perf" / f"{stamp}-analyze"
        out.mkdir(parents=True, exist_ok=True)
        if not csv_path.is_file():
            print(f"CSV not found: {csv_path}", file=sys.stderr)
            return 2
        if csv_path != (out / "profile.csv").resolve():
            shutil.copyfile(csv_path, out / "profile.csv")
        if log_path and log_path.is_file() and log_path != (out / "engine.log").resolve():
            shutil.copyfile(log_path, out / "engine.log")
        code, summary, rows, hitches = analyze(csv_path, log_path, args)
        summary["run"] = {"mode": "analyze", "analysed_utc": utc_now().isoformat(), "git": git_info(ROOT)}
        write_outputs(out, summary, rows, hitches)
        print_summary(out, summary)
        return code
    return launch(args)


if __name__ == "__main__":
    sys.exit(main())
