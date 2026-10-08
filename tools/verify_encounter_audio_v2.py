"""v2 of the encounter audio probe. Same capture as v1, plus a WAV analysis
that fails on digital silence, and a restored editor sound setting.

Run only through tools/run_encounter_test.py. No asset or map saves.

Why v1's probe.wav was silent (measured 2026-10-08, M1 B7):
  The runner adds -NoSound unless TEDDY_TEST_AUDIO=1. With that set, the
  editor still recorded an 8-channel 48 kHz PCM file whose every sample was
  zero, while the RoomTone component reported playing and Rifle was triggered
  into the same window. The script only checked that probe.wav existed.
  -NoSound is handled here by failing with an explicit reason instead of
  recording silence. The remaining cause (the offscreen editor's audio device
  or submix capture writing zeros) is recorded, not guessed at.

Requires TEDDY_TEST_AUDIO=1; without it the script fails before PIE.

Checks (4):
  probe_wav_exists
  probe_not_digitally_silent     peak >= -60 dBFS and not all samples zero
  probe_has_signal_after_trigger peak in the window after the Rifle trigger
  game_sound_setting_restored     EnableGameSound back to its pre-run value
"""
import os, sys, time, json, struct, math, traceback
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from finish_editor import finish_editor

OUT = Path(os.environ['TEDDY_TEST_DIR'])
lev = u.get_editor_subsystem(u.LevelEditorSubsystem)
ed = u.get_editor_subsystem(u.UnrealEditorSubsystem)
s = {'stage': 0, 'wall': time.monotonic(), 'finished': False}
r = {'passed': False, 'checks': {}, 'asset_writes': False, 'suite': 'verify_encounter_audio_v2',
     'method': 'v1 probe plus per-channel WAV peak/RMS, silence failure, and restored EnableGameSound.'}
handle = None
SILENCE_DBFS = -60.

def analyse_wav(path, window=None):
    data = path.read_bytes()
    assert data[:4] == b'RIFF' and data[8:12] == b'WAVE', 'not a WAV'
    pos = 12
    fmt = None
    samples = None
    while pos + 8 <= len(data):
        chunk, size = data[pos:pos + 4], struct.unpack_from('<I', data, pos + 4)[0]
        body = data[pos + 8:pos + 8 + size]
        if chunk == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', body)
        elif chunk == b'data':
            samples = body
        pos += 8 + size + (size & 1)
    tag, channels, rate, _, _, bits = fmt
    assert tag == 1 and bits == 16, 'expected 16-bit PCM, got tag %s bits %s' % (tag, bits)
    count = len(samples) // 2
    values = struct.unpack('<%dh' % count, samples)
    frames = count // channels
    per_channel = []
    for c in range(channels):
        column = values[c::channels]
        peak = max(abs(v) for v in column) / 32768.
        rms = math.sqrt(sum(v * v for v in column) / len(column)) / 32768.
        per_channel.append({'channel': c,
                            'peak_dbfs': round(20 * math.log10(peak + 1e-12), 2),
                            'rms_dbfs': round(20 * math.log10(rms + 1e-12), 2)})
    window_peak = None
    if window:
        a, b = int(window[0] * rate) * channels, int(window[1] * rate) * channels
        part = values[a:b]
        window_peak = round(20 * math.log10((max(abs(v) for v in part) / 32768. if part else 0) + 1e-12), 2)
    return {'format': 'PCM', 'channels': channels, 'sample_rate': rate, 'bits': bits,
            'duration_s': round(frames / rate, 3), 'all_samples_zero': all(v == 0 for v in values),
            'trigger_window_s': window, 'trigger_window_peak_dbfs': window_peak,
            'channels_detail': per_channel,
            'peak_dbfs': max(c['peak_dbfs'] for c in per_channel),
            'rms_dbfs': max(c['rms_dbfs'] for c in per_channel)}

def restore():
    if 'original_game_sound' in s and not s.get('restored'):
        settings = u.get_default_object(u.load_class(None, '/Script/UnrealEd.LevelEditorPlaySettings'))
        settings.set_editor_property('EnableGameSound', s['original_game_sound'])
        r['game_sound_after'] = settings.get_editor_property('EnableGameSound')
        r['checks']['game_sound_setting_restored'] = r['game_sound_after'] == s['original_game_sound']
        s['restored'] = True

