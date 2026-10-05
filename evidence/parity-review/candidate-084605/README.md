# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T084605-capture_parity_room\01-matched-gameplay.png`

Framing declared **matched**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 56.16 | [36.5779, 52.4381, 49.1935] | [47.333, 59.1951, 52.1424] |
| player_body | 53.46 | 62.71 | [38.1664, 57.4, 59.52] | [42.3333, 68.1427, 68.9497] |
| player_pool | 219.44 | 209.23 | [213.3316, 220.6666, 225.2371] | [202.2208, 211.0549, 211.7431] |
| pool_surround | 109.12 | 105.74 | [84.6181, 115.5032, 118.0389] | [72.3759, 114.465, 117.6044] |
| boss_shadow | 25.82 | 25.58 | [12.3669, 29.4047, 29.9048] | [15.1427, 28.352, 28.8106] |
| shadow_surround | 129.28 | 129.15 | [96.3685, 138.3482, 136.3448] | [92.6505, 138.7238, 141.825] |
| cloth_detail | 48.65 | 72.12 | [43.8042, 50.5866, 43.6721] | [72.5097, 73.585, 56.4289] |
| floor_detail | 88.93 | 89.63 | [61.1805, 96.5745, 94.8922] | [59.7583, 97.4207, 100.4001] |
| far_haze | 78.61 | 106.53 | [41.1981, 88.7439, 88.3233] | [62.1535, 118.6397, 117.1879] |
| central_floor | 117.28 | 128.99 | [83.08, 126.6076, 125.5852] | [92.5626, 138.5676, 141.3544] |
| left_debris | 47.94 | 68.01 | [30.0047, 52.8852, 51.7256] | [42.2891, 74.7585, 76.8937] |
| dark_perimeter | 23.93 | 47.34 | [12.9043, 26.9115, 26.8352] | [26.7133, 52.8944, 53.0729] |
| dark_corners | 0.53 | 17.02 | [0.1784, 0.6285, 0.657] | [6.4103, 19.8747, 19.9832] |
| whole_image | 57.36 | 69.82 | [35.826, 63.2332, 62.6539] | [44.6146, 76.5392, 77.4381] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"player_pool_over_pool_surround": 1.9786, "boss_shadow_over_shadow_surround": 0.198, "central_floor_over_dark_perimeter": 2.7246, "far_haze_over_dark_perimeter": 2.2502}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
