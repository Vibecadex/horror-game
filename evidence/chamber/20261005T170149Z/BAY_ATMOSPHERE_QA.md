# Bay, red practicals, and overhead — 5 October 2026

The visible floor is still FloorRecoveryV4. Exposure bias stays 3.8. Gameplay camera stays pitch −46° and FOV 54. The original kit FBX `Assets/Adapted/ChamberParity/SM_ChamberServiceDoorBay.fbx` is unchanged (`02394c41440c7016c073fa760f2c8a9936fd01ebdeb8272894b8e057b4592a56`). The open recess is a separate export in `Assets/Adapted/ChamberParity/BayDepth`, imported onto the existing mesh path.

## What changed

The solid bay leaf is gone. The frame, a dark back wall, and one drum stay inside the existing 77 cm reveal. The shell face at about X −1610 blocks a deeper corridor. Two warm spots, `TE_Chamber_BayDepthL` and `TE_Chamber_BayDepthR`, light those openings on the environment channel only.

The side lenses `TE_Room_BeaconLens_0` and `_1` went from scales (0.05, 0.17, 0.52) to (0.09, 0.09, 0.11). Their point lights dropped to 35 cd and a 90 cm radius. In the front frame, the tall red clusters shrank from about 13×24 and 18×27 pixels to 6×6 and 7×6. The door pins stayed about 4×10.

The overhead rect moved from Z 1750, 2800×2800 cm, to Z 1100, 1400×900 cm, 100,000 cd, scattering 14, diffuse and specular 0. Height fog is density 0.012, falloff 0.35, extinction 0.70. Volumetric fog distance is 12,000 cm.

## Measured change from the 16:37 pair

| Region | 16:37 | 17:03 |
| --- | ---: | ---: |
| Reverse bay openings, mean Y | 22.4 and 19.5 | 56.7 and 54.4 |
| Front air above the floor, mean Y | 27.0 | 57.4 |
| Front floor, mean Y | 81.4 | 85.9 |
| Reverse floor, mean Y | 97.4 | 109.2 |
| Front void above the walls, mean Y | 19.1 | 15.4 |

The openings are brighter and warmer. The room air carries more teal. The void above the walls did not become a luminous bar. The floor lift is small and exposure was not raised.

## Evidence

| Evidence | Result |
| --- | --- |
| Before | [16:37 views](../../implementation/20261005T163731-capture_chamber_views/receipt.json) |
| After | [17:03 views](../../implementation/20261005T170326-capture_chamber_views/receipt.json). Native 1920×1280. Exposure 3.8. |
| Chamber | [17:05](../../implementation/20261005T170523-verify_chamber_runtime/receipt.json), **34/34**. |
| Room | [17:06](../../implementation/20261005T170600-verify_full_room/receipt.json), **28/28**. Floor trace still hits `TE_ArenaFloor` at Z −5. |

Map `616822f1d349a710ddbb8ced99babe8b0dbc95f69c41299f3f82d843faba117d`. Door mesh `792bc84b924faf519bda22bf5726f2e6581ef1a5e9126f4205e8cc08a236e56b`. Cutaway `678a4ff5cf56e1c190024c1847cecf3eca59d8f3cb47bbbc01c1fddba59d8c0a`. Settings `8821466ce8acdec9960ceec919b2f6a73ae000bc9fdfd5f441c59efe947645a8`.

## Still open

The bays are lit recesses, not the target's deep doorways. The overhead teal is stronger in the room and still thinner than the suspended column. Straight floor splits and quiet chunks were left as recovered. Exact visual parity and user acceptance are open. This pass has no new motion picture. The 16:40 boss-defeat movie is the floor-recovery take.
