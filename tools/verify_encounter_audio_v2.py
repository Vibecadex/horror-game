"""v2 of the encounter audio probe. Same capture as v1, plus a WAV analysis
that fails on digital silence, the editor's background-audio switch turned on
for the run, and both editor sound settings restored.

Run only through tools/run_encounter_test.py. No asset or map saves.

Why v1's probe.wav was silent (measured 2026-10-08, M1 B7; diagnosis from
Horror Unreal Tech's review of 2026-10-08, A1-A4):
  The runner adds -NoSound unless TEDDY_TEST_AUDIO=1. With that set, the
  editor still recorded an 8-channel 48 kHz PCM file whose every sample was
  zero, while the RoomTone component reported playing and Rifle was triggered
  into the same window.
  There IS an audio device: the M1 engine.log shows WASAPI device 2
  (SteelSeries Sonar - Gaming, 48 kHz, 8 ch) created for the PIE world. Every
  editor PIE recording since 4 Oct peaks at 0, while the two -game runs on the
  same device and the same UnfocusedVolumeMultiplier=1.0 override peak at
  5402 / 5620 (about -15.5 dBFS). Likely cause: UEditorEngine::Tick keeps the
  volume only when the editor is foreground or
  LevelEditorMiscSettings.bAllowBackgroundAudio is set, and an offscreen
  -unattended editor is never foreground (UnfocusedVolumeMultiplier is the
  game path, which is why it fixes -game but not PIE).
  This script sets bAllowBackgroundAudio=True in memory on the CDO before PIE
  and restores it afterwards, the same way as EnableGameSound. Nothing is saved.

If the capture is still silent with background audio on, the fallback is the
proven -game capture (StartRecordingOutput -> StopRecordingOutput(WavFile), the
run_standalone_evidence.py shape minus its asset authoring, which needs a lock
and Tech), or a watched PLAY.cmd with B7's listener pass. Not a WASAPI loopback.

Requires TEDDY_TEST_AUDIO=1; without it the script fails before PIE.

Checks (4):
  probe_wav_exists
  probe_not_digitally_silent     peak >= -60 dBFS and not all samples zero
  probe_has_signal_after_trigger peak in the window after the Rifle trigger
  game_sound_setting_restored     EnableGameSound AND bAllowBackgroundAudio back to
                                  their pre-run values (the background-audio restore is
                                  folded in to keep 4 checks; both are logged separately)

Expected: 4/4 if the unfocused-mute diagnosis is right; 2/4 (only the two
signal checks false) if PIE is still silent, which points to the -game fallback.
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
     'method': 'v1 probe plus per-channel WAV peak/RMS, silence failure, editor background audio '
               'allowed for the run, and restored EnableGameSound and bAllowBackgroundAudio.'}
handle = None
SILENCE_DBFS = -60.
MISC_SETTINGS = '/Script/UnrealEd.LevelEditorMiscSettings'
# Python may reject the C++ name; fall back to the snake_case name.
BG_AUDIO_NAMES = ('bAllowBackgroundAudio', 'allow_background_audio')

def bg_audio_get(misc):
    errors = []
    for n in BG_AUDIO_NAMES:
        try:
            return n, misc.get_editor_property(n)
        except Exception as e:
            errors.append('%s: %s' % (n, e))
    raise RuntimeError('bAllowBackgroundAudio not readable: ' + '; '.join(errors))

def peak_at(values, channels, rate, offset=0):
    if not values:
        return None
    i = max(range(len(values)), key=lambda k: abs(values[k]))
    frame = (offset + i) // channels
    return {'sample_index': offset + i, 'frame': frame, 'time_s': round(frame / rate, 4),
            'channel': (offset + i) % channels, 'value': values[i]}

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
    if fmt is None or samples is None:
        raise ValueError('WAV has no fmt or data chunk')
    tag, channels, rate, _, _, bits = fmt
    if not (tag == 1 and bits == 16):
        # A4: e.g. a float capture. Raised to the caller, which records it and fails the signal checks.
        raise ValueError('expected 16-bit PCM, got tag %s bits %s' % (tag, bits))
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
    window_peak = window_peak_at = None
    if window:
        a, b = int(window[0] * rate) * channels, int(window[1] * rate) * channels
        part = values[a:b]
        window_peak = round(20 * math.log10((max(abs(v) for v in part) / 32768. if part else 0) + 1e-12), 2)
        window_peak_at = peak_at(part, channels, rate, a)
    return {'format': 'PCM', 'channels': channels, 'sample_rate': rate, 'bits': bits,
            'duration_s': round(frames / rate, 3), 'all_samples_zero': all(v == 0 for v in values),
            'trigger_window_s': window, 'trigger_window_peak_dbfs': window_peak,
            'trigger_window_peak_at': window_peak_at, 'peak_at': peak_at(values, channels, rate),
            'channels_detail': per_channel,
            'peak_dbfs': max(c['peak_dbfs'] for c in per_channel),
            'rms_dbfs': max(c['rms_dbfs'] for c in per_channel)}

def restore():
    if 'original_game_sound' in s and not s.get('restored'):
        s['restored'] = True
        bg_ok = True
        if 'original_bg_audio' in s:
            try:
                misc = u.get_default_object(u.load_class(None, MISC_SETTINGS))
                misc.set_editor_property(s['bg_audio_name'], s['original_bg_audio'])
                r['bg_audio_after'] = misc.get_editor_property(s['bg_audio_name'])
                bg_ok = r['bg_audio_after'] == s['original_bg_audio']
            except Exception:
                r['bg_audio_restore_error'] = traceback.format_exc()
                bg_ok = False
        settings = u.get_default_object(u.load_class(None, '/Script/UnrealEd.LevelEditorPlaySettings'))
        settings.set_editor_property('EnableGameSound', s['original_game_sound'])
        r['game_sound_after'] = settings.get_editor_property('EnableGameSound')
        r['restore_detail'] = {'game_sound_restored': r['game_sound_after'] == s['original_game_sound'],
                               'bg_audio_restored': bg_ok,
                               'bg_audio_changed': 'original_bg_audio' in s}
        r['checks']['game_sound_setting_restored'] = r['restore_detail']['game_sound_restored'] and bg_ok

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
            try:
                r['bg_audio_during_pie'] = bg_audio_get(u.get_default_object(u.load_class(None, MISC_SETTINGS)))[1]
            except Exception as e:
                r['bg_audio_during_pie'] = 'unreadable: %s' % e
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
            # Unverified (Tech A4): recording t=0 = start_recording_output. The 0.6 s window
            # around a 0.19 s Rifle at 0.25 s is generous; peak offsets are logged to check it.
            start = s.get('trigger_at_s', .25)
            try:
                analysis = analyse_wav(OUT / 'probe.wav', (start, start + .6))
            except Exception:
                r['probe_error'] = traceback.format_exc()
                r['checks']['probe_not_digitally_silent'] = False
                r['checks']['probe_has_signal_after_trigger'] = False
                finish()
                return
            r['probe'] = analysis
            r['checks']['probe_not_digitally_silent'] = (not analysis['all_samples_zero']
                                                         and analysis['peak_dbfs'] >= SILENCE_DBFS)
            r['checks']['probe_has_signal_after_trigger'] = (analysis['trigger_window_peak_dbfs'] is not None
                                                             and analysis['trigger_window_peak_dbfs'] >= SILENCE_DBFS)
            if not r['checks']['probe_not_digitally_silent']:
                r['silence_cause'] = ('probe.wav decoded but is silent without -NoSound. The audio device exists '
                                      '(M1 log: WASAPI device 2 for the PIE world). Likely cause: editor PIE is muted '
                                      'while unfocused. bAllowBackgroundAudio during PIE was %r; if it was True and '
                                      'this is still silent, use the -game StartRecordingOutput capture instead.'
                                      % (r.get('bg_audio_during_pie'),))
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
    # A2: let the unfocused offscreen editor keep its volume. In memory on the CDO, not saved;
    # restored in finish(). If it cannot be set the run continues and records why.
    try:
        misc = u.get_default_object(u.load_class(None, MISC_SETTINGS))
        s['bg_audio_name'], s['original_bg_audio'] = bg_audio_get(misc)
        r['bg_audio_before'] = s['original_bg_audio']
        r['bg_audio_property_name'] = s['bg_audio_name']
        misc.set_editor_property(s['bg_audio_name'], True)
        r['bg_audio_set'] = misc.get_editor_property(s['bg_audio_name'])
    except Exception:
        r['bg_audio_error'] = traceback.format_exc()
    lev.editor_request_begin_play()
    handle = u.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
