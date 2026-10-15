# Velxio wired bench prototype

Open Pothole_Rover_Wired.vlx using Velxio's Import / Open project command. Save your existing workspace first. This is a native multi-board Velxio project, not a Wokwi single-board project.

## Included
- Raspberry Pi 3B coordinator, classic ESP32 DevKit V1, Arduino Uno R3.
- 58 connections: shared ground; Pi pins 8/10 crossed to ESP32 RX2/TX2; request/acknowledgement signals to Uno; 3 voltage dividers; front and downward HC-SR04; I2C OLED; servo; stop button; battery-simulation potentiometer.
- Regulated 5 V load supply; L293D model; four 47-ohm winding loads.
- Starter code grouped under the correct board. Motors stay OFF. Pi sends STATUS only. The ESP32 samples sensors and checks OLED I2C address 0x3c; it does not draw an OLED dashboard. Uno opens/closes its servo gate when the repair-request input is asserted.

## Motor-model limitation
The inspected public Velxio catalog lists an L293D driver, but no stock L298N module or rotating DC motor part. The L293D is a simulation substitute. The four 47-ohm resistors represent test winding loads; they are not rotating wheels or a mechanical robot model. Current published catalog/renderer support must still be checked in Velxio. Your eventual physical L298N module has a different pinout; do not copy L293D pin labels onto it.

## Pin map
Pi physical 6 -> ESP GND -> Uno GND.
Pi physical 8 (GPIO14/TX) -> ESP RX2/GPIO16.
ESP TX2/GPIO17 -> Pi physical 10 (GPIO15/RX).
ESP GPIO23 -> Uno D2, with a 10k pull-down to GND.
Uno D3 -> 1k -> junction -> ESP GPIO33; junction -> 2k -> GND.
Uno D9 -> servo PWM. Servo V+ -> external regulated 5 V; GND shared.
Front HC-SR04 TRIG -> ESP4; ECHO -> divider -> ESP34.
Downward HC-SR04 TRIG -> ESP13; ECHO -> divider -> ESP35.
Each echo divider is ECHO -> 1k -> junction -> ESP input; junction -> 2k -> GND.
OLED VCC -> ESP3V3, GND -> GND, SDA -> ESP21, SCL -> ESP22.
Stop switch -> ESP32/GND; firmware uses INPUT_PULLUP.
Battery-simulation pot: VCC -> ESP3V3, GND -> GND, SIG -> VP/GPIO36.
Motor control: ESP25 -> EN1; ESP26 -> IN1; ESP27 -> IN2; ESP14 -> EN2; ESP18 -> IN3; ESP19 -> IN4.
Driver VCC1 and VCC2 -> regulated 5 V test supply; all four driver ground pins -> common GND.
Four winding loads: left pair across OUT1/OUT2, right pair across OUT3/OUT4.
The breadboard is included as an optional spare; current connections run directly between parts.

## Running
1. Import the .vlx file.
2. Start/compile the Uno and ESP32 boards, then run the Pi Python script.
3. Read STATUS replies from the Pi. The starter never commands motion.
4. The repair controller accepts a REPAIR line through the wired UART, closes the gate after 2 seconds and reports completion through the acknowledgement wire. The supplied Pi script does not send REPAIR automatically.
5. Select the ESP32 code group for the I2C-detection result at startup. There is no camera or vision emulation in this bench project.

Placing/wiring Pi boards does not prove the account can execute their Python code. Velxio's own Pi execution/trial restrictions still apply.

## Verification
Native .vlx outer structure, board kinds, all 20 component metadata IDs, 58 endpoint references, code-group ownership and divider values were checked against Velxio's public source. Full visual import, firmware compilation and simultaneous three-board execution have not been verified. Browser control was unavailable; the existing open editor was not modified.

Source format reference:
https://github.com/davidmonterocrespo24/velxio/blob/master/frontend/src/utils/vlxFile.ts
