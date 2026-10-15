# Pothole Rover — Webots R2025a

A Python-controlled, four-wheel skid-steer rover on a supervised closed test course.
This is a simulation project, not public-road software or verified hardware firmware.

## Open on Windows

1. Install **Webots R2025a**: https://cyberbotics.com/#download
2. Install 64-bit **Python 3.11 or 3.12** from https://www.python.org/downloads/windows/ . Enable Add Python to PATH. No pip packages are needed.
3. Extract the entire ZIP to a writable folder such as `Documents\PotholeRover`. Do not run inside the ZIP.
4. Double-click **START_ROVER.bat**. It locates common Webots installations or offers a file picker. Alternatively, open Webots and choose File → Open World → `worlds/closed_course.wbt`.
5. In Webots Tools → Preferences → General, set the Python command to your installed `python.exe` if the controller fails to start. Use Python 3.12 if a newer Python version fails; this project was tested with Python 3.12.
6. Press Play (real-time) or Fast. Four camera overlays can be enabled by double-clicking the camera devices in the scene tree; the browser dashboard also shows all four images.
7. Double-click **OPEN_DASHBOARD.bat** or visit **http://127.0.0.1:8765** after the controller starts. Only run one copy; otherwise dashboard port 8765 conflicts.
8. With the Webots 3D view focused, press **Space** or **E** to latch an emergency stop; press **R** to request return to dock when not dispensing.
9. Reset the complete world between scenarios, using Reload World (Ctrl+Shift+R), so fill patches and controller state are reset together. Merely pausing/resuming does not reset the mission.

A first-run Webots firewall prompt may appear. Dashboard binds to localhost only.
If the dashboard is blank, read the Webots console for Python/controller errors and check that simulation time is advancing.

## What runs

- 40 cm chassis; four independently motorized 65 mm radius wheels, encoders and physical joint dynamics. Outer width about 32.5 cm.
- Front/rear/left/right 160×120 RGB cameras, 100° horizontal fields of view, overlapping adjacent views, 128 ms sampling. These cover horizontal bearings, not every nearby point: occlusion and near-field blind areas remain.
- Webots `Recognition` detections are fused into four directional clearance values. These are simulator-assisted labelled-object detections, **not** a trained neural detector or stitched panoramic image. Only tagged course obstacles are recognized by the cameras; supplemental depth scanlines also measure untagged solid surfaces. No claim of detecting arbitrary real people/vehicles is made.
- Downward 32×24 depth image at 64 ms sampling, 1 mm configured noise, 1.5–40 cm range. Median center patch rejects isolated bad samples. An attitude-compensated comparison against expected flat-road depth suppresses body-height changes; turning and excessive tilt inhibit scanning. A pass over both depth edges estimates the depression midpoint, then the rover aligns its center nozzle over the estimate.
- Two actual 25×25 cm, 4 cm deep road depressions; no painted fake potholes. Wheel track straddles these small depressions. Larger holes, slopes and irregular terrain are outside this test.
- Low-speed waypoint navigation (default 0.13 m/s), GPS position and IMU heading with configured noise. Coordinates are simulated metres in an ENU frame. GPS is a deliberate simulation localization aid, not a solution for indoor hardware localization.
- A moving 1.6 m upright pedestrian proxy and a moving vehicle proxy; both are kinematic collision solids, with no human behavior model. The robot waits at obstacles and faults if blocked for 30 seconds; there is no local detour planner.
- Protective stops consider all four directions when turning; forward sector during forward motion. Stops include reaction and braking margins. A front contact bumper and invalid-sensor conditions latch a fault. This is a test safety model, not a certified collision-avoidance system. No reverse motion is commanded. Four horizontal depth scanlines supplement recognition for actual surface clearance, including road barriers.
- Repairs are an idealized timed dispensing event, followed by a request to the environment supervisor. The supervisor checks alignment and near-zero speed, then inserts a collidable patch at road height and acknowledges it. Repair logs are committed only after acknowledgement. It does not simulate granular flow, compaction, curing, strength or material transport mass.
- Return to dock after route completion or simulated battery below 30%; low-speed final position and yaw alignment (4 cm acquisition, 10 cm drift tolerance during rotation), then simulated charging. The dock is a marked pad; no electrical contacts or mechanical latch are modeled.
- Battery is an elapsed-time abstraction (600 seconds from full to empty), independent of current draw/payload. Wheel faults are diagnosed from commanded speed versus measured encoder motion over 1.2 seconds. A real slipping wheel or encoder fault needs more diagnostics.
- Dashboard status, camera images, pothole positions and acknowledged repairs. Latest telemetry, images, and a one-second `telemetry.jsonl` history are in `logs/`. No cloud service is used.

