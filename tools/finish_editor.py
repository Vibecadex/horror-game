"""Let PIE and outstanding render work finish before requesting editor shutdown."""
import unreal as u,time,gc
_handle=None
def finish_editor(play_callback,release=None):
    global _handle
    if play_callback is not None:u.unregister_slate_post_tick_callback(play_callback)
    lev=u.get_editor_subsystem(u.LevelEditorSubsystem);lev.editor_request_end_play()
    if release:release()
    deadline=time.monotonic()+3
    def drain(dt):
        global _handle
        if time.monotonic()<deadline:return
        if u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world():return
        u.unregister_slate_post_tick_callback(_handle);_handle=None;gc.collect()
        # The installed EditorPythonExecuter defers QUIT_EDITOR on its next tick
        # when this flag clears, after destroying the active-script notification.
        u.EditorPythonScripting.set_keep_python_script_alive(False)
    _handle=u.register_slate_post_tick_callback(drain)
