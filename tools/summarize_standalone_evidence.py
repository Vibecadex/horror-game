"""Archive the native game's CSV profile and measure its actual audio samples."""
from pathlib import Path
from array import array
import csv, hashlib, json, math, shutil, statistics, subprocess, sys

out = Path(sys.argv[1]).resolve()
source = Path(sys.argv[2]).resolve()
profile = out / 'runtime-profile.csv'
if profile.exists():
    assert profile.read_bytes() == source.read_bytes()
else:
    shutil.copyfile(source, profile)
rows = list(csv.reader(profile.open(newline='')))
# Unreal appends columns as new stats appear, then emits the complete header.
header = rows[-2]
assert header[0] == 'EVENTS' and header[:len(rows[0])] == rows[0]
records = []
for row in rows[1:-2]:
    try:
        if len(row) > header.index('GPUTime') and float(row[header.index('FrameTime')]) > 0:
            records.append(dict(zip(header, row)))
    except ValueError:
        pass

def percentile(values, p):
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low, high = math.floor(index), math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)

metrics = {}
for name in ['FrameTime', 'GameThreadTime', 'RenderThreadTime', 'GPUTime']:
    values = [float(row[name]) for row in records if float(row[name]) > 0]
    metrics[name] = {'samples': len(values), 'median_ms': statistics.median(values),
                     'p95_ms': percentile(values, .95), 'max_ms': max(values)}
raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-xerror', '-i',
    str(out / 'standalone-audio.wav'), '-f', 'f32le', '-acodec', 'pcm_f32le', '-'])
samples = array('f'); samples.frombytes(raw)
peak = max(abs(x) for x in samples)
rms = math.sqrt(sum(x*x for x in samples) / len(samples))
result = {
    'passed': bool(records) and peak > 0,
    'map': json.loads((out / 'authoring.json').read_text())['map'],
    'source_map': '/Game/Maps/TeddyEncounter',
    'resolution': [1280, 720], 'process': 'UnrealEditor.exe -game -RenderOffscreen',
    'capture_window': 'Saved Blueprint starts CSV after 3 game seconds and stops after another 5; capture finishes before screenshot.',
    'conditions': 'Development runtime, warm local shader cache, no input injected; ordinary boss pursuit/attack. Not a packaged-build or long-session benchmark.',
    'metrics': metrics, 'csv': str(profile),
    'csv_sha256': hashlib.sha256(profile.read_bytes()).hexdigest(),
    'metadata': dict(zip(rows[-1][::2], rows[-1][1::2])),
    'audio': {'sample_count_all_channels': len(samples), 'peak_dbfs': 20*math.log10(peak),
              'rms_dbfs': 20*math.log10(rms), 'nonzero': peak > 0,
              'scope': 'Native game master output; proposed original ambience and boss impacts. Source reference audio not auditioned.'}
}
(out / 'performance-audio.json').write_text(json.dumps(result, indent=2))
print(json.dumps({k:v for k,v in result.items() if k != 'metadata'}, indent=2))
