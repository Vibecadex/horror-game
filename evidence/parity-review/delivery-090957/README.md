# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T090957-capture_parity_delivery\01-matched-gameplay.png`

Framing declared **matched**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 56.83 | [36.5779, 52.4381, 49.1935] | [44.7621, 60.4941, 56.0336] |
| player_body | 53.46 | 65.23 | [38.1664, 57.4, 59.52] | [43.8127, 70.9468, 71.6925] |
| player_pool | 219.44 | 210.07 | [213.3316, 220.6666, 225.2371] | [203.0259, 211.9146, 212.5522] |
| pool_surround | 109.12 | 108.79 | [84.6181, 115.5032, 118.0389] | [74.5433, 117.7612, 120.7837] |
| boss_shadow | 25.82 | 26.77 | [12.3669, 29.4047, 29.9048] | [15.6468, 29.7378, 30.1573] |
| shadow_surround | 129.28 | 133.22 | [96.3685, 138.3482, 136.3448] | [95.9386, 143.0215, 145.8451] |
| cloth_detail | 48.65 | 72.37 | [43.8042, 50.5866, 43.6721] | [65.7086, 75.1814, 64.1768] |
| floor_detail | 88.93 | 92.09 | [61.1805, 96.5745, 94.8922] | [61.3981, 100.1151, 102.9891] |
| far_haze | 78.61 | 68.90 | [41.1981, 88.7439, 88.3233] | [34.2024, 78.3642, 77.3655] |
| central_floor | 117.28 | 132.34 | [83.08, 126.6076, 125.5852] | [95.3494, 142.0852, 144.6622] |
| left_debris | 47.94 | 70.73 | [30.0047, 52.8852, 51.7256] | [43.9423, 77.773, 79.8011] |
| dark_perimeter | 23.93 | 30.79 | [12.9043, 26.9115, 26.8352] | [14.7819, 35.0819, 35.421] |
| dark_corners | 0.53 | 9.69 | [0.1784, 0.6285, 0.657] | [3.5351, 11.3324, 11.5464] |
| whole_image | 57.36 | 64.39 | [35.826, 63.2332, 62.6539] | [40.8, 70.6637, 71.6671] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"player_pool_over_pool_surround": 1.931, "boss_shadow_over_shadow_surround": 0.201, "central_floor_over_dark_perimeter": 4.2979, "far_haze_over_dark_perimeter": 2.2378}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
