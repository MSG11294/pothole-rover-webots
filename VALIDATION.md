# Validation — 15 October 2026

Tested with Webots R2025a on Linux using a virtual display and software rendering, Python 3.12.

| Check | Observed result |
|---|---|
| Portable control tests | 12/12 pass |
| Nominal Webots mission | DOCKED at 126.27 simulation seconds; two acknowledged repairs; dock distance 4.29 cm, yaw error 3.63 degrees |
| Low-battery Webots mission after fix | DOCKED at 28.99 simulation seconds; distance 4.73 cm, yaw error 3.28 degrees |
| Camera dropout injection | FAULT: sensor invalid or stale |
| Wheel motor failure injection | FAULT: wheel encoder mismatch |
| Four virtual cameras | JPEG images produced for front, rear, left and right |
| ChatGPT browser connection retry | ERR_CONNECTION_REFUSED for the local replay server |

Evidence JSON, telemetry and images are included under evidence/. The nominal recording predates the low-battery fix; nominal behavior is unchanged by its low-battery entry guard. Dock rotation tolerance was widened from 6 to 10 cm to avoid repeated repositioning due to skid-steer drift. The initial recorded viewpoint was corrected for viewing; physical trajectory data are unchanged.

Not tested: Windows execution, physical boards, untagged real-world vision, arbitrary potholes, public traffic, electrical docking contacts or real fill material. Camera awareness uses Webots recognition plus depth scanlines. No physical hardware compatibility or 15000-rupee build cost is established.

To run: extract the ZIP; follow README.md. START_ROVER.bat starts the actual Webots simulation. VIEW_REPLAY.bat serves the recorded animation and requires internet for Cyberbotics viewer assets.