def finish(error=None):
    if s['finished']:
        return
    s['finished'] = True
    try:
        restore()
    except Exception:
        r['restore_error'] = traceback.format_exc()
    if error:
        r['error'] = error
    r['expected_check_count'] = 4
    r['passed'] = not error and len(r['checks']) == 4 and all(r['checks'].values())
    r['wall_seconds'] = time.monotonic() - s['wall']
    (OUT / 'receipt.json').write_text(json.dumps(r, indent=2, default=str))
    finish_editor(handle)

def tick(dt):
    try:
        w = ed.get_game_world()
        if not w:
            return
        game = u.GameplayStatics.get_time_seconds(w)
        if s['stage'] == 0 and game > 1:
            r['components'] = [{'name': x.get_path_name(), 'sound': str(x.sound),
                                'volume': x.volume_multiplier, 'playing': x.is_playing(), 'active': x.is_active()}
                               for x in u.ObjectIterator(u.AudioComponent) if x.get_world() == w]
            r['sounds'] = []
            for name in ['Rifle', 'Slam', 'RoomTone']:
                obj = u.load_asset('/Game/TeddyEncounter/Audio/' + name)
                r['sounds'].append({'name': name, 'duration': obj.duration})
            settings = u.get_default_object(u.load_class(None, '/Script/UnrealEd.LevelEditorPlaySettings'))
            r['game_sound_enabled'] = settings.get_editor_property('EnableGameSound')
            u.AudioMixerLibrary.start_recording_output(w, 10)
            s['stage'] = 1
            s['t'] = game
        elif s['stage'] == 1 and game - s['t'] > .25:
            u.GameplayStatics.play_sound2d(w, u.load_asset('/Game/TeddyEncounter/Audio/Rifle'), 1., 1.)
            s['trigger_at_s'] = game - s['t']
            s['stage'] = 2
        elif s['stage'] == 2 and game - s['t'] > 3:
            u.AudioMixerLibrary.stop_recording_output(w, u.AudioRecordingExportType.WAV_FILE, 'probe', str(OUT))
            s['stage'] = 3
        elif s['stage'] == 3 and (OUT / 'probe.wav').exists():
            r['checks']['probe_wav_exists'] = True
            # TODO(Tech): confirm recording t=0 aligns with start_recording_output; the
            # window is widened to 0.6 s to absorb device latency.
            start = s.get('trigger_at_s', .25)
            analysis = analyse_wav(OUT / 'probe.wav', (start, start + .6))
            r['probe'] = analysis
            r['checks']['probe_not_digitally_silent'] = (not analysis['all_samples_zero']
                                                         and analysis['peak_dbfs'] >= SILENCE_DBFS)
            r['checks']['probe_has_signal_after_trigger'] = (analysis['trigger_window_peak_dbfs'] is not None
                                                             and analysis['trigger_window_peak_dbfs'] >= SILENCE_DBFS)
            if not r['checks']['probe_not_digitally_silent']:
                r['silence_cause'] = ('probe.wav decoded but is silent without -NoSound. The offscreen editor '
                                      'likely has no active audio device, or AudioMixerLibrary recording captured '
                                      'a submix that PIE never feeds. Not asserted beyond the measurement.')
            finish()
        if time.monotonic() - s['wall'] > 50:
            finish('timeout')
    except Exception:
        finish(traceback.format_exc())

try:
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    # run_encounter_test.py passes os.environ through tool_environment(), and adds
    # -NoSound unless TEDDY_TEST_AUDIO=1. With -NoSound the capture can only be silence.
    r['teddy_test_audio'] = os.environ.get('TEDDY_TEST_AUDIO')
    if r['teddy_test_audio'] != '1':
        r['silence_cause'] = ('TEDDY_TEST_AUDIO is not 1, so run_encounter_test.py launched the editor with '
                              '-NoSound and any recording is silence. Re-run with TEDDY_TEST_AUDIO=1.')
        raise RuntimeError(r['silence_cause'])
    assert lev.load_level('/Game/Maps/TeddyEncounter')
    settings = u.get_default_object(u.load_class(None, '/Script/UnrealEd.LevelEditorPlaySettings'))
    s['original_game_sound'] = settings.get_editor_property('EnableGameSound')
    r['game_sound_before'] = s['original_game_sound']
    settings.set_editor_property('EnableGameSound', True)
    lev.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
