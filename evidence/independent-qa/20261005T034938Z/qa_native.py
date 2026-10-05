"""Independent native-game observation using OS input; no asset authoring or action injection."""
from pathlib import Path
import ctypes, json, os, subprocess, sys, time, traceback
from ctypes import wintypes as w
from PIL import Image, ImageStat

ROOT = Path(r'C:\Projects\to-deploy\horror-game')
OUT = Path(__file__).resolve().parent / 'native-final'
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'tools'))
import astra_setup as setup

u = ctypes.WinDLL('user32', use_last_error=True)
u.SetProcessDPIAware()
u.GetForegroundWindow.restype = w.HWND
u.SetForegroundWindow.argtypes = [w.HWND]
u.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
u.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
u.GetClientRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
u.ClientToScreen.argtypes = [w.HWND, ctypes.POINTER(w.POINT)]
u.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]

class Mouse(ctypes.Structure):
    _fields_ = [('dx',w.LONG),('dy',w.LONG),('data',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',ctypes.c_size_t)]
class Keyboard(ctypes.Structure):
    _fields_ = [('vk',w.WORD),('scan',w.WORD),('flags',w.DWORD),('time',w.DWORD),('extra',ctypes.c_size_t)]
class Hardware(ctypes.Structure):
    _fields_ = [('message',w.DWORD),('low',w.WORD),('high',w.WORD)]
class InputUnion(ctypes.Union):
    _fields_ = [('mouse',Mouse),('key',Keyboard),('hardware',Hardware)]
class Input(ctypes.Structure):
    _fields_ = [('type',w.DWORD),('value',InputUnion)]
u.SendInput.argtypes = [w.UINT, ctypes.POINTER(Input), ctypes.c_int]

r = {'map':'/Game/Maps/TeddyEncounter','method':'Windows SendInput into the owned ordinary -game window; no pawn teleports, AI freezes, health edits or asset changes','physical_human_test':False,'events':[],'captures':[]}
started = time.monotonic(); game = None; movie = None; hwnd = None; pressed = set(); mouse_down = False
old_foreground = u.GetForegroundWindow(); old_cursor = w.POINT(); u.GetCursorPos(ctypes.byref(old_cursor))

def save():
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2),encoding='utf-8')

def note(name, **kwargs):
    event = {'wall_seconds':round(time.monotonic()-started,3),'name':name,**kwargs}
    r['events'].append(event); save(); print(json.dumps(event),flush=True)

def owned_foreground():
    global hwnd
    foreground = u.GetForegroundWindow()
    if foreground != hwnd:
        foreground_pid=w.DWORD();u.GetWindowThreadProcessId(foreground,ctypes.byref(foreground_pid))
        rect=w.RECT();u.GetClientRect(foreground,ctypes.byref(rect))
        if foreground_pid.value == game.pid and rect.right >= 1000 and rect.bottom >= 600:
            hwnd=foreground
        else:
            raise RuntimeError(f'Game lost foreground to PID {foreground_pid.value}; refusing to send input elsewhere')
    pid = w.DWORD(); u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
    assert pid.value == game.pid, 'Window ownership changed'

def key(vk, down):
    owned_foreground(); event=Input(); event.type=1; event.value.key=Keyboard(vk,0,0 if down else 2,0,0)
    assert u.SendInput(1,ctypes.byref(event),ctypes.sizeof(Input))==1,ctypes.get_last_error()
    (pressed.add if down else pressed.discard)(vk)
    note('key_down' if down else 'key_up',vk=vk)

def tap(vk):
    key(vk,True);time.sleep(.08);key(vk,False)

def mouse(down):
    global mouse_down
    owned_foreground();event=Input();event.type=0;event.value.mouse=Mouse(0,0,0,2 if down else 4,0,0)
    assert u.SendInput(1,ctypes.byref(event),ctypes.sizeof(Input))==1,ctypes.get_last_error()
    mouse_down=down;note('left_mouse_down' if down else 'left_mouse_up')

