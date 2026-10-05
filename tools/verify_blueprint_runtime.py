"""Editor-hosted play test of saved Blueprint logic and the stock input action path.

Run with -ExecutePythonScript (not the Python commandlet) so Slate/game frames tick.
No physical keyboard or mouse events are generated and no other window is touched.
"""
from pathlib import Path
import json
import math
import os
import time
import traceback
import unreal

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("TEDDY_RUNTIME_REPORT", str(ROOT / "evidence/setup/blueprint-candidate/runtime.json")))
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
report = {"passed": False, "checks": {}, "input_method": "Enhanced Input action injection in editor play",
          "physical_device_verified": False, "proves_new_encounter": False, "images": []}
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
state = {"started": time.monotonic(), "play_started": None, "stage": 0, "max_projectiles": 0,
         "max_enemies": 0, "positions": [], "yaws": [], "finished": False}
handle = None
AUTHORED = json.loads(Path(os.environ.get("TEDDY_AUTHORING_REPORT", str(ROOT / "evidence/setup/blueprint-candidate/authoring.json"))).read_text())


def finish(error=None):
    global handle
    if state["finished"]:
        return
    state["finished"] = True
    if error:
        report["error"] = error
    report["passed"] = not error and bool(report["checks"]) and all(report["checks"].values())
    report["wall_seconds"] = round(time.monotonic() - state["started"], 3)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
    level.editor_request_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(delta):
    try:
        if time.monotonic() - state["started"] > 100:
            raise RuntimeError("Timed out waiting for runtime verification")
        world = editor.get_game_world()
        if world is None:
            return
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
        if pc is None or pawn is None:
            return
        if state["play_started"] is None:
            state["play_started"] = unreal.GameplayStatics.get_time_seconds(world)
            state["start_position"] = pawn.get_actor_location()
            inputs = [s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem)
                      if s.get_world() == world]
            if len(inputs) != 1:
                raise RuntimeError(f"Expected one player input subsystem; found {len(inputs)}")
            state["input"] = inputs[0]
            prefix = "/Game/Variant_TwinStick/Input/Actions/IA_Action_"
            state["actions"] = {name: unreal.load_asset(prefix + name) for name in ("Move", "StickAim", "Fire", "Dash")}
            report["checks"]["player_possessed"] = pawn.get_controller() == pc
            proofs = unreal.GameplayStatics.get_all_actors_of_class(world, state["proof_class"])
            state["proofs"] = proofs
            report["pawn_class"] = pawn.get_class().get_path_name()
            report["proof_instances"] = [p.get_path_name() for p in proofs]
            report["world_start_time"] = unreal.GameplayStatics.get_time_seconds(world)
            report["actors_at_start"] = [a.get_class().get_path_name() for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)]
        elapsed = unreal.GameplayStatics.get_time_seconds(world) - state["play_started"]
        inputs = state["input"]
        def inject(name, x, y=0):
            inputs.inject_input_vector_for_action(state["actions"][name], unreal.Vector(x, y, 0), [], [])
        if 2 < elapsed < 3:
            inject("Move", 1, 0)
        if 3 < elapsed < 5:
            inject("StickAim", 1, 0)
            inject("Fire", 1)
        if 5 < elapsed < 7:
            inject("StickAim", 0, 1)
            inject("Fire", 1)
        state["max_projectiles"] = max(state["max_projectiles"],
            len(unreal.GameplayStatics.get_all_actors_of_class(world, state["projectile"])))
        state["max_enemies"] = max(state["max_enemies"],
            len(unreal.GameplayStatics.get_all_actors_of_class(world, state["enemy"])))
        if state["stage"] < 3 and elapsed > (2, 5, 9)[state["stage"]]:
            location = pawn.get_actor_location()
            state["positions"].append([location.x, location.y, location.z])
            state["yaws"].append(pawn.get_actor_rotation().yaw)
            image = OUTPUT.parent / f"runtime-{state['stage'] + 1:02}.png"
            state["stage"] += 1
            unreal.SystemLibrary.execute_console_command(world,
                f'HighResShot 1280x720 filename="{image.as_posix()}"', pc)
            report["images"].append(str(image))
        if elapsed > 13:
            report["world_end_time"] = unreal.GameplayStatics.get_time_seconds(world)
            report["positions"] = state["positions"]
            report["yaws"] = state["yaws"]
            report["max_projectiles"] = state["max_projectiles"]
            report["max_enemies"] = state["max_enemies"]
            report["checks"]["saved_graph_executed"] = len(state["proofs"]) == 1 and state["proofs"][0].get_editor_property("SetupProofPassed") is True
            report["checks"]["movement_action_moves_player"] = math.dist(state["positions"][0], state["positions"][1]) > 30
            report["checks"]["aim_action_turns_player"] = abs(state["yaws"][1] - state["yaws"][2]) > 20
            report["checks"]["fire_action_spawns_projectiles"] = state["max_projectiles"] > 0
            report["checks"]["enemy_spawning"] = state["max_enemies"] > 0
            report["checks"]["three_rendered_captures"] = len(report["images"]) == 3 and all(Path(p).is_file() for p in report["images"])
            finish()
    except Exception:
        finish(traceback.format_exc())


try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    assert level.load_level(AUTHORED["map"])
    state["proof_class"] = unreal.EditorAssetLibrary.load_blueprint_class(AUTHORED["blueprint"])
    state["projectile"] = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Variant_TwinStick/Blueprints/BP_TwinStickProjectile")
    state["enemy"] = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Variant_TwinStick/Blueprints/AI/BP_TwinStickNPC")
    level.editor_request_begin_play()
    handle = unreal.register_slate_post_tick_callback(tick)
except Exception:
    finish(traceback.format_exc())
