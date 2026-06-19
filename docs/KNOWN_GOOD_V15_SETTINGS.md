# Known-good v15 settings

Date: 2026-06-20

Status: manually verified by the user as stable and visually correct.

## Runtime result

The uploaded runtime log shows a clean session: config loaded, camera started, virtual camera started, camera switches completed, virtual camera restarted several times, and resources released on exit. No traceback or ERROR entries were observed in the inspected log tail.

## Core window and virtual camera settings

| Parameter | Value |
|---|---:|
| window shape | circle |
| window size | 360 |
| always on top | true |
| window mirror | true |
| virtual camera enabled | true |
| virtual camera mirror | false |
| virtual camera fit | letterbox |
| virtual camera mode | circle |
| edge feather | 20 |
| window opacity | 1.0 |

## Chroma key settings

| Parameter | Value |
|---|---:|
| enabled | true |
| mode | HSV + pipettes |
| HSV hue | 70..108 |
| HSV saturation | 0..58 |
| HSV value | 135..235 |
| feather | 15 |
| active pipettes | 3 |

## Dynamic crop settings

| Parameter | Value |
|---|---:|
| enabled | true |
| detector | mediapipe |
| tracking mode | eyes_ipd |
| auto zoom | true |
| zoom mode | auto |
| analysis scale | 25 |
| circle to head | 1.83 |
| crop padding | 1.16 |
| vertical offset | 0.10 |
| position smoothing | 0.73 |
| scale smoothing | 0.26 |
| position dead zone | 0.03 |
| scale dead zone | 0.08 |
| return speed | 0.85 |
| fast ROI tracking | true |
| face ROI margin | 2.8 |

## PTZ settings

PTZ is disabled in the known-good preset. Keep PTZ as optional hardware-dependent functionality.

## Hotkeys retained

| Action | Key |
|---|---|
| chroma toggle | K |
| chroma settings | Ctrl+K |
| virtual camera toggle | V |
| virtual camera mirror | B |
| window mirror | M |
| scale up | + / = |
| scale down | - |
| dynamic nudge | arrows |
| reset | 0 |
| quit | Ctrl+Q |

## Product decision

This preset is the baseline for production UX work. Future changes should preserve this visual/behavioral result and focus on making the interface self-explanatory rather than changing the working video pipeline.