def aim(x,y):
    owned_foreground();rect=w.RECT();origin=w.POINT(0,0)
    assert u.GetClientRect(hwnd,ctypes.byref(rect));assert u.ClientToScreen(hwnd,ctypes.byref(origin))
    point=(origin.x+int(x*rect.right),origin.y+int(y*rect.bottom))
    assert u.SetCursorPos(*point);note('mouse_position',normalized=[x,y],screen=list(point))

def capture(label):
    owned_foreground();path=OUT/(label+'.png')
    assert not path.exists()
    rect=w.RECT();origin=w.POINT();u.GetClientRect(hwnd,ctypes.byref(rect));u.ClientToScreen(hwnd,ctypes.byref(origin))
    cmd=[setup.tool('ffmpeg.exe'),'-v','error','-xerror','-f','gdigrab','-draw_mouse','1','-framerate','30','-video_size',f'{rect.right}x{rect.bottom}','-offset_x',str(origin.x),'-offset_y',str(origin.y),'-i','desktop','-frames:v','1','-update','1',str(path)]
    subprocess.run(cmd,check=True,timeout=12,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=setup.HIDDEN)
    with Image.open(path) as image:
        image.load();size=list(image.size)
        assert max(ImageStat.Stat(image.convert('RGB')).mean)>1,'Capture is black; not accepted as rendered evidence'
    r['captures'].append({'label':label,'path':str(path),'pixels':size,'wall_seconds':round(time.monotonic()-started,3)})
    save();print('CAPTURE '+label,flush=True)

