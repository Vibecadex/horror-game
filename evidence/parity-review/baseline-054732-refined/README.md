# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T054732-capture_room_gallery\01-gameplay-initial.png`

Framing declared **approximate**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 57.48 | [36.5779, 52.4381, 49.1935] | [42.7982, 61.2647, 63.2777] |
| player_body | 53.46 | 33.01 | [38.1664, 57.4, 59.52] | [16.1167, 37.1943, 41.3291] |
| pool_surround | 109.12 | 26.74 | [84.6181, 115.5032, 118.0389] | [6.7614, 31.6178, 37.3065] |
| boss_shadow | 25.82 | 13.05 | [12.3669, 29.4047, 29.9048] | [3.9193, 15.2085, 18.5012] |
| shadow_surround | 129.28 | 35.47 | [96.3685, 138.3482, 136.3448] | [11.3742, 41.3443, 48.1743] |
| cloth_detail | 48.65 | 100.59 | [43.8042, 50.5866, 43.6721] | [82.7024, 105.3606, 105.9408] |
| floor_detail | 88.93 | 36.46 | [61.1805, 96.5745, 94.8922] | [11.1199, 42.7407, 48.8522] |
| far_haze | 78.61 | 24.32 | [41.1981, 88.7439, 88.3233] | [7.9827, 28.2815, 33.225] |
| central_floor | 117.28 | 31.60 | [83.08, 126.6076, 125.5852] | [9.807, 36.8792, 43.5093] |
| left_debris | 47.94 | 32.86 | [30.0047, 52.8852, 51.7256] | [11.1053, 38.2856, 43.1863] |
| dark_perimeter | 23.93 | 18.24 | [12.9043, 26.9115, 26.8352] | [5.3403, 21.3858, 25.0404] |
| dark_corners | 0.53 | 12.33 | [0.1784, 0.6285, 0.657] | [3.5474, 14.459, 17.1647] |
| whole_image | 57.36 | 24.88 | [35.826, 63.2332, 62.6539] | [8.3173, 28.9294, 33.561] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"boss_shadow_over_shadow_surround": 0.3679, "central_floor_over_dark_perimeter": 1.7327, "far_haze_over_dark_perimeter": 1.3336}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
