# Lighting, camera, and color

5 October 2026. The grade is the selected still [direction-close-best.jpg](../visuals/direction-close-best.jpg). Whole-frame luma there is about 57. Manual exposure stays +3.8 EV. A brighter mean is not a reason to lift exposure.

Teal is the key. It is not a wall color and not a floor puddle. The shadow is the key on the teddy. It is not a baked card. The white pool is the player spot. It is not painted into the concrete.

## Lights

| Actor | Job | Keep |
| --- | --- | --- |
| `TE_Parity_Key` | Cool pool on the upper-middle floor and the long shadow. About (900, 60, 1600), aim (100, 0, −5), color (0.50, 0.94, 1), attenuation 4400, inner 22, outer 40. The hold from look-03 onward is 165000 cd and source radius 70. | Do not put the look-02 trial of 130000 cd and source radius 30 back. Do not add a second key. |
| `ParityPlayerLight` | Near-white ground patch on the aim. The held baseline is relative (105, 0, 170), pitch −80, inner 15, outer 26, about 16000 cd, color (0.94, 0.96, 1), volumetric 0, cast shadows off. | The comfy trial at 8500 cd, cones 18 and 48, offset (160, 0, 95), pitch −62, was the wide disc. Do not widen the cone to 48°. |
| `RedPractical_1` | Pin at (740, −1530, 235), about 180 cd, color (1, 0.034, 0.014). | Short spill. No red floor pool. |
| `RedPractical_2` | Pin at (−920, 1530, 235), same size. | |
| `RedPractical_3` | Pin at (1630, 400, 240), about 160 cd. | The third and last. |
| `TE_Parity_FarFog` | Upper teal haze. Feet stay clear. | Density stays a veil. |
| Older rim, face fill, ambient fill, corner bounce | They were turned down because they lifted the corners. | Leave them down. |

Strip-light meshes stay housings. Their emissive slot stays a slit. They are not a fourth red practical and they are not a row of spots.

## Cameras

These are witness frames for a later capture. They are not a request to recapture while the other session owns the editor. The matched gameplay camera is the one already used: player near (−230, 570, 85), camera near (−1679, 170, 1874), pitch −46, FOV 54, 1280×720.

| Frame | What it has to prove |
| --- | --- |
| Matched combat | Warm boss, three darker stitchlings, long shadow, dark corners, white pool, two or three red pins. |
| Cloth crop | Crown lips and bridges, not a black crack. |
| Floor crop | Branching chips with thickness. Damp darker than dry. No cyan paint. |
| Left pipes | Pipe run, hangers, drip trays. No corridor and no roof. |
| Right cabinets | Cabinets, breaker, shutter, cables. |
| Reverse | The same bulkhead and the low cutaway. The opening is not a hall. |
| Wide | Open air over the fight. Shell instead of the wall boxes. |
| Telegraph | Right arm up, room unchanged. |
| Crawl | Three stitchlings, low, from the right grate. |
| Defeat | Body on the floor, breath only, no get-up. |
| Near cutaway | Sill at 40–70 cm, lanes still open. |
| Far corner | One column, one tank family, the bulkhead wheel still the only wheel. |

## Color across the fight

The centre is the cool key on charcoal concrete. The corners fall off. The pool is a small neutral core on the aim. Cloth is olive under that cool light, not a second grade. Red is three pins. Oxide is the brown of the pipes, muted, not an orange accent. Recesses stay near-black.

## Do not

Do not raise global exposure. Do not bake the pool, the shadow, or the teal. Do not add a ceiling, a truss, or a row of spotlights. Do not paint a cyan puddle to imitate the key.
