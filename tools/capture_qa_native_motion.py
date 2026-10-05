"""Capture only the owned native game client rectangle at 30 fps, without OS input."""
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from PIL import Image, ImageStat
import astra_setup as setup

setup.require_editor_closed()
ROOT = setup.ROOT
capture_root = Path(os.environ.get('TEDDY_NATIVE_CAPTURE_ROOT', str(ROOT / 'evidence/qa-repair/20261005T042900Z'))).resolve()
assert capture_root.is_relative_to(ROOT/'evidence'), 'Capture output must stay under project evidence'
capture_root.mkdir(parents=True, exist_ok=True)
OUT = capture_root / ('native-motion-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
OUT.mkdir()
print(str(OUT), flush=True)
env = dict(setup.tool_environment(), TEDDY_NATIVE_MOTION_DIR=str(OUT))
subprocess.run([sys.executable, str(ROOT/'tools/astra_setup.py'), 'editor-script', 'tools/author_qa_native_motion.py'], cwd=ROOT, env=env, check=True)
author = json.loads((OUT/'authoring.json').read_text())
assert author['passed']
u = ctypes.WinDLL('user32', use_last_error=True)
u.SetProcessDPIAware()
u.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
u.GetClientRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
u.ClientToScreen.argtypes = [w.HWND, ctypes.POINTER(w.POINT)]
u.SetWindowPos.argtypes = [w.HWND, w.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
u.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
u.IsWindowVisible.argtypes = [w.HWND]
callback_type = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
u.EnumWindows.argtypes = [callback_type, w.LPARAM]
engine = Path(setup.SETTINGS['engine_root'])/'Engine/Binaries/Win64/UnrealEditor.exe'
args = [str(engine), str(ROOT/setup.SETTINGS['project']), author['map'], '-game', '-windowed', '-ResX=1280', '-ResY=720', '-ForceRes', '-WinX=60', '-WinY=60', '-nosplash', '-nop4', '-ExecCmds=t.MaxFPS 60', '-ini:Engine:[Audio]:UnfocusedVolumeMultiplier=1.0', f'-abslog={OUT/"engine.log"}', *setup.unreal_local_arguments()]
result = {'passed': False, 'authoring': author, 'arguments': args, 'method': '30 fps desktop capture restricted to owned game client rectangle held topmost; no SendInput, no physical-device claim. Input driver is in a separate QA map.'}
hwnd = None
game = None
movie = None
started = time.monotonic()
try:
    with (OUT/'process.log').open('w') as log:
        game = subprocess.Popen(args, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=setup.HIDDEN)
        result['process_id'] = game.pid
        @callback_type
        def visit(window, parameter):
            global hwnd
            pid = w.DWORD()
            u.GetWindowThreadProcessId(window, ctypes.byref(pid))
            if pid.value == game.pid and u.IsWindowVisible(window):
                rect = w.RECT(); u.GetClientRect(window, ctypes.byref(rect))
                if rect.right == 1280 and rect.bottom == 720:
                    hwnd = window
                    return False
            return True
        while not hwnd or not (OUT/'engine.log').exists() or 'LogLoad: (Engine Initialization) Total time:' not in (OUT/'engine.log').read_text(errors='replace'):
            assert game.poll() is None, 'Owned game exited during startup'
            assert time.monotonic()-started < 60, 'Native window startup timeout'
            u.EnumWindows(visit, 0)
            time.sleep(.1)
        # Keep the bounded capture rectangle filled by this owned window without
        # taking keyboard focus or sending any global input.
        assert u.SetWindowPos(hwnd, w.HWND(-1), 0, 0, 0, 0, 0x0001|0x0002|0x0010|0x0040)
        origin = w.POINT(); rect = w.RECT()
        assert u.GetClientRect(hwnd, ctypes.byref(rect)) and u.ClientToScreen(hwnd, ctypes.byref(origin))
        result['capture_rectangle'] = [origin.x, origin.y, rect.right, rect.bottom]
        capture_args = [setup.tool('ffmpeg.exe'), '-v', 'warning', '-xerror', '-f', 'gdigrab', '-draw_mouse', '0', '-framerate', '30', '-video_size', '1280x720', '-offset_x', str(origin.x), '-offset_y', str(origin.y), '-i', 'desktop', '-t', '25', '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT/'native-motion.mp4')]
        result['capture_arguments'] = capture_args
        result['capture_started_utc'] = datetime.now(timezone.utc).isoformat()
        with (OUT/'capture.log').open('w') as capture_log:
            movie = subprocess.Popen(capture_args, stdin=subprocess.PIPE, stdout=capture_log, stderr=subprocess.STDOUT, creationflags=setup.HIDDEN)
            while game.poll() is None and movie.poll() is None:
                pid = w.DWORD(); u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                assert pid.value == game.pid and u.IsWindowVisible(hwnd), 'Capture window ownership changed'
                text = (OUT/'engine.log').read_text(errors='replace')
                if 'QA_NATIVE_MOTION_FINISHED' in text:
                    break
                assert time.monotonic()-started < 70, 'Native capture timeout'
                time.sleep(.1)
            if movie.poll() is None:
                movie.communicate(b'q', timeout=12)
            result['capture_exit_code'] = movie.returncode
        assert movie.returncode == 0, 'FFmpeg capture failed'
        result['finished_marker_seen'] = 'QA_NATIVE_MOTION_FINISHED' in (OUT/'engine.log').read_text(errors='replace')
        assert result['finished_marker_seen']
        game.wait(timeout=15)
        result['game_exit_code'] = game.returncode
        assert game.returncode == 0
    video = OUT/'native-motion.mp4'
    subprocess.run([setup.tool('ffmpeg.exe'), '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'], check=True, creationflags=setup.HIDDEN)
    result['metadata'] = json.loads(subprocess.check_output([setup.tool('ffprobe.exe'), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)], creationflags=setup.HIDDEN))
    result['video_sha256'] = hashlib.sha256(video.read_bytes()).hexdigest()
    result['all_frames_decoded'] = True
    subprocess.run([setup.tool('ffmpeg.exe'), '-v', 'error', '-xerror', '-ss', '4', '-i', str(video), '-frames:v', '1', '-update', '1', str(OUT/'motion-still.png')], check=True, creationflags=setup.HIDDEN)
    with Image.open(OUT/'motion-still.png') as img:
        img.load()
        result['still_mean_rgb'] = ImageStat.Stat(img.convert('RGB')).mean
        assert max(result['still_mean_rgb']) > 2, 'Captured video is black'
    result['passed'] = True
except Exception:
    result['error'] = traceback.format_exc()
finally:
    if movie and movie.poll() is None:
        try: movie.communicate(b'q', timeout=10)
        except Exception: movie.terminate(); movie.wait(timeout=10)
    if game and game.poll() is None:
        if hwnd: u.PostMessageW(hwnd, 0x0010, 0, 0)
        try: game.wait(timeout=10)
        except subprocess.TimeoutExpired: game.terminate(); game.wait(timeout=10)
    result['wall_seconds'] = time.monotonic()-started
    (OUT/'receipt.json').write_text(json.dumps(result, indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['arguments','capture_arguments','metadata','authoring']}, indent=2))
raise SystemExit(0 if result['passed'] else 1)
