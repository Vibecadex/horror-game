"""Prove built-in UE5.8 graph authoring and save an isolated runtime test map."""
from pathlib import Path
import json
import os
import re
import traceback
import unreal

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("TEDDY_AUTHORING_REPORT", str(ROOT / "evidence/setup/blueprint-candidate/authoring.json")))
report = {"passed": False, "native_module_required": False}
LIB = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary
PROOF_ID = os.environ.get("TEDDY_PROOF_ID", "candidate")
assert re.fullmatch(r"[A-Za-z0-9_]+", PROOF_ID), "Invalid proof namespace"
BP_PATH = "/Game/SetupValidation/Proof_" + PROOF_ID + "/BP_AuthoringProof"
MAP = "/Game/SetupValidation/Proof_" + PROOF_ID + "/BlueprintRuntime"
TAG = "TeddySetup.GraphAuthoring"
try:
    assert hasattr(unreal, "BlueprintGraphEditor"), "UE5.8 graph API unavailable"
    if ASSETS.does_asset_exist(BP_PATH):
        bp = ASSETS.load_asset(BP_PATH)
        assert ASSETS.get_metadata_tag(bp, TAG) == "v1", "Preserving unowned proof asset"
    else:
        bp = LIB.create_blueprint_asset_with_parent(BP_PATH, unreal.Actor.static_class())
        assert bp
        ASSETS.set_metadata_tag(bp, TAG, "v1")
        graph = unreal.BlueprintGraphEditor.get_graph_editor(LIB.find_event_graph(bp))
        assert graph.add_member_variable("SetupProofPassed", LIB.get_basic_type_by_name("bool"), "false")
        begin = LIB.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, 0))
        setter = graph.add_set_member_variable_node("SetupProofPassed")
        assert setter.find_input_pin("SetupProofPassed").set_pin_value("true")
        assert begin.find_output_pin("then").try_create_connection(setter.find_execute_pin())
        marker = graph.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
        assert marker.find_input_pin("InString").set_pin_value("TEDDY_BLUEPRINT_RUNTIME_AUTHORING_OK")
        assert setter.find_output_pin("then").try_create_connection(marker.find_execute_pin())
        # This isolated proof level can also verify the ordinary -game launch.
        # The editor input test exits before this delayed standalone capture.
        delay = graph.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        assert delay.find_input_pin("Duration").set_pin_value("17.0")
        assert marker.find_output_pin("then").try_create_connection(delay.find_execute_pin())
        capture = graph.add_call_function_node("/Script/Engine.KismetSystemLibrary.ExecuteConsoleCommand")
        image_path = (OUTPUT.parent / "standalone.png").as_posix()
        assert capture.find_input_pin("Command").set_pin_value(f'HighResShot 1280x720 filename="{image_path}"')
        assert delay.find_output_pin("then").try_create_connection(capture.find_execute_pin())
        wait_capture = graph.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        assert wait_capture.find_input_pin("Duration").set_pin_value("2.0")
        assert capture.find_output_pin("then").try_create_connection(wait_capture.find_execute_pin())
        quit_game = graph.add_call_function_node("/Script/Engine.KismetSystemLibrary.ExecuteConsoleCommand")
        assert quit_game.find_input_pin("Command").set_pin_value("Quit")
        assert wait_capture.find_output_pin("then").try_create_connection(quit_game.find_execute_pin())
    assert LIB.compile_blueprint(bp), "Graph did not compile"
    assert ASSETS.save_loaded_asset(bp, False), "Graph did not save"
    cls = LIB.generated_class(bp)
    assert unreal.get_default_object(cls).get_editor_property("SetupProofPassed") is False
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if ASSETS.does_asset_exist(MAP):
        assert level.load_level(MAP)
    else:
        assert level.new_level_from_template(MAP, "/Game/Variant_TwinStick/LVL_TwinStick")
        # Saving a map under a new name does not change the active editor world.
        assert level.load_level(MAP)
    existing = [a for a in actors.get_all_level_actors() if a.get_class() == cls]
    assert len(existing) < 2, "Duplicate proof actors"
    if not existing:
        proof = actors.spawn_actor_from_class(cls, unreal.Vector(0, 0, 100), transient=False)
        proof.set_actor_label("SetupGraphAuthoringProof")
        assert level.save_current_level()
        assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    # A second engine process will load this saved map and verify runtime state.
    report.update(passed=True, blueprint=BP_PATH, map=MAP,
                  generated_class=cls.get_path_name(), default_state=False,
                  runtime_marker="TEDDY_BLUEPRINT_RUNTIME_AUTHORING_OK",
                  standalone_image=str(OUTPUT.parent / "standalone.png"),
                  runtime_execution_verified=False)
    report["runtime_apis"] = {name: getattr(unreal, name).__doc__ for name in ("InputActionValue",)}
    report["input_apis"] = {name: getattr(unreal.EnhancedInputLocalPlayerSubsystem, name).__doc__
                            for name in ("inject_input_vector_for_action",)}
    report["subsystem_apis"] = [x for x in dir(unreal) if "subsystem" in x.lower() and "player" in x.lower()]
except Exception:
    report["passed"] = False
    report["error"] = traceback.format_exc()
    unreal.log_error(report["error"])
finally:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
if not report["passed"]:
    raise RuntimeError(report["error"])
