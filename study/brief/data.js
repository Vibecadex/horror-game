/* Reconciled encounter brief. Local study data. Parity is not accepted. */
const BRIEF = {
  updated: "5 October 2026",
  statusLine: "Functional checks passed at 09:30 UTC. Exact visual parity, physical-device play, and audio matching are still open.",
  hero: {
    kicker: "Teddy Encounter",
    title: "How to build a fight like the End of Abyss scene",
    lede: "One elevated camera looks down a dark industrial room. A small armed human moves and aims independently, fires, and dodges. One grounded monstrous teddy is the boss. Three smaller crawlers of the same family share the floor. Teal light, black corners, a damp concrete floor, and three red pins make the air. The phone clip supplies that picture. It does not supply the numbers. The numbers on this site are the holds this project actually wrote down."
  },
  routes: [
    { id: "camera", label: "Camera", text: "Pitch −46°, FOV 54, 1280×720. One view on the near side of the room, looking toward the far wall. It widens as the two bodies separate. It never cuts to a low hero shot." },
    { id: "models", label: "3D models", text: "Keep the CC0 teddy and the 16-bone body. TeddyV2 is a stitch skin, not a new creature. The room is a repeated kit: 10 props, 17 shell modules, 36 dressings, 6 floor meshes. A 21-mesh subset is already in the level." },
    { id: "air", label: "Atmospherics", text: "One teal key at 165000 cd, manual exposure +3.8 EV, a moving pool at the saved 17500 cd, three red pins, and atmosphere-14 haze. Corners stay dark. Teal is light, not a wall color." },
    { id: "play", label: "Gameplay", text: "Move, aim, shoot, dodge one telegraphed slam. Boss health 300 at 105 cm/s. Player health 100. Three stitchlings at 24 health die when the boss dies. No new phase and no new weapon." }
  ],
  poses: [
    { id: "start", name: "Start", camera: [-1679, 170, 1874], look: [-24, 170, 160], player: [-230, 570, 85], boss: [250, -230, 232], note: "Matched plate. Player spawn actor is Z 95; the plate stood near Z 85. Look-at is written only for this pose." },
    { id: "wide", name: "Wide", camera: [-5522, 0, 5690], look: null, player: [-1300, -1400], boss: [1300, 1400], note: "Both fighters at opposite corners. Look-at is not written beside this pose. Height comes from the separation formula." },
    { id: "far", name: "Far edge", camera: [-1945, -75, 2900], look: null, player: [1300, 80], boss: null, note: "Player deep in the room. Boss position is not written for this sample." },
    { id: "reverse", name: "Reverse", camera: [-1683, -155, 2540], look: null, player: [1100, -80], boss: null, note: "The camera stays on the near side and still looks toward the far wall. This is not a camera behind the boss." }
  ],
  models: [
    { family: "Creature", name: "Original GLB", state: "keep", detail: "Horror Teddy Bear Monster, Aiden Reynolds, CC0. 3660 triangles, no skeleton, no animation. SHA-256 9fe8c87ab5eab6d05f19c936d8ae993d07727aa9871100118aa21452f7a9a8bb. Never replace this file." },
    { family: "Creature", name: "Adapted body", state: "level", detail: "Teddy_Encounter.blend, 4.6 m, 16 bones, 21960 triangles. Six shipped clips. Do not replace the mesh or the rig." },
    { family: "Creature", name: "TeddyV2 skin", state: "level", detail: "Same skeleton. 2.4 cm crown seam, 13 thread bridges, 24698 triangles. On all four creatures. No upper-back continuation." },
    { family: "Creature", name: "Stitchlings", state: "level", detail: "Three instances, actor scale 0.35, crawl about 55 cm/s, health 24. Spawns (650, 600, 65), (−480, −500, 65), (20, 1070, 65)." },
    { family: "Creature", name: "Player", state: "level", detail: "Twin Stick human with the service rifle. Spawn (−230, 570, 95), yaw −145. Health 100. Shot damage 12." },
    { family: "Kit", name: "10 room props", state: "level", detail: "All 41 placed instances are in: pilasters, one bulkhead with its locking wheel, fans, two tanks of one family, cabinets, pipe racks including the valve, crates, spool, grates, strip housings. 49280 triangles." },
    { family: "Shell", name: "17 modules", state: "partial", detail: "7 types and 46 instances are in the level. The other 10 modules are on disk. The 303-placement plan’s 107 shell copies are a superset, not a second import." },
    { family: "Dressing", name: "36 modules", state: "partial", detail: "14 types and 38 instances are in. 22 modules remain on disk. Cluster what remains. Do not add a wheel, tank, crate, or ceiling." },
    { family: "Floor", name: "6 parity meshes", state: "level", detail: "45 non-colliding placements. Fracture fields, edge spall, rubble, micro chips. Z −5, no collision." },
    { family: "Floor", name: "FloorV3", state: "level", detail: "SM_ParityFractureField_A_V3 replaces two of those forty-five. Interrupted plates and larger fragments. It does not replace the old mesh asset." },
    { family: "Animation", name: "20 preprod clips", state: "disk", detail: "On the same rig, in Assets/Adapted/AnimPreprod. Not assigned. DefeatBreath stays unassigned. The live death is A_Teddy_DefeatGrounded." },
    { family: "Ban", name: "Do not author", state: "ban", detail: "No new GLB, no fourth creature, no ceiling or truss, no open hall, no second wheel, no second tank or crate family, no luminous sign, no baked pool, no HUD art, no cloth simulation." }
  ],
  lights: [
    { name: "Key", value: "165000 cd", detail: "(900, 60, 1600) aimed at (100, 0, −5). Color (0.50, 0.94, 1). Attenuation 4400. Source radius 70. Inner 22°, outer 40°.", source: "parity-combined-settings.json" },
    { name: "Player pool", value: "17500 cd saved", detail: "Relative (105, 0, 170), pitch −80°. Prose desks still say about 16000 cd and cones 15° / 26°. Those cones are not in the combined file. Color in the lighting note is (0.94, 0.96, 1), volumetric off, shadows off.", source: "parity-combined-settings.json and LIGHTING.md" },
    { name: "Exposure", value: "+3.8 EV", detail: "Manual. A brighter reference mean is not a reason to lift it.", source: "LIGHTING.md, LIVE_BRIEF.md" },
    { name: "Red pins", value: "180 / 180 / 160 cd", detail: "(740, −1530, 235), (−920, 1530, 235), (1630, 400, 240). Color (1, 0.034, 0.014). Three only.", source: "LIGHTING.md, layout.json" },
    { name: "Haze", value: "atmosphere-14", detail: "No local fog volumes. Height fog density 0.017, falloff 2.0, extinction 1, volumetric distance 12000. One rect at (900, −100, 650), 150000 cd, 1200×1200, scattering 16, aimed down.", source: "parity-atmosphere-settings.json" },
    { name: "Character fill", value: "6000 cd rear", detail: "Rear centre (1250, 0, 420), radius 650, source 70, color (0.35, 0.50, 0.55). Perimeter 14000 cd and foreground 22000 cd are character-only. They must not light the floor or feed fog.", source: "parity-atmosphere-settings.json, WORK_STATUS 09:30" }
  ],
  beats: [
    { t: "0:00", title: "Start", text: "Player at the start pose. Boss at (250, −230, 232). The door is shut." },
    { t: "0:12", title: "Near approach", text: "The player uses the near lane, X −1400 to −500, and turns onto the pipe orbit." },
    { t: "0:28", title: "Slam", text: "In the 220 cm pipe lane the boss shows the ring for about 0.92 s. Space dodges. Damage is ignored for 0.26 s. The next dodge waits 0.80 s." },
    { t: "0:42", title: "Far approach", text: "The player takes the far lane. The bulkhead stays closed. No new phase starts." },
    { t: "0:55", title: "Power orbit", text: "The player is on the right-hand lane. Stitchlings are still up until the boss health hits 0." }
  ],
  lanes: [
    { name: "Near approach", box: "X −1400..−500, Y −40..240", width: "280 cm" },
    { name: "Pipe orbit", box: "X −1100..1200, Y −1180..−960", width: "220 cm" },
    { name: "Far approach", box: "X 860..1080, Y −900..1000", width: "220 cm" },
    { name: "Power orbit", box: "X −900..1100, Y 700..920", width: "220 cm" }
  ],
  clips: {
    shipped: ["Idle 90", "Walk 37", "Crawl 37", "Attack 54", "Hit 16", "Defeat 72"],
    extra: ["TurnLeft", "TurnRight", "StepLeft", "StepRight", "Telegraph", "Recover", "AttackLeft", "Stagger", "IdleHeavy", "Threat", "WalkStop", "StitchlingIdle", "StitchlingFlinch", "DefeatBreath", "Brace", "HitLeft", "SwipeLow", "Search", "Slump", "WeightShift"],
    channel: "Pitch is local X. A few degrees of local Z is the shipped sway. Twenty-five degrees of spine Z folded the chest, so larger turns use local Y. Root travel stays in the blueprint."
  },
  audio: [
    { name: "Rifle", seconds: "0.19", use: "Player shot, volume 0.26 in the feedback script. Not auditioned." },
    { name: "Slam", seconds: "0.80", use: "Boss strike 0.5, stitchling strike 0.18. Not auditioned." },
    { name: "ClothHit", seconds: "0.22", use: "Imported only. The sheet maps it to hit clips. The feedback script never plays it." },
    { name: "RoomTone", seconds: "16.0", use: "Looping bed at 0.5 on the camera. Not auditioned." }
  ],
  numbers: [
    ["Player health", "100", "tools/build_combat.py"],
    ["Shot damage", "12", "tools/build_combat.py"],
    ["Boss health", "300", "tools/build_boss.py"],
    ["Boss attack / strike", "380 / 475 cm", "tools/build_boss.py"],
    ["Boss damage", "24", "tools/build_boss.py"],
    ["Boss speed", "105 cm/s published", "Stitchling builder sets the class default. The boss builder’s variable default is still 125."],
    ["Stitchling health / speed / damage", "24 / 55 cm/s / 10", "tools/build_stitchlings.py"],
    ["Stitchling ranges", "190 / 215 cm", "tools/build_stitchlings.py"],
    ["Dodge", "Space, proposal", "0.26 s of ignored damage, 0.80 s before another. The video does not show the button."],
    ["Fire", "Left mouse, proposal", "Aim is independent of travel. The video does not show the button."]
  ],
  steps: {
    camera: [
      "Use one combat view for the whole fight. Pitch stays −46°. Horizontal FOV stays 54. Compare at 1280×720.",
      "WASD moves relative to that view. The mouse aims on the floor and fires along the aim. The mouse does not yaw the camera.",
      "Look at the pair, not the player alone. The look point is their midpoint, pulled toward −X by 0.07 times their X separation, at Z 160.",
      "Park the camera on the near side so it looks toward +X. Height is clamp(max(1.8|dx|, |dy|) + 850, 1700, 5600).",
      "Leave the centre overhead empty. The near edge is a 42–68 cm cutaway, not a wall in front of the lens.",
      "Check the four poses on this page before calling the framing done. Widening is the same camera, not a second mode."
    ],
    models: [
      "Keep the original GLB byte-identical and keep the 16-bone body. TeddyV2 stays a skin on that skeleton.",
      "Do not run tools/build_full_room.py. It only reimports the ten kit props and would rebuild the old room.",
      "The 41 kit props and all 45 floor placements are already saved. Do not drop the 303-row plan on top of them.",
      "Add only shell and dressing modules that are not among the 21 already active. Hide a box only when a mesh replaces its look. Keep the box collision.",
      "Left wall stays pipes. Right wall stays cabinets and power. Two tanks of one mesh. The bulkhead wheel and the pipe-rack valve already exist.",
      "Leave the twenty preprod clips on disk until a later pass. Do not assign DefeatBreath over the grounded death."
    ],
    air: [
      "Grade to direction-close-best.jpg. Keep exposure at +3.8 EV.",
      "One stationary teal spot is the key and the contact shadow. Use the combined-settings numbers. Do not restore 130000 cd or source radius 30.",
      "The player pool stays a moving, unbaked spot at the saved 17500 cd. Do not widen it to 48°. An IES profile is how a cone stops being only a soft disc.",
      "Three red pins only. Strip housings stay slits.",
      "Haze is atmosphere-14: height fog plus one downward rect. The glowing sphere still stored in the combined file is historical.",
      "Cloth stays on the Cloth shading model. Amount 0.32 is wired through the ClearCoat pin. Fuzz Color is still unwired. Take a closer crop before more seam mesh.",
      "Walls use four families: charcoal concrete, worn green-grey steel, muted oxide, near-black recess. Floor roughness stays damp 0.40–0.65 and dry 0.75–0.95."
    ],
    play: [
      "Do not rerun tools/build_boss.py. That script resets the boss graph and writes speed 125.",
      "Keep the loop that is already there: chase, a 0.92 s ring, the strike, recovery, a hit flinch, and grounded death.",
      "Publish 105 cm/s for the boss and 55 cm/s for the stitchlings. Root motion stays in the blueprint.",
      "The win is boss health at 0. Both stitchlings zero themselves on that check. F5 restarts the level.",
      "Audition Rifle, Slam, ClothHit, and RoomTone before calling them a match. There is no footstep asset.",
      "The proof still owed is a physical play of the minute, with the ring, the dodge, a shot, a crawl, both deaths, and audible Rifle and Slam."
    ]
  },
  proof: [
    { name: "Full room", result: "28/28", note: "20261005T091420. Boundaries, extension bounds, clearance, wall walks, twelve camera pairs." },
    { name: "Runtime", result: "48/48", note: "20261005T084751. Four V2 skins, seven clips, moving light, damage-triggered deaths, grounded poses." },
    { name: "Keys", result: "12/12", note: "20261005T080258. Move, dodge, fire, pause, restart. Injected input, not a physical device." },
    { name: "Rear views", result: "3 plates", note: "20261005T092532. Head, shoulder, and weapon readable at x 1000, 1300, and 1400." },
    { name: "Delivery plates", result: "6 views", note: "20261005T092659. Matched, opposite corner, and four architectural views at 1280×720." },
    { name: "Native movie", result: "30 fps", note: "20261005T092830. Isolated QA copy, four-second hold, frames decoded. Not a physical-device test and not an audio match." }
  ],
  open: [
    "Exact visual parity with direction-close-best.jpg. The review still sees finer threads, less varied floor wear, a brighter centre floor, and simpler anatomy.",
    "Physical keyboard, mouse, and gamepad. The key test injected actions.",
    "Audio. The four files have not been auditioned. gameplay-audio.wav never arrived. ClothHit is not played by the feedback script.",
    "Fuzz Color on the cloth material, and a closer crop before any more seam geometry.",
    "An IES profile so the player pool is not only a round cone. No IES file is assigned.",
    "A grey ball in the same camera. The candela numbers were tuned by eye.",
    "The rest of the shell and dressing catalogs, placed without duplicating the 41 kit props or the 45 floor chips.",
    "Packaging and sustained performance."
  ],
  retired: [
    { name: "Low hero camera", why: "The End of Abyss PDF looks up from a low angle and blends to a wider hero shot. The clip and MASTER_PROMPT.md look down. The PDF is not the camera." },
    { name: "FOV 48", why: "Still written in older room notes. The 5 October holds, the combined settings, and the 09:30 status use 54." },
    { name: "Fixed FOV 55 camera", why: "tools/build_encounter_scene.py places a static view at pitch −51. Later notes replaced it. Do not rerun that builder for the camera." },
    { name: "Key at 130000 cd", why: "Look-02. Source radius 30 belongs with it. The hold is 165000 cd and source radius 70." },
    { name: "Pool at 8500 cd", why: "Cones 18° and 48°, offset (160, 0, 95), pitch −62°. Still inside parity-settings.json and the comfy soften function. That file is look-04, not current." },
    { name: "Glowing fog sphere", why: "The combined file still stores far-fog emission and a uniform scale of 2.45. Atmosphere-14 replaced it with an empty fog list and one rect. Do not restore the sphere or the bright bar." },
    { name: "Lifted exposure", why: "The selected still is brighter in the middle than the old grade. Exposure stays +3.8 EV." },
    { name: "Baked teal, pool, or shadow", why: "The pool has to move with aim. Teal is the key, not a texture." },
    { name: "Second wheel or ChamberParity door", why: "A side kit on disk proposes another wheel. The bulkhead already has its locking wheel. That kit is not this plan." },
    { name: "Default Lit cloth", why: "LIVE_BRIEF.md still has an older sentence that says Default Lit. The applied graph sets the Cloth shading model. The 09:30 status confirms Cloth shading." }
  ],
  contradictions: [
    { conflict: "Older pre-production notes say shell and dressing were never imported.", winner: "WORK_STATUS.md at 09:30. 84 instances of 21 meshes are in the level. The full 17 and 36 catalogs are not." },
    { conflict: "The next-gaps draft still treats grounded death and the seven-clip check as open.", winner: "The 09:30 runtime receipt says 48/48, including grounded settled poses. Physical play and audio remain open. The draft is older than the header." },
    { conflict: "Player pool candela is written as about 16000 and as 17500.", winner: "parity-combined-settings.json is the saved intensity: 17500. The cone angles 15° and 26° live only in the prose." },
    { conflict: "Boss speed 125 and 105.", winner: "The study publishes 105. build_boss.py still defaults the variable to 125, and a rerun would put that back." },
    { conflict: "Some notes say the camera looks toward −X.", winner: "The coordinates. The camera sits on −X and looks toward +X, at the far wall." },
    { conflict: "Walk is 48 frames in adaptation.json and 37 in the motion notes.", winner: "ANIMATION.md and motion-refinement.json. The study publishes 37 frames." },
    { conflict: "Attack ring material name.", winner: "Timing agrees at about 0.92 s. The study names M_QA_AttackWarning. build_boss.py assigns M_WarningLamp." }
  ],
  citations: [
    { title: "Material Inputs — Cloth", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/material-inputs-in-unreal-engine/?application_version=5.6", claim: "Opened 5 October 2026. The Cloth shading model adds Fuzz Color and Cloth. Cloth masks the fuzz: 0 leaves the base color, 1 blends fully to the fuzz color." },
    { title: "Spot Lights, Unreal 5.8", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/spot-lights-in-unreal-engine", claim: "Opened 5 October 2026. Inner and outer cones make a disc with a soft penumbra. The same page says Use IES Brightness off keeps the light’s own brightness, and a light function is a separate material." },
    { title: "IES Light Profiles, Unreal 5.8", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/using-ies-light-profiles-in-unreal-engine", claim: "Opened 5 October 2026. An IES profile shapes falloff faster than a light function. On a spot, the cone masks the profile." },
    { title: "Substrate overview, Unreal 5.8", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine", claim: "Opened 5 October 2026. Existing projects stay on the legacy shading models unless Substrate is turned on. This encounter uses the Cloth shading model, not a Substrate conversion." },
    { title: "Clothing Tool, Unreal 5.7", url: "https://docs.unrealengine.com/5.7/en-US/clothing-tool-in-unreal-engine/", claim: "Chaos Cloth is a particle simulation. It is a different system from the Cloth shading model and stays out of this encounter." },
    { title: "Spring Arm", url: "https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/SpringArm", claim: "A spring arm can lag a camera and probe collision. This project does not use the early 2300 cm pawn boom. The near wall is cut away instead." },
    { title: "Cameras in Unreal Engine", url: "https://dev.epicgames.com/documentation/unreal-engine/cameras-in-unreal-engine", claim: "A view target can blend between camera modes. This fight keeps one combat view. It does not blend to the PDF’s low hero camera." },
    { title: "Audio issues across 382 playtests", url: "https://weplaytestgames.com/blog/audio-issues/", claim: "Opened 5 October 2026. Action silence — no footstep, no land, no hit, no confirmation an attack connected — is a repeated playtest failure. Missing sound is missing feedback." },
    { title: "Chapter-scale production notes", url: "https://www.manillagames.com/poppy-playtime-chapter-3/", claim: "A small clip library, driven with blend trees and animation events, is how a chapter fight stays reusable. The slice is done when an internal play holds up in light and audio." },
    { title: "What a vertical slice is for", url: "https://game-developers.org/game-development-vertical-slice", claim: "Visual quality does not stand in for a legible core loop. Deepen the encounter you have before widening the cast." }
  ],
  checks: [
    { id: "cam", desk: "Camera", text: "Four poses checked at pitch −46° and FOV 54" },
    { id: "cut", desk: "Camera", text: "Feet near X −1400 stay visible over the 42–68 cm sill" },
    { id: "glb", desk: "Models", text: "Original GLB hash unchanged" },
    { id: "v2", desk: "Models", text: "TeddyV2 still the only stitch skin" },
    { id: "dup", desk: "Models", text: "No second copy of the 41 kit props or 45 floor chips" },
    { id: "wheel", desk: "Models", text: "No second wheel and no ceiling" },
    { id: "exp", desk: "Air", text: "Exposure still +3.8 EV" },
    { id: "key", desk: "Air", text: "Key still 165000 cd, source radius 70" },
    { id: "pool", desk: "Air", text: "Pool still unbaked, cone not widened to 48°" },
    { id: "fog", desk: "Air", text: "Haze is atmosphere-14, not the fog sphere" },
    { id: "fuzz", desk: "Air", text: "Closer cloth crop taken before more seam mesh" },
    { id: "spd", desk: "Play", text: "Boss speed still the published 105 cm/s" },
    { id: "ring", desk: "Play", text: "Ring, dodge, shot, crawl, and both deaths visible in one minute" },
    { id: "ear", desk: "Play", text: "Rifle, Slam, ClothHit, and RoomTone auditioned" },
    { id: "hands", desk: "Proof", text: "A person played it on a physical keyboard and mouse" }
  ],
  pictures: [
    { src: "../visuals/direction-close-best.jpg", cap: "Selected look. Grade to this still. It is not a capture of the level." },
    { src: "../visuals/parity-expanded-reference.png", cap: "Four-panel concept: matched combat, full chamber, cloth and floor, reverse. Not a screenshot." },
    { src: "../preprod/plan.svg", cap: "303-placement study plan. Centimetres. The level already contains a smaller subset." },
    { src: "../preprod/concept/01-canonical.jpg", cap: "Canonical concept. Later stills that added a roof, a hall, or a fourth creature were rejected." },
    { src: "../preprod/anim-contact.png", cap: "Twenty in-place clips on the existing rig. They are not assigned in the level." }
  ]
};
