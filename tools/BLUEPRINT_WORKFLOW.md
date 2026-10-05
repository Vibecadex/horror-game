# Astra: native-module-free Unreal authoring

Use this recipe when the next implementation run selects the prepared Unreal 5.8 Blueprint project. Read `RUN_ASTRA.md`, `MASTER_PROMPT.md`, `REFERENCE_BRIEF.md` and current setup/status evidence first. Resolve the active `.uproject` from the current settings and launcher; do not assume the preserved C++ BossShot baseline is the implementation destination. Keep the reference originals and baseline intact.

This workflow prepares and extends runtime Blueprint assets using the installed editor. It does not compile a new native project module, install a plugin or change Windows protection. Python performs editor authoring; the saved Blueprint graphs execute gameplay.

## Evidence boundary

`tools/verify_blueprint_authoring.py` has created, compiled and saved an isolated `BP_AuthoringProof`. Separate editor play and ordinary `-game` processes reopened and executed its generated behavior successfully; the complete local receipt is `evidence/setup/blueprint-final-host-2/engine-probe.json`. Consult the latest full setup receipt for authenticated Astra verification. Graph-authoring readiness and the stock template's playability do not establish the completed horror encounter.

The authoritative local API evidence is under `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Editor/BlueprintEditorLibrary/`:

- `Private/BlueprintEditorLibrary/BlueprintGraphEditor.h`: reflected `BlueprintGraphEditor`, including Epic's Python example, node creation, graph functions and events.
- `Public/BlueprintEditorLibrary.h`: Blueprint creation, event overrides, generated classes and compilation.
- `Public/BlueprintEditorLibrary/BlueprintGraphPin.h`: pin lookup helpers, literal values and validated connections.

The graph editor's header being in `Private` does not make its reflected Python interface unavailable: the current editor exposed it successfully. Use the installed 5.8 API and runtime reflection when documentation differs. For a future documentation question, follow the project's Context7 instructions before consulting official Epic release notes or Python documentation; do not import older claims that Python cannot edit Blueprint graphs into this installation.

## Start with the shipped encounter

Use the Blueprint Top Down TwinStick variant already prepared by setup. Keep one writer for `.uasset` files and maps. Duplicate the map and the gameplay assets that need changes into an owned namespace such as `/Game/TeddyEncounter`; preserve the source template assets. Use `EditorAssetLibrary.duplicate_asset`, then explicitly inspect and update references: duplicating one Blueprint does not automatically redirect its game mode, controller, pawn, projectile, spawner or AI references.

Before editing, inventory each Blueprint's parent, graphs, variables, component templates and input actions. Use `BlueprintEditorLibrary.list_graphs`, `BlueprintGraphEditor.get_graph_editor`, `list_all_nodes` and the node's pin inspection methods. Record existing execution/data connections. Add behavior through deliberate extension points; do not disconnect stock movement, aiming, spawning or firing merely to make a new graph compile.

## A proven graph-authoring pattern

These exact calls are exercised by `verify_blueprint_authoring.py`; adapt them in owned assets, not by re-running the proof over gameplay assets:

```python
import unreal
lib = unreal.BlueprintEditorLibrary
assets = unreal.EditorAssetLibrary

bp = lib.create_blueprint_asset_with_parent(
    "/Game/OwnedPrototype/BP_Example", unreal.Actor.static_class()
)
graph = unreal.BlueprintGraphEditor.get_graph_editor(lib.find_event_graph(bp))
assert graph.add_member_variable(
    "SetupProofPassed", lib.get_basic_type_by_name("bool"), "false"
)
begin = lib.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, 0))
setter = graph.add_set_member_variable_node("SetupProofPassed")
assert setter.find_input_pin("SetupProofPassed").set_pin_value("true")
assert begin.find_output_pin("then").try_create_connection(setter.find_execute_pin())
marker = graph.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
assert marker.find_input_pin("InString").set_pin_value("PROTOTYPE_RUNTIME_PROOF")
assert setter.find_output_pin("then").try_create_connection(marker.find_execute_pin())
assert lib.compile_blueprint(bp)
assert assets.save_loaded_asset(bp, False)
```

