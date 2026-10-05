import unreal as u,json
from pathlib import Path
r={n:getattr(u.AudioMixerLibrary,n).__doc__ for n in ['start_recording_output','stop_recording_output']};r['enum']=[n for n in dir(u.AudioRecordingExportType) if n.isupper()]
(Path(__file__).resolve().parents[1]/'evidence/implementation/audio-api.json').write_text(json.dumps(r,indent=2))