## Configuration and faults

Edit `config.json` while stopped, then reload the world.

| `scenario` | Behavior |
|---|---|
| `nominal` | Complete route, detect and repair selected discoveries, return to dock |
| `camera_dropout` | Camera health becomes invalid after `fault_at`; latched stop |
| `motor_failure` | Front-left motor is held at zero after `fault_at`; encoder mismatch should latch a stop |
| `low_battery` | Battery drops to 20% after `fault_at`; return and align to dock |

`fault_at` is simulation seconds. `selected_potholes` uses **discovery IDs** P1/P2, not supervisor scene names. Detection order can differ if the route is changed. Use `[]` for survey-only operation. Route points, dock pose, sampling periods, speed and battery model can be edited in the same file. Webots sensor periods should be multiples of the world's 32 ms timestep.

Sensor faults and contact faults need a full reload to clear. Exceptions immediately command all motors to zero. A physical ESP32 must independently enforce a heartbeat timeout; Python exception handling alone is not a hardware safety circuit.

## Software map

```
worlds/closed_course.wbt       Road, dock, rover and dynamic obstacles
protos/Rover.proto             Physical four-wheel robot and sensors
controllers/rover/core.py      Navigation/mission state machine; no Webots imports
controllers/rover/hardware.py  Webots sensor/motor adapter
controllers/rover/dashboard.py Local read-only HTTP dashboard
controllers/rover/rover.py     Composition, stepping, telemetry and safe shutdown
controllers/course/course.py  Environment actor motion and repair physics changes
config.json                   Route and selectable fault injection
tests/test_core.py            Portable behavior tests and kinematic mission test
```

Run `RUN_TESTS.bat` or `python -m unittest discover -s tests -v`. The kinematic mission test is separate from full Webots physics testing. See `VALIDATION.md` for actual verification results and limits.

## Eventual boards and ₹15,000 limit

The simulation runs on the Windows PC. It does not run Webots on the Pi.
A future adapter could send velocity commands/telemetry over a heartbeat-protected serial link: Pi Zero 2 W → ESP32 wheel controller; Pi → Uno dispensing controller. Those transports and board firmware are **not implemented or hardware-tested** here. Four camera streams plus recognition may exceed Pi Zero 2 W performance; Webots assisted recognition has no direct hardware equivalent.

Do not purchase four cameras based on this simulation. The physical ₹15,000 cap needs a separately verified bill of materials, including camera interfaces, power supply, motor current, chassis, depth sensing, battery protection and repair payload. No live supplier prices or hardware performance are claimed. A single movable camera or reduced-resolution sequential processing may be necessary, but would change simultaneous awareness.

## Reference APIs

- https://cyberbotics.com/doc/reference/camera
- https://cyberbotics.com/doc/reference/rangefinder
- https://cyberbotics.com/doc/reference/motor
- https://cyberbotics.com/doc/reference/supervisor

Project controllers use Python's standard library and the Webots controller API supplied with Webots.

## Recorded run

Double-click VIEW_REPLAY.bat to serve the included Webots 3D animation in a browser. It is a recording, not a live simulation; Webots web-view assets require internet access. Raw recorded telemetry and four camera snapshots are in evidence/. ChatGPT browser access to the live local server was retried and returned ERR_CONNECTION_REFUSED.