This minimal example assumes its destination does not exist. Real scripts must refuse unowned collisions and use metadata ownership tags, as the verification script does. Never duplicate BeginPlay or replace its existing wiring blindly.

For additional behavior, the installed graph editor offers function graphs, custom events, branches, variable getter/setter nodes, native function calls, component-bound events and `create_node_from_name`. Enumerate available actions before using display names. Inspect actual pin names/types and check every connection or literal-setting return value. Compile after small coherent changes and inspect compiler errors. Latent behavior belongs in an appropriate event graph, not an ordinary function graph.

## Assets, components and controls

For exposed defaults, use `lib.generated_class(bp)`, `unreal.get_default_object(...)` and verified `get_editor_property`/`set_editor_property` names. Compile and save the owning Blueprint, then reopen to prove persistence. A changed transient actor or class default object alone is insufficient evidence.

To copy a template level, use `LevelEditorSubsystem.new_level_from_template(new_path, template_path)`, then explicitly `load_level(new_path)` before spawning actors. Saving under a new map name does not automatically switch the active world. Save the map and dirty external actor packages, and verify the new actor exists after reopening. `verify_blueprint_authoring.py` demonstrates this sequence in a fresh owned namespace.

For Blueprint component templates, inspect `SubobjectDataSubsystem.k2_gather_subobject_data_for_blueprint` and `SubobjectDataBlueprintFunctionLibrary.get_data` / `get_object_for_blueprint`. Resolve the intended component instead of assuming the first mesh or camera is correct. Use `LevelEditorSubsystem` and `EditorActorSubsystem` for saved level edits, and `MaterialEditingLibrary` for material graphs. Inspect rendered output after lighting, camera, material or scale changes.

Enhanced Input mappings must be inspected through `default_key_mappings`; the old `mappings` field is deprecated and can be empty on 5.7+. Check the installed property's actual value/structure before editing. Preserve modifiers, triggers and existing device mappings. Reopening the mapping asset and testing real input are required; seeing a key string in an asset is not proof that its action works.

The template already contains dash, movement, independent aim, firing and enemy spawning. Read and reuse that logic. The downloaded teddy is an unrigged static mesh: it cannot simply replace Quinn's skeletal mesh and inherit compatible animation. Rigging, animation, silhouette/material improvement and reference-quality review remain implementation work.

## Future encounter behavior

These are implementation directions, not completed features:

- **Dodge:** inspect the stock dash graph, its direction/cooldown and collision behavior; map the agreed action and test repeated use.
- **Pause:** generate calls to existing `GameplayStatics.SetGamePaused`. Ensure the chosen input can trigger while paused (`InputAction.bTriggerWhenPaused`) so unpause remains possible. Test repeated toggles and movement/fire suppression.
- **Restart:** use existing `GameplayStatics.GetCurrentLevelName` and `OpenLevel`, or a deliberately tested reset routine. Verify possession, health, enemies, timers and camera return to their intended initial state.
- **Boss:** use explicit idle/chase/telegraph/attack/recovery/dead state, generated custom events/branches, and existing timer functions such as `KismetSystemLibrary.K2_SetTimer`. Separate visible telegraph timing from damage activation. Cancel or invalidate obsolete callbacks on death/reset; prevent overlapping attack transitions.

The native function paths and graph API are available in installed engine source; each generated gameplay feature still needs a compile, saved readback and behavioral test. No new project DLL is required for these Blueprint designs.

## Finish each milestone with evidence

Save the edited assets and map, close/reopen in a separate editor process, and inspect their values, references and graph/compiler state. Exercise a real gameplay session; capture the new behavior and actual viewport. Report which checks used physical input, input injection or direct function calls rather than treating them as interchangeable. A runtime log marker proves that graph executed, not that every gameplay interaction works.

For the horror encounter, compare matching gameplay views with the supplied upright reference frames: elevated camera, grounded creature proportions, player readability, cyan/teal pools of light, dark worn floor and restrained red edge glows. Continue toward the current master prompt's visual and playable acceptance criteria; the template and authoring proof are the starting tools, not the finished game.
