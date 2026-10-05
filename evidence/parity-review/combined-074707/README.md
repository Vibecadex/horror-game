# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T074707-capture_parity_look\01-matched-gameplay.png`

Framing declared **matched**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 50.87 | [36.5779, 52.4381, 49.1935] | [43.7485, 53.387, 46.8765] |
| player_body | 53.46 | 62.81 | [38.1664, 57.4, 59.52] | [43.1691, 68.0273, 68.9981] |
| player_pool | 219.44 | 211.60 | [213.3316, 220.6666, 225.2371] | [205.0357, 213.3175, 213.9688] |
| pool_surround | 109.12 | 108.53 | [84.6181, 115.5032, 118.0389] | [75.3314, 117.1825, 120.5943] |
| boss_shadow | 25.82 | 21.44 | [12.3669, 29.4047, 29.9048] | [14.0702, 23.3617, 24.0543] |
| shadow_surround | 129.28 | 127.40 | [96.3685, 138.3482, 136.3448] | [91.9941, 136.6277, 140.219] |
| cloth_detail | 48.65 | 69.91 | [43.8042, 50.5866, 43.6721] | [70.4306, 71.2854, 54.7157] |
| floor_detail | 88.93 | 100.23 | [61.1805, 96.5745, 94.8922] | [68.7039, 108.4371, 111.7228] |
| far_haze | 78.61 | 35.99 | [41.1981, 88.7439, 88.3233] | [12.5913, 42.1204, 44.1508] |
| central_floor | 117.28 | 126.64 | [83.08, 126.6076, 125.5852] | [91.5724, 135.7976, 139.2248] |
| left_debris | 47.94 | 69.48 | [30.0047, 52.8852, 51.7256] | [44.2074, 76.0823, 78.5347] |
| dark_perimeter | 23.93 | 27.47 | [12.9043, 26.9115, 26.8352] | [13.6384, 31.0724, 32.4604] |
| dark_corners | 0.53 | 10.12 | [0.1784, 0.6285, 0.657] | [5.0453, 11.4351, 12.0201] |
| whole_image | 57.36 | 58.10 | [35.826, 63.2332, 62.6539] | [37.8166, 63.4136, 65.2461] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"player_pool_over_pool_surround": 1.9497, "boss_shadow_over_shadow_surround": 0.1683, "central_floor_over_dark_perimeter": 4.6109, "far_haze_over_dark_perimeter": 1.3103}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
