# Local haze QA — 5 October 2026

Judged pair: `evidence/implementation/20261005T133413-capture_chamber_views`. Native 1920×1280, exposure bias still 3.8, vignette 0.38, bloom 0.25. Gameplay hold remains pitch −46° / FOV 54. This is not visual acceptance. Simulated input is not physical-device play.

## What changed

The existing downward fog light `TE_Parity_FarFog_Light` stayed a surface-dark rect (diffuse 0, specular 0). It moved from about (900, −100, 650) at 150,000 cd and scattering 4 to (80, 40, 1750), 120,000 cd, 2800×2800 cm, scattering 7. No new fog volume, sphere, or bar was added.

`TE_LowMist` density went from 0.017 to 0.010 and height falloff from 2.0 to 0.42. Extinction scale went from 1.0 to 0.85. Inscattering stayed about (0.004, 0.012, 0.010).

The combat-floor return dropped from 55,000 cd / outer cone 56° to 14,000 cd / outer cone 36°. Side wall washes dropped from 16,000 and 15,000 cd to 11,000 and 10,500 cd and aim at the wall services. The morphology sheet stays off the environment light channel, so those washes do not repaint the combat floor. The reverse-wall spot on the cutaway moved up to relative z 1180 and to 9,000 cd, scattering 3.5. Characters, key intensity, camera, and exposure were not edited.

## Trials

The first editor launch did not save. It stopped on a missing `volumetric_fog` property after reading the original fog values.

`20261005T133030-capture_chamber_views` is the rejected middle look. Scattering 10 at the old low position left the reverse ceiling black and the service walls too dark. That pair is evidence of the miss, not the saved result.

## Judged read

Both directions are less evenly washed than `20261005T131840`. The player pool is a tighter white disc. The front still has a teal shaft on the B-3 door, and the right-hand tanks and fan are readable again. The reverse upper frame is a dark teal gradient instead of a hard black void, and the side cabinets and pipe run are easier to separate from the wall.

The hanging mist is still weaker and more local than either concept. The two service bays stay dark inside. Red points are not balanced: the side fixtures read as tall bars, while the door pins stay small. Floor breaks are still sparse and shallow, and the older floor still shows outside the sheet. Passing 31/31 and 28/28 does not establish parity.

## Audits on the judged save

- `20261005T133117-verify_chamber_runtime` also passed 31/31, but it audited the rejected middle save. It is not the judged look.
- Chamber: `20261005T133512-verify_chamber_runtime`, 31/31, on the judged save.
- Room: `20261005T133546-verify_full_room`, 28/28. Walk trace still hits `TE_ArenaFloor` at about Z −5. Spawns and the four combat bounds are unchanged.
