# Real bear: an example scan

A real teddy bear scanned with a phone (22 photos, one eye-level lap) and built by the
current pipeline. Use it to try scanned bears in a game before you've scanned your own.

| File | What it is |
|---|---|
| `model.glb` | The model (1.4 MB). Nodes `LOD0` (8,000 triangles), `LOD1` (2,500), `LOD2` (800), smooth normals, one 2048 JPEG texture |
| `collider.json` | Convex hull for physics: `{ vertices: [[x,y,z]...], faces: [[a,b,c]...] }` |
| `report.json` | The 14 quality checks for this scan |
| `viewer.html` | One self-contained page: orbit it, cut it open, see the checks (open it straight from disk) |
| `index.html` | A small three.js scene loading it the way a game would (needs a web server, below) |
| `thumb.webp` | Cut-out thumbnail |

## Try it

From the repo folder:

```powershell
uv run python -m http.server 8000 --directory web
```

Then open <http://localhost:8000/examples/real-bear/>. (If the scanner is running, it's also
at `https://localhost:8443/examples/real-bear/`.) Toggle **Colour by LOD** and orbit away to
watch the detail levels switch; **Show collider** shows the physics hull.

## Use it in a game

Every scanned bear follows the same rules: meters, +Y up, the front faces +Z, feet on
y = 0, centred on x = z = 0.

```js
import { loadScannedBear, loadBearCollider } from './bearLoader.js';  // web/js/bearLoader.js

const bear = await loadScannedBear('real-bear.glb');            // a THREE.LOD inside a Group
bear.position.set(1, 0, -2);
scene.add(bear);                                                // levels switch by distance

const hull = await loadBearCollider('real-bear-collider.json');
// Rapier:     RAPIER.ColliderDesc.convexHull(new Float32Array(hull.vertices.flat()))
// cannon-es:  new CANNON.ConvexPolyhedron({ vertices: hull.vertices.map(v => new CANNON.Vec3(...v)), faces: hull.faces })
```

## Use it in Unreal Engine 5

In the UE editor run **Tools > Execute Python Script...** with `unreal/import_bears.py`
from this repo, after setting `SOURCE` at its top to this folder's `model.glb`. You get
`/Game/ScannedBears/real_bear/SM_Bear_real_bear`: one Static Mesh with LOD0-2, convex collision
and the texture, 9.7 units (cm) tall, pivot under the box. Details and caveats are in the
main README, "Unreal Engine 5".

Other engines (Unity, Godot, Blender, Babylon): load `model.glb` with any glTF loader and
use the `LOD0` node, or set up LODs from the three nodes.

## Know before you use it

- **The box is part of it.** The bear sat on a box while being scanned, and anything touching
  the bear becomes part of the model.
- **It's small: 9.7 cm tall**, its real size (the height entered while scanning was 10 cm).
  Scale it up as you like: `bear.scale.setScalar(3)`. The LODs follow the scale.
- **Quality: warnings, no failures.** This capture had no lap from above, so the top of the
  head is partly guessed (13% of the surface filled in), and the room's lighting swung
  between photos. A scan with the two guided laps comes out cleaner; see `report.json` or
  open `viewer.html` → Checks.
