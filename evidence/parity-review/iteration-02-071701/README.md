# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T071701-capture_parity_look\01-matched-gameplay.png`

Framing declared **matched**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 35.91 | [36.5779, 52.4381, 49.1935] | [25.5312, 39.0182, 35.6125] |
| player_body | 53.46 | 55.19 | [38.1664, 57.4, 59.52] | [37.3511, 59.8927, 61.17] |
| player_pool | 219.44 | 217.08 | [213.3316, 220.6666, 225.2371] | [212.4368, 218.2545, 219.1769] |
| pool_surround | 109.12 | 87.49 | [84.6181, 115.5032, 118.0389] | [57.957, 95.112, 98.8862] |
| boss_shadow | 25.82 | 18.89 | [12.3669, 29.4047, 29.9048] | [11.8963, 20.6957, 21.5602] |
| shadow_surround | 129.28 | 109.14 | [96.3685, 138.3482, 136.3448] | [75.8584, 117.7381, 121.9836] |
| cloth_detail | 48.65 | 37.93 | [43.8042, 50.5866, 43.6721] | [33.1268, 40.1578, 30.0364] |
| floor_detail | 88.93 | 70.80 | [61.1805, 96.5745, 94.8922] | [44.7213, 77.52, 81.0484] |
| far_haze | 78.61 | 33.47 | [41.1981, 88.7439, 88.3233] | [10.9411, 39.3627, 41.4999] |
| central_floor | 117.28 | 103.14 | [83.08, 126.6076, 125.5852] | [70.2046, 111.652, 115.8624] |
| left_debris | 47.94 | 85.10 | [30.0047, 52.8852, 51.7256] | [54.4489, 93.0218, 96.9182] |
| dark_perimeter | 23.93 | 24.07 | [12.9043, 26.9115, 26.8352] | [11.3298, 27.3653, 28.9054] |
| dark_corners | 0.53 | 10.59 | [0.1784, 0.6285, 0.657] | [5.2124, 11.9674, 12.7986] |
| whole_image | 57.36 | 49.02 | [35.826, 63.2332, 62.6539] | [30.0739, 53.923, 56.2199] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"player_pool_over_pool_surround": 2.4814, "boss_shadow_over_shadow_surround": 0.1731, "central_floor_over_dark_perimeter": 4.2856, "far_haze_over_dark_perimeter": 1.3909}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
