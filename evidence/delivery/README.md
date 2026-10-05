# Teddy Encounter review

[Play guide and controls](../../ENCOUNTER.md) · [Offline visual viewer](review.html) · [Gameplay movie](TeddyEncounter-gameplay.mp4)

The saved encounter uses `/Game/Maps/TeddyEncounter` in Unreal 5.8.3. The movie shows approach, independent aim, a dodged strike, damage, moving fire, animated boss defeat, pause/resume and restart. It uses normal saved Blueprint gameplay driven through Enhanced Input; there are no staging teleports, health edits or AI freezes after its initial loading pause.

The movie is **silent** because this offscreen PIE capture route returned empty audio. That empty track is omitted. The ordinary `-game` process separately produced nonzero sound: [native game audio](native-game-audio.wav), a stereo downmix of the preserved master recording. Sound design is proposed original synthesis; source reference audio was not auditioned.

The source recording contains 180 unique captured frames at 1014×550, about 9.2 captures/second, encoded into a 19.83-second 30 fps container using frame duplication. It is actual runtime output, not an animation render or a claim of 30 unique captures/second. Request-time telemetry is contextual, not exact rendered-frame identity.

## Comparison stills

[Reference 5 seconds](comparison-05.png) · [Reference 10 seconds](comparison-10.png) · [Reference 16 seconds](comparison-16.png) · [Gameplay sequence](gameplay-contact-sheet.png)

The references use the recorded upright crop `[76,0,700,384]`; social overlays are covered by explicit rectangles rather than reconstructed. [comparison-method.json](comparison-method.json) records all masks. The game side uses 1280×720 held gameplay plates, resized without changing aspect ratio. NPC movement and the player are staged for composition, the world is paused, and the HUD is hidden only for these plates. Camera/pawn state remains held until CRC validation and full pixel decoding complete. These plates establish a reviewable composition, not physical input or dynamic frame identity. Ordinary `Shot` captures in the gameplay movie retain the HUD and normal rendering.

The main framing error is corrected: an elevated -51-degree view tracks the player/boss pair and widens at greater separation. The pale teddy, small human, crawling threats, cool floor lighting, dark perimeter, red practicals and cyan aim/fire feedback now share the combat composition. A late edge review also corrected foreground clipping and the rifle's reversed hand attachment.

The three largest remaining visual differences are:

1. **Creature surface and anatomy:** the requested teddy substitution is unmistakable, but its cloth and silhouette remain smoother and simpler than the reference's irregular creature. Bulk, welded smoothing, a weighted rig and grounded motion improved the downloaded base; this is not a fidelity-equivalent replacement.
2. **Environment:** the floor has worn texture and hairline cracks, but its slab rhythm and straight containment walls remain more regular than the source's broken, mottled ground. Long-distance camera widening reveals more arena architecture than the source frames.
3. **Motion and effects:** foot-targeted walking/crawling, anticipation, hit response and a grounded fall are present; turning and procedural deformation remain less nuanced than the source. The attack circle is a proposed gameplay aid, brighter and more explicit than anything recoverable from the obscured source HUD.

## Verification

| Evidence | Result and scope |
| --- | --- |
| [Main encounter](../implementation/20261004T222645-verify_encounter/receipt.json) | 15/15 checks: possession, no-input baseline, mapped movement, aiming while moving, attributed fire/damage, dodge, telegraph, defeat, pause and two restarts |
| [Collision and input edges](../implementation/20261004T222258-verify_encounter_edges/receipt.json) | 13/13: wall/dash collision, cursor aiming, rifle direction, invulnerability, actual strike evasion, player defeat/input suppression and restart |
| [Camera bounds](../implementation/20261004T222544-verify_encounter_camera/receipt.json) | 12/12 staged edge/diagonal compositions; conservative player/boss bounds, plus three actual corner screenshots |
| [Held image proof](../implementation/20261004T222718-capture_encounter/receipt.json) | Three fresh 1280×720 PNGs; all CRCs and full pixel decode; held state through completion |
| [Continuous play](../implementation/20261004T222920-record_encounter/receipt.json) | Normal saved encounter, all source PNGs and final MP4 decoded; boss and minions defeated; restart restores 100/300 health |
| [Ordinary game](../implementation/native-20261004T223036/receipt.json) | Saved Blueprints executed under `-game`; native 1280×720 PNG fully decoded before process exit; nonzero audio; clean exit |
| [Preservation](../implementation/preservation-audit.json) | 555/555 archived baseline files unchanged; source video, source ZIP and original GLB hashes unchanged |

The ordinary game's CSV profiler recorded 1,162 frames over about five seconds, following three game seconds of warmup, at **1280×720** on **RTX 5080 / Ryzen 9 9900X**. Median frame time was **4.04 ms**, p95 **6.56 ms**; median GPU time was **3.21 ms**. [Full profile and conditions](../implementation/native-20261004T223036/performance-audio.json). This is a short offscreen Development run with a warm shader cache, not a packaged-build or sustained-performance benchmark. The 1014×550 editor capture timing is not substituted for this measurement.

All controls above are automated action/cursor evidence. Physical-device behavior, gamepad support, exact visual fidelity and user acceptance are unverified. The isolated starter's earlier fire-attribution gap remains preserved; these encounter-specific fire/damage checks are independent. Some earlier editor runs returned 0xC0000005 after normal shutdown logs and completed images; those failures remain recorded. The final results do not establish that the intermittent editor shutdown issue is permanently resolved.

Editable Blender files, FBXs, textures, WAVs and source/license evidence are linked from [ENCOUNTER.md](../../ENCOUNTER.md). No original or baseline was replaced. [manifest.json](manifest.json) records delivery and final owned-asset hashes.
