# Design session notes - Oct 17, 2026

Decisions
- Dropped the Raspberry Pi from the boxes; all boxes identical, dashboard lives on the server.
- Returned the Waveshare ESP32-S3-Relay-6CH (no Ethernet, no DI). Boxes use the ESP32-S3-POE-ETH-8DI-8RO,
  PoE-powered from the switch (Amazon ~$65.27). The RP2350 variant shown in an old render is NOT used.
- Sensors moved off the reader's GPIO onto the relay board's inputs so all logic is in C# and visible on the
  dashboard. Truck sensor = DIHOOL M16 laser (NPN NO) -> DI1. Beam = JUTAI IRR-7M (dry contact) -> DI2 / DGND.
- Truck sensor is NO on purpose: a cut wire reads "no truck" -> red (safe).
- Added TB1 (12 V distribution), PSU2 (48 V for the switch), F1 (AC fuse) and the C4 uplink gland.
- Gland map: G1 AC in, G2 beam B2, G3 truck sensor B1, G4 network uplink, G5 stack lights.
- Wire numbers: 101-103 AC, 201/202 12 V, 203 48 V, 301-304 stack light, 401-403 sensors, C1-C5 Ethernet/PoE, A1-A4 coax.
- Dashboard plan: ASP.NET Core + SignalR page on the C# service; Grafana optional for history.

Open items
- Price and source F1 and the C4 Cat6 run. Run the uplink to each door.
- Confirm K1 terminal order + DGND wiring, ETH reset pin, PoE class.
- Confirm GoodTop total PoE budget covers SPL1 (reader, up to 25.5 W) + K1.
- Reader may need 3 A at 12 V at full RF; if the splitter browns out, feed U1 from TB1 and use SPL1 for data only.
- Splitter plug is 5.5x2.5 mm; check the reader jack (often 5.5x2.1).
- B2 model: IRR-7M ordered, IRR-7R in photos.

# Session - Oct 28, 2026 (board arriving)

Done
- Firmware 1.1.0: settings moved to `config.h`; buzzer on CH4 (`buzzer/set` on/beep/chirp, 30 s cap);
  S1 lamp on CH5 (`pilot/set`); `<color>_blink` lights; `/info` adds fw, MAC, relay_ok, failsafe_reason;
  fail-safe also on `dock/server/status` = offline; task watchdog; relay expander re-written every 1 s;
  on-board RGB status LED. Compiles clean on esp32 core 3.3.12 (44 % flash). Not yet run on hardware.
- Pins checked against a Tasmota user's logs for this board: I2C SDA 42 / SCL 41, TCA9554 @0x20, SPI SCK 15 /
  MOSI 13 / MISO 14, WS2812 on 38. W5500 CS 16 / INT 12 / RST 39 and DI GPIO 4-11 still from the wiki.
- Wiring diagram rev 9 (proposed), 5 sheets, and control concept images (CS1 station, storyboard, dashboard).

Proposed for rev 9 (approve before marking up the DXF): TB0 AC terminals + PE stud, TB1 to 14 positions with
fused F2-F4, TB2 lamp marshalling, own gland G6 for HL2, CS1 operator station on G7, wire 204 for 48 V return.

Open items (new)
- DI wiring polarity on the real board (W3 "Option B" if dry contacts to DGND don't switch).
- Stack-light common polarity and lead colors (W2 notes).
- C# service: add LWT `dock/server/status`, buzzer/pilot handling, maint/release/ack logic (MQTT_CONTRACT.md).
- Price CS1 parts, TB0/TB2 terminals, fuses, G6/G7 glands.

Reader GPI1 trigger (added same day, from the M-808EK sheet)
- U1 GPIO block (3.81 mm × 12): 1 VOUT, 2/3 RS485, 4 GND, 5-8 GPO, 9/10 GPI2−/+, 11/12 GPI1−/+.
- Pin 12 GPI1+ gets +12 V all the time from TB1-6 (new fused terminal F5, 0.5 A), wire 416.
- Pin 11 GPI1− sinks to TB1 0 V when the beam trips, wire 415. B2 has one relay contact, so it is split with two
  diodes on TB3 (D1 → K1 DI2, D2 → GPI1−, cathodes on B2 NO). Without them the open contact puts both input
  LEDs in series across 12 V and either input can false-trigger.
- To verify: GPI input voltage range (sheet doesn't say; 12 V is common, meter ≤ 20 mA), reader trigger
  mode settings, and that K1 DI2 still reads through D1's 0.7 V drop.
