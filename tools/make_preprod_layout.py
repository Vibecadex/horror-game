"""Measured pre-production layout. Writes study files only. Does not open Unreal."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "study" / "preprod"
FLOOR = ROOT / "Assets" / "Adapted" / "Parity" / "Floor" / "manifest.json"

items = []


def add(mesh, x, y, z, yaw=0, scale=None, kind="dressing", note=""):
    scale = [1, 1, 1] if scale is None else list(scale)
    items.append({
        "mesh": mesh,
        "location_cm": [round(x, 1), round(y, 1), round(z, 1)],
        "yaw": yaw,
        "scale": scale,
        "kind": kind,
        "collision": False,
        "note": note,
    })


# Shell joints. Far centre X=1720, interior face X=1660.
# One 200 cm bay plus eight 400 cm bays cover Y -1700..1700.
# Side bays cover X -1540..1660. Yaw 0 faces +Y, yaw 90 faces -X, yaw 180 faces -Y.
Z = -5
far_y = [-1300, -900, -500, -100, 300, 700, 1100, 1500]
side_x = [-1340, -940, -540, -140, 260, 660, 1060, 1460]
add("SM_ShellWallBayNarrow", 1720, -1600, Z, 90, kind="shell", note="Far wall, Y -1700..-1500.")
for y in far_y:
    add("SM_ShellWallBay", 1720, y, Z, 90, kind="shell", note="Replaces FarWall. Hide the box.")
for x in side_x:
    add("SM_ShellWallBay", x, -1740, Z, 0, kind="shell", note="Left wall, X -1540..1660. Hide SideWall_-1.")
    add("SM_ShellWallBay", x, 1740, Z, 180, kind="shell", note="Right wall. Hide SideWall_1.")

for y in far_y:
    add("SM_ShellCornice", 1630, y, 760, 90, kind="shell", note="Seat at Z=760. Brackets hang below.")
for x in side_x:
    add("SM_ShellCornice", x, 1645, 760, 0, kind="shell")
    add("SM_ShellCornice", x, -1645, 760, 180, kind="shell")

for y in [-1200, -400, 400, 1200]:
    add("SM_ShellFoundation", 1570, y, Z, 90, kind="shell")
    add("SM_ShellGutter", 1560, y, Z, 90, kind="shell")
for x in [-1200, -400, 400, 1200]:
    add("SM_ShellFoundation", x, 1575, Z, 0, kind="shell")
    add("SM_ShellFoundation", x, -1575, Z, 180, kind="shell")
    add("SM_ShellGutter", x, 1550, Z, 0, kind="shell")
    add("SM_ShellGutter", x, -1550, Z, 180, kind="shell")

for y in [-1270, -640, 0, 640, 1220]:
    add("SM_ShellCutawaySill", -1530, y, Z, 90, kind="shell", note="Foreground curb, 42–68 cm, with gaps.")
add("SM_ShellCutawayReturn", -1540, -1680, Z, 0, kind="shell", note="Near corner pier.")
add("SM_ShellCutawayReturn", -1540, 1680, Z, 180, kind="shell", note="Near corner pier.")

for y in [-900, 900]:
    add("SM_ShellRearInset", 1651, y, 340, 90, kind="shell")
add("SM_ShellShutterNiche", 200, 1688, 180, 180, kind="shell", note="Right wall only.")
for x in [-1000, -500, 0, 500, 1000]:
    add("SM_ShellPipeStandoff", x, -1620, 461, 0, kind="shell", note="Under the left pipe run.")
add("SM_ShellBeaconHousing", 740, -1530, 188, 0, kind="shell", note="Red practical 1. The light is separate.")
add("SM_ShellBeaconHousing", -920, 1530, 188, 180, kind="shell", note="Red practical 2.")
add("SM_ShellBeaconHousing", 1630, 400, 200, 90, kind="shell", note="Red practical 3. Pin, not a bar.")
add("SM_ShellCornerRiser", 1600, -1620, Z, 0, kind="shell", note="Far-left corner. Elbow points outside. No valve.")
add("SM_ShellCornerRiser", 1600, 1620, Z, 180, kind="shell", note="Far-right corner. No valve.")
add("SM_ShellUtilityCurb", 1500, 200, Z, 90, kind="shell")
for x in [-800, 200, 1100]:
    add("SM_ShellUpperBracket", x, 1600, 640, 180, kind="shell", note="Arm only. No lamp and no span.")
for x in [-600, 100, 800]:
    add("SM_ShellCableTray", x, 1660, 520, 180, kind="shell", note="Right wall.")
add("SM_ShellDarkBacking", 1900, 0, 300, 90, kind="shell", note="Outside the far wall.")
add("SM_ShellDarkBacking", 90, -1900, 300, 0, kind="shell", note="Outside the left wall.")
add("SM_ShellDarkBacking", 90, 1900, 300, 180, kind="shell", note="Outside the right wall.")
for x, y in [(-1800, -1800), (1800, -1800), (-1800, 1800), (1800, 1800)]:
    add("SM_ShellOuterApron", x, y, Z, 0, kind="shell", note="Dark ground outside the shell.")

# Kit already used by tools/build_full_room.py. Keep these. Do not add a second family.
kit = [
    ("SM_RoomBulkhead", 1630, 180, 62, 90, "Already has the locking wheel."),
    ("SM_RoomPilaster", 1635, -1360, -5, 90, "Far wall."),
    ("SM_RoomPilaster", 1635, -780, -5, 90, "Far wall."),
    ("SM_RoomPilaster", 1635, 780, -5, 90, "Far wall."),
    ("SM_RoomPilaster", 1635, 1380, -5, 90, "Far wall."),
    ("SM_RoomVentFan", 1612, -1100, 365, 90, "Far wall, static."),
    ("SM_RoomUtilityTank", 1570, 1080, 62, 90, "Same tank family. One on the far wall."),
    ("SM_RoomVentFan", -20, -1630, 275, 0, "Left wall."),
    ("SM_RoomServiceCabinet", -770, 1580, 62, 180, "Right wall."),
    ("SM_RoomServiceCabinet", -545, 1580, 62, 180, "Right wall."),
    ("SM_RoomUtilityTank", 970, 1555, 62, 180, "Same tank family. Right wall."),
    ("SM_RoomPipeRack", 890, 1550, 470, 180, "One run on the right. The valve stays on the left racks."),
    ("SM_RoomVentFan", 225, 1630, 340, 180, "Right wall."),
    ("SM_RoomCargoCrate", -825, -1565, 65, 5, "Peripheral. Same crate family."),
    ("SM_RoomCableSpool", -50, 1580, 65, 0, "Right wall, low."),
    ("SM_RoomCargoCrate", 1530, -585, 65, -90, "Same crate family. Far edge."),
    ("SM_RoomStripLight", 1630, -620, 545, 90, "Housing. Emissive stays a slit."),
    ("SM_RoomStripLight", 1630, 720, 545, 90, "Housing. Emissive stays a slit."),
]
for mesh, x, y, z, yaw, note in kit:
    add(mesh, x, y, z, yaw, kind="kit", note=note)
for x in [-1180, -460, 420, 1350]:
    add("SM_RoomPilaster", x, -1650, -5, 0, kind="kit", note="Left wall.")
for x in [-1150, -120, 680, 1360]:
    add("SM_RoomPilaster", x, 1650, -5, 180, kind="kit", note="Right wall.")
for x in [-1000, -500, 0, 500, 1000]:
    add("SM_RoomPipeRack", x, -1550, 460, 0, kind="kit", note="Left wall. Valve is on this mesh.")
for sign in (-1, 1):
    for x in [-1070, -550, -10, 550, 1090]:
        add("SM_RoomFloorGrate", x, sign * 1548, -5, 0, [1, 0.85, 0.7], "kit", "Discontinuous. Not a stripe across the fight.")

# Dressing. Repeat with gaps. Stay outside the combat rectangle.
panels_left = [-1300, -700, 100, 900]
for x in panels_left:
    add("SM_DressPanel", x, -1665, 160, 0, kind="dressing", note="Left wall tile.")
    add("SM_DressRib", x + 130, -1672, 160, 0, kind="dressing")
for x in [-1250, -350, 550, 1250]:
    add("SM_DressPanel", x, 1665, 160, 180, kind="dressing", note="Right wall tile.")
    add("SM_DressPanelNarrow", x + 180, 1668, 200, 180, kind="dressing")
add("SM_DressPanelTall", 1500, 1660, 240, 180, kind="dressing", note="Right wall, clear of the shutter.")
for x in [-1100, -200, 700]:
    add("SM_DressRepairPlate", x, 1672, 280, 180, kind="dressing")
    add("SM_DressWallSpall", x, -1670, 90, 0, kind="dressing")
for i, x in enumerate([-800, -200, 400, 1000, 1500]):
    add("SM_DressConduitStraight", x, 1635, 430, 180, kind="dressing", note="Right wall power.")
    add("SM_DressUnistrut", x, 1648, 455, 180, kind="dressing")
add("SM_DressConduitElbow", -1450, 1635, 430, 180, kind="dressing")
add("SM_DressConduitElbow", 1550, 1635, 430, 180, kind="dressing")
add("SM_DressConduitTee", 200, 1638, 430, 180, kind="dressing")
add("SM_DressConduitTee", 900, 1638, 430, 180, kind="dressing")
for x, z in [(-1000, 360), (100, 390), (1200, 350)]:
    add("SM_DressJunctionBox", x, 1642, z, 180, kind="dressing")
for x in [-900, -100, 600, 1300]:
    add("SM_DressCableLoop", x, 1628, 300, 180, kind="dressing")
for x in [-700, 300, 1100]:
    add("SM_DressCableDrop", x, 1610, 220, 180, kind="dressing")
add("SM_DressBreaker", 480, 1605, 150, 180, kind="dressing", note="Right wall only.")
for x in [-1100, -200, 700, 1400]:
    add("SM_DressGangBox", x, 1612, 145, 180, kind="dressing")
for x in [-400, 800]:
    add("SM_DressBundle", x, 1655, 480, 180, kind="dressing")
add("SM_DressLouver", 1450, 1615, 260, 180, kind="dressing")
add("SM_DressLouver", -200, 1615, 240, 180, kind="dressing")
add("SM_DressHatch", 1100, 1648, 180, 180, kind="dressing", note="Dogs are handles. Not a wheel.")
add("SM_DressHoseCoil", -1350, 1595, 40, 200, kind="dressing")
add("SM_DressDuctBoot", 200, 1608, 40, 180, kind="dressing")

for x in [-1000, -500, 0, 500, 1000]:
    add("SM_DressPipeHanger", x, -1588, 390, 0, kind="dressing", note="Left wall pipes.")
    add("SM_DressClamp", x - 40, -1572, 460, 0, kind="dressing")
for x in [-750, -250, 250, 750]:
    add("SM_DressFlangeJoint", x, -1555, 460, 0, kind="dressing")
add("SM_DressPipeElbow", -1450, -1560, 460, 0, kind="dressing")
add("SM_DressPipeElbow", 1450, -1560, 460, 0, kind="dressing")
for x in [-1000, 0, 1000]:
    add("SM_DressDripTray", x, -1520, -5, 0, kind="dressing", note="Under the left pipes. Outside the footprint.")
add("SM_DressMeter", -1350, -1605, 150, 0, kind="dressing")
add("SM_DressDownspout", 1400, -1610, 80, 0, kind="dressing")
add("SM_DressHeader", 1635, 180, 520, 90, kind="dressing", note="Over the bulkhead. Not a sign.")
for y in [-600, -200, 500, 1100]:
    add("SM_DressRepairPlate", 1668, y, 260, 90, kind="dressing")
add("SM_DressColumn", 1580, -1620, Z, 15, kind="dressing", note="Far corner only.")
for x, y, yaw in [(-1600, -1600, 45), (1600, -1600, -45), (-1600, 1600, 135), (1600, 1600, -135)]:
    add("SM_DressCornerGuard", x, y, 40, yaw, kind="dressing")
    add("SM_DressCornerGuard", x, y, 180, yaw, kind="dressing")
for x, y in [(-1200, -1525), (1200, -1525), (-1200, 1525), (800, 1525)]:
    add("SM_DressDrainBox", x, y, -5, 10, kind="dressing")
    add("SM_DressAnchor", x + 70, y, -5, 0, kind="dressing")
add("SM_DressThreshold", -1535, -800, -5, 90, kind="dressing")
add("SM_DressThreshold", -1535, 700, -5, 90, kind="dressing")
for y in [-1100, -200, 500, 1300]:
    add("SM_DressKicker", -1488, y, -5, 90, kind="dressing", note="At the cutaway, outside the lanes.")
for y in [-400, 800]:
    add("SM_DressEscutcheon", 1670, y, 120, 90, kind="dressing")

floor_doc = json.loads(FLOOR.read_text(encoding="utf-8"))
for entry in floor_doc["recommended_placements"]:
    loc = entry["location_cm"]
    add(
        entry["mesh"], loc[0], loc[1], -5, entry.get("yaw", 0),
        entry.get("scale", [1, 1, 1]), "floor",
        "From the floor manifest. Do not regenerate the FBX.",
    )

COMBAT_X = 1480
COMBAT_Y = 1500
inside = []
for item in items:
    x, y, _z = item["location_cm"]
    if item["kind"] == "floor":
        continue
    if abs(x) <= COMBAT_X and abs(y) <= COMBAT_Y:
        inside.append(item)
if inside:
    raise SystemExit("Combat footprint blocked: " + json.dumps(inside[:5]))

forbidden_names = ("ceiling", "truss", "wheel", "barrel", "sign")
for item in items:
    low = item["mesh"].lower()
    if any(word in low for word in forbidden_names):
        raise SystemExit("Forbidden mesh name: " + item["mesh"])

lights = [
    {"name": "TE_Parity_Key", "location_cm": [900, 60, 1600], "aim_cm": [100, 0, -5],
     "intensity_cd": 165000, "source_radius_cm": 70, "color": [0.50, 0.94, 1.0],
     "note": "Hold from look-03. Do not restore 130000 cd or source radius 30. Do not bake the shadow."},
    {"name": "ParityPlayerLight", "relative_cm": [105, 0, 170], "intensity_cd": 16000,
     "pitch": -80, "inner_deg": 15, "outer_deg": 26, "color": [0.94, 0.96, 1.0],
     "note": "Held baseline. Do not widen the cone to 48. Not a floor texture."},
    {"name": "RedPractical_1", "location_cm": [740, -1530, 235], "color": [1.0, 0.034, 0.014],
     "intensity_cd": 180, "note": "Pin. No red floor pool."},
    {"name": "RedPractical_2", "location_cm": [-920, 1530, 235], "color": [1.0, 0.034, 0.014],
     "intensity_cd": 180, "note": "Pin."},
    {"name": "RedPractical_3", "location_cm": [1630, 400, 240], "color": [1.0, 0.034, 0.014],
     "intensity_cd": 160, "note": "Third pin, on the far wall. Stop at three."},
]

beats = [
    {"t": "Enter", "where": "Cutaway, X about -1400", "clips": ["IdleHeavy", "WeightShift"],
     "note": "Player comes in over the low sill. Boss holds."},
    {"t": "Notice", "where": "Boss stays in the centre", "clips": ["Search", "Threat"],
     "note": "Head scan, then both arms open. In place."},
    {"t": "Strike", "where": "Boss, then the other arm", "clips": ["Telegraph", "Attack", "AttackLeft", "Recover"],
     "note": "Telegraph holds the raised arm. Recover returns to idle."},
    {"t": "Hit", "where": "Boss", "clips": ["Hit", "HitLeft", "Stagger", "Brace", "Slump"],
     "note": "Directional hits. Brace is both arms in. Slump settles."},
    {"t": "Minions", "where": "Right grate, +Y, outside the lanes", "clips": ["Crawl", "StitchlingIdle", "SwipeLow", "StitchlingFlinch"],
     "note": "Three only, scale 0.35. They enter from the cabinet side."},
    {"t": "Move", "where": "Inside X -1400..1480, Y -1500..1500", "clips": ["Walk", "WalkStop", "TurnLeft", "TurnRight", "StepLeft", "StepRight"],
     "note": "The blueprint moves the actor. These clips stay in place. Walk is 105 cm/s."},
    {"t": "Down", "where": "On the floor", "clips": ["Defeat", "DefeatBreath"],
     "note": "Breath holds the last defeat frame. No get-up."},
]

def zone_of(x, y):
    ax, ay = abs(x) <= 1480, abs(y) <= 1500
    if ax and ay:
        return "arena"
    if x < -1400 and y < -1500:
        return "corner near left"
    if x < -1400 and y > 1500:
        return "corner near right"
    if x > 1480 and y < -1500:
        return "corner far left"
    if x > 1480 and y > 1500:
        return "corner far right"
    if y < -1500:
        return "left pipe run"
    if y > 1500:
        return "right electrical bay"
    if x > 1480:
        return "far bulkhead apron"
    return "near cutaway"


for index, item in enumerate(items, start=1):
    x, y, z = item["location_cm"]
    item["id"] = f"p{index:03d}"
    item["x"] = x
    item["y"] = y
    item["z"] = z
    item["zone"] = zone_of(x, y)

lanes = [
    {"name": "near approach", "x": [-1400, -500], "y": [-40, 240], "width_cm": 280},
    {"name": "pipe orbit", "x": [-1100, 1200], "y": [-1180, -960], "width_cm": 220},
    {"name": "far approach", "x": [860, 1080], "y": [-900, 1000], "width_cm": 220},
    {"name": "power orbit", "x": [-900, 1100], "y": [700, 920], "width_cm": 220},
]
actors = [
    {"name": "TE_PlayerStart", "location_cm": [-230, 570, 95],
     "note": "Spawn in build_encounter_scene.py. The matched plate stood near Z 85."},
    {"name": "TE_MainTeddy", "location_cm": [250, -230, 232],
     "note": "Spawn in build_encounter_scene.py. Health 300."},
    {"name": "TE_Stitchling_1", "location_cm": [650, 600, 65], "scale": 0.35,
     "note": "Spawn in build_stitchlings.py. Health 24."},
    {"name": "TE_Stitchling_2", "location_cm": [-480, -500, 65], "scale": 0.35,
     "note": "Same family. North of the pipe orbit."},
    {"name": "TE_Stitchling_3", "location_cm": [20, 1070, 65], "scale": 0.35,
     "note": "Same family. North of the power orbit."},
]

by_kind = {}
for item in items:
    by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1

layout = {
    "owner": "teddy-preprod-layout-20261005",
    "units": "cm",
    "up": "+Z",
    "far": "+X",
    "combat_footprint_cm": {"x": [-1400, 1480], "y": [-1500, 1500]},
    "not_imported": True,
    "counts": {"total": len(items), **by_kind, "lights": len(lights)},
    "lights": lights,
    "lanes": lanes,
    "actors": actors,
    "beats": beats,
    "placements": items,
    "rules": [
        "Hide the wall box when its shell bay is in. Do not stack them.",
        "No second collision shell.",
        "No ceiling, truss, second wheel, second tank family, or fourth creature.",
        "Left wall is pipes. Right wall is cabinets.",
        "Floor meshes come from the existing manifest.",
    ],
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "layout.json").write_text(json.dumps(layout, indent=2) + "\n", encoding="utf-8")

# Plan in centimetres. +X to the right, +Y up. Labels stay upright.
colors = {
    "shell": "#8a8478",
    "kit": "#6e8f86",
    "dressing": "#c4a574",
    "floor": "#5c6b73",
}
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1100" viewBox="-3200 -3200 6400 6400">',
    '<rect x="-3200" y="-3200" width="6400" height="6400" fill="#14181b"/>',
    '<g transform="scale(1,-1)">',
    '<rect x="-1400" y="-1500" width="2880" height="3000" fill="#1d2830" stroke="#9fd6d2" stroke-width="12" stroke-dasharray="40 24"/>',
]
for lane in lanes:
    x0, x1 = lane["x"]
    y0, y1 = lane["y"]
    parts.append(
        f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="none" '
        'stroke="#d7c4a3" stroke-width="8" stroke-dasharray="28 18"/>'
    )
for item in items:
    x, y, _z = item["location_cm"]
    r = 28 if item["kind"] != "floor" else 16
    parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{colors[item["kind"]]}"/>')
for actor, color in (
    (actors[0], "#f4f1ea"),
    (actors[1], "#c46a4a"),
    (actors[2], "#8a5a42"),
    (actors[3], "#8a5a42"),
    (actors[4], "#8a5a42"),
):
    x, y, _z = actor["location_cm"]
    parts.append(f'<circle cx="{x}" cy="{y}" r="36" fill="{color}"/>')
parts.append("</g>")
parts.append('<g font-family="Segoe UI, sans-serif" fill="#f2efe6" font-size="150" text-anchor="middle">')
for x, y, label in ((0, 0, "ARENA"), (0, -2300, "PIPES"), (0, 2300, "POWER"), (2500, 0, "BULKHEAD"), (-2500, 0, "CUTAWAY")):
    parts.append(f'<text x="{x}" y="{-y}">{label}</text>')
parts.append('<text x="-3000" y="-3000" font-size="90" text-anchor="start">Centimetres. +X right, +Y up. Not imported.</text>')
parts.append("</g></svg>")
(OUT / "plan.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")

lines = [
    "# Level design",
    "",
    "5 October 2026. Measured plan for the same chamber. Nothing here is placed in the level. The scene agent owns the editor. Coordinates are centimetres. +X is far, +Z is up.",
    "",
    f"Placements: **{len(items)}**. Shell {by_kind.get('shell', 0)}, kit {by_kind.get('kit', 0)}, dressing {by_kind.get('dressing', 0)}, floor {by_kind.get('floor', 0)}. Lights: {len(lights)}. The drawing is [plan.svg](plan.svg). The records are [layout.json](layout.json).",
    "",
    "## Footprint",
    "",
    "Combat stays inside X −1400..1480 and Y −1500..1500. The generator refuses a shell, kit, or dressing point inside that rectangle. Floor chips are the exception, and they are the ones already listed in `Assets/Adapted/Parity/Floor/manifest.json`. Dense piles stay off the lanes. Z scale on those chips stays 1. Place them at Z −5.",
    "",
    "The near edge is the cutaway, five `SM_ShellCutawaySill` pieces at X −1530 plus two return piers. That sill is 42–68 cm tall. It is not a wall and not a corridor.",
    "",
    "The far wall is one narrow bay at Y −1600 and eight 400 cm bays from Y −1300 to 1500, all at X 1720, yaw 90. That run covers Y −1700 to 1700 and puts the interior face on X 1660. Hide `FarWall` when they go in. Each side wall is eight bays at X −1340, −940, −540, −140, 260, 660, 1060, and 1460, so the run meets X −1540 and X 1660. Left centre is Y −1740, yaw 0. Right centre is Y 1740, yaw 180. Yaw 0 faces +Y, yaw 90 faces −X, yaw 180 faces −Y. Hide both `SideWall` boxes. Do not give the shell a collision volume. Confirm the imported front on one bay before repeating it.",
    "",
    "## Sides",
    "",
    "Left is −Y, pipes. Five `SM_RoomPipeRack` stay at Y −1550. Hangers, flanges, two elbows, three drip trays, the meter, and the downspout cluster under that run. The rack already has the valve. There is no second wheel.",
    "",
    "Right is +Y, cabinets and power. The two service cabinets, the shutter niche, the breaker, gang boxes, conduits, and the cable tray stay on this side. One tank here and one tank on the far wall are the same family. Stitchlings enter from this grate side. There are three of them.",
    "",
    "The bulkhead stays at (1630, 180, 62), yaw 90, with its own locking wheel. A header dresses the top of the door. It is not a sign. One column sits in the far-left corner only.",
    "",
    "## Light",
    "",
    "Three red practicals. The pipe pin is (740, −1530, 235) at 180 cd. The power pin is (−920, 1530, 235) at 180 cd. The bulkhead pin is (1630, 400, 240) at 160 cd. A 300 cm and a 240 cm limit keep those spills off the lanes. The key hold is 165000 cd with source radius 70. The player spot hold is relative (105, 0, 170), pitch −80, inner 15, outer 26, about 16000 cd. Corner bounce lights stay turned down. Nothing in this plan is a ceiling, a truss, or a row of spots.",
    "",
    "## Beats",
    "",
    "| Beat | Where | Clips |",
    "| --- | --- | --- |",
]
for beat in beats:
    lines.append(f"| {beat['t']} | {beat['where']} | {', '.join(beat['clips'])} |")
lines += [
    "",
    "Walk speed stays 105 cm/s for the boss and about 55 cm/s for a stitchling crawl. Turns and steps do not move the root. Defeat breath does not stand the teddy up.",
    "",
    "## Circulation",
    "",
    "The saved spawns stay. Player start is (−230, 570, 95). The matched plate stood near Z 85. The boss is (250, −230, 232), health 300. The three stitchlings are (650, 600, 65), (−480, −500, 65), and (20, 1070, 65), scale 0.35, health 24. Movement stays WASD relative to the view, mouse aim, left button fire, Space dodge.",
    "",
    "Four lanes stay open. The near approach is X −1400..−500 and Y −40..240, 280 cm wide. The pipe orbit is X −1100..1200 and Y −1180..−960, 220 cm wide. The far approach is X 860..1080 and Y −900..1000, 220 cm wide. The power orbit is X −900..1100 and Y 700..920, 220 cm wide. Solid centres stay outside the combat rectangle. The centre between the lanes stays walkable.",
    "",
    "## Camera",
    "",
    "Pitch stays −46 and FOV stays 54. Height is clamp(max(1.8|dx|, |dy|) + 850, 1700, 5600). The look point is the midpoint shifted toward −X by 0.07|dx|, at Z 160. The camera stays on the −X side of the fight.",
    "",
    "Start, with the saved pair, is camera (−1679, 170, 1874), look (−24, 170, 160). Wide, at a separation the rig already allows, is camera (−5522, 0, 5690) when the player is (−1300, −1400) and the boss is (1300, 1400). Far edge, player (1300, 80), is camera (−1945, −75, 2900). Reverse, player (1100, −80), is camera (−1683, −155, 2540), still looking toward +X. At the tall pose a sightline to feet at X −1400 crosses the cutaway near Z 190. The 42–68 cm sill leaves that body visible.",
    "",
    "## One minute",
    "",
    "Boss health stays 300. Player health stays 100. Each stitchling stays at 24 and drops when the boss drops.",
    "",
    "At 0:00 the frame is the start pose. By 0:12 the player is in the near approach and turning onto the pipe orbit. By 0:28 the player is in that 220 cm lane and dodges the existing slam warning. By 0:42 the player takes the far approach. The door stays shut. By 0:55 the player is on the power orbit. Cabinets, the shutter, and the tank on that wall read. The sill stays low. The centre overhead stays open.",
    "",
    "## When this is allowed into the level",
    "",
    "One writer. Import shell and dressing only after the other session has released the map. Hide the box a mesh replaces. Save, reopen, and look at the matched camera before judging the room. This document is not that capture.",
    "",
]
(OUT / "LEVEL_DESIGN.md").write_text("\n".join(lines), encoding="utf-8")
print("LAYOUT", len(items), by_kind)
