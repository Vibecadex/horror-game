# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T085410-capture_parity_room\01-matched-gameplay.png`

Framing declared **matched**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 56.49 | [36.5779, 52.4381, 49.1935] | [47.5926, 59.5416, 52.406] |
| player_body | 53.46 | 64.76 | [38.1664, 57.4, 59.52] | [43.4741, 70.4387, 71.1992] |
| player_pool | 219.44 | 210.01 | [213.3316, 220.6666, 225.2371] | [202.9725, 211.8537, 212.4953] |
| pool_surround | 109.12 | 108.56 | [84.6181, 115.5032, 118.0389] | [74.3914, 117.5029, 120.5362] |
| boss_shadow | 25.82 | 26.56 | [12.3669, 29.4047, 29.9048] | [15.6376, 29.4796, 29.8596] |
| shadow_surround | 129.28 | 132.82 | [96.3685, 138.3482, 136.3448] | [95.6117, 142.6042, 145.4592] |
| cloth_detail | 48.65 | 72.29 | [43.8042, 50.5866, 43.6721] | [72.6848, 73.7709, 56.5102] |
| floor_detail | 88.93 | 91.91 | [61.1805, 96.5745, 94.8922] | [61.2791, 99.9124, 102.798] |
| far_haze | 78.61 | 67.26 | [41.1981, 88.7439, 88.3233] | [33.1356, 76.5677, 75.6096] |
| central_floor | 117.28 | 131.89 | [83.08, 126.6076, 125.5852] | [94.9857, 141.613, 144.227] |
| left_debris | 47.94 | 70.46 | [30.0047, 52.8852, 51.7256] | [43.7806, 77.4748, 79.5162] |
| dark_perimeter | 23.93 | 30.33 | [12.9043, 26.9115, 26.8352] | [14.5301, 34.5664, 34.9156] |
| dark_corners | 0.53 | 9.54 | [0.1784, 0.6285, 0.657] | [3.497, 11.1462, 11.3635] |
| whole_image | 57.36 | 63.91 | [35.826, 63.2332, 62.6539] | [40.5918, 70.1247, 71.0733] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"player_pool_over_pool_surround": 1.9346, "boss_shadow_over_shadow_surround": 0.2, "central_floor_over_dark_perimeter": 4.3482, "far_haze_over_dark_perimeter": 2.2176}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
