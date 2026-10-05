# Material, VFX, and audio

5 October 2026. A read for the pre-production set. Nothing here is imported. The four encounter sounds were not opened and were not auditioned. `Assets/Adapted/Audio/provenance.json` records `reference_audio_auditioned: false`.

The gameplay frame is 1280×720, pitch about −46°, FOV 54. The boss is 4.6 m. At that framing a centimetre on the body is about a pixel. Fibre survives only as a clump, not as a drawn thread.

## Material read

Cloth has to stay olive-taupe, with a darker belly, and the stitchlings darker than the boss. The weave target is 2–6 mm fibre and 1–2 cm clumps. The fibre is below the pixel. The clump can survive as albedo and roughness. The matched plate still shows a smooth warm brown body.

The crown seam is two fabric lips, 1–3 cm, and 8–14 thread bridges. Thread is about 1–2 cm thick, each crossing 10–16 cm, interval 8–14 cm. It reads when one lip takes a cool highlight, the gap stays dark, and the bridges break that gap. A single dark stripe fails. The current plate still reads the seam as a crack.

Floor fractures are the six parity meshes. Field A is about 6.3×5.0 m and under 3 cm high. Edge spall belongs at the wall, up to about 10 cm. Micro-chips are about 1 cm and matter in the foreground. The four graphic decals stay retired.

Dry roughness is 0.75–0.95. Damp is 0.40–0.65, darker, with a small moving highlight. It is not a mirror and not a cyan paint.

The player pool is the spot on the player. The held baseline is relative (105, 0, 170), pitch −80°, inner 15°, outer 26°, about 16000 cd, color (0.94, 0.96, 1), no shadows and no volumetric. A wider 48° cone was the round disc. Do not put that cone back. The pool is still smoother than the fractures under it.

Wall families, from the shell surface maps, not from the placed level:

| Family | Mean sRGB | Roughness |
| --- | --- | --- |
| Charcoal concrete | 44, 42, 39 | 0.82–0.95 |
| Worn green-grey steel | 27, 30, 29 | 0.55–0.80 |
| Muted oxide | 54, 31, 24 | 0.65–0.88 |
| Near-black recess | 12, 13, 14 | 0.84–0.92 |

Teal stays in the light. The red point is a light, not a bar. The beacon slit is 4×18 cm.

## VFX

Carriers are the existing key, the player spot, and `AttackRing` on the dim `M_QA_AttackWarning`. No new crack, stain, or debris card. No blood. No hanging dust, because that reads as a ceiling. The rifle flash stays the existing short mesh on `M_Muzzle`, about 0.05 s. Fidelity stills keep the ring hidden.

`AttackRing` is the boss warning, about a 13 cm band near a 475 cm strike, shown for about 0.92 s, then hidden as the strike lands. Stitchling rings use the same material at the smaller world size. Threat, Search, Brace, Idle, and IdleHeavy do not show the ring. Telegraph can fade the ring up. It does not go hotter than the dim QA color.

Foot reads are the contact shadow from the key, about 30 cm under a boss plant and about 12 cm under a stitchling plant. They are not a stamped decal.

## Audio

Files named on disk, none auditioned:

| Name | Seconds recorded in provenance | Rate |
| --- | ---: | ---: |
| `Rifle` | 0.19 | 48000 |
| `Slam` | 0.80 | 48000 |
| `ClothHit` | 0.22 | 48000 |
| `RoomTone` | 16.0 | 48000 |

`tools/make_encounter_audio.py` generated them with seed 74. That is not a listen. The wiring notes in `tools/add_encounter_feedback.py` are the map available without opening the blueprint:

| Beat | Sound | Level noted in that script |
| --- | --- | --- |
| Player shot | `Rifle` | 0.26, with the short muzzle mesh |
| Boss strike | `Slam` | 0.5, when the attack count increments |
| Stitchling strike | `Slam` | 0.18 |
| Camera bed | `RoomTone` | 0.5, looping |

`ClothHit` is imported in that script. A `PlaySound` on Hit, HitLeft, Stagger, and StitchlingFlinch is the mapping for this sheet. It is not a claim that the saved blueprint already plays it. There is no footstep file. `gameplay-audio.wav` never arrived from the record pass. It is not a design cue.

Idle, Walk, Crawl, the turns, the steps, Threat, Search, WeightShift, WalkStop, Brace, Recover, Defeat, and DefeatBreath stay on `RoomTone` alone. DefeatBreath does not add a breath file.

## If a concept still is treated as a capture

The rejected frames in [concept/rejected/](concept/rejected/) add a roof, a hall, a fourth small creature, button eyes, or painted cyan. Those are not materials, not lights, and not a new creature. The accepted cloth crop is the seam target. The gameplay plate is still the one that has to show the bridges.
