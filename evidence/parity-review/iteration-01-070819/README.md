# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T070819-capture_room_gallery\01-gameplay-initial.png`

Framing declared **approximate**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 88.89 | [36.5779, 52.4381, 49.1935] | [71.2259, 95.1314, 79.0319] |
| player_body | 53.46 | 141.86 | [38.1664, 57.4, 59.52] | [122.9723, 147.571, 140.8924] |
| player_pool | 219.44 | 218.32 | [213.3316, 220.6666, 225.2371] | [211.9108, 220.1415, 219.1761] |
| pool_surround | 109.12 | 171.28 | [84.6181, 115.5032, 118.0389] | [142.3213, 179.8494, 171.6148] |
| boss_shadow | 25.82 | 27.65 | [12.3669, 29.4047, 29.9048] | [19.7447, 30.0446, 27.2033] |
| shadow_surround | 129.28 | 183.48 | [96.3685, 138.3482, 136.3448] | [156.5566, 191.4619, 183.6948] |
| cloth_detail | 48.65 | 69.68 | [43.8042, 50.5866, 43.6721] | [56.0586, 75.2765, 54.3737] |
| floor_detail | 88.93 | 156.13 | [61.1805, 96.5745, 94.8922] | [123.8159, 165.7405, 156.0967] |
| far_haze | 78.61 | 80.39 | [41.1981, 88.7439, 88.3233] | [44.3813, 91.065, 80.6195] |
| central_floor | 117.28 | 194.21 | [83.08, 126.6076, 125.5852] | [169.372, 201.5675, 194.5145] |
| dark_perimeter | 23.93 | 81.90 | [12.9043, 26.9115, 26.8352] | [53.6501, 90.2891, 82.0135] |
| dark_corners | 0.53 | 61.28 | [0.1784, 0.6285, 0.657] | [40.6383, 67.4124, 61.2831] |
| whole_image | 57.36 | 119.57 | [35.826, 63.2332, 62.6539] | [92.4127, 127.6765, 119.2671] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"player_pool_over_pool_surround": 1.2747, "boss_shadow_over_shadow_surround": 0.1507, "central_floor_over_dark_perimeter": 2.3713, "far_haze_over_dark_perimeter": 0.9815}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