try:
    setup.require_editor_closed()
    engine=Path(setup.SETTINGS['engine_root'])/'Engine/Binaries/Win64/UnrealEditor.exe'
    args=[str(engine),str(ROOT/setup.SETTINGS['project']),r['map'],'-game','-windowed','-ResX=1280','-ResY=720','-ForceRes','-WinX=60','-WinY=60','-nosplash','-nop4','-ExecCmds=t.MaxFPS 60',f'-abslog={OUT/"engine.log"}',*setup.unreal_local_arguments()]
    r['arguments']=args;r['frame_cap_for_capture']=60
    log=(OUT/'process.log').open('w',encoding='utf-8')
    game=subprocess.Popen(args,cwd=ROOT,env=setup.tool_environment(),stdout=log,stderr=subprocess.STDOUT,creationflags=setup.HIDDEN)
    r['process_id']=game.pid;save()
    callback_type=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @callback_type
    def visit(window, parameter):
        global hwnd
        pid=w.DWORD();u.GetWindowThreadProcessId(window,ctypes.byref(pid))
        if pid.value==game.pid and u.IsWindowVisible(window):
            rect=w.RECT();u.GetClientRect(window,ctypes.byref(rect))
            if rect.right>=1000 and rect.bottom>=600:hwnd=window;return False
        return True
    while not hwnd:
        assert game.poll() is None,'Game exited during startup'
        assert time.monotonic()-started<75,'No owned game window appeared'
        u.EnumWindows(visit,0);time.sleep(.2)
    while 'LogLoad: (Engine Initialization) Total time:' not in (OUT/'engine.log').read_text(errors='replace'):
        assert game.poll() is None and time.monotonic()-started<90,'Engine initialization did not complete'
        time.sleep(.2)
    time.sleep(3)
    hwnd=None;u.EnumWindows(visit,0)
    u.SetForegroundWindow(hwnd);time.sleep(.4);owned_foreground()
    title=ctypes.create_unicode_buffer(512);u.GetWindowTextW(hwnd,title,512)
    r['window_title']=title.value;r['window_handle']=hwnd
    capture('00-first-live-view')
    (OUT/'ready.json').write_text(json.dumps({'pid':game.pid,'hwnd':hwnd,'title':title.value}))
    note('ready_for_independent_inspection')
    while not (OUT/'run-inputs.json').exists():
        assert game.poll() is None,'Game exited while waiting'
        assert time.monotonic()-started<170,'QA controller timed out before input phase'
        time.sleep(.2)
    settings=json.loads((OUT/'run-inputs.json').read_text())
    u.SetForegroundWindow(hwnd);time.sleep(.3);owned_foreground()
    movie_log=(OUT/'movie.log').open('w',encoding='utf-8')
    rect=w.RECT();origin=w.POINT();u.GetClientRect(hwnd,ctypes.byref(rect));u.ClientToScreen(hwnd,ctypes.byref(origin))
    r['capture_rectangle']=[origin.x,origin.y,rect.right,rect.bottom]
    movie_args=[setup.tool('ffmpeg.exe'),'-v','warning','-f','gdigrab','-draw_mouse','1','-framerate','30','-video_size',f'{rect.right}x{rect.bottom}','-offset_x',str(origin.x),'-offset_y',str(origin.y),'-i','desktop','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'independent-input-run.mp4')]
    r['recording_arguments']=movie_args
    movie=subprocess.Popen(movie_args,cwd=ROOT,stdin=subprocess.PIPE,stdout=movie_log,stderr=subprocess.STDOUT,creationflags=setup.HIDDEN)
    tap(0x74);time.sleep(1.2);aim(*settings.get('aim',[.42,.33]));capture('01-restarted')
    key(ord('W'),True);time.sleep(.65);key(ord('W'),False);capture('02-move-w')
    key(ord('D'),True);time.sleep(.55);key(ord('D'),False);capture('03-move-d')
    key(ord('A'),True);time.sleep(.12);tap(0x20);time.sleep(.22);key(ord('A'),False);capture('04-space-dodge')
    tap(0x74);time.sleep(.8);aim(*settings.get('aim',[.42,.33]));mouse(True)
    key(ord('A'),True);time.sleep(.7);key(ord('A'),False);time.sleep(.8);capture('05-move-and-fire');mouse(False)
    tap(0x1b);time.sleep(.25);capture('06-pause-before-input')
    key(ord('W'),True);mouse(True);time.sleep(.6);mouse(False);key(ord('W'),False);capture('07-pause-after-input')
    tap(0x1b);time.sleep(.6);capture('08-resumed')
    tap(0x74);time.sleep(.8);capture('09-restarted-again')
    time.sleep(8);capture('10-no-input-pursuit')
    time.sleep(4);capture('11-no-input-outcome')
    tap(0x74);time.sleep(.8);capture('12-final-restart')
    r['input_sequence_completed']=True;note('input_sequence_completed')
except Exception:
    r['error']=traceback.format_exc();print(r['error'],flush=True)
finally:
    if hwnd and u.GetForegroundWindow()==hwnd:
        for vk in list(pressed):
            try:key(vk,False)
            except Exception:pass
        if mouse_down:
            try:mouse(False)
            except Exception:pass
    if movie and movie.poll() is None:
        try:movie.communicate(b'q',timeout=15)
        except Exception:movie.terminate();movie.wait(timeout=10)
        r['movie_exit_code']=movie.returncode
    if game and game.poll() is None:
        if hwnd:u.PostMessageW(hwnd,0x0010,0,0)
        try:game.wait(timeout=20)
        except subprocess.TimeoutExpired:game.terminate();game.wait(timeout=10);r['forced_close']=True
        r['game_exit_code']=game.returncode
    if old_foreground:u.SetForegroundWindow(old_foreground)
    u.SetCursorPos(old_cursor.x,old_cursor.y)
    r['wall_seconds']=round(time.monotonic()-started,3);save()
    print(json.dumps({'completed':r.get('input_sequence_completed',False),'error':r.get('error'),'game_exit_code':r.get('game_exit_code'),'directory':str(OUT)}),flush=True)
