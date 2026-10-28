# RFID Panel Box — Claude Code handoff

You are picking up firmware work for Gielow Pickles' dock-door RFID panel boxes.
Read `README.md` first, then `docs/MQTT_CONTRACT.md`, then `firmware/rfid_panel_box/rfid_panel_box.ino`.

## What to do (in order)

1. **Toolchain.** Arduino IDE 2.x (or arduino-cli). Install:
   - Board package: `esp32` by Espressif Systems, **3.x** (the W5500 Ethernet path in `ETH.h`
     needs 3.x; the 2.0.12 core from Waveshare's older docs will NOT compile this sketch).
   - Library: `PubSubClient` 2.8.
   - Board: ESP32S3 Dev Module. Enable `USB CDC On Boot` so Serial works over the USB-C port.
2. **Verify pins against the real board.** The sketch uses the pin map from the Waveshare wiki
   (https://www.waveshare.com/wiki/ESP32-S3-ETH-8DI-8RO): W5500 on MOSI 13 / MISO 14 / SCLK 15 / CS 16 / INT 12,
   relays via TCA9554 on I2C SDA 42 / SCL 41 (addr 0x20), DI1-DI8 on GPIO 4-11. Compare with Waveshare's own
   demo sketch for this board and fix anything that differs. ETH_RST (39) is a guess - confirm.
3. **Compile, flash, bench test** (README "Bench test"). Fix whatever doesn't work. Keep the fail-safe
   behaviour (red on boot, red after 10 s without MQTT) - that is a safety feature, not a bug.
4. **Make per-door config easy**: `DOOR_ID`, broker IP, optional static IP at the top of the sketch is fine,
   or move them to a `config.h`. Don't add Wi-Fi; the boxes are wired (Ethernet + PoE).
5. **After it works:** drive the buzzer on CH4 (`dock/doorXX/buzzer/set`), publish firmware version + MAC
   in `/info`. OTA is not required.

## Hard rules
- The box is "dumb": it reports inputs and shows the light it is told to. Door logic lives in the C# service.
- Exactly one light on at a time (red / yellow / green) - never two.
- Never publish `light/set` as a retained message; never leave green on without the server.
- The board is PoE-powered. Leave the 7-36 V input alone in docs and wiring.
- US units in notes; short comments.
