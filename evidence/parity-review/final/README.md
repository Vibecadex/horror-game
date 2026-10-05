# Visual parity diagnostic evidence

Reference: `C:\Projects\to-deploy\horror-game\study\visuals\direction-close-best.jpg`
Candidate: `C:\Projects\to-deploy\horror-game\evidence\implementation\20261005T092659-capture_parity_delivery\01-matched-gameplay.png`

Framing declared **matched**. Capture kind **staged-gameplay**. Candidate regions were manually marked.

**Visual parity remains a separate human/art review. Artifact creation and numeric proximity cannot mark it passed.**

[Full comparison](comparison.jpg) · [Marked regions](regions.jpg) · [Detail crops](details.png) · [Fixed luminance map](luminance.png) · [Measurements and hashes](metrics.json)

Full images are shown side by side without cropping, exposure correction or image warping. Detail crops preserve aspect ratio and are labelled with their source bounds; crops are individually fit for inspection and do not demonstrate size parity.

| Region | Reference display luma | Candidate display luma | Reference mean RGB | Candidate mean RGB |
| --- | ---: | ---: | --- | --- |
| boss_body | 48.83 | 57.67 | [36.5779, 52.4381, 49.1935] | [45.1619, 61.455, 57.0215] |
| player_body | 53.46 | 65.48 | [38.1664, 57.4, 59.52] | [43.8573, 71.25, 71.9995] |
| player_pool | 219.44 | 210.13 | [213.3316, 220.6666, 225.2371] | [203.0484, 211.9779, 212.6167] |
| pool_surround | 109.12 | 109.28 | [84.6181, 115.5032, 118.0389] | [74.8718, 118.2959, 121.3073] |
| boss_shadow | 25.82 | 27.57 | [12.3669, 29.4047, 29.9048] | [15.9833, 30.6595, 31.0528] |
| shadow_surround | 129.28 | 134.07 | [96.3685, 138.3482, 136.3448] | [96.6188, 143.9295, 146.6739] |
| cloth_detail | 48.65 | 73.28 | [43.8042, 50.5866, 43.6721] | [66.3397, 76.162, 65.1887] |
| floor_detail | 88.93 | 92.39 | [61.1805, 96.5745, 94.8922] | [61.5808, 100.4532, 103.3062] |
| far_haze | 78.61 | 73.61 | [41.1981, 88.7439, 88.3233] | [37.3848, 83.4924, 82.4304] |
| central_floor | 117.28 | 133.30 | [83.08, 126.6076, 125.5852] | [96.1334, 143.1085, 145.614] |
| left_debris | 47.94 | 71.28 | [30.0047, 52.8852, 51.7256] | [44.2546, 78.3988, 80.4035] |
| dark_perimeter | 23.93 | 32.19 | [12.9043, 26.9115, 26.8352] | [15.5961, 36.6445, 36.9632] |
| dark_corners | 0.53 | 10.16 | [0.1784, 0.6285, 0.657] | [3.6637, 11.9012, 12.1034] |
| whole_image | 57.36 | 65.69 | [35.826, 63.2332, 62.6539] | [41.615, 72.1048, 73.0734] |

Display luma is the weighted sRGB value on a 0–255 scale. This describes the delivered image, not physical lighting units. Linear luminance, percentiles, dark/bright coverage and 2 px detail residuals are separately recorded in the JSON. No SSIM, pixel error or image-wide acceptance score is used.

Reference light-pool, shadow and haze ratios: `{"player_pool_over_pool_surround": 2.011, "boss_shadow_over_shadow_surround": 0.1997, "central_floor_over_dark_perimeter": 4.9014, "far_haze_over_dark_perimeter": 3.2851}`
Candidate ratios: `{"player_pool_over_pool_surround": 1.9228, "boss_shadow_over_shadow_surround": 0.2056, "central_floor_over_dark_perimeter": 4.1408, "far_haze_over_dark_perimeter": 2.2866}`

Use `study/PARITY_QA.md` for the independent seven-axis review and motion/regression requirements. Any architectural or incorrectly framed view remains supplementary evidence.
