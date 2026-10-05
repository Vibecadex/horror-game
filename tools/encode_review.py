"""Encode actual Unreal viewport captures using their recorded game timestamps."""
import argparse
import csv
import json
from pathlib import Path
import statistics
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("capture_directory", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--ffmpeg", default=r"C:\Users\4elut\scoop\shims\ffmpeg.exe")
args = parser.parse_args()
root = args.capture_directory.resolve()
with (root / "sequence.csv").open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
if len(rows) < 2:
    raise SystemExit("Not enough captured frames")
files, times = [], []
for row in rows:
    path = (root / row["filename"]).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size == 0:
        raise SystemExit("Missing or invalid captured frame")
    files.append(path)
    times.append(float(row["request_game_seconds"]))
intervals = [b - a for a, b in zip(times, times[1:])]
if min(intervals) <= 0:
    raise SystemExit("Capture timestamps are not strictly increasing")
durations = intervals + [statistics.median(intervals)]
script = ["ffconcat version 1.0"]
for path, duration in zip(files, durations):
    safe_path = path.as_posix().replace("'", "'\\''")
    script.extend(["file '" + safe_path + "'", "duration " + format(duration, ".6f")])
script.append("file '" + files[-1].as_posix().replace("'", "'\\''") + "'")
concat = root / "review.ffconcat"
concat.write_text("\n".join(script) + "\n", encoding="utf-8")
args.output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([args.ffmpeg, "-hide_banner", "-loglevel", "error", "-n", "-f", "concat", "-safe", "0",
                "-i", str(concat), "-fps_mode", "vfr", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(args.output)], check=True)
record = {"capture_directory": str(root), "output": str(args.output.resolve()), "frames": len(files),
          "recorded_game_duration_seconds": sum(durations), "minimum_interval": min(intervals),
          "maximum_interval": max(intervals), "audio": False,
          "timing": "Actual capture request game timestamps; variable frame duration; no interpolation"}
args.output.with_suffix(".json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps(record, indent=2))
